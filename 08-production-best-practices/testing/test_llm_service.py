#!/usr/bin/env python3
"""
Unit Tests for LLM Service

Demonstrates testing best practices for production LLM applications:
- Mocking external API calls
- Testing error handling
- Testing retry logic
- Testing caching
- Testing failover
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "examples" / "api-wrapper"))

from llm_service import (
    LLMService,
    LLMConfig,
    Provider,
    LLMResponse,
    Usage,
    ClaudeClient,
    OpenAIClient
)

class TestLLMService:
    """Test LLM service functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        return redis_mock

    @pytest.fixture
    def primary_config(self):
        """Primary LLM configuration."""
        return LLMConfig(
            provider=Provider.CLAUDE,
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            max_retries=3
        )

    @pytest.fixture
    def fallback_config(self):
        """Fallback LLM configuration."""
        return LLMConfig(
            provider=Provider.OPENAI,
            model="gpt-4-turbo-preview",
            max_tokens=2048,
            max_retries=3
        )

    @patch('llm_service.redis')
    @patch('llm_service.Anthropic')
    def test_successful_chat(self, mock_anthropic, mock_redis, primary_config):
        """Test successful chat request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(
            input_tokens=10,
            output_tokens=20
        )
        mock_anthropic.return_value.messages.create.return_value = mock_response

        # Create service
        service = LLMService(primary_config)
        service.cache = None  # Disable cache for this test

        # Test
        messages = [{"role": "user", "content": "Test"}]
        response = service.chat(messages)

        # Verify
        assert response.text == "Test response"
        assert response.provider == Provider.CLAUDE
        assert response.usage.input_tokens == 10
        assert response.usage.output_tokens == 20
        assert response.usage.total_tokens == 30
        assert not response.cached

    @patch('llm_service.Anthropic')
    def test_retry_logic(self, mock_anthropic, primary_config):
        """Test retry logic on API errors."""
        # Setup mock to fail twice then succeed
        mock_anthropic.return_value.messages.create.side_effect = [
            Exception("Rate limit"),
            Exception("Server error"),
            Mock(
                content=[Mock(text="Success")],
                usage=Mock(input_tokens=10, output_tokens=20)
            )
        ]

        service = LLMService(primary_config)
        service.cache = None

        # Test
        messages = [{"role": "user", "content": "Test"}]
        response = service.chat(messages)

        # Verify retry happened
        assert response.text == "Success"
        assert mock_anthropic.return_value.messages.create.call_count == 3

    @patch('llm_service.Anthropic')
    @patch('llm_service.OpenAI')
    def test_failover_to_backup(
        self,
        mock_openai,
        mock_anthropic,
        primary_config,
        fallback_config
    ):
        """Test failover to backup provider on primary failure."""
        # Primary fails
        mock_anthropic.return_value.messages.create.side_effect = Exception("Primary failed")

        # Fallback succeeds
        mock_openai_response = Mock()
        mock_openai_response.choices = [Mock(message=Mock(content="Fallback response"))]
        mock_openai_response.usage = Mock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        mock_openai.return_value.chat.completions.create.return_value = mock_openai_response

        # Create service with fallback
        service = LLMService(primary_config, fallback_config)
        service.cache = None

        # Test
        messages = [{"role": "user", "content": "Test"}]
        response = service.chat(messages)

        # Verify fallback was used
        assert response.text == "Fallback response"
        assert response.provider == Provider.OPENAI

    def test_caching(self, primary_config, mock_redis):
        """Test response caching."""
        with patch('llm_service.Anthropic') as mock_anthropic:
            # Setup mock
            mock_response = Mock()
            mock_response.content = [Mock(text="Cached response")]
            mock_response.usage = Mock(input_tokens=10, output_tokens=20)
            mock_anthropic.return_value.messages.create.return_value = mock_response

            # Create service with cache
            service = LLMService(primary_config)
            service.cache = mock_redis

            # First call - should call API and cache
            messages = [{"role": "user", "content": "Test"}]
            response1 = service.chat(messages)

            assert response1.text == "Cached response"
            assert not response1.cached
            assert mock_redis.setex.called

            # Setup cache to return saved response
            import json
            cached_data = {
                "text": "Cached response",
                "provider": "claude",
                "model": "claude-3-5-sonnet-20241022",
                "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30, "cost": 0.0},
                "latency_ms": 100.0
            }
            mock_redis.get.return_value = json.dumps(cached_data)

            # Second call - should use cache
            response2 = service.chat(messages)

            assert response2.text == "Cached response"
            assert response2.cached

    @patch('llm_service.Anthropic')
    def test_cost_calculation(self, mock_anthropic, primary_config):
        """Test cost calculation for Claude."""
        # Setup mock
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=1_000_000  # 1M tokens
        )
        mock_anthropic.return_value.messages.create.return_value = mock_response

        service = LLMService(primary_config)
        service.cache = None

        # Test
        messages = [{"role": "user", "content": "Test"}]
        response = service.chat(messages)

        # Verify cost calculation
        # For claude-3-5-sonnet: $3/M input + $15/M output = $18 total
        assert response.usage.cost == pytest.approx(18.0, rel=0.01)

class TestClaudeClient:
    """Test Claude-specific client."""

    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider=Provider.CLAUDE,
            model="claude-3-5-sonnet-20241022"
        )

    @patch('llm_service.Anthropic')
    def test_chat(self, mock_anthropic, config):
        """Test Claude chat."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Claude response")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=100)
        mock_anthropic.return_value.messages.create.return_value = mock_response

        client = ClaudeClient(config)
        response = client.chat([{"role": "user", "content": "Test"}])

        assert response.text == "Claude response"
        assert response.provider == Provider.CLAUDE
        assert response.usage.total_tokens == 150

class TestOpenAIClient:
    """Test OpenAI-specific client."""

    @pytest.fixture
    def config(self):
        return LLMConfig(
            provider=Provider.OPENAI,
            model="gpt-4-turbo-preview"
        )

    @patch('llm_service.OpenAI')
    def test_chat(self, mock_openai, config):
        """Test OpenAI chat."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="GPT response"))]
        mock_response.usage = Mock(
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150
        )
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        client = OpenAIClient(config)
        response = client.chat([{"role": "user", "content": "Test"}])

        assert response.text == "GPT response"
        assert response.provider == Provider.OPENAI
        assert response.usage.total_tokens == 150

# Integration tests (require actual API keys)
@pytest.mark.integration
class TestIntegration:
    """Integration tests with real APIs."""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_claude_real_api(self):
        """Test with real Claude API."""
        import os

        config = LLMConfig(
            provider=Provider.CLAUDE,
            model="claude-3-5-haiku-20241022",  # Use cheaper model
            max_tokens=100
        )

        service = LLMService(config)
        service.cache = None  # Disable cache

        messages = [{"role": "user", "content": "Say 'test successful'"}]
        response = service.chat(messages)

        assert "test successful" in response.text.lower()
        assert response.usage.total_tokens > 0
        assert response.usage.cost > 0

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    def test_openai_real_api(self):
        """Test with real OpenAI API."""
        import os

        config = LLMConfig(
            provider=Provider.OPENAI,
            model="gpt-3.5-turbo",  # Use cheaper model
            max_tokens=100
        )

        service = LLMService(config)
        service.cache = None

        messages = [{"role": "user", "content": "Say 'test successful'"}]
        response = service.chat(messages)

        assert "test successful" in response.text.lower()
        assert response.usage.total_tokens > 0
        assert response.usage.cost > 0

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
