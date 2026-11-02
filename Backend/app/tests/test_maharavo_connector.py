"""Unit fixtures only. MockTransport is not a real Maharavo service or a live test."""
import os
os.environ.setdefault('DATABASE_URL', os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:'))
os.environ.setdefault('ENVIRONMENT', 'test')
import asyncio
import copy
from datetime import datetime, timezone, timedelta
import json
import unittest
from uuid import uuid4
import httpx
from pydantic import ValidationError
from app.integrations.maharavo.binding import WireRequest
from app.integrations.maharavo.client import MaharavoClient
from app.integrations.maharavo.config import MaharavoSettings
from app.integrations.maharavo.contracts import TaskRequest, TaskType, TASK_SPACES, TaskResponse
from app.integrations.maharavo.errors import (MaharavoNotConfigured, MaharavoProtocolError,
    MaharavoLimitError, MaharavoTimeout, MaharavoUnavailable, MaharavoCredentialsError)
from app.integrations.maharavo.limits import RequestLimiter
from app.integrations.maharavo.provenance import ConsultationManifest, record_materialized_document
from app.integrations.maharavo.transport import AsyncHTTPTransport
from app.integrations.maharavo.validation import validate_response

KEY = 'UNIT-TEST-NOT-A-REAL-API-KEY'


class FixtureAdapter:
    documentation_reference = 'unit-test-fixture://not-a-real-provider-contract'
    api_version = 'unit-tests-only'

    def encode(self, request, api_key):
        return WireRequest('POST', '/unit-fixtures/task', {'Fixture-Api-Key': api_key.get_secret_value()},
                           request.model_dump(mode='json'), 'Fixture-Idempotency-Key')

    def normalize(self, payload):
        return payload


class NoWaitLimiter:
    def __init__(self): self.count = 0
    async def acquire(self): self.count += 1


class ConnectorContracts(unittest.TestCase):
    def setUp(self):
        self.settings = MaharavoSettings(enabled=True, base_url='https://maharavo-unit.example.invalid',
            api_key=KEY, allowed_model_versions=['unit-fixture-model-1'])
        self.document = record_materialized_document(document_id=uuid4(),
            url='https://source.example.invalid/document', text='A fictional document. Exact fixture quotation. Nothing is real.')
        self.task_id = uuid4()
        self.request = TaskRequest(task_id=self.task_id, task_type='research', model_version='unit-fixture-model-1',
            submitted_at=datetime.now(timezone.utc), instructions='Unit test research only.', documents=[self.document])
        self.manifest = ConsultationManifest(self.task_id, 1, 'demo', (self.document,))
        self.response = {
            'contract_version': 'fa-ai-marinana.proposal.v1', 'task_id': str(self.task_id), 'task_type': 'research',
            'status': 'completed', 'space': 'research', 'model_version': 'unit-fixture-model-1',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'sources': [{key: value for key, value in self.document.model_dump(mode='json').items() if key != 'text'}],
            'evidence': [{'evidence_id': 'quote-1', 'document_id': str(self.document.document_id),
                          'consultation_id': str(self.document.consultation_id), 'quote': 'Exact fixture quotation.'}],
            'analysis': {'summary': 'A proposed unit-test summary.', 'summary_evidence_ids': ['quote-1']},
            'limitations': ['Entirely fictitious unit-test corpus; not a real engine result.'], 'errors': []}

    def test_normalized_response_requires_materialized_document_and_quote(self):
        result = validate_response(self.response, self.request, self.manifest, self.settings)
        self.assertEqual(result.status, 'completed')
        self.assertEqual(result.space, 'research')

    def test_malformed_unknown_and_editorial_fields_are_rejected(self):
        mutations = [lambda r: r.pop('task_id'), lambda r: r.update(space='publications'),
            lambda r: r.update(validated_by_id=1), lambda r: r.update(status='published'),
            lambda r: r.update(model_version='unknown-model'), lambda r: r.update(task_id=str(uuid4())),
            lambda r: r['analysis'].update(publication={'body': 'not allowed'}),
            lambda r: r['analysis'].update(summary='   '),
            lambda r: r.update(generated_at=datetime.now().replace(tzinfo=None).isoformat())]
        for mutate in mutations:
            response = copy.deepcopy(self.response); mutate(response)
            with self.subTest(response_keys=list(response)):
                with self.assertRaises(MaharavoProtocolError):
                    validate_response(response, self.request, self.manifest, self.settings)

    def test_missing_changed_or_fabricated_references_are_rejected(self):
        mutations = [lambda r: r['sources'][0].update(document_id=str(uuid4())),
            lambda r: r['sources'][0].update(sha256='0'*64),
            lambda r: r['sources'][0].update(url='https://unknown.example.invalid'),
            lambda r: r['sources'][0].update(consultation_id=str(uuid4())),
            lambda r: r['evidence'][0].update(quote='A fabricated quotation.'),
            lambda r: r['analysis'].update(summary_evidence_ids=['nonexistent-evidence']),
            lambda r: r['evidence'].append(dict(r['evidence'][0]))]
        for mutate in mutations:
            response = copy.deepcopy(self.response); mutate(response)
            with self.assertRaises(MaharavoProtocolError):
                validate_response(response, self.request, self.manifest, self.settings)

    def test_stale_and_future_generation_dates_are_rejected(self):
        for date in [self.request.submitted_at-timedelta(hours=1), datetime.now(timezone.utc)+timedelta(hours=1)]:
            response=copy.deepcopy(self.response); response['generated_at']=date.isoformat()
            with self.assertRaises(MaharavoProtocolError):
                validate_response(response,self.request,self.manifest,self.settings)

    def test_partial_and_failed_are_not_success(self):
        response=copy.deepcopy(self.response); response['status']='partial'
        with self.assertRaises(MaharavoProtocolError):
            validate_response(response,self.request,self.manifest,self.settings)
        response['errors']=[{'code':'source_unavailable','message':'Unit fixture source unavailable'}]
        self.assertEqual(validate_response(response,self.request,self.manifest,self.settings).status,'partial')
        response.update(status='failed', analysis=None, sources=[], evidence=[])
        self.assertEqual(validate_response(response,self.request,self.manifest,self.settings).status,'failed')
        response['errors']=[]
        with self.assertRaises(MaharavoProtocolError):
            validate_response(response,self.request,self.manifest,self.settings)

    def test_model_pin_task_and_backend_manifest_are_bound(self):
        wrong=ConsultationManifest(uuid4(),1,'demo',(self.document,))
        with self.assertRaises(MaharavoProtocolError):
            validate_response(self.response,self.request,wrong,self.settings)
        settings=self.settings.model_copy(update={'allowed_model_versions':['other-version']})
        with self.assertRaises(MaharavoProtocolError):
            validate_response(self.response,self.request,self.manifest,settings)

    def test_configured_limits_are_enforced(self):
        response=copy.deepcopy(self.response)
        response['analysis']['summary']='x'*101
        with self.assertRaises(MaharavoLimitError):
            validate_response(response,self.request,self.manifest,self.settings.model_copy(update={'max_analysis_chars':100}))
        response=copy.deepcopy(self.response)
        response['evidence'][0]['quote']=self.document.text
        with self.assertRaises(MaharavoLimitError):
            validate_response(response,self.request,self.manifest,self.settings.model_copy(update={'max_quote_chars':10}))

    def test_all_seven_task_types_have_only_their_allowed_space(self):
        for kind in TaskType:
            response=copy.deepcopy(self.response)
            request=self.request.model_copy(update={'task_type':kind})
            response.update(task_type=kind.value, space=TASK_SPACES[kind])
            if kind==TaskType.DOCUMENT_ANALYSIS:
                response['analysis']['documents']=[{'document_id':str(self.document.document_id),'summary':'Unit document analysis','evidence_ids':['quote-1']}]
            if kind==TaskType.CLAIM_EXTRACTION:
                response['analysis']['claims']=[{'claim_id':'claim-1','statement':'Proposed fixture claim','evidence_ids':['quote-1']}]
            if kind==TaskType.DRAFT_PREPARATION:
                response['analysis']['draft']={'title':'Unit draft','body':'Private unit proposal','language':'fr','evidence_ids':['quote-1']}
            if kind==TaskType.SOURCE_MATCHING:
                # Requires two distinct, materialized sources: one is intentionally insufficient.
                with self.assertRaises(MaharavoProtocolError):
                    validate_response(response,request,self.manifest,self.settings)
                continue
            result=validate_response(response,request,self.manifest,self.settings)
            self.assertIn(result.space,{'research','analysis','drafts'})

    def test_source_matching_and_contradictions_are_grounded(self):
        second=record_materialized_document(document_id=uuid4(),url='https://other.example.invalid/doc',
            text='An entirely fictitious second document. Contrary fixture quotation.')
        request=self.request.model_copy(update={'task_type':TaskType.SOURCE_MATCHING,'documents':[self.document,second]})
        manifest=ConsultationManifest(self.task_id,1,'demo',(self.document,second))
        response=copy.deepcopy(self.response)
        response.update(task_type='source_matching',space='analysis')
        response['sources'].append({key:value for key,value in second.model_dump(mode='json').items() if key!='text'})
        response['evidence'].append({'evidence_id':'quote-2','document_id':str(second.document_id),
            'consultation_id':str(second.consultation_id),'quote':'Contrary fixture quotation.'})
        response['analysis']['source_matches']=[{'document_ids':[str(self.document.document_id),str(second.document_id)],
            'explanation':'Unit comparison only','evidence_ids':['quote-1','quote-2']}]
        self.assertEqual(validate_response(response,request,manifest,self.settings).task_type,TaskType.SOURCE_MATCHING)
        response['analysis']['contradictions']=[{'statement':'Proposed unit contradiction','evidence_ids':['quote-1','quote-2']}]
        response['task_type']='contradiction_analysis'
        request=request.model_copy(update={'task_type':TaskType.CONTRADICTION_ANALYSIS})
        self.assertEqual(validate_response(response,request,manifest,self.settings).task_type,TaskType.CONTRADICTION_ANALYSIS)
        response['analysis']['contradictions'][0]['evidence_ids']=['quote-1','quote-1']
        with self.assertRaises(MaharavoProtocolError): validate_response(response,request,manifest,self.settings)

    def test_internal_document_contradiction_can_reference_two_distinct_passages(self):
        request=self.request.model_copy(update={'task_type':TaskType.CONTRADICTION_ANALYSIS})
        response=copy.deepcopy(self.response)
        response.update(task_type='contradiction_analysis',space='analysis')
        response['evidence'].append({**response['evidence'][0],'evidence_id':'quote-2','quote':'Nothing is real.'})
        response['analysis']['contradictions']=[{'statement':'A proposed internal inconsistency',
            'evidence_ids':['quote-1','quote-2']}]
        self.assertEqual(validate_response(response,request,self.manifest,self.settings).status,'completed')

    def test_configuration_has_no_default_remote_interface(self):
        settings=MaharavoSettings()
        self.assertFalse(settings.enabled); self.assertIsNone(settings.base_url)
        with self.assertRaises(ValidationError): MaharavoSettings(enabled=True)
        for url in ['http://insecure.example.invalid','https://user:password@host.example.invalid',
                    'https://host.example.invalid?api_key=secret']:
            with self.assertRaises(ValidationError): MaharavoSettings(base_url=url)


class ConnectorTransport(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fixture=ConnectorContracts(); self.fixture.setUp()
        self.settings=self.fixture.settings
        self.calls=[]; self.delays=[]

    async def sleep(self,delay): self.delays.append(delay)

    def transport(self,handler,settings=None):
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        self.addAsyncCleanup(client.aclose)
        return AsyncHTTPTransport(settings or self.settings,http_client=client,sleep=self.sleep,limiter=NoWaitLimiter())

    def wire(self,idempotent=True,method='POST'):
        return WireRequest(method,'/unit-fixtures/task',{'Fixture-Api-Key':KEY},{'task':'unit'},
                           'Fixture-Idempotency-Key' if idempotent else None)

    async def send(self,transport,wire=None):
        return await transport.send(wire or self.wire(),task_id=self.fixture.task_id,
            task_type='research',api_version='unit-fixture',model_version='unit-fixture-model-1')

    async def test_client_without_documented_adapter_performs_no_http(self):
        def handler(request): self.fail('No HTTP is allowed without a documented adapter')
        transport=self.transport(handler)
        client=MaharavoClient(self.settings,transport=transport)
        with self.assertRaises(MaharavoNotConfigured):
            await client.execute(self.fixture.request,self.fixture.manifest)
        client=MaharavoClient(MaharavoSettings(),adapter=FixtureAdapter(),transport=transport)
        with self.assertRaises(MaharavoNotConfigured):
            await client.execute(self.fixture.request,self.fixture.manifest)

    async def test_fixture_adapter_is_unit_only_and_result_is_validated(self):
        def handler(request):
            self.calls.append(request)
            return httpx.Response(200,json=self.fixture.response)
        transport=self.transport(handler)
        client=MaharavoClient(self.settings,adapter=FixtureAdapter(),transport=transport)
        result=await client.execute(self.fixture.request,self.fixture.manifest)
        self.assertEqual(result.status,'completed')
        self.assertEqual(self.calls[0].headers['fixture-api-key'],KEY)
        self.assertEqual(self.calls[0].headers['fixture-idempotency-key'],str(self.fixture.task_id))
        self.assertNotIn(KEY,self.calls[0].content.decode())
        self.fixture.response['evidence'][0]['quote']='Invented passage'
        with self.assertRaises(MaharavoProtocolError):
            await client.execute(self.fixture.request,self.fixture.manifest)

    async def test_retry_backoff_and_rate_budget_count_every_attempt(self):
        def handler(request):
            self.calls.append(request)
            return httpx.Response(503 if len(self.calls)<3 else 200,json={'unit':'ok'})
        transport=self.transport(handler)
        result=await self.send(transport)
        self.assertEqual(result,{'unit':'ok'}); self.assertEqual(len(self.calls),3)
        self.assertEqual(transport.limiter.count,3)
        self.assertGreaterEqual(self.delays[0],0.5); self.assertGreaterEqual(self.delays[1],1.0)
        self.assertEqual(len({r.headers['fixture-idempotency-key'] for r in self.calls}),1)

    async def test_post_without_documented_idempotency_is_never_retried(self):
        def handler(request):
            self.calls.append(request); return httpx.Response(503)
        with self.assertRaises(MaharavoUnavailable): await self.send(self.transport(handler),self.wire(False))
        self.assertEqual(len(self.calls),1); self.assertEqual(self.delays,[])

    async def test_auth_failures_redirects_and_bad_requests_are_not_retried(self):
        for status,error in [(401,MaharavoCredentialsError),(403,MaharavoCredentialsError),
                             (302,MaharavoProtocolError),(422,MaharavoProtocolError)]:
            calls=[]
            def handler(request):
                calls.append(request); return httpx.Response(status,headers={'Location':'https://other.example.invalid'})
            with self.assertRaises(error): await self.send(self.transport(handler))
            self.assertEqual(len(calls),1)

    async def test_retry_after_is_respected_or_rejected_if_outside_budget(self):
        def handler(request):
            self.calls.append(request)
            return httpx.Response(429,headers={'Retry-After':'2'}) if len(self.calls)==1 else httpx.Response(200,json={})
        await self.send(self.transport(handler))
        self.assertGreaterEqual(self.delays[0],2)
        def excessive(request): return httpx.Response(429,headers={'Retry-After':'3600'})
        with self.assertRaises(MaharavoUnavailable): await self.send(self.transport(excessive))

    async def test_malformed_json_mime_compression_and_oversize_are_rejected(self):
        for body in [b'not json',b'{"a":1,"a":2}',b'{"a":NaN}']:
            with self.assertRaises(MaharavoProtocolError):
                await self.send(self.transport(lambda r:httpx.Response(200,content=body,headers={'Content-Type':'application/json'})))
        with self.assertRaises(MaharavoProtocolError):
            await self.send(self.transport(lambda r:httpx.Response(200,text='html')))
        with self.assertRaises(MaharavoLimitError):
            await self.send(self.transport(lambda r:httpx.Response(200,json={'text':'x'*2000}),
                                           self.settings.model_copy(update={'max_response_bytes':1024})))

    async def test_streamed_response_limit_does_not_depend_on_content_length(self):
        class Stream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b'x'*800; yield b'x'*800
        with self.assertRaises(MaharavoLimitError):
            await self.send(self.transport(lambda r:httpx.Response(200,stream=Stream(),headers={'Content-Type':'application/json'}),
                self.settings.model_copy(update={'max_response_bytes':1024})))

    async def test_timeouts_and_total_deadline(self):
        def timeout(request): raise httpx.ReadTimeout('unit timeout',request=request)
        with self.assertRaises(MaharavoTimeout): await self.send(self.transport(timeout),self.wire(False))
        async def slow(request):
            await asyncio.sleep(0.1); return httpx.Response(200,json={})
        with self.assertRaises(MaharavoTimeout):
            await self.send(self.transport(slow,self.settings.model_copy(update={'total_timeout':0.01})))

    async def test_logs_do_not_contain_api_key_or_content(self):
        transport=self.transport(lambda r:httpx.Response(200,json={'private':'PRIVATE_BODY_SENTINEL'}))
        with self.assertLogs('app.integrations.maharavo',level='INFO') as logs:
            await self.send(transport)
        rendered=' '.join(logs.output)+str([record.__dict__ for record in logs.records])
        self.assertNotIn(KEY,rendered); self.assertNotIn('PRIVATE_BODY_SENTINEL',rendered)

    async def test_path_escape_and_sensitive_headers_are_refused_before_io(self):
        transport=self.transport(lambda request:self.fail('Forbidden wire request must never reach HTTP'))
        for path in ['https://other.example.invalid','//other.example.invalid','/../publish','/%2e%2e/publish','/task?key=secret']:
            with self.assertRaises(MaharavoProtocolError):
                await self.send(transport,WireRequest('POST',path,{},{}))
        with self.assertRaises(MaharavoProtocolError):
            await self.send(transport,WireRequest('POST','/unit',{'Host':'other.example.invalid'},{}))

    async def test_concurrency_budget_and_cancellation(self):
        active=[0]; maximum=[0]
        async def handler(request):
            active[0]+=1; maximum[0]=max(maximum[0],active[0])
            try:
                await asyncio.sleep(0.01)
                return httpx.Response(200,json={})
            finally: active[0]-=1
        transport=self.transport(handler)
        await asyncio.gather(*(self.send(transport) for _ in range(6)))
        self.assertEqual(maximum[0],self.settings.max_concurrent_requests)
        started=asyncio.Event()
        async def never(request):
            started.set(); await asyncio.Event().wait()
        task=asyncio.create_task(self.send(self.transport(never)))
        await started.wait(); task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task

    async def test_outbound_body_and_compressed_responses_are_bounded(self):
        transport=self.transport(lambda request:self.fail('Oversize request must not be sent'),
            self.settings.model_copy(update={'max_request_bytes':1024}))
        with self.assertRaises(MaharavoLimitError):
            await self.send(transport,WireRequest('POST','/fixture',{}, {'text':'x'*2000}))
        class Stream(httpx.AsyncByteStream):
            async def __aiter__(self): yield b'not consumed'
        with self.assertRaises(MaharavoProtocolError):
            await self.send(self.transport(lambda request:httpx.Response(200,stream=Stream(),
                headers={'Content-Type':'application/json','Content-Encoding':'gzip'})))

    async def test_process_limiter_paces_calls(self):
        value=[0.0]; delays=[]
        async def sleep(delay): delays.append(delay); value[0]+=delay
        limiter=RequestLimiter(30,clock=lambda:value[0],sleep=sleep)
        await limiter.acquire(); await limiter.acquire(); await limiter.acquire()
        self.assertEqual(delays,[2.0,2.0])


if __name__=='__main__': unittest.main()
