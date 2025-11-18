# Section 5: Error Handling

**Duration:** 20 minutes | **Difficulty:** Intermediate

## Why This Matters for LLM APIs

LLM APIs fail in predictable ways: rate limits, timeouts, overloaded servers, invalid inputs. Robust error handling is the difference between a demo and production code.

## Concepts

### Anthropic SDK Exceptions

```python
from anthropic import (
    APIError,           # Base class for API errors
    AuthenticationError, # 401: Invalid API key
    PermissionDeniedError, # 403: No access
    NotFoundError,      # 404: Resource not found
    RateLimitError,     # 429: Too many requests
    InternalServerError, # 500+: Server issues
    APIConnectionError,  # Network issues
    APITimeoutError,    # Request timeout
)
```

### Error Handling Pattern

```python
try:
    response = client.messages.create(...)
except RateLimitError:
    # Wait and retry
except APITimeoutError:
    # Retry with longer timeout
except AuthenticationError:
    # Check API key
except APIError as e:
    # Log and handle other API errors
```

## Examples

### Basic Error Handling

```python
# examples/error_basic.py
"""Basic error handling for Claude API."""

from anthropic import Anthropic, RateLimitError, APITimeoutError, APIError
from dotenv import load_dotenv

load_dotenv()


def call_claude(prompt: str) -> str | None:
    """Make API call with basic error handling.

    Args:
        prompt: User message.

    Returns:
        Response text or None on error.
    """
    client = Anthropic()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    except RateLimitError as e:
        print(f"Rate limited. Retry after: {e.response.headers.get('retry-after', '?')}s")
        return None

    except APITimeoutError:
        print("Request timed out. Try again or increase timeout.")
        return None

    except APIError as e:
        print(f"API error {e.status_code}: {e.message}")
        return None


if __name__ == "__main__":
    result = call_claude("What is 2+2?")
    if result:
        print(f"Response: {result}")
```

### Retry with Exponential Backoff

```python
# examples/retry_backoff.py
"""Retry logic with exponential backoff."""

import time
import random
from anthropic import Anthropic, RateLimitError, APITimeoutError, InternalServerError
from dotenv import load_dotenv

load_dotenv()


def call_with_retry(
    prompt: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> str:
    """Make API call with exponential backoff retry.

    Args:
        prompt: User message.
        max_retries: Maximum retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap.

    Returns:
        Response text.

    Raises:
        Exception: If all retries exhausted.
    """
    client = Anthropic()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except (RateLimitError, APITimeoutError, InternalServerError) as e:
            last_error = e

            if attempt == max_retries:
                break

            # Calculate delay with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = random.uniform(0, delay * 0.1)
            total_delay = delay + jitter

            error_type = type(e).__name__
            print(f"Attempt {attempt + 1} failed ({error_type}). "
                  f"Retrying in {total_delay:.1f}s...")

            time.sleep(total_delay)

    raise Exception(f"All {max_retries + 1} attempts failed. Last error: {last_error}")


if __name__ == "__main__":
    try:
        result = call_with_retry("Explain Ohm's law briefly.")
        print(f"Response: {result}")
    except Exception as e:
        print(f"Failed: {e}")
```

### Custom Exceptions

```python
# examples/custom_exceptions.py
"""Custom exceptions for better error categorization."""


class LLMError(Exception):
    """Base exception for LLM operations."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    def __init__(self, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited. Retry after {retry_after}s" if retry_after else "Rate limited")


class LLMTimeoutError(LLMError):
    """Request timed out."""
    pass


class LLMAuthError(LLMError):
    """Authentication failed."""
    pass


class LLMContentFilterError(LLMError):
    """Content was filtered by safety system."""
    pass


# Usage in API wrapper
from anthropic import (
    Anthropic, RateLimitError, APITimeoutError,
    AuthenticationError, APIError
)


def call_claude(prompt: str) -> str:
    """Make API call with custom exception mapping."""
    client = Anthropic()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        # Check for content filtering
        if response.stop_reason == "content_filter":
            raise LLMContentFilterError("Response was filtered")

        return response.content[0].text

    except RateLimitError as e:
        retry_after = e.response.headers.get("retry-after")
        raise LLMRateLimitError(int(retry_after) if retry_after else None) from e

    except APITimeoutError as e:
        raise LLMTimeoutError("Request timed out") from e

    except AuthenticationError as e:
        raise LLMAuthError("Invalid API key") from e

    except APIError as e:
        raise LLMError(f"API error: {e.message}") from e
```

### Error Context and Logging

