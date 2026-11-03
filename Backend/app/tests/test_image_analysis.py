import base64
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
from pydantic import SecretStr, ValidationError
import httpx
from app.core.errors import IntegrationUnavailableError
from app.schemas.vision import ImageAnalysisRequest
from app.services.image_analysis import analyze_cloud_image, analyze_image


class ImageAnalysisTests(unittest.TestCase):
    def test_input_accepts_image_and_rejects_other_content(self):
        image = base64.b64encode(b'\x89PNG\r\n\x1a\nimage').decode()
        self.assertEqual(ImageAnalysisRequest(image_base64=image).image_base64, image)
        with self.assertRaises(ValidationError):
            ImageAnalysisRequest(image_base64=base64.b64encode(b'not an image file').decode())

    def test_annotations_are_not_presented_as_authenticity_scores(self):
        settings = SimpleNamespace(google_cloud_vision_api_key=SecretStr('test-key'))
        provider = httpx.Response(200, json={'responses': [{'labelAnnotations': [{'description': 'Tree', 'score': 0.9}],
            'fullTextAnnotation': {'text': 'Example'}}]}, request=httpx.Request('POST', 'https://vision.googleapis.com'))
        with patch('app.services.image_analysis.get_settings', return_value=settings), \
             patch('app.services.image_analysis.httpx.post', return_value=provider) as post:
            result = analyze_cloud_image('encoded')
        self.assertEqual(result['labels'], ['Tree'])
        self.assertEqual(result['text'], 'Example')
        self.assertNotIn('score', result)
        self.assertIn('ne déterminent pas', result['notice'])
        self.assertEqual(post.call_args.kwargs['headers']['x-goog-api-key'], 'test-key')

    def test_billing_or_restrictions_produce_actionable_error(self):
        settings = SimpleNamespace(google_cloud_vision_api_key=SecretStr('test-key'))
        with patch('app.services.image_analysis.get_settings', return_value=settings), \
             patch('app.services.image_analysis.httpx.post', return_value=httpx.Response(403)):
            with self.assertRaisesRegex(IntegrationUnavailableError, 'facturation'):
                analyze_cloud_image('encoded')

    def test_gemini_image_uses_private_request_and_returns_no_verdict(self):
        image = base64.b64encode(b'\x89PNG\r\n\x1a\nimage').decode()
        settings = SimpleNamespace(gemini_api_key=SecretStr('test'), gemini_vision_model='test-model')
        result_json = '{"labels":["arbre"],"text":"panneau","summary":"Un arbre."}'
        with patch('app.services.image_analysis.get_settings', return_value=settings), \
             patch('app.services.image_analysis._request', return_value={'status': 'completed', 'output_text': result_json}) as request:
            result = analyze_image(image)
        self.assertEqual(result['provider'], 'gemini')
        self.assertEqual(result['labels'], ['arbre'])
        self.assertNotIn('score', result)
        self.assertEqual(request.call_args.args[0]['input'][0]['mime_type'], 'image/png')
        self.assertIs(request.call_args.args[0]['store'], False)
