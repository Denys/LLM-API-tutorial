# Claude API Quick Reference

A cheat sheet for common operations covered in this tutorial.

## Table of Contents
- [Basic API Calls](#basic-api-calls)
- [Token Optimization](#token-optimization)
- [Function Calling](#function-calling)
- [Streaming](#streaming)
- [Vision API](#vision-api)
- [Best Practices](#best-practices)
- [Common Errors](#common-errors)

---

## Basic API Calls

### Python

```python
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key")

# Simple message
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(message.content[0].text)
```

### JavaScript

```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const message = await client.messages.create({
  model: 'claude-3-5-sonnet-20241022',
  max_tokens: 1024,
  messages: [
    { role: 'user', content: 'Hello, Claude!' }
  ]
});

console.log(message.content[0].text);
```

---

## Token Optimization

### Count Tokens

```python
import tiktoken

# Approximate token counting
def count_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

tokens = count_tokens("Your text here")
print(f"Tokens: {tokens}")
```

### Prompt Caching

```python
# Cache system prompts and large contexts
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a helpful assistant...",
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[...]
)
```

### Streaming for Better UX

```python
# Stream responses
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

## Function Calling

### Define Tools

```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    }
]
```

### Use Tools

```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"}
    ]
)

# Check if Claude wants to use a tool
if message.stop_reason == "tool_use":
    tool_use = next(block for block in message.content if block.type == "tool_use")
    tool_name = tool_use.name
    tool_input = tool_use.input

    # Execute your function
    result = get_weather(tool_input["location"])

    # Send result back to Claude
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather in Paris?"},
            {"role": "assistant", "content": message.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": str(result)
                    }
                ]
            }
        ]
    )
```

---

## Streaming

### Basic Streaming

```python
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Count to 10"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Streaming with Events

```python
with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            print(event.delta.text, end="", flush=True)
        elif event.type == "message_stop":
            print("\n[Complete]")
```

---

## Vision API

### Analyze Image (Base64)

```python
import base64

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": encode_image("image.jpg")
                    }
                },
                {
                    "type": "text",
                    "text": "Describe this image"
                }
            ]
        }
    ]
)
```

### Analyze Image (URL)

```python
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": "https://example.com/image.jpg"
                    }
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }
    ]
)
```

---

## Best Practices

### System Prompts

```python
# Use system prompts for role/context
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system="You are a helpful Python tutor. Explain concepts clearly with examples.",
    messages=[
        {"role": "user", "content": "What are list comprehensions?"}
    ]
)
```

### Temperature Control

```python
# Creative tasks: higher temperature (0.7-1.0)
creative = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    temperature=0.9,
    messages=[{"role": "user", "content": "Write a creative story"}]
)

# Analytical tasks: lower temperature (0.0-0.3)
analytical = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    temperature=0.2,
    messages=[{"role": "user", "content": "Analyze this data"}]
)
```

### Error Handling

```python
from anthropic import APIError, APITimeoutError, RateLimitError
import time

def call_claude_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.messages.create(...)
        except RateLimitError:
            wait_time = 2 ** attempt
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
        except APITimeoutError:
            print(f"Timeout on attempt {attempt + 1}")
        except APIError as e:
            print(f"API error: {e}")
            raise

    raise Exception("Max retries exceeded")
```

### Conversation History

```python
# Maintain conversation context
conversation = []

def chat(user_message: str):
    conversation.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=conversation
    )

    assistant_message = response.content[0].text
    conversation.append({"role": "assistant", "content": assistant_message})

    return assistant_message

# Use it
chat("Hello!")
chat("What's 2+2?")
chat("Why?")  # Claude remembers context
```

---

## Common Errors

### Authentication Error

```
Error: 401 Unauthorized
```
**Fix:** Check your API key in .env file

### Rate Limit Error

```
Error: 429 Too Many Requests
```
**Fix:** Implement exponential backoff, upgrade tier

### Token Limit Exceeded

```
Error: max_tokens exceeds maximum
```
**Fix:** Reduce max_tokens or use a model with larger context

### Invalid Model Name

```
Error: Invalid model
```
**Fix:** Use correct model names:
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`
- `claude-3-opus-20240229`

### Content Moderation

```
Error: Content violates usage policy
```
**Fix:** Review content policy, rephrase request

---

## Cost Estimation

### Model Pricing (as of 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Haiku | $0.25 | $1.25 |
| Sonnet | $3.00 | $15.00 |
| Opus | $15.00 | $75.00 |

### Calculate Cost

```python
def calculate_cost(input_tokens: int, output_tokens: int, model: str = "haiku"):
    rates = {
        "haiku": (0.25, 1.25),
        "sonnet": (3.00, 15.00),
        "opus": (15.00, 75.00)
    }

    input_rate, output_rate = rates[model]
    cost = (input_tokens / 1_000_000 * input_rate +
            output_tokens / 1_000_000 * output_rate)
    return cost

# Example
cost = calculate_cost(1000, 500, "sonnet")
print(f"Cost: ${cost:.6f}")
```

---

## Model Selection Guide

- **Haiku** - Fast, cheap, simple tasks
  - Classification
  - Data extraction
  - Simple Q&A

- **Sonnet** - Balanced, most versatile
  - Complex reasoning
  - Code generation
  - Most production use cases

- **Opus** - Most capable, expensive
  - Research tasks
  - Advanced reasoning
  - Creative writing

---

## Useful Links

- [Anthropic Documentation](https://docs.anthropic.com)
- [API Reference](https://docs.anthropic.com/api-reference)
- [Prompt Engineering Guide](https://docs.anthropic.com/prompt-engineering)
- [Community Discord](https://discord.gg/anthropic)
- [Anthropic Console](https://console.anthropic.com)

---

**Need more details?** Refer to the specific module in the tutorial:
- Module 1: Basics
- Module 2: Optimization
- Module 3: Advanced Features
- Module 4: RAG
- Module 5: MCP
- Module 6: Claude Code
- Module 7: Agents
- Module 8: Production
