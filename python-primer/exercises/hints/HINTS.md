# Capstone Hints

Progressive hints for the capstone mini-project. Try to solve each challenge yourself before revealing hints.

---

## Configuration Loading

<details>
<summary>Hint 1: Basic structure</summary>

```python
from dotenv import load_dotenv
import os

@classmethod
def from_env(cls) -> "Config":
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY required")

    return cls(
        api_key=api_key,
        model=os.getenv("MODEL", cls.model_fields["model"].default),
        # ... other fields
    )
```
</details>

<details>
<summary>Hint 2: Type conversion for env vars</summary>

```python
max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
temperature = float(os.getenv("TEMPERATURE", "0.7"))

# Better with error handling:
try:
    max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
except ValueError:
    raise ValueError(f"MAX_TOKENS must be int, got: {os.getenv('MAX_TOKENS')}")
```
</details>

---

## Retry Decorator

<details>
<summary>Hint 1: Basic retry structure</summary>

```python
from functools import wraps
from anthropic import RateLimitError, APITimeoutError

def retry(max_attempts=3, base_delay=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, APITimeoutError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(base_delay * (2 ** attempt))
            return wrapper
    return decorator
```
</details>

<details>
<summary>Hint 2: Add jitter to prevent thundering herd</summary>

```python
import random

delay = base_delay * (2 ** attempt)
jitter = random.uniform(0, delay * 0.1)
time.sleep(delay + jitter)
```
</details>

---

## Streaming Implementation

<details>
<summary>Hint 1: Basic streaming</summary>

```python
def stream(self, prompt: str, **kwargs):
    with self._client.messages.stream(
        model=self.config.model,
        max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield text
```
</details>

<details>
<summary>Hint 2: Get final usage stats</summary>

```python
def stream(self, prompt: str, **kwargs):
    with self._client.messages.stream(...) as stream:
        for text in stream.text_stream:
            yield text

        # After streaming completes
        final = stream.get_final_message()
        self._update_stats(final.usage)
```
</details>

<details>
<summary>Hint 3: Return both text and stats</summary>

```python
def stream_with_stats(self, prompt: str, **kwargs):
    """Yield chunks, then final stats."""
    chunks = []

    with self._client.messages.stream(...) as stream:
        for text in stream.text_stream:
            chunks.append(text)
            yield {"type": "text", "content": text}

        final = stream.get_final_message()
        yield {
            "type": "final",
            "text": "".join(chunks),
            "usage": Usage(
                input_tokens=final.usage.input_tokens,
                output_tokens=final.usage.output_tokens
            )
        }
```
</details>

---

## Async Batch Processing

<details>
<summary>Hint 1: Basic parallel execution</summary>

```python
import asyncio
from anthropic import AsyncAnthropic

async def batch_async(self, prompts: list[str], **kwargs) -> list[Response]:
    tasks = [self.chat_async(p, **kwargs) for p in prompts]
    return await asyncio.gather(*tasks)
```
</details>

<details>
<summary>Hint 2: Rate limiting with semaphore</summary>

```python
async def batch_async(self, prompts: list[str], max_concurrent=5, **kwargs):
    semaphore = asyncio.Semaphore(max_concurrent)

    async def limited_call(prompt):
        async with semaphore:
            return await self.chat_async(prompt, **kwargs)

    tasks = [limited_call(p) for p in prompts]
    return await asyncio.gather(*tasks)
```
</details>

<details>
<summary>Hint 3: Handle individual failures</summary>

```python
async def batch_async(self, prompts: list[str], **kwargs):
    async def safe_call(prompt):
        try:
            return await self.chat_async(prompt, **kwargs)
        except Exception as e:
            return Response(
                text="",
                usage=Usage(input_tokens=0, output_tokens=0),
                model=self.config.model,
                stop_reason="error",
                error=str(e)
            )

    tasks = [safe_call(p) for p in prompts]
    return await asyncio.gather(*tasks)
```
</details>

---

## Cost Tracking

<details>
<summary>Hint 1: Cost calculation</summary>

```python
# Claude Sonnet pricing per 1M tokens
INPUT_COST = 3.0   # $3 per 1M input tokens
OUTPUT_COST = 15.0  # $15 per 1M output tokens

def calculate_cost(usage: Usage) -> float:
    return (
        usage.input_tokens * INPUT_COST / 1_000_000 +
        usage.output_tokens * OUTPUT_COST / 1_000_000
    )
```
</details>

<details>
<summary>Hint 2: Tracking in client</summary>

```python
class LLMClient:
    def __init__(self, config: Config):
        self._stats = {
            "calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0.0
        }

    def _update_stats(self, usage: Usage):
        self._stats["calls"] += 1
        self._stats["input_tokens"] += usage.input_tokens
        self._stats["output_tokens"] += usage.output_tokens
        self._stats["cost"] += self._calculate_cost(usage)
```
</details>

---

## Logging

<details>
<summary>Hint 1: Basic logging setup</summary>

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_client")
```
</details>

<details>
<summary>Hint 2: Log decorator</summary>

```python
def log_call(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        logger.info(f"Calling {func.__name__}")
        try:
            result = func(self, *args, **kwargs)
            logger.info(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    return wrapper
```
</details>

---

## Testing

<details>
<summary>Hint 1: Test fixtures</summary>

```python
import pytest

@pytest.fixture
def client():
    from llm_client import LLMClient, Config
    return LLMClient(Config.from_env())

def test_chat(client):
    response = client.chat("Say 'test'")
    assert response.text
    assert response.usage.total > 0
```
</details>

<details>
<summary>Hint 2: Mock API for unit tests</summary>

```python
from unittest.mock import Mock, patch

def test_retry_on_rate_limit():
    with patch.object(client._client.messages, 'create') as mock:
        mock.side_effect = [
            RateLimitError("rate limited"),
            Mock(content=[Mock(text="success")], usage=Mock(...))
        ]

        response = client.chat("test")
        assert response.text == "success"
        assert mock.call_count == 2
```
</details>

---

## Context Manager Pattern

<details>
<summary>Hint: Client as context manager</summary>

```python
class LLMClient:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stats = self.get_stats()
        logger.info(f"Session complete: {stats}")
        return False  # Don't suppress exceptions

# Usage
with LLMClient(config) as client:
    response = client.chat("Hello")
# Stats logged automatically on exit
```
</details>

---

## Complete Solution

If you're completely stuck, see [llm_client_solution.py](../capstone/llm_client_solution.py)

But remember: struggling through the implementation is where the learning happens!