```python
# examples/error_logging.py
"""Error handling with proper logging and context."""

import logging
from anthropic import Anthropic, APIError
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def call_with_context(prompt: str, context: dict = None) -> str:
    """Make API call with contextual error logging.

    Args:
        prompt: User message.
        context: Additional context for logging.

    Returns:
        Response text.

    Raises:
        APIError: On API failure.
    """
    client = Anthropic()
    context = context or {}

    try:
        logger.info(f"Making API call", extra={"context": context})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        logger.info(
            f"API call successful",
            extra={
                "tokens_in": response.usage.input_tokens,
                "tokens_out": response.usage.output_tokens,
                **context
            }
        )

        return response.content[0].text

    except APIError as e:
        logger.error(
            f"API call failed: {e.message}",
            extra={
                "status_code": e.status_code,
                "request_id": getattr(e, 'request_id', None),
                **context
            },
            exc_info=True
        )
        raise


if __name__ == "__main__":
    result = call_with_context(
        "What is 2+2?",
        context={"user_id": "user_123", "session": "abc"}
    )
    print(result)
```

### Circuit Breaker Pattern

```python
# examples/circuit_breaker.py
"""Circuit breaker to prevent cascading failures."""

import time
from enum import Enum
from anthropic import Anthropic, APIError
from dotenv import load_dotenv

load_dotenv()


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if recovered


class CircuitBreaker:
    """Circuit breaker for API calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = 0

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset on successful call."""
        self.failures = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Track failure and potentially open circuit."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN


# Usage
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
client = Anthropic()


def make_call(prompt: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


# Protected call
try:
    result = breaker.call(make_call, "Hello")
    print(result)
except Exception as e:
    print(f"Call failed: {e}")
    print(f"Circuit state: {breaker.state.value}")
```

## Exercise

**Task:** Build a robust API caller that:

1. Retries on rate limits and server errors (max 3 retries)
2. Uses exponential backoff with jitter
3. Has a total timeout (don't retry forever)
4. Returns a result object with success/error info
5. Logs each attempt

**Function signature:**
```python
def robust_call(
    prompt: str,
    max_retries: int = 3,
    total_timeout: float = 120.0
) -> dict:
    """Returns {success: bool, response: str, attempts: int, error: str}"""
```

### Hints

<details>
<summary>Hint 1: Track total time</summary>

```python
start_time = time.time()
while time.time() - start_time < total_timeout:
    # try call
    # if retryable error, sleep and continue
    # else break
```
</details>

<details>
<summary>Hint 2: Retryable vs non-retryable</summary>

```python
RETRYABLE = (RateLimitError, APITimeoutError, InternalServerError)
NON_RETRYABLE = (AuthenticationError, BadRequestError)

except RETRYABLE:
    # retry
except NON_RETRYABLE:
    # don't retry, return error
```
</details>

<details>
<summary>Hint 3: Result structure</summary>

```python
return {
    "success": True,
    "response": response_text,
    "attempts": attempt + 1,
    "error": None
}
# or
return {
    "success": False,
    "response": None,
    "attempts": attempts_made,
    "error": str(last_error)
}
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Always Include Request ID in Error Reports

```python
except APIError as e:
    request_id = getattr(e, 'request_id', 'unknown')
    logger.error(f"API error (request_id: {request_id}): {e}")
    # Include request_id when contacting support
```

### 2. Distinguish Retryable from Fatal Errors

```python
RETRYABLE_ERRORS = (RateLimitError, APITimeoutError, InternalServerError)
FATAL_ERRORS = (AuthenticationError, PermissionDeniedError, BadRequestError)

except RETRYABLE_ERRORS:
    # Retry with backoff
except FATAL_ERRORS:
    # Don't retry, fix the root cause
```

### 3. Use Retry-After Header

```python
except RateLimitError as e:
    retry_after = int(e.response.headers.get('retry-after', 60))
    time.sleep(retry_after)
```

### 4. Set Appropriate Timeouts

```python
# Default might be too short for LLMs
client = Anthropic(
    timeout=httpx.Timeout(
        connect=5.0,
        read=120.0,  # LLM responses can be slow
        write=10.0,
        pool=5.0
    )
)
```

### 5. Graceful Degradation

```python
def get_response(prompt: str) -> str:
    try:
        return call_claude_opus(prompt)  # Best model
    except RateLimitError:
        return call_claude_sonnet(prompt)  # Fallback
    except APIError:
        return "Service temporarily unavailable"  # User message
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Catching `Exception` | Hides bugs | Catch specific exceptions |
| No retry limit | Infinite loop | Set max_retries |
| Fixed retry delay | Thundering herd | Use exponential backoff + jitter |
| Ignoring 400 errors | Won't fix itself | Log and alert on bad requests |
| Retrying auth errors | Won't help | Fix API key instead |

## LLM API Connection

Error handling patterns appear in:

```python
# Module 1: Basic resilience
response = call_with_retry(prompt)

# Module 7: Agent tool calls
# Agents need to handle tool failures gracefully
try:
    result = await tool.execute()
except ToolError:
    return "I couldn't complete that action"

# Module 8: Production
# Circuit breakers, monitoring, alerting
if breaker.state == CircuitState.OPEN:
    alert_ops_team()
```

## Next Section

[Section 6: Type Hints & Pydantic →](../06-type-hints-pydantic/)
