# Section 4: Async/Await Essentials

**Duration:** 25 minutes | **Difficulty:** Intermediate

## Why This Matters for LLM APIs

LLM API calls are I/O-bound (waiting for network). Async enables:
- **Streaming:** Process tokens as they arrive
- **Parallel calls:** Multiple API requests simultaneously
- **Efficient batching:** Process many prompts without blocking

Synchronous code waits idle during network calls. Async code does useful work while waiting.

## Concepts

### Sync vs Async Mental Model

```python
# Synchronous - blocking
def get_responses():
    r1 = call_api(prompt1)  # Wait 2s
    r2 = call_api(prompt2)  # Wait 2s
    r3 = call_api(prompt3)  # Wait 2s
    return [r1, r2, r3]     # Total: 6s

# Asynchronous - concurrent
async def get_responses():
    tasks = [
        call_api_async(prompt1),
        call_api_async(prompt2),
        call_api_async(prompt3)
    ]
    return await asyncio.gather(*tasks)  # Total: ~2s
```

### Core Syntax

```python
import asyncio

# Define async function
async def fetch_data():
    await some_io_operation()  # Yield control during I/O
    return result

# Run async code
asyncio.run(fetch_data())

# Run multiple tasks concurrently
results = await asyncio.gather(task1, task2, task3)
```

### Key Rules

1. `async def` creates a coroutine function
2. `await` can only be used inside `async` functions
3. `await` yields control, allowing other tasks to run
4. `asyncio.run()` is the entry point from sync code

## Examples

### Basic Async Function

```python
# examples/async_basic.py
"""Basic async/await pattern."""

import asyncio
import time

async def simulate_api_call(prompt: str, delay: float = 1.0) -> str:
    """Simulate an async API call.

    Args:
        prompt: The input prompt.
        delay: Simulated network delay.

    Returns:
        Simulated response.
    """
    print(f"Starting: {prompt[:20]}...")
    await asyncio.sleep(delay)  # Non-blocking sleep
    print(f"Completed: {prompt[:20]}...")
    return f"Response to: {prompt}"


async def main():
    """Run a single async call."""
    result = await simulate_api_call("What is Python?")
    print(f"Result: {result}")


# Entry point
if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    print(f"Total time: {time.time() - start:.2f}s")
```

### Parallel API Calls

```python
# examples/parallel_calls.py
"""Run multiple API calls in parallel."""

import asyncio
import time
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()


async def call_claude(client: AsyncAnthropic, prompt: str) -> str:
    """Make async API call to Claude.

    Args:
        client: Async Anthropic client.
        prompt: User message.

    Returns:
        Response text.
    """
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


async def main():
    """Process multiple prompts in parallel."""
    client = AsyncAnthropic()

    prompts = [
        "What is a resistor? (1 sentence)",
        "What is a capacitor? (1 sentence)",
        "What is an inductor? (1 sentence)",
        "What is a diode? (1 sentence)",
    ]

    # Create tasks for all prompts
    tasks = [call_claude(client, prompt) for prompt in prompts]

    # Run all tasks concurrently
    start = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    # Display results
    for prompt, result in zip(prompts, results):
        component = prompt.split()[3].rstrip("?")
        print(f"{component}: {result}\n")

    print(f"Processed {len(prompts)} prompts in {elapsed:.2f}s")
    print(f"(Sequential would take ~{len(prompts) * 2}s)")


if __name__ == "__main__":
    asyncio.run(main())
```

### Async with Rate Limiting

```python
# examples/rate_limited_async.py
"""Async calls with rate limiting using semaphore."""

import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()


async def call_with_limit(
    semaphore: asyncio.Semaphore,
    client: AsyncAnthropic,
    prompt: str
) -> str:
    """Make rate-limited async API call.

    Args:
        semaphore: Concurrency limiter.
        client: Async Anthropic client.
        prompt: User message.

    Returns:
        Response text.
    """
    async with semaphore:  # Only N concurrent calls
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


async def main():
    """Process many prompts with concurrency limit."""
    client = AsyncAnthropic()

    # Limit to 5 concurrent requests
    semaphore = asyncio.Semaphore(5)

    prompts = [f"What is the number {i}?" for i in range(20)]

    tasks = [
        call_with_limit(semaphore, client, prompt)
        for prompt in prompts
    ]

    results = await asyncio.gather(*tasks)
    print(f"Processed {len(results)} prompts")


if __name__ == "__main__":
    asyncio.run(main())
```

### Async Streaming

