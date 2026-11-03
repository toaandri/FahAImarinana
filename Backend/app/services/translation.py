"""Dedicated Cloud Translation, then existing AI providers, with link preservation."""
import html
import re

import httpx

from ..core.config import get_settings
from ..core.errors import IntegrationUnavailableError
from ..integrations.ai.openrouter import answer_question, OpenRouterUnavailableError
from ..integrations.ai.gemini import translate_text, GeminiUnavailableError

URL_PATTERN = re.compile(r'https?://[^\s<>\]\)]+')


def _restore_links(translated: str, links: dict[str, str]) -> str:
    if URL_PATTERN.search(translated):
        raise ValueError('Unexpected translated link')
    for marker, url in links.items():
        if translated.count(marker) != 1:
            raise ValueError('Missing or duplicated link')
        translated = translated.replace(marker, url)
    return translated


def translate_answer(text: str, language: str) -> dict:
    settings = get_settings()
    links = {}

    def protect(match):
        marker = f'FAHAIURL{len(links)}TOKEN'
        # Do not allow source text to collide with placeholders.
        while marker in text:
            marker += 'X'
        links[marker] = match.group()
        return marker

    protected = URL_PATTERN.sub(protect, text)
    if settings.google_translation_api_key.get_secret_value().strip():
        try:
            with httpx.Client(timeout=settings.translation_timeout_seconds) as client:
                response = client.post('https://translation.googleapis.com/language/translate/v2',
                    headers={'X-Goog-Api-Key': settings.google_translation_api_key.get_secret_value()},
                    json={'q': protected, 'target': language, 'format': 'text'})
                response.raise_for_status()
                translated = html.unescape(response.json()['data']['translations'][0]['translatedText'])
                if not translated.strip():
                    raise ValueError('Empty translation')
                return {'text': _restore_links(translated, links), 'language': language, 'provider': 'google_translation'}
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            pass
    if settings.openrouter_api_key.get_secret_value().strip():
        try:
            translated = answer_question(protected, [], language=language, translate=True)
            return {'text': _restore_links(translated, links), 'language': language, 'provider': 'openrouter'}
        except (OpenRouterUnavailableError, ValueError):
            pass
    if settings.gemini_api_key.get_secret_value().strip():
        try:
            translated = translate_text(protected, language)
            return {'text': _restore_links(translated, links), 'language': language, 'provider': 'gemini'}
        except (GeminiUnavailableError, ValueError):
            pass
    message = ('Tsy afaka mandika teny amin’izao fotoana izao. Andramo indray azafady.' if language == 'mg'
               else 'La traduction est indisponible. Réessayez plus tard.')
    raise IntegrationUnavailableError(message)
