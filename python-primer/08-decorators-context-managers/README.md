# Section 8: Decorators & Context Managers

**Duration:** 15 minutes | **Difficulty:** Intermediate

## Why This Matters for LLM APIs

- **Decorators:** Add retry logic, caching, logging, timing to API calls
- **Context Managers:** Ensure resources (clients, files, connections) are properly cleaned up

These patterns make your code more maintainable and reusable.

## Concepts

### Decorators

A decorator wraps a function to add behavior:

```python
@decorator
def my_function():
    pass

# Equivalent to:
my_function = decorator(my_function)
```

### Context Managers

Ensure cleanup happens even on errors:

```python
with open("file.txt") as f:
    data = f.read()
# File is closed automatically, even if read() raises an exception

# Custom context manager
with resource_manager() as resource:
    use(resource)
# Cleanup happens automatically
```

## Examples

### Simple Decorator

```python
# examples/decorator_simple.py
"""Simple decorator patterns."""

import time
from functools import wraps


def timer(func):
    """Measure function execution time."""
    @wraps(func)  # Preserve original function metadata
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper


@timer
def slow_function():
    """A slow function."""
    time.sleep(1)
    return "done"


# Usage
result = slow_function()
# Output: slow_function took 1.00s
```

### Retry Decorator

```python
# examples/retry_decorator.py
"""Retry decorator for API calls."""

import time
import random
from functools import wraps
from anthropic import RateLimitError, APITimeoutError, InternalServerError


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple = (RateLimitError, APITimeoutError, InternalServerError)
):
    """Decorator to retry function on specific exceptions.

    Args:
        max_attempts: Maximum retry attempts.
        base_delay: Initial delay between retries.
        exceptions: Exceptions to catch and retry.

    Returns:
        Decorator function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        jitter = random.uniform(0, delay * 0.1)
                        time.sleep(delay + jitter)
                        print(f"Retry {attempt + 1}/{max_attempts - 1}...")

            raise last_exception

        return wrapper
    return decorator


# Usage
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

@retry(max_attempts=3, base_delay=1.0)
def call_claude(prompt: str) -> str:
    """Make API call with automatic retries."""
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

### Caching Decorator

```python
# examples/cache_decorator.py
"""Caching decorator for expensive API calls."""

import hashlib
import json
import time
from functools import wraps


def cache_response(ttl_seconds: int = 3600):
    """Cache function results for specified duration.

    Args:
        ttl_seconds: Cache time-to-live in seconds.

    Returns:
        Decorator function.
    """
    cache = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            # Check cache
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl_seconds:
                    print(f"Cache hit for {func.__name__}")
                    return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            print(f"Cache miss for {func.__name__}")

            return result

        # Allow cache clearing
        wrapper.clear_cache = lambda: cache.clear()

        return wrapper
    return decorator


# Usage
@cache_response(ttl_seconds=300)  # 5 minutes
def get_embedding(text: str) -> list[float]:
    """Get embedding for text (expensive operation)."""
    # ... API call to embedding service
    pass
```

### Logging Decorator

```python
# examples/logging_decorator.py
"""Logging decorator for API calls."""

