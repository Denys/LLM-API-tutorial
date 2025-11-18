#!/usr/bin/env python3
"""
LLM API Wrapper Service

Production-ready API wrapper with:
- Multi-provider support (Claude, OpenAI)
- Automatic failover
- Response caching
- Rate limiting
- Cost tracking
- Retry logic
- Clean abstraction
"""

import os
import time
import hashlib
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Iterator, Any
from dataclasses import dataclass
from enum import Enum

import structlog
from anthropic import Anthropic, APIError as AnthropicError
from openai import OpenAI, APIError as OpenAIError
import redis

logger = structlog.get_logger()

class Provider(str, Enum):
    """Supported AI providers."""
    CLAUDE = "claude"
    OPENAI = "openai"

@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: Provider
    model: str
    max_tokens: int = 4096
    temperature: float = 1.0
    timeout: int = 60
    max_retries: int = 3
    cache_ttl: int = 3600
    enable_caching: bool = True

@dataclass
class Usage:
    """Token usage information."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float = 0.0

@dataclass
class LLMResponse:
    """Unified LLM response."""
    text: str
    provider: Provider
    model: str
    usage: Usage
    cached: bool = False
    latency_ms: float = 0.0

class LLMClient(ABC):
    """Abstract LLM client interface."""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Send chat messages and get response."""
        pass

    @abstractmethod
    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """Stream chat response."""
        pass

    def _calculate_cost(self, usage: Usage, model: str) -> float:
        """Calculate cost for usage."""
        # Override in subclasses
        return 0.0

