# Track A, Section 1: Object-Oriented Programming

**Duration:** 60-90 minutes | **Level:** Intermediate

## Why This Matters for LLM APIs

OOP enables you to build:
- **Extensible clients:** Support multiple LLM providers with same interface
- **Reusable components:** Share conversation handlers, token trackers
- **Maintainable code:** Separate concerns, reduce duplication
- **Testable systems:** Mock dependencies, isolate behavior

## Concepts

### Class Basics

```python
class LLMClient:
    """A basic LLM client."""

    def __init__(self, api_key: str, model: str = "claude-sonnet"):
        self.api_key = api_key  # Instance attribute
        self.model = model
        self._call_count = 0    # Private by convention

    def chat(self, prompt: str) -> str:
        """Make a chat request."""
        self._call_count += 1
        # ... implementation
        return response

    @property
    def call_count(self) -> int:
        """Read-only access to call count."""
        return self._call_count

    @classmethod
    def from_env(cls) -> "LLMClient":
        """Alternative constructor from environment."""
        return cls(api_key=os.getenv("API_KEY"))

    @staticmethod
    def estimate_cost(tokens: int) -> float:
        """Utility that doesn't need instance."""
        return tokens * 0.00001
```

### Inheritance vs Composition

```python
# Inheritance: "is-a" relationship
class ClaudeClient(LLMClient):
    """Claude-specific client."""
    pass

# Composition: "has-a" relationship (preferred)
class LLMClient:
    def __init__(self, provider: Provider, tracker: TokenTracker):
        self.provider = provider  # Has a provider
        self.tracker = tracker    # Has a tracker
```

### Abstract Base Classes

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def complete(self, messages: list) -> str:
        """Generate completion. Must be implemented."""
        pass

    @abstractmethod
    def stream(self, messages: list):
        """Stream completion. Must be implemented."""
        pass

class ClaudeProvider(LLMProvider):
    def complete(self, messages: list) -> str:
        # Concrete implementation
        ...
```

## Examples

### Multi-Provider Client

```python
# examples/multi_provider.py
"""Multi-provider LLM client using OOP."""

from abc import ABC, abstractmethod
from typing import Generator
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Response:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @abstractmethod
    def complete(self, messages: list[Message], **kwargs) -> Response:
        """Generate completion."""
        pass

    @abstractmethod
    def stream(self, messages: list[Message], **kwargs) -> Generator[str, None, None]:
        """Stream completion."""
        pass


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model

    @property
    def name(self) -> str:
        return "claude"

    def complete(self, messages: list[Message], **kwargs) -> Response:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": m.role, "content": m.content} for m in messages]
        )
        return Response(
            text=response.content[0].text,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=response.model
        )

    def stream(self, messages: list[Message], **kwargs) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": m.role, "content": m.content} for m in messages]
        ) as stream:
            for text in stream.text_stream:
                yield text


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    @property
    def name(self) -> str:
        return "openai"

    def complete(self, messages: list[Message], **kwargs) -> Response:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": m.role, "content": m.content} for m in messages]
        )
        return Response(
            text=response.choices[0].message.content,
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
            model=response.model
        )

    def stream(self, messages: list[Message], **kwargs) -> Generator[str, None, None]:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": m.role, "content": m.content} for m in messages],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class UnifiedClient:
    """Unified client that works with any provider."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.history: list[Message] = []

    def chat(self, content: str, **kwargs) -> str:
        """Send message and get response."""
        self.history.append(Message(role="user", content=content))
        response = self.provider.complete(self.history, **kwargs)
        self.history.append(Message(role="assistant", content=response.text))
        return response.text

    def clear_history(self):
        """Clear conversation history."""
        self.history = []


# Usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    # Same interface, different providers
    claude = UnifiedClient(ClaudeProvider(os.getenv("ANTHROPIC_API_KEY")))
    # openai = UnifiedClient(OpenAIProvider(os.getenv("OPENAI_API_KEY")))

    response = claude.chat("What is 2+2?")
    print(f"Claude: {response}")
```

### Strategy Pattern for Retry Logic

```python
# examples/strategy_pattern.py
"""Strategy pattern for different retry behaviors."""

from abc import ABC, abstractmethod
import time
import random


class RetryStrategy(ABC):
    """Abstract retry strategy."""

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        pass

    @abstractmethod
    def should_retry(self, attempt: int, max_attempts: int) -> bool:
        """Determine if should retry."""
        pass


class ExponentialBackoff(RetryStrategy):
    """Exponential backoff with jitter."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    def should_retry(self, attempt: int, max_attempts: int) -> bool:
        return attempt < max_attempts