import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_call(func):
    """Log function calls with arguments and results."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Log call
        arg_str = ", ".join(
            [repr(a) for a in args] +
            [f"{k}={v!r}" for k, v in kwargs.items()]
        )
        logger.info(f"Calling {func.__name__}({arg_str})")

        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} returned successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise

    return wrapper


@log_call
def process_prompt(prompt: str, max_tokens: int = 100) -> str:
    """Process a prompt."""
    return f"Processed: {prompt[:20]}..."
```

### Context Manager Basics

```python
# examples/context_basic.py
"""Basic context manager patterns."""

from contextlib import contextmanager
import time


@contextmanager
def timer_context(name: str = "Operation"):
    """Time a block of code.

    Args:
        name: Name for the timed operation.

    Yields:
        None (just provides timing).
    """
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        print(f"{name} took {elapsed:.2f}s")


# Usage
with timer_context("API call"):
    # ... do work
    time.sleep(1)
# Output: API call took 1.00s


@contextmanager
def temporary_env_var(key: str, value: str):
    """Temporarily set an environment variable.

    Args:
        key: Environment variable name.
        value: Temporary value.

    Yields:
        None.
    """
    import os
    old_value = os.environ.get(key)

    try:
        os.environ[key] = value
        yield
    finally:
        if old_value is None:
            del os.environ[key]
        else:
            os.environ[key] = old_value


# Usage
with temporary_env_var("MODEL", "claude-haiku"):
    # Use haiku temporarily
    pass
# Original MODEL restored
```

### API Client Context Manager

```python
# examples/client_context.py
"""Context manager for API client lifecycle."""

from contextlib import contextmanager
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def claude_client(model: str = "claude-sonnet-4-20250514"):
    """Context manager for Claude API client.

    Args:
        model: Default model to use.

    Yields:
        Tuple of (client, call_function).
    """
    client = Anthropic()
    call_count = 0
    total_tokens = 0

    def call(prompt: str, **kwargs) -> str:
        nonlocal call_count, total_tokens

        response = client.messages.create(
            model=model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": "user", "content": prompt}]
        )

        call_count += 1
        total_tokens += response.usage.input_tokens + response.usage.output_tokens

        return response.content[0].text

    try:
        yield call
    finally:
        print(f"Session complete: {call_count} calls, {total_tokens} tokens")


# Usage
with claude_client() as call:
    result1 = call("What is 2+2?")
    result2 = call("What is 3+3?")
# Output: Session complete: 2 calls, 150 tokens
```

### Combining Decorators

```python
# examples/combined.py
"""Combining multiple decorators."""

from functools import wraps
import time


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {time.time() - start:.2f}s")
        return result
    return wrapper


def retry(max_attempts=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_attempts - 1:
                        raise
                    time.sleep(1)
        return wrapper
    return decorator


# Order matters: bottom decorator applied first
@timer          # Applied second (wraps the retried function)
@retry(3)       # Applied first (wraps original function)
def api_call():
    """Make API call with retry and timing."""
    pass

# Equivalent to: timer(retry(3)(api_call))
```

## Exercise

**Task:** Create a decorator suite for LLM API calls:

1. `@rate_limit(calls_per_minute=10)` - Enforce rate limiting
2. `@track_cost(model="sonnet")` - Track and display cumulative cost
3. Combine them with existing retry and timer decorators

**Test with:**
```python
@track_cost(model="sonnet")
@rate_limit(calls_per_minute=10)
@retry(max_attempts=3)
def my_api_call(prompt: str) -> str:
    ...
```

### Hints

<details>
<summary>Hint 1: Rate limiting with timestamps</summary>

```python
def rate_limit(calls_per_minute: int):
    call_times = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_times
            now = time.time()

            # Remove old timestamps
            call_times = [t for t in call_times if now - t < 60]

            if len(call_times) >= calls_per_minute:
                sleep_time = 60 - (now - call_times[0])
                time.sleep(sleep_time)
                call_times = []

            result = func(*args, **kwargs)
            call_times.append(time.time())
            return result
        return wrapper
    return decorator
```
</details>

<details>
<summary>Hint 2: Cost tracking with closure</summary>

```python
COSTS = {"sonnet": (3, 15), "opus": (15, 75)}  # (input, output) per 1M

def track_cost(model: str = "sonnet"):
    total_cost = 0

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal total_cost
            result = func(*args, **kwargs)
            # Need access to token counts somehow
            # Could return dict or use response object
        return wrapper
    return decorator
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Always Use `@wraps`

```python
from functools import wraps

def my_decorator(func):
    @wraps(func)  # Preserves __name__, __doc__, etc.
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

### 2. Decorator Order Matters

```python
@decorator_a  # Applied last (outermost)
@decorator_b  # Applied first (innermost)
def func():
    pass

# = decorator_a(decorator_b(func))
```

### 3. Class-Based Decorators for State

```python
class CallCounter:
    def __init__(self, func):
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)

@CallCounter
def my_func():
    pass

my_func()
print(my_func.count)  # 1
```

### 4. Async Context Managers

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_client():
    client = AsyncAnthropic()
    try:
        yield client
    finally:
        await client.close()

async with async_client() as client:
    await client.messages.create(...)
```

### 5. Context Manager as Decorator

```python
from contextlib import contextmanager

@contextmanager
def error_handler():
    try:
        yield
    except APIError as e:
        logger.error(f"API error: {e}")
        raise

# Use as context manager
with error_handler():
    api_call()

# Or as decorator
@error_handler()
def api_call():
    pass
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Forgetting `@wraps` | Lost function metadata | Always use `@wraps(func)` |
| Wrong decorator order | Unexpected behavior | Inner decorators wrap first |
| Not handling exceptions in context manager | Cleanup skipped | Use `try/finally` |
| Mutable default in decorator | Shared state | Use closure or class |
| Not yielding in context manager | Nothing returned | Must have `yield` |

## LLM API Connection

These patterns appear throughout:

```python
# Module 5: MCP tools
@mcp_tool("calculator")
def calculate(operation: str, a: float, b: float):
    ...

# Module 7: Agent action logging
@log_action
async def agent_step(state: AgentState):
    ...

# Module 8: Production patterns
@rate_limit(100)
@retry(3)
@track_tokens
async def production_call(prompt: str):
    ...

# Streaming with context manager
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        yield text
```

## Capstone

You've completed all sections! Now combine everything in the [Capstone Mini-Project →](../exercises/capstone/)