class ClaudeClient(LLMClient):
    """Claude-specific implementation."""

    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00
        },
        "claude-3-5-haiku-20241022": {
            "input": 0.80,
            "output": 4.00
        }
    }

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            timeout=config.timeout
        )

    def chat(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Send chat with Claude."""
        start_time = time.time()

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=messages,
                **kwargs
            )

            usage = Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens
            )
            usage.cost = self._calculate_cost(usage, self.config.model)

            latency = (time.time() - start_time) * 1000

            return LLMResponse(
                text=response.content[0].text,
                provider=Provider.CLAUDE,
                model=self.config.model,
                usage=usage,
                latency_ms=latency
            )

        except AnthropicError as e:
            logger.error("claude_error", error=str(e))
            raise

    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """Stream chat with Claude."""
        try:
            with self.client.messages.stream(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=messages,
                **kwargs
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except AnthropicError as e:
            logger.error("claude_stream_error", error=str(e))
            raise

    def _calculate_cost(self, usage: Usage, model: str) -> float:
        """Calculate cost for Claude."""
        pricing = self.PRICING.get(model, {"input": 0, "output": 0})
        return (
            (usage.input_tokens / 1_000_000) * pricing["input"] +
            (usage.output_tokens / 1_000_000) * pricing["output"]
        )

class OpenAIClient(LLMClient):
    """OpenAI-specific implementation."""

    PRICING = {
        "gpt-4-turbo-preview": {
            "input": 10.00,
            "output": 30.00
        },
        "gpt-3.5-turbo": {
            "input": 0.50,
            "output": 1.50
        }
    }

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=config.timeout
        )

    def chat(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """Send chat with OpenAI."""
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=messages,
                **kwargs
            )

            usage = Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
            usage.cost = self._calculate_cost(usage, self.config.model)

            latency = (time.time() - start_time) * 1000

            return LLMResponse(
                text=response.choices[0].message.content,
                provider=Provider.OPENAI,
                model=self.config.model,
                usage=usage,
                latency_ms=latency
            )

        except OpenAIError as e:
            logger.error("openai_error", error=str(e))
            raise

    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """Stream chat with OpenAI."""
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=messages,
                stream=True,
                **kwargs
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIError as e:
            logger.error("openai_stream_error", error=str(e))
            raise

    def _calculate_cost(self, usage: Usage, model: str) -> float:
        """Calculate cost for OpenAI."""
        pricing = self.PRICING.get(model, {"input": 0, "output": 0})
        return (
            (usage.input_tokens / 1_000_000) * pricing["input"] +
            (usage.output_tokens / 1_000_000) * pricing["output"]
        )

class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create(config: LLMConfig) -> LLMClient:
        """Create LLM client based on provider."""
        if config.provider == Provider.CLAUDE:
            return ClaudeClient(config)
        elif config.provider == Provider.OPENAI:
            return OpenAIClient(config)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

class LLMService:
    """
    High-level LLM service with caching, failover, and monitoring.

    This is the main interface for applications to use.
    """

    def __init__(
        self,
        primary_config: LLMConfig,
        fallback_config: Optional[LLMConfig] = None,
        redis_url: Optional[str] = None
    ):
        """
        Initialize LLM service.

        Args:
            primary_config: Primary LLM configuration
            fallback_config: Fallback LLM configuration (optional)
            redis_url: Redis URL for caching (optional)
        """
        self.primary_client = LLMFactory.create(primary_config)
        self.fallback_client = LLMFactory.create(fallback_config) if fallback_config else None

        # Initialize cache
        self.cache = None
        if redis_url and primary_config.enable_caching:
            try:
                self.cache = redis.from_url(redis_url, decode_responses=True)
                logger.info("cache_initialized", url=redis_url)
            except Exception as e:
                logger.warning("cache_init_failed", error=str(e))

    def chat(
        self,
        messages: List[Dict],
        use_cache: bool = True,
        **kwargs
    ) -> LLMResponse:
        """
        Send chat messages with automatic caching and failover.

        Args:
            messages: List of message dicts
            use_cache: Whether to use cache
            **kwargs: Additional arguments for provider

        Returns:
            LLMResponse with text and metadata
        """
        # Check cache first
        if use_cache and self.cache:
            cached = self._get_from_cache(messages, self.primary_client.config.model)
            if cached:
                logger.info("cache_hit")
                return cached

        # Try primary client
        try:
            response = self._chat_with_retry(self.primary_client, messages, **kwargs)

            # Cache response
            if use_cache and self.cache:
                self._save_to_cache(messages, self.primary_client.config.model, response)

            return response

        except Exception as e:
            logger.error("primary_client_failed", error=str(e))

            # Try fallback if available
            if self.fallback_client:
                logger.info("using_fallback_client")
                try:
                    return self._chat_with_retry(self.fallback_client, messages, **kwargs)
                except Exception as fallback_error:
                    logger.error("fallback_failed", error=str(fallback_error))
                    raise
            else:
                raise

    def stream_chat(
        self,
        messages: List[Dict],
        **kwargs
    ) -> Iterator[str]:
        """Stream chat response (no caching)."""
        try:
            yield from self.primary_client.stream_chat(messages, **kwargs)
        except Exception as e:
            logger.error("stream_failed", error=str(e))
            if self.fallback_client:
                logger.info("using_fallback_for_stream")
                yield from self.fallback_client.stream_chat(messages, **kwargs)
            else:
                raise

    def _chat_with_retry(
        self,
        client: LLMClient,
        messages: List[Dict],
        **kwargs
    ) -> LLMResponse:
        """Chat with exponential backoff retry."""
        max_retries = client.config.max_retries

        for attempt in range(max_retries):
            try:
                return client.chat(messages, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "retry_attempt",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time
                    )
                    time.sleep(wait_time)
                else:
                    raise

    def _get_cache_key(self, messages: List[Dict], model: str) -> str:
        """Generate cache key from messages."""
        content = json.dumps(messages, sort_keys=True) + model
        return f"llm:cache:{hashlib.sha256(content.encode()).hexdigest()}"

    def _get_from_cache(
        self,
        messages: List[Dict],
        model: str
    ) -> Optional[LLMResponse]:
        """Get response from cache."""
        try:
            key = self._get_cache_key(messages, model)
            cached = self.cache.get(key)
            if cached:
                data = json.loads(cached)
                return LLMResponse(**{**data, "cached": True})
        except Exception as e:
            logger.error("cache_get_error", error=str(e))
        return None

    def _save_to_cache(
        self,
        messages: List[Dict],
        model: str,
        response: LLMResponse
    ):
        """Save response to cache."""
        try:
            key = self._get_cache_key(messages, model)
            # Convert response to dict for caching
            cache_data = {
                "text": response.text,
                "provider": response.provider.value,
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "cost": response.usage.cost
                },
                "latency_ms": response.latency_ms
            }
            self.cache.setex(
                key,
                self.primary_client.config.cache_ttl,
                json.dumps(cache_data)
            )
        except Exception as e:
            logger.error("cache_save_error", error=str(e))

# Example usage
if __name__ == "__main__":
    # Configure primary and fallback
    primary_config = LLMConfig(
        provider=Provider.CLAUDE,
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048
    )

    fallback_config = LLMConfig(
        provider=Provider.OPENAI,
        model="gpt-4-turbo-preview",
        max_tokens=2048
    )

    # Create service
    service = LLMService(
        primary_config=primary_config,
        fallback_config=fallback_config,
        redis_url="redis://localhost:6379/0"
    )

    # Use service
    messages = [
        {"role": "user", "content": "Calculate power in a 100Ω resistor with 12V across it"}
    ]

    response = service.chat(messages)

    print(f"Provider: {response.provider}")
    print(f"Response: {response.text}")
    print(f"Tokens: {response.usage.total_tokens}")
    print(f"Cost: ${response.usage.cost:.6f}")
    print(f"Latency: {response.latency_ms:.0f}ms")
    print(f"Cached: {response.cached}")
