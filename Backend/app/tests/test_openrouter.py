import unittest
from unittest.mock import MagicMock, patch

import httpx

from app.core.config import Settings
from app.integrations.ai.openrouter import OpenRouterUnavailableError, answer_question


class OpenRouterTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(openrouter_api_key="test-secret", jwt_secret="test-secret")

    def test_completion_sends_context_and_server_authorization(self):
        response = httpx.Response(200, json={"choices": [{"message": {"content": " Réponse test "}}]},
                                  request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"))
        with patch("app.integrations.ai.openrouter.get_settings", return_value=self.settings), \
             patch("app.integrations.ai.openrouter.httpx.Client") as client:
            post = client.return_value.__enter__.return_value.post
            post.return_value = response
            self.assertEqual(answer_question("Bonjour", [{"titre": "Source certifiée"}]), "Réponse test")
            self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-secret")
            self.assertIn("Source certifiée", post.call_args.kwargs["json"]["messages"][1]["content"])

    def test_rejects_empty_malformed_and_error_responses(self):
        for status, body in [(200, {}), (200, {"choices": []}),
                             (200, {"choices": [{"message": {"content": ""}}]}),
                             (401, {"error": {"message": "test-secret"}}), (429, {})]:
            with self.subTest(status=status, body=body), \
                 patch("app.integrations.ai.openrouter.get_settings", return_value=self.settings), \
                 patch("app.integrations.ai.openrouter.httpx.Client") as client:
                client.return_value.__enter__.return_value.post.return_value = httpx.Response(
                    status, json=body, request=httpx.Request("POST", "https://openrouter.ai"))
                with self.assertRaises(OpenRouterUnavailableError) as error:
                    answer_question("Bonjour", [])
                self.assertNotIn("test-secret", str(error.exception))

    def test_chat_uses_openrouter_and_falls_back_on_failure(self):
        from app.services.research import build_research_answer
        with patch("app.services.research.get_settings", return_value=self.settings), \
             patch("app.services.research.search_knowledge_base", return_value=[]), \
             patch("app.services.research.answer_question", return_value="Bonjour") as answer:
            self.assertEqual(build_research_answer(MagicMock(), "Salut", use_openrouter=True), ("Bonjour", [], []))
            answer.side_effect = OpenRouterUnavailableError("Unavailable")
            fallback, citations, chronology = build_research_answer(MagicMock(), "Salut", use_openrouter=True)
            self.assertIn("Aucun document certifié", fallback)
            self.assertEqual((citations, chronology), ([], []))


if __name__ == "__main__":
    unittest.main()
