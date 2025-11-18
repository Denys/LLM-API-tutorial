# Capstone Mini-Project: Build a Production-Ready LLM Client

**Duration:** 30-45 minutes | **Difficulty:** Intermediate

## Objective

Build a complete LLM client that combines all concepts from the primer:
- Environment configuration
- JSON handling
- HTTP understanding
- Async operations
- Error handling with retries
- Type hints and Pydantic models
- Streaming responses
- Decorators and context managers

## Requirements

### Core Features

1. **Configuration** (Section 1)
   - Load API key from environment
   - Support configurable model, max_tokens, temperature
   - Validate configuration on startup

2. **Type Safety** (Section 6)
   - Define Pydantic models for Message, Response, Usage
   - Type hints on all functions

3. **API Client** (Sections 3, 5)
   - Support both sync and async calls
   - Automatic retry with exponential backoff
   - Proper error handling and custom exceptions

4. **Streaming** (Section 7)
   - Stream responses with real-time display
   - Track tokens during streaming

5. **Observability** (Sections 5, 8)
   - Log all API calls
   - Track cumulative token usage and cost
   - Measure response times

### Stretch Goals

- Conversation history management
- Prompt caching support
- Parallel batch processing
- Rate limiting

## Specification

```python
# Usage should look like this:

from llm_client import LLMClient, Config

# Initialize
config = Config.from_env()
client = LLMClient(config)

# Single call
response = client.chat("What is Python?")
print(response.text)
print(f"Tokens: {response.usage.total}")

# Streaming
for chunk in client.stream("Explain async/await"):
    print(chunk, end="", flush=True)

# Async batch
results = await client.batch_async([
    "What is a list?",
    "What is a dict?",
    "What is a tuple?"
])

# Session stats
print(client.get_stats())
```

## File Structure

```
exercises/capstone/
├── README.md           # This file
├── llm_client.py       # Your implementation
├── models.py           # Pydantic models
└── test_client.py      # Test your implementation
```

## Implementation Guide

### Step 1: Models (models.py)

Define your data structures:

```python
from pydantic import BaseModel, Field
from typing import Optional

class Config(BaseModel):
    """Client configuration."""
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: float = 60.0

    @classmethod
    def from_env(cls) -> "Config":
        """Load from environment."""
        ...

class Usage(BaseModel):
    """Token usage."""
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
```

### Step 2: Client Class (llm_client.py)

```python
class LLMClient:
    def __init__(self, config: Config):
        self.config = config
        self._client = Anthropic(api_key=config.api_key)
        self._stats = {"calls": 0, "tokens": 0, "cost": 0.0}

    def chat(self, prompt: str, **kwargs) -> Response:
        """Single chat completion."""
        ...

    def stream(self, prompt: str, **kwargs):
        """Stream chat completion."""
        ...

    async def chat_async(self, prompt: str, **kwargs) -> Response:
        """Async chat completion."""
        ...

    async def batch_async(self, prompts: list[str], **kwargs) -> list[Response]:
        """Process multiple prompts in parallel."""
        ...

    def get_stats(self) -> dict:
        """Get session statistics."""
        ...
```

### Step 3: Decorators

Add decorators for cross-cutting concerns:

```python
@retry(max_attempts=3)
@log_call
@track_time
def _make_request(self, ...):
    ...
```

### Step 4: Testing

```python
# test_client.py
def test_basic_call():
    client = LLMClient(Config.from_env())
    response = client.chat("Say 'hello' and nothing else")
    assert "hello" in response.text.lower()
    assert response.usage.total > 0

def test_streaming():
    client = LLMClient(Config.from_env())
    chunks = list(client.stream("Count to 3"))
    assert len(chunks) > 0
```

## Evaluation Criteria

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Functionality** | 30 | All features work correctly |
| **Error Handling** | 20 | Graceful handling of all error cases |
| **Type Safety** | 15 | Complete type hints, Pydantic validation |
| **Code Quality** | 15 | Clean, readable, well-documented |
| **Testing** | 10 | Comprehensive test coverage |
| **Observability** | 10 | Logging, metrics, cost tracking |

## Hints

See [../hints/HINTS.md](../hints/HINTS.md) for progressive hints if you get stuck.

## Solution

A reference implementation is available at [llm_client_solution.py](./llm_client_solution.py) - but try to complete it yourself first!

## Next Steps

After completing this capstone:
- You're ready for [Module 1: Basic API](../../01-basic-api/)
- All Python patterns used in the tutorial are now familiar
- Consider Part 2 for deeper Python knowledge if needed