class LinearBackoff(RetryStrategy):
    """Linear backoff."""

    def __init__(self, delay: float = 2.0):
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        return self.delay * attempt

    def should_retry(self, attempt: int, max_attempts: int) -> bool:
        return attempt < max_attempts


class NoRetry(RetryStrategy):
    """No retry strategy."""

    def get_delay(self, attempt: int) -> float:
        return 0

    def should_retry(self, attempt: int, max_attempts: int) -> bool:
        return False


class ResilientClient:
    """Client with configurable retry strategy."""

    def __init__(self, provider, strategy: RetryStrategy = None):
        self.provider = provider
        self.strategy = strategy or ExponentialBackoff()

    def call_with_retry(self, messages, max_attempts: int = 3):
        """Make call with retry strategy."""
        attempt = 0
        last_error = None

        while True:
            try:
                return self.provider.complete(messages)
            except Exception as e:
                last_error = e
                attempt += 1

                if not self.strategy.should_retry(attempt, max_attempts):
                    raise last_error

                delay = self.strategy.get_delay(attempt)
                print(f"Retry {attempt} in {delay:.1f}s...")
                time.sleep(delay)


# Usage: Easy to swap strategies
# client = ResilientClient(provider, ExponentialBackoff())
# client = ResilientClient(provider, LinearBackoff(5.0))
# client = ResilientClient(provider, NoRetry())
```

### Factory Pattern for Provider Creation

```python
# examples/factory_pattern.py
"""Factory pattern for creating providers."""

from enum import Enum
import os


