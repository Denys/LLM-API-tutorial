"""LLM Client - Capstone Solution.

A production-ready LLM client demonstrating all Python primer concepts.

Run: python llm_client_solution.py
Requires: .env file with ANTHROPIC_API_KEY
"""

import asyncio
import logging
import time
import random
from functools import wraps
from typing import Generator

from pydantic import BaseModel, Field
from anthropic import (
    Anthropic,
    AsyncAnthropic,
    RateLimitError,
    APITimeoutError,
    InternalServerError,
    AuthenticationError,
    APIError
)
from dotenv import load_dotenv
import os


# =============================================================================
# Configuration
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_client")


# =============================================================================
# Models (Section 6: Type Hints & Pydantic)
# =============================================================================

class Config(BaseModel):
    """Client configuration."""
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: float = 60.0

    @classmethod
    def from_env(cls, env_file: str = None) -> "Config":
        """Load configuration from environment.

        Args:
            env_file: Optional path to .env file.

        Returns:
            Config instance.

        Raises:
            ValueError: If required config is missing.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set in .env file or environment."
            )

        return cls(
            api_key=api_key,
            model=os.getenv("MODEL", "claude-sonnet-4-20250514"),
            max_tokens=int(os.getenv("MAX_TOKENS", "1024")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            timeout=float(os.getenv("TIMEOUT", "60.0")),
        )

    def __repr__(self) -> str:
        return (
            f"Config(model={self.model!r}, "
            f"max_tokens={self.max_tokens}, "
            f"api_key='{self.api_key[:8]}...')"
        )


class Usage(BaseModel):
    """Token usage information."""
    input_tokens: int
    output_tokens: int

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


class Response(BaseModel):
    """API response."""
    text: str
    usage: Usage
    model: str
    stop_reason: str
    error: str | None = None


# =============================================================================
# Decorators (Section 8: Decorators & Context Managers)
# =============================================================================

def retry(max_attempts: int = 3, base_delay: float = 1.0):
    """Retry decorator with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, APITimeoutError, InternalServerError) as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        jitter = random.uniform(0, delay * 0.1)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {type(e).__name__}. "
                            f"Retrying in {delay + jitter:.1f}s..."
                        )
                        time.sleep(delay + jitter)
            raise last_error
        return wrapper
    return decorator


def log_call(func):
    """Log function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__}")
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    return wrapper


# =============================================================================
# Client (All sections combined)
# =============================================================================

class LLMClient:
    """Production-ready LLM client."""

    # Cost per 1M tokens (Sonnet pricing)
    INPUT_COST = 3.0
    OUTPUT_COST = 15.0

    def __init__(self, config: Config):
        """Initialize client.

        Args:
            config: Client configuration.
        """
        self.config = config
        self._client = Anthropic(api_key=config.api_key)
        self._async_client = None  # Lazy init
        self._stats = {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0.0,
            "errors": 0
        }
        logger.info(f"Client initialized: {config}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stats = self.get_stats()
        logger.info(
            f"Session complete: {stats['calls']} calls, "
            f"{stats['total_tokens']} tokens, ${stats['cost']:.6f}"
        )
        return False

    @log_call
    @retry(max_attempts=3)
    def chat(self, prompt: str, **kwargs) -> Response:
        """Make a chat completion request.

        Args:
            prompt: User message.
            **kwargs: Override config (max_tokens, temperature, etc.)

        Returns:
            Response object with text and usage.
        """
        response = self._client.messages.create(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            messages=[{"role": "user", "content": prompt}]
        )

        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )

        self._update_stats(usage)

        return Response(
            text=response.content[0].text,
            usage=usage,
            model=response.model,
            stop_reason=response.stop_reason
        )

    def stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Stream a chat completion.

        Args:
            prompt: User message.
            **kwargs: Override config.

        Yields:
            Text chunks as they arrive.
        """
        logger.info("Starting stream")

        with self._client.messages.stream(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text

            # Get final stats
            final = stream.get_final_message()
            usage = Usage(
                input_tokens=final.usage.input_tokens,
                output_tokens=final.usage.output_tokens
            )
            self._update_stats(usage)

        logger.info(f"Stream complete: {usage.total} tokens")

    async def chat_async(self, prompt: str, **kwargs) -> Response:
        """Async chat completion.

        Args:
            prompt: User message.
            **kwargs: Override config.

        Returns:
            Response object.
        """
        if self._async_client is None:
            self._async_client = AsyncAnthropic(api_key=self.config.api_key)

        response = await self._async_client.messages.create(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            messages=[{"role": "user", "content": prompt}]
        )

        usage = Usage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )

        self._update_stats(usage)

        return Response(
            text=response.content[0].text,
            usage=usage,
            model=response.model,
            stop_reason=response.stop_reason
        )

    async def batch_async(
        self,
        prompts: list[str],
        max_concurrent: int = 5,
        **kwargs
    ) -> list[Response]:
        """Process multiple prompts in parallel.

        Args:
            prompts: List of prompts.
            max_concurrent: Max concurrent requests.
            **kwargs: Override config.

        Returns:
            List of responses (in same order as prompts).
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_call(prompt: str) -> Response:
            async with semaphore:
                try:
                    return await self.chat_async(prompt, **kwargs)
                except Exception as e:
                    self._stats["errors"] += 1
                    return Response(
                        text="",
                        usage=Usage(input_tokens=0, output_tokens=0),
                        model=self.config.model,
                        stop_reason="error",
                        error=str(e)
                    )

        logger.info(f"Batch processing {len(prompts)} prompts")
        tasks = [limited_call(p) for p in prompts]
        results = await asyncio.gather(*tasks)
        logger.info(f"Batch complete")

        return results

    def _update_stats(self, usage: Usage):
        """Update cumulative statistics."""
        self._stats["calls"] += 1
        self._stats["input_tokens"] += usage.input_tokens
        self._stats["output_tokens"] += usage.output_tokens
        self._stats["cost"] += (
            usage.input_tokens * self.INPUT_COST / 1_000_000 +
            usage.output_tokens * self.OUTPUT_COST / 1_000_000
        )

    def get_stats(self) -> dict:
        """Get session statistics.

        Returns:
            Dictionary with calls, tokens, cost, errors.
        """
        return {
            **self._stats,
            "total_tokens": self._stats["input_tokens"] + self._stats["output_tokens"]
        }


# =============================================================================
# Demo
# =============================================================================

async def demo_async():
    """Demo async batch processing."""
    config = Config.from_env()

    with LLMClient(config) as client:
        # Batch async
        prompts = [
            "What is a resistor? (1 sentence)",
            "What is a capacitor? (1 sentence)",
            "What is an inductor? (1 sentence)"
        ]

        print("\nBatch async processing:")
        results = await client.batch_async(prompts, max_concurrent=3)

        for prompt, response in zip(prompts, results):
            component = prompt.split()[3].rstrip("?")
            if response.error:
                print(f"  {component}: ERROR - {response.error}")
            else:
                print(f"  {component}: {response.text}")


def main():
    """Demo the LLM client."""
    config = Config.from_env()

    with LLMClient(config) as client:
        # Single call
        print("Single call:")
        response = client.chat("What is Ohm's law? (1 sentence)")
        print(f"  Response: {response.text}")
        print(f"  Tokens: {response.usage.total}")
        print()

        # Streaming
        print("Streaming:")
        print("  ", end="")
        for chunk in client.stream("Count from 1 to 5, one number per line"):
            print(chunk, end="", flush=True)
        print()

    # Async demo
    asyncio.run(demo_async())


if __name__ == "__main__":
    main()