```python
# examples/async_streaming.py
"""Stream responses asynchronously."""

import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()


async def stream_response(prompt: str):
    """Stream Claude's response token by token.

    Args:
        prompt: User message.
    """
    client = AsyncAnthropic()

    print(f"Prompt: {prompt}\nResponse: ", end="", flush=True)

    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)

    print("\n")


async def main():
    await stream_response("Explain MOSFET gate charge in 3 sentences.")


if __name__ == "__main__":
    asyncio.run(main())
```

### Mixing Sync and Async

```python
# examples/sync_async_bridge.py
"""Bridge between sync and async code."""

import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()


async def async_call(prompt: str) -> str:
    """Async API call."""
    client = AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def sync_wrapper(prompt: str) -> str:
    """Call async function from sync code.

    Args:
        prompt: User message.

    Returns:
        Response text.
    """
    return asyncio.run(async_call(prompt))


# For use in existing sync codebase
if __name__ == "__main__":
    result = sync_wrapper("What is 2+2?")
    print(result)
```

## Exercise

**Task:** Build an async batch processor that:

1. Takes a list of prompts
2. Processes them in parallel with configurable concurrency limit
3. Returns results in original order
4. Tracks total tokens used
5. Handles individual failures without stopping others

**Function signature:**
```python
async def batch_process(
    prompts: list[str],
    max_concurrent: int = 5
) -> list[dict]:
    """Process prompts in parallel.

    Returns:
        List of {prompt, response, tokens, error} dicts
    """
```

### Hints

<details>
<summary>Hint 1: Semaphore for concurrency</summary>

```python
semaphore = asyncio.Semaphore(max_concurrent)

async def process_one(prompt):
    async with semaphore:
        # make API call
```
</details>

<details>
<summary>Hint 2: Handle errors without stopping</summary>

```python
async def process_one(prompt):
    try:
        response = await client.messages.create(...)
        return {"prompt": prompt, "response": response.content[0].text, "error": None}
    except Exception as e:
        return {"prompt": prompt, "response": None, "error": str(e)}
```
</details>

<details>
<summary>Hint 3: Preserve order with gather</summary>

```python
tasks = [process_one(p) for p in prompts]
results = await asyncio.gather(*tasks)
# Results are in same order as tasks
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Use AsyncClient for Connection Reuse

```python
# BAD - new client per call
async def call():
    client = AsyncAnthropic()
    return await client.messages.create(...)

# GOOD - reuse client
client = AsyncAnthropic()
async def call():
    return await client.messages.create(...)
```

### 2. asyncio.gather vs asyncio.wait

```python
# gather: Returns results in order, raises on first error
results = await asyncio.gather(*tasks)

# gather with return_exceptions: Capture errors instead of raising
results = await asyncio.gather(*tasks, return_exceptions=True)

# wait: More control over completion handling
done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
```

### 3. Timeouts for Async Operations

```python
try:
    result = await asyncio.wait_for(
        client.messages.create(...),
        timeout=30.0
    )
except asyncio.TimeoutError:
    print("Request timed out")
```

### 4. Don't Block the Event Loop

```python
# BAD - blocks event loop
import time
await asyncio.sleep(0)
time.sleep(1)  # Blocks everything!

# GOOD - use async sleep
await asyncio.sleep(1)

# For CPU-bound work, use executor
loop = asyncio.get_event_loop()
result = await loop.run_in_executor(None, cpu_bound_function)
```

### 5. Debug with asyncio.current_task()

```python
import asyncio

async def my_task():
    task = asyncio.current_task()
    print(f"Running: {task.get_name()}")
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Forgetting `await` | Returns coroutine object | Always await async calls |
| `asyncio.run()` inside async | RuntimeError | Use `await` instead |
| Creating too many tasks | Memory exhaustion | Use semaphore to limit |
| Not handling exceptions | Silent failures | Use try/except or `return_exceptions=True` |
| Mixing sync HTTP clients | Blocks event loop | Use httpx.AsyncClient |

## LLM API Connection

Async is used throughout advanced modules:

```python
# Module 2: Batch processing for cost analysis
results = await asyncio.gather(*[analyze(doc) for doc in docs])

# Module 3: Parallel tool calls
tool_results = await asyncio.gather(*[call_tool(t) for t in tools])

# Module 7: Agents
# Multi-agent systems use async for concurrent agent execution
await asyncio.gather(
    agent1.think(),
    agent2.think(),
    agent3.think()
)

# Module 8: Production
# Async enables high-throughput API servers
@app.post("/generate")
async def generate(request: Request):
    return await client.messages.create(...)
```

## Next Section

[Section 5: Error Handling →](../05-error-handling/)
