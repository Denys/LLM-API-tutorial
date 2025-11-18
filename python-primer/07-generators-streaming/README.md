# Section 7: Generators & Streaming

**Duration:** 20 minutes | **Difficulty:** Intermediate

## Why This Matters for LLM APIs

LLMs generate tokens sequentially. Streaming lets you:
- **Show responses immediately** - Better UX than waiting for complete response
- **Process incrementally** - Parse/filter as tokens arrive
- **Save memory** - Don't load entire response into memory
- **Implement timeouts** - Cancel if first token takes too long

## Concepts

### Generator Basics

```python
# Regular function - returns all at once
def get_all():
    return [1, 2, 3, 4, 5]  # Builds entire list in memory

# Generator - yields one at a time
def get_one_by_one():
    for i in range(1, 6):
        yield i  # Produces value, pauses, resumes on next()

# Usage
for value in get_one_by_one():
    print(value)  # Processes each value as it's generated
```

### Generator vs List

| Aspect | List | Generator |
|--------|------|-----------|
| Memory | All items at once | One item at a time |
| Creation | Immediate | Lazy (on demand) |
| Reusable | Yes | No (exhausted after use) |
| Length | Known | Unknown until exhausted |

### Async Generators

```python
async def async_generator():
    for i in range(5):
        await asyncio.sleep(0.1)
        yield i

# Usage
async for value in async_generator():
    print(value)
```

## Examples

### Basic Generator

```python
# examples/generator_basic.py
"""Basic generator patterns."""


def count_up_to(n: int):
    """Generate integers from 1 to n.

    Args:
        n: Upper limit.

    Yields:
        Integers 1 through n.
    """
    i = 1
    while i <= n:
        yield i
        i += 1


def token_stream(text: str):
    """Simulate token streaming.

    Args:
        text: Text to stream as tokens.

    Yields:
        Individual words with small delay simulation.
    """
    import time
    for word in text.split():
        time.sleep(0.1)  # Simulate network delay
        yield word + " "


# Usage
if __name__ == "__main__":
    print("Numbers:")
    for num in count_up_to(5):
        print(num, end=" ")
    print()

    print("\nStreamed text:")
    for token in token_stream("This is a streaming response from the model."):
        print(token, end="", flush=True)
    print()
```

### Streaming Claude Responses

```python
# examples/claude_streaming.py
"""Stream Claude API responses."""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


def stream_response(prompt: str):
    """Stream Claude's response token by token.

    Args:
        prompt: User message.

    Yields:
        Text chunks as they arrive.
    """
    client = Anthropic()

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield text


def stream_with_stats(prompt: str):
    """Stream response with token counting.

    Args:
        prompt: User message.

    Yields:
        Text chunks.

    Returns:
        Final message with usage stats.
    """
    client = Anthropic()

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield text

        # After streaming completes, get final message
        response = stream.get_final_message()
        print(f"\n\n[Tokens: {response.usage.input_tokens} in, "
              f"{response.usage.output_tokens} out]")


if __name__ == "__main__":
    prompt = "Explain PWM in 3 sentences."

    print(f"Prompt: {prompt}\n")
    print("Response: ", end="")

    for chunk in stream_with_stats(prompt):
        print(chunk, end="", flush=True)
```

### Processing Stream Incrementally

```python
# examples/stream_processing.py
"""Process streaming responses incrementally."""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


def stream_and_detect(prompt: str, stop_phrase: str):
    """Stream until a phrase is detected.

    Args:
        prompt: User message.
        stop_phrase: Phrase to stop on (case-insensitive).

    Yields:
        Text chunks until stop phrase.

    Returns:
        Whether stop phrase was found.
    """
    client = Anthropic()
    buffer = ""
    found = False

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            buffer += text
            yield text

            if stop_phrase.lower() in buffer.lower():
                found = True
                print(f"\n[Detected: '{stop_phrase}']")
                break

    return found


def stream_to_lines(prompt: str):
    """Convert token stream to line stream.

    Args:
        prompt: User message.

    Yields:
        Complete lines as they become available.
    """
    client = Anthropic()
    buffer = ""

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            buffer += text

            # Yield complete lines
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                yield line

        # Yield remaining buffer
        if buffer:
            yield buffer


if __name__ == "__main__":
    # Example: Stream until key phrase
    prompt = "List 5 electronic components with brief descriptions."

    print("Streaming with detection:\n")
    for chunk in stream_and_detect(prompt, "resistor"):
        print(chunk, end="", flush=True)
```

### Async Streaming

```python
# examples/async_streaming.py
"""Async streaming for better concurrency."""

import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()


async def stream_response_async(prompt: str):
    """Async stream Claude's response.

    Args:
        prompt: User message.

    Yields:
        Text chunks asynchronously.
    """
    client = AsyncAnthropic()

    async with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def parallel_streams():
    """Stream multiple prompts in parallel."""
    prompts = [
        "What is a resistor? (1 sentence)",
        "What is a capacitor? (1 sentence)",
        "What is an inductor? (1 sentence)"
    ]

    async def stream_one(i: int, prompt: str):
        """Stream a single prompt and collect result."""
        client = AsyncAnthropic()
        chunks = []

        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                chunks.append(text)

        return i, "".join(chunks)

    # Run all streams in parallel
    tasks = [stream_one(i, p) for i, p in enumerate(prompts)]
    results = await asyncio.gather(*tasks)

    # Print results in order
    for i, response in sorted(results):
        component = prompts[i].split()[3].rstrip("?")
        print(f"{component}: {response}\n")


async def main():
    print("Single async stream:")
    async for chunk in stream_response_async("What is Ohm's law?"):
        print(chunk, end="", flush=True)
    print("\n")

    print("Parallel streams:")
    await parallel_streams()


if __name__ == "__main__":
    asyncio.run(main())
```

