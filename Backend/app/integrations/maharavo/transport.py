"""Bounded async HTTP primitives, without inventing a Maharavo wire protocol."""
import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import logging
import math
import random
import re
import time
from urllib.parse import unquote, urlsplit
from uuid import UUID
import httpx
from .binding import WireRequest
from .config import MaharavoSettings
from .errors import (MaharavoProtocolError, MaharavoLimitError, MaharavoTimeout,
                     MaharavoUnavailable, MaharavoCredentialsError, MaharavoNotConfigured)
from .limits import RequestLimiter

logger = logging.getLogger(__name__)


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('Non-finite JSON constant')


class AsyncHTTPTransport:
    def __init__(self, settings: MaharavoSettings, *, http_client=None, sleep=asyncio.sleep, limiter=None):
        self.settings = settings
        self.http_client = http_client
        self.owns_client = http_client is None
        self.sleep = sleep
        self.limiter = limiter or RequestLimiter(settings.requests_per_minute, sleep=sleep)
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

    def _client(self):
        if self.http_client is None:
            timeout = httpx.Timeout(connect=self.settings.connect_timeout, read=self.settings.read_timeout,
                                    write=self.settings.write_timeout, pool=self.settings.pool_timeout)
            self.http_client = httpx.AsyncClient(timeout=timeout, follow_redirects=False, trust_env=False,
                limits=httpx.Limits(max_connections=self.settings.max_concurrent_requests,
                                   max_keepalive_connections=self.settings.max_concurrent_requests))
        return self.http_client

    async def aclose(self):
        if self.owns_client and self.http_client is not None:
            await self.http_client.aclose()

    def _wire(self, wire, task_id):
        if not self.settings.enabled or not self.settings.base_url:
            raise MaharavoNotConfigured()
        if wire.method not in {'GET', 'POST'}:
            raise MaharavoProtocolError('Méthode HTTP non autorisée pour le transport IA.')
        decoded = unquote(unquote(wire.path))
        parts = urlsplit(decoded)
        if (not decoded.startswith('/') or decoded.startswith('//') or '\\' in decoded
            or parts.scheme or parts.netloc or parts.query or parts.fragment or any(item in {'.', '..'} for item in parts.path.split('/'))):
            raise MaharavoProtocolError('Chemin de transport IA non autorisé.')
        headers = dict(wire.headers)
        forbidden = {'host', 'content-length', 'transfer-encoding', 'cookie', 'proxy-authorization'}
        if any(key.lower() in forbidden or not re.fullmatch(r'[A-Za-z0-9_-]+', key)
               or '\r' in value or '\n' in value for key, value in headers.items()):
            raise MaharavoProtocolError('En-têtes de transport IA non autorisés.')
        if wire.idempotency_header:
            header = wire.idempotency_header
            if not re.fullmatch(r'[A-Za-z0-9_-]+', header) or header.lower() in forbidden | {key.lower() for key in headers}:
                raise MaharavoProtocolError('Contrat d’idempotence invalide.')
            headers[header] = str(task_id)
        headers.update({'Accept': 'application/json', 'Accept-Encoding': 'identity', 'Content-Type': 'application/json'})
        try:
            body = json.dumps(wire.payload, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode() if wire.payload is not None else None
        except (ValueError, TypeError):
            raise MaharavoProtocolError('Corps HTTP IA non sérialisable.') from None
        if body and len(body) > self.settings.max_request_bytes:
            raise MaharavoLimitError('La requête IA dépasse la taille autorisée.')
        url = self.settings.base_url.rstrip('/') + '/' + wire.path.lstrip('/')
        return url, headers, body

    def _delay(self, response, attempt):
        delay = min(self.settings.max_backoff_seconds, self.settings.backoff_seconds * 2 ** (attempt - 1))
        if response is not None and response.headers.get('retry-after'):
            value = response.headers['retry-after']
            try:
                retry = float(value)
            except ValueError:
                try:
                    stamp = parsedate_to_datetime(value)
                    stamp = stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp
                    retry = (stamp - datetime.now(timezone.utc)).total_seconds()
                except (ValueError, TypeError, OverflowError):
                    retry = 0
            if math.isfinite(retry):
                if retry > self.settings.max_backoff_seconds:
                    raise MaharavoUnavailable('Le délai de quota du fournisseur dépasse le budget autorisé.')
                delay = max(delay, retry)
        return min(self.settings.max_backoff_seconds, delay + random.uniform(0, min(0.1, delay / 4)))

    async def send(self, wire: WireRequest, *, task_id: UUID, task_type: str, api_version: str, model_version: str):
        url, headers, body = self._wire(wire, task_id)
        retry_safe = wire.method == 'GET' or bool(wire.idempotency_header)
        attempts = self.settings.max_attempts if retry_safe else 1
        metadata = {'integration': 'maharavo', 'task_id': str(task_id), 'task_type': task_type,
                    'api_version': api_version, 'model_version': model_version}
        try:
            async with asyncio.timeout(self.settings.total_timeout):
                for attempt in range(1, attempts + 1):
                    response = None
                    started = time.monotonic()
                    await self.limiter.acquire()
                    try:
                        async with self.semaphore:
                            timeout = httpx.Timeout(connect=self.settings.connect_timeout, read=self.settings.read_timeout,
                                write=self.settings.write_timeout, pool=self.settings.pool_timeout)
                            async with self._client().stream(wire.method, url, content=body, headers=headers,
                                                            timeout=timeout, follow_redirects=False) as response:
                                logger.info('Maharavo HTTP call', extra={**metadata, 'attempt': attempt,
                                    'status_code': response.status_code, 'duration_ms': round((time.monotonic() - started) * 1000)})
                                if response.status_code in {401, 403}:
                                    raise MaharavoCredentialsError('Authentification du fournisseur IA refusée.')
                                if response.status_code in {408, 429, 500, 502, 503, 504}:
                                    if attempt == attempts:
                                        raise MaharavoUnavailable('Fournisseur IA indisponible ou quota atteint.')
                                elif not 200 <= response.status_code < 300:
                                    raise MaharavoProtocolError('Requête IA refusée par le fournisseur.')
                                else:
                                    mime = response.headers.get('content-type', '').split(';', 1)[0].strip().lower()
                                    if mime != 'application/json' and not mime.endswith('+json'):
                                        raise MaharavoProtocolError('Le fournisseur IA ne renvoie pas de JSON.')
                                    if response.headers.get('content-encoding', 'identity').lower() != 'identity':
                                        raise MaharavoProtocolError('Réponse IA compressée non autorisée.')
                                    length = response.headers.get('content-length')
                                    if length is not None:
                                        try:
                                            size = int(length)
                                        except ValueError:
                                            raise MaharavoProtocolError('Taille de réponse IA invalide.') from None
                                        if size < 0 or size > self.settings.max_response_bytes:
                                            raise MaharavoLimitError('La réponse IA dépasse la taille autorisée.')
                                    chunks = bytearray()
                                    async for chunk in response.aiter_bytes(chunk_size=8192):
                                        if len(chunks) + len(chunk) > self.settings.max_response_bytes:
                                            raise MaharavoLimitError('La réponse IA dépasse la taille autorisée.')
                                        chunks.extend(chunk)
                                    try:
                                        return json.loads(chunks.decode('utf-8'), object_pairs_hook=strict_object,
                                                          parse_constant=reject_constant)
                                    except (ValueError, UnicodeError, RecursionError):
                                        raise MaharavoProtocolError('JSON IA mal formé.') from None
                    except (httpx.TimeoutException, httpx.RequestError) as exc:
                        logger.warning('Maharavo transport failed', extra={**metadata, 'attempt': attempt,
                                       'error_type': type(exc).__name__})
                        if attempt == attempts:
                            if isinstance(exc, httpx.TimeoutException):
                                raise MaharavoTimeout('Délai de transport IA dépassé.') from None
                            raise MaharavoUnavailable('Connexion au fournisseur IA impossible.') from None
                    await self.sleep(self._delay(response, attempt))
        except TimeoutError:
            raise MaharavoTimeout('Budget de temps total de l’appel IA dépassé.') from None