class ProviderType(Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    GEMINI = "gemini"


class ProviderFactory:
    """Factory for creating LLM providers."""

    @staticmethod
    def create(
        provider_type: ProviderType | str,
        api_key: str = None,
        **kwargs
    ) -> "LLMProvider":
        """Create provider by type.

        Args:
            provider_type: Provider type or string name.
            api_key: API key (defaults to env var).
            **kwargs: Provider-specific options.

        Returns:
            Configured provider instance.

        Raises:
            ValueError: If provider type unknown.
        """
        if isinstance(provider_type, str):
            provider_type = ProviderType(provider_type.lower())

        if provider_type == ProviderType.CLAUDE:
            key = api_key or os.getenv("ANTHROPIC_API_KEY")
            model = kwargs.get("model", "claude-sonnet-4-20250514")
            return ClaudeProvider(key, model)

        elif provider_type == ProviderType.OPENAI:
            key = api_key or os.getenv("OPENAI_API_KEY")
            model = kwargs.get("model", "gpt-4")
            return OpenAIProvider(key, model)

        else:
            raise ValueError(f"Unknown provider: {provider_type}")

    @classmethod
    def from_config(cls, config: dict) -> "LLMProvider":
        """Create provider from config dict."""
        return cls.create(
            provider_type=config["provider"],
            api_key=config.get("api_key"),
            model=config.get("model")
        )


# Usage
provider = ProviderFactory.create("claude")
provider = ProviderFactory.create(ProviderType.OPENAI, model="gpt-4-turbo")
provider = ProviderFactory.from_config({"provider": "claude", "model": "claude-opus"})
```

---

## Exercises

### Simple: Token Counter Class

**Task:** Create a `TokenCounter` class that:
- Tracks input and output tokens
- Calculates cost based on model pricing
- Provides a summary method

```python
counter = TokenCounter(model="claude-sonnet")
counter.add(input_tokens=100, output_tokens=50)
counter.add(input_tokens=200, output_tokens=100)
print(counter.summary())
# Total: 450 tokens, Cost: $0.000825
```

<details>
<summary>Hints</summary>

1. Store pricing as class attribute dict
2. Use instance attributes for running totals
3. Summary can be a formatted string or dict
</details>

<details>
<summary>Solution</summary>

```python
class TokenCounter:
    """Track token usage and costs."""

    PRICING = {
        "claude-sonnet": {"input": 3.0, "output": 15.0},
        "claude-opus": {"input": 15.0, "output": 75.0},
        "claude-haiku": {"input": 0.25, "output": 1.25},
    }

    def __init__(self, model: str = "claude-sonnet"):
        self.model = model
        self.input_tokens = 0
        self.output_tokens = 0

        if model not in self.PRICING:
            raise ValueError(f"Unknown model: {model}")

    def add(self, input_tokens: int, output_tokens: int):
        """Add token usage."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost(self) -> float:
        pricing = self.PRICING[self.model]
        return (
            self.input_tokens * pricing["input"] / 1_000_000 +
            self.output_tokens * pricing["output"] / 1_000_000
        )

    def summary(self) -> str:
        return f"Total: {self.total_tokens} tokens, Cost: ${self.cost:.6f}"

    def reset(self):
        self.input_tokens = 0
        self.output_tokens = 0
```
</details>

---

### Intermediate: Conversation Manager

**Task:** Create a `ConversationManager` class that:
- Maintains conversation history
- Supports system prompts
- Limits history to N messages (sliding window)
- Provides methods to export/import history

```python
manager = ConversationManager(max_history=10)
manager.set_system("You are helpful.")
manager.add_user("Hello")
manager.add_assistant("Hi there!")
messages = manager.get_messages()  # For API call
manager.export_json("conversation.json")
```

<details>
<summary>Hints</summary>

1. Store system prompt separately from messages
2. Use a deque with maxlen for sliding window
3. get_messages() combines system + history
4. Export/import with json module
</details>

<details>
<summary>Solution</summary>

```python
from collections import deque
import json
from dataclasses import dataclass, asdict


@dataclass
class Message:
    role: str
    content: str


class ConversationManager:
    """Manage conversation history with sliding window."""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.system_prompt: str | None = None
        self.messages: deque[Message] = deque(maxlen=max_history)

    def set_system(self, prompt: str):
        """Set system prompt."""
        self.system_prompt = prompt

    def add_user(self, content: str):
        """Add user message."""
        self.messages.append(Message(role="user", content=content))

    def add_assistant(self, content: str):
        """Add assistant message."""
        self.messages.append(Message(role="assistant", content=content))

    def get_messages(self) -> list[dict]:
        """Get messages formatted for API call."""
        result = []
        if self.system_prompt:
            result.append({"role": "system", "content": self.system_prompt})
        result.extend(asdict(m) for m in self.messages)
        return result

    def clear(self):
        """Clear history (keeps system prompt)."""
        self.messages.clear()

    def export_json(self, filepath: str):
        """Export conversation to JSON."""
        data = {
            "system_prompt": self.system_prompt,
            "messages": [asdict(m) for m in self.messages]
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def import_json(cls, filepath: str) -> "ConversationManager":
        """Import conversation from JSON."""
        with open(filepath) as f:
            data = json.load(f)

        manager = cls(max_history=len(data["messages"]) + 10)
        manager.system_prompt = data.get("system_prompt")

        for msg in data["messages"]:
            manager.messages.append(Message(**msg))

        return manager
```
</details>

---

### Advanced: Plugin-Based Tool System

**Task:** Build a plugin-based tool system that:
- Defines a `Tool` base class with `execute()` and `schema()` methods
- Supports dynamic tool registration
- Generates tool schemas for Claude API
- Executes tools by name with input validation

```python
class WeatherTool(Tool):
    name = "get_weather"
    description = "Get weather for a location"

    def execute(self, location: str, unit: str = "celsius") -> dict:
        return {"temperature": 22, "unit": unit}

registry = ToolRegistry()
registry.register(WeatherTool())
registry.register(CalculatorTool())

schemas = registry.get_schemas()  # For Claude tools parameter
result = registry.execute("get_weather", {"location": "NYC"})
```

<details>
<summary>Hints</summary>

1. Use ABC for Tool base class
2. Schema can be generated from type hints or defined manually
3. Registry uses dict mapping name → tool instance
4. Execute should validate inputs exist
5. Consider using Pydantic for schema generation
</details>

<details>
<summary>Solution</summary>

```python
from abc import ABC, abstractmethod
from typing import Any, get_type_hints
from pydantic import BaseModel, create_model


class Tool(ABC):
    """Abstract base for tools."""

    name: str
    description: str

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the tool with given inputs."""
        pass

    def get_schema(self) -> dict:
        """Generate JSON schema for Claude API."""
        # Get type hints from execute method
        hints = get_type_hints(self.execute)
        hints.pop("return", None)

        # Build Pydantic model from hints
        fields = {}
        for param, type_hint in hints.items():
            # Check if has default
            import inspect
            sig = inspect.signature(self.execute)
            default = sig.parameters[param].default
            if default is inspect.Parameter.empty:
                fields[param] = (type_hint, ...)
            else:
                fields[param] = (type_hint, default)

        model = create_model(f"{self.name}_input", **fields)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": model.model_json_schema()
        }


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool."""
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str):
        """Unregister a tool."""
        del self._tools[name]

    def get(self, name: str) -> Tool:
        """Get tool by name."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]

    def get_schemas(self) -> list[dict]:
        """Get all tool schemas for API."""
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, name: str, inputs: dict) -> Any:
        """Execute tool by name."""
        tool = self.get(name)
        return tool.execute(**inputs)

    def list_tools(self) -> list[str]:
        """List registered tool names."""
        return list(self._tools.keys())