### Generator Pipeline

```python
# examples/generator_pipeline.py
"""Chain generators for processing pipeline."""


def token_source(text: str):
    """Generate tokens from text."""
    for word in text.split():
        yield word


def filter_short(tokens, min_length: int = 3):
    """Filter tokens by minimum length."""
    for token in tokens:
        if len(token) >= min_length:
            yield token


def add_prefix(tokens, prefix: str = "> "):
    """Add prefix to each token."""
    for token in tokens:
        yield prefix + token


def collect(generator, separator: str = "\n") -> str:
    """Collect generator output into string."""
    return separator.join(generator)


# Pipeline example
text = "A quick brown fox jumps over the lazy dog"

# Chain generators
pipeline = add_prefix(
    filter_short(
        token_source(text),
        min_length=4
    ),
    prefix="- "
)

result = collect(pipeline)
print(result)

# Equivalent using intermediate variables:
# tokens = token_source(text)
# filtered = filter_short(tokens, 4)
# prefixed = add_prefix(filtered, "- ")
# result = collect(prefixed)
```

## Exercise

**Task:** Build a streaming response processor that:

1. Streams a Claude response
2. Counts words as they arrive
3. Detects and extracts any numbers mentioned
4. Returns a summary after completion

**Function signature:**
```python
def stream_and_analyze(prompt: str) -> dict:
    """Stream response and analyze content.

    Returns:
        {
            "response": str,  # Full response
            "word_count": int,
            "numbers_found": list[float],
            "tokens_in": int,
            "tokens_out": int
        }
    """
```

### Hints

<details>
<summary>Hint 1: Extract numbers with regex</summary>

```python
import re

def extract_numbers(text: str) -> list[float]:
    pattern = r'-?\d+\.?\d*'
    return [float(x) for x in re.findall(pattern, text)]
```
</details>

<details>
<summary>Hint 2: Count words incrementally</summary>

```python
word_count = 0
buffer = ""
for chunk in stream:
    buffer += chunk
    # Count complete words
    words = buffer.split()
    if buffer.endswith(' ') or buffer.endswith('\n'):
        word_count += len(words)
        buffer = ""
    else:
        word_count += len(words) - 1
        buffer = words[-1] if words else ""
```
</details>

<details>
<summary>Hint 3: Get final message for token counts</summary>

```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        # process text
        pass

    # After stream completes
    final = stream.get_final_message()
    tokens_in = final.usage.input_tokens
    tokens_out = final.usage.output_tokens
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Always Use `flush=True` for Real-Time Display

```python
for chunk in stream:
    print(chunk, end="", flush=True)  # Immediate display
```

### 2. Get Final Message for Complete Info

```python
with client.messages.stream(...) as stream:
    for text in stream.text_stream:
        yield text

    # Full response object available after streaming
    final = stream.get_final_message()
    print(f"Stop reason: {final.stop_reason}")
    print(f"Usage: {final.usage}")
```

### 3. Handle First-Token Timeout

```python
import time

first_token_received = False
start_time = time.time()

for chunk in stream:
    if not first_token_received:
        first_token_time = time.time() - start_time
        if first_token_time > 10:  # Too slow
            raise TimeoutError("First token timeout")
        first_token_received = True
    yield chunk
```

### 4. Buffer for Complete Sentences

```python
def stream_sentences(prompt: str):
    """Yield complete sentences instead of tokens."""
    buffer = ""
    for chunk in stream_response(prompt):
        buffer += chunk
        while '. ' in buffer or '.\n' in buffer:
            # Find sentence end
            for end in ['. ', '.\n']:
                if end in buffer:
                    sentence, buffer = buffer.split(end, 1)
                    yield sentence + '.'
                    break
    if buffer.strip():
        yield buffer
```

### 5. Use Generator Expressions for Simple Cases

```python
# Instead of explicit generator function
def squares(n):
    for i in range(n):
        yield i ** 2

# Use generator expression
squares = (i ** 2 for i in range(n))
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Not flushing output | Text appears in chunks | Use `flush=True` |
| Trying to reuse generator | Already exhausted | Create new generator |
| Not getting final message | Missing usage stats | Call `get_final_message()` |
| Blocking in async generator | Defeats purpose | Use `await` for I/O |
| Large buffer accumulation | Memory usage | Process and clear buffer |

## LLM API Connection

Streaming is used throughout:

```python
# Module 1: Basic streaming
for chunk in client.messages.stream(...):
    print(chunk.text, end="")

# Module 3: Streaming with tools
# Tool calls come as complete events
for event in stream:
    if event.type == "content_block_start":
        if event.content_block.type == "tool_use":
            # Handle tool call

# Module 7: Agent streaming
# Stream agent thoughts and actions to user
async for chunk in agent.run_stream(prompt):
    display_to_user(chunk)

# Module 8: Production APIs
@app.post("/stream")
async def stream_endpoint(request: Request):
    async def generate():
        async for chunk in stream_response(request.prompt):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
    return StreamingResponse(generate())
```

## Next Section

[Section 8: Decorators & Context Managers →](../08-decorators-context-managers/)
