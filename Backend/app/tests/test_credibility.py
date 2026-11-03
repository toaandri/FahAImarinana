import os
os.environ['DATABASE_URL'] = os.environ.get('FANILO_TEST_DATABASE_URL', 'sqlite:///:memory:')
os.environ['ENVIRONMENT'] = 'test'
os.environ['JWT_SECRET'] = 'isolated-test-secret-at-least-thirty-two-bytes'
os.environ['AUTO_CREATE_TABLES'] = 'false'

import unittest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.credibility import CredibilityRequest
from app.services.credibility import calculate_corroboration
from app.tests.fixtures import reset_schema, make_account, tokens_for


def payload(*sources):
    return CredibilityRequest(claim='Une affirmation précise', sources=[
        {'url': f'https://{host}/article', 'assessment': verdict} for host, verdict in sources])


class CredibilityTests(unittest.TestCase):
    def test_requires_two_conclusive_source_groups(self):
        for entries in [(('a.example', 'supports'),),
                        (('a.example', 'supports'), ('b.example', 'inconclusive')),
                        (('a.example', 'inconclusive'), ('b.example', 'inconclusive'))]:
            with self.subTest(entries=entries):
                self.assertIsNone(calculate_corroboration(payload(*entries))['corroboration_percent'])

    def test_calculates_support_share_and_excludes_inconclusive(self):
        result = calculate_corroboration(payload(('a.example', 'supports'), ('b.example', 'contradicts'),
                                                ('c.example', 'supports'), ('d.example', 'inconclusive')))
        self.assertEqual(result['corroboration_percent'], 66.7)
        self.assertEqual((result['supports'], result['contradicts'], result['inconclusive']), (2, 1, 1))
        self.assertIn('ne mesure pas la probabilité de vérité', result['limitation'])

    def test_subdomains_and_conflicting_judgements_are_not_double_counted(self):
        result = calculate_corroboration(payload(('news.example.com', 'supports'),
                                                ('www.example.com', 'contradicts'),
                                                ('other.example.org', 'supports')))
        self.assertEqual(result['source_groups'], 2)
        self.assertEqual(result['excluded_duplicates'], 1)
        self.assertEqual(result['inconclusive'], 1)
        self.assertIsNone(result['corroboration_percent'])

    def test_all_support_and_all_contradict_are_not_truth_probabilities(self):
        for verdict, expected in [('supports', 100.0), ('contradicts', 0.0)]:
            result = calculate_corroboration(payload(('a.example', verdict), ('b.example', verdict)))
            self.assertEqual(result['corroboration_percent'], expected)
            self.assertIn('ne vérifie pas les liens', result['limitation'])

    def test_route_requires_permission_and_valid_payload(self):
        reset_schema()
        journalist = make_account('JOURNALISTE', email='creditest@example.invalid')
        journalist = make_account('JOURNALISTE', email='journalistcred@example.invalid')
        with TestClient(create_app()) as client:
            body = {'claim': 'Une affirmation', 'sources': [
                {'url': 'https://example.org/a', 'assessment': 'supports'},
                {'url': 'https://example.net/b', 'assessment': 'contradicts'}]}
            self.assertEqual(client.post('/api/v1/copilot/credibility', json=body).status_code, 401)
            headers = {'Authorization': 'Bearer ' + tokens_for(journalist).access_token}
            response = client.post('/api/v1/copilot/credibility', headers=headers, json=body)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()['corroboration_percent'], 50.0)
            self.assertEqual(response.headers['cache-control'], 'no-store')
            body['sources'][0]['assessment'] = 'invented'
            self.assertEqual(client.post('/api/v1/copilot/credibility', headers=headers, json=body).status_code, 422)


if __name__ == '__main__':
    unittest.main()