# Example tools
class WeatherTool(Tool):
    name = "get_weather"
    description = "Get current weather for a location"

    def execute(self, location: str, unit: str = "celsius") -> dict:
        # Mock implementation
        return {
            "location": location,
            "temperature": 22,
            "unit": unit,
            "conditions": "sunny"
        }


class CalculatorTool(Tool):
    name = "calculator"
    description = "Perform basic math operations"

    def execute(self, operation: str, a: float, b: float) -> float:
        ops = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else float("inf"),
        }
        if operation not in ops:
            raise ValueError(f"Unknown operation: {operation}")
        return ops[operation](a, b)


# Usage
if __name__ == "__main__":
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(CalculatorTool())

    print("Registered tools:", registry.list_tools())
    print("\nSchemas for Claude API:")
    for schema in registry.get_schemas():
        print(f"  - {schema['name']}")

    print("\nExecuting get_weather:")
    result = registry.execute("get_weather", {"location": "San Francisco"})
    print(f"  {result}")

    print("\nExecuting calculator:")
    result = registry.execute("calculator", {"operation": "multiply", "a": 6, "b": 7})
    print(f"  6 * 7 = {result}")
```
</details>

---

## Pro Tips

### 1. Prefer Composition Over Inheritance

```python
# Instead of deep inheritance chains
class ClaudeClient(LLMClient):
    class EnhancedClaudeClient(ClaudeClient):
        pass

# Use composition
class EnhancedClient:
    def __init__(self, provider: LLMProvider, cache: Cache, tracker: Tracker):
        self.provider = provider
        self.cache = cache
        self.tracker = tracker
```

### 2. Use dataclasses for Simple Data

```python
from dataclasses import dataclass, field

@dataclass
class APIResponse:
    text: str
    tokens: int
    model: str
    metadata: dict = field(default_factory=dict)
```

### 3. Properties for Computed Values

```python
class TokenStats:
    @property
    def cost(self) -> float:
        """Calculate cost on access, not storage."""
        return self.tokens * self.price_per_token
```

### 4. Use __slots__ for Memory Efficiency

```python
class Message:
    __slots__ = ["role", "content", "timestamp"]

    def __init__(self, role, content):
        self.role = role
        self.content = content
        self.timestamp = time.time()
```

### 5. Context Managers for Resource Management

```python
class LLMSession:
    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        self.log_session(elapsed)
```

---

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Giant base classes | Hard to maintain | Keep classes focused, use composition |
| Deep inheritance | Fragile, tight coupling | Prefer composition |
| Mutable class attributes | Shared state bugs | Use instance attributes |
| Missing `@abstractmethod` | No enforcement | Always mark abstract methods |
| Public attributes for internals | No encapsulation | Use `_private` convention |

---

## Next Section

[Section 2: Testing →](../02-testing/)
