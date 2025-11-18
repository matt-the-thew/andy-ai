"""Unit tests for LLM Service."""
import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from services.llm_service import LLMService
from config import Config


class TestLLMService(unittest.TestCase):
    """Test cases for LLMService."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = LLMService(api_key="test-key")

    def test_initialization(self):
        """Test LLM service initialization."""
        self.assertEqual(self.service.api_key, "test-key")
        self.assertEqual(self.service.model, Config.LLM_MODEL)
        self.assertEqual(self.service.max_retries, Config.LLM_MAX_RETRIES)

    def test_cache_key_generation(self):
        """Test cache key generation is consistent."""
        system = "system prompt"
        user = "user prompt"
        key1 = self.service._build_cache_key(system, user)
        key2 = self.service._build_cache_key(system, user)
        self.assertEqual(key1, key2)

    def test_cache_key_different_prompts(self):
        """Test cache keys are different for different prompts."""
        key1 = self.service._build_cache_key("system1", "user1")
        key2 = self.service._build_cache_key("system2", "user2")
        self.assertNotEqual(key1, key2)

    def test_ask_with_empty_prompt(self):
        """Test ask raises ValueError on empty prompt."""
        with self.assertRaises(ValueError):
            self.service.ask("")

    def test_ask_with_whitespace_prompt(self):
        """Test ask raises ValueError on whitespace-only prompt."""
        with self.assertRaises(ValueError):
            self.service.ask("   ")

    @patch("services.llm_service.OpenAI")
    def test_ask_success(self, mock_openai_class):
        """Test successful LLM response."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="  Test response  "))]
        mock_client.chat.completions.create.return_value = mock_response

        service = LLMService(api_key="test-key")
        result = service.ask("Test prompt")

        self.assertEqual(result, "Test response")

    @patch("services.llm_service.OpenAI")
    def test_ask_with_custom_system_prompt(self, mock_openai_class):
        """Test ask with custom system prompt."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response

        service = LLMService(api_key="test-key")
        service.ask("Test prompt", system_prompt="Custom system")

        # Verify the system prompt was used
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "Custom system")

    @patch("services.llm_service.OpenAI")
    def test_cache_stores_response(self, mock_openai_class):
        """Test that successful responses are cached."""
        if not Config.CACHING_ENABLED:
            self.skipTest("Caching disabled in config")

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Cached response"))]
        mock_client.chat.completions.create.return_value = mock_response

        service = LLMService(api_key="test-key")

        # First call should hit API
        result1 = service.ask("Test prompt")
        call_count_1 = mock_client.chat.completions.create.call_count

        # Second call should use cache
        result2 = service.ask("Test prompt")
        call_count_2 = mock_client.chat.completions.create.call_count

        self.assertEqual(result1, result2)
        self.assertEqual(call_count_1, call_count_2)  # API not called again

    def test_cache_clear(self):
        """Test cache clearing."""
        if not Config.CACHING_ENABLED:
            self.skipTest("Caching disabled in config")

        service = LLMService(api_key="test-key")
        if service.cache:
            service.cache.set("key1", "value1")
            self.assertGreater(service.cache.size(), 0)
            service.clear_cache()
            self.assertEqual(service.cache.size(), 0)


if __name__ == "__main__":
    unittest.main()
