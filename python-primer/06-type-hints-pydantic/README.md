# Section 6: Type Hints & Pydantic

**Duration:** 25 minutes | **Difficulty:** Intermediate

## Why This Matters for LLM APIs

- **Tool/Function Calling:** Define JSON schemas for Claude to call your functions
- **Structured Output:** Validate and parse LLM responses into typed objects
- **API Contracts:** Clear interfaces for your LLM wrappers
- **IDE Support:** Better autocomplete and error detection

## Concepts

### Type Hints Basics

```python
# Basic types
name: str = "Claude"
count: int = 42
ratio: float = 0.95
active: bool = True

# Collections
items: list[str] = ["a", "b"]
mapping: dict[str, int] = {"x": 1}
coords: tuple[float, float] = (1.0, 2.0)

# Optional (can be None)
from typing import Optional
value: Optional[str] = None  # or: str | None

# Function signatures
def process(text: str, max_len: int = 100) -> str:
    return text[:max_len]
```

### Pydantic Models

```python
from pydantic import BaseModel

class Message(BaseModel):
    role: str
    content: str

# Auto-validation on creation
msg = Message(role="user", content="Hello")

# From dict
msg = Message(**{"role": "user", "content": "Hello"})

# To dict
data = msg.model_dump()
```

## Examples

### Function Signatures for LLM Wrappers

```python
# examples/typed_functions.py
"""Type-safe LLM wrapper functions."""

from typing import Optional


def call_claude(
    prompt: str,
    *,  # Force keyword arguments after this
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    temperature: float = 0.7,
    system: Optional[str] = None,
    stop_sequences: Optional[list[str]] = None,
) -> str:
    """Make a Claude API call.

    Args:
        prompt: The user message.
        model: Model identifier.
        max_tokens: Maximum response tokens.
        temperature: Sampling temperature (0-1).
        system: Optional system prompt.
        stop_sequences: Optional stop sequences.

    Returns:
        The assistant's response text.
    """
    # Implementation would go here
    pass


# Type checker catches errors:
# call_claude(123)  # Error: expected str
# call_claude("Hi", max_tokens="big")  # Error: expected int
```

### Pydantic for API Responses

```python
# examples/pydantic_response.py
"""Parse API responses with Pydantic."""

from pydantic import BaseModel, Field
from typing import Optional


class Usage(BaseModel):
    """Token usage information."""
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None


class ContentBlock(BaseModel):
    """A content block in the response."""
    type: str
    text: Optional[str] = None
    # For tool use
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[dict] = None


class ClaudeResponse(BaseModel):
    """Parsed Claude API response."""
    id: str
    type: str = "message"
    role: str = "assistant"
    content: list[ContentBlock]
    model: str
    stop_reason: str
    usage: Usage


# Usage
response_data = {
    "id": "msg_123",
    "type": "message",
    "role": "assistant",
    "content": [{"type": "text", "text": "Hello!"}],
    "model": "claude-sonnet-4-20250514",
    "stop_reason": "end_turn",
    "usage": {"input_tokens": 10, "output_tokens": 5}
}

response = ClaudeResponse(**response_data)
print(f"Response: {response.content[0].text}")
print(f"Tokens: {response.usage.input_tokens} + {response.usage.output_tokens}")
```

### Tool Definitions with Pydantic

```python
# examples/tool_definitions.py
"""Define tools for Claude using Pydantic."""

from pydantic import BaseModel, Field
from typing import Literal


class WeatherInput(BaseModel):
    """Input schema for get_weather tool."""
    location: str = Field(description="City name or coordinates")
    unit: Literal["celsius", "fahrenheit"] = Field(
        default="celsius",
        description="Temperature unit"
    )


class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""
    operation: Literal["add", "subtract", "multiply", "divide"] = Field(
        description="Math operation to perform"
    )
    a: float = Field(description="First operand")
    b: float = Field(description="Second operand")


def pydantic_to_tool_schema(model: type[BaseModel], name: str, description: str) -> dict:
    """Convert Pydantic model to Claude tool schema.

    Args:
        model: Pydantic model class.
        name: Tool name.
        description: Tool description.

    Returns:
        Tool definition dict for Claude API.
    """
    return {
        "name": name,
        "description": description,
        "input_schema": model.model_json_schema()
    }


# Generate tool definitions
weather_tool = pydantic_to_tool_schema(
    WeatherInput,
    "get_weather",
    "Get current weather for a location"
)

calculator_tool = pydantic_to_tool_schema(
    CalculatorInput,
    "calculator",
    "Perform basic math operations"
)

# These can be passed to Claude API
tools = [weather_tool, calculator_tool]
```

### Structured Output Parsing

```python
# examples/structured_output.py
"""Parse structured LLM output with Pydantic."""

import json
from pydantic import BaseModel, Field, ValidationError
from typing import Optional


class ComponentAnalysis(BaseModel):
    """Structured analysis of an electronic component."""
    name: str = Field(description="Component name")
    category: str = Field(description="Component category")
    key_parameters: list[str] = Field(description="Important parameters")
    typical_applications: list[str] = Field(description="Common uses")
    considerations: Optional[str] = Field(
        default=None,
        description="Design considerations"
    )


def parse_component_analysis(llm_output: str) -> ComponentAnalysis | None:
    """Parse LLM output into structured ComponentAnalysis.

    Args:
        llm_output: Raw LLM response (expected to be JSON).

    Returns:
        Parsed ComponentAnalysis or None on error.
    """
    try:
        # Try to extract JSON from response
        # (LLM might include extra text)
        start = llm_output.find('{')
        end = llm_output.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in response")

        json_str = llm_output[start:end]
        data = json.loads(json_str)

        return ComponentAnalysis(**data)

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return None

    except ValidationError as e:
        print(f"Validation error: {e}")
        return None


# Example usage
llm_response = '''
Here's the analysis:
{
    "name": "LM7805",
    "category": "Linear Voltage Regulator",
    "key_parameters": ["Input voltage: 7-35V", "Output: 5V", "Max current: 1.5A"],
    "typical_applications": ["USB power supplies", "Arduino projects"],
    "considerations": "Requires heatsink above 500mA due to power dissipation"
}
'''

analysis = parse_component_analysis(llm_response)
if analysis:
    print(f"Component: {analysis.name}")
    print(f"Category: {analysis.category}")
    for param in analysis.key_parameters:
        print(f"  - {param}")
```

### Validation with Pydantic

```python
# examples/validation.py
"""Input validation with Pydantic."""

from pydantic import BaseModel, Field, field_validator, model_validator


class APIRequest(BaseModel):
    """Validated API request parameters."""
    model: str = Field(default="claude-sonnet-4-20250514")
    max_tokens: int = Field(default=1024, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0, le=1)
    messages: list[dict]

    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        for msg in v:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("Each message must have 'role' and 'content'")
            if msg['role'] not in ('user', 'assistant', 'system'):
                raise ValueError(f"Invalid role: {msg['role']}")
        return v

    @model_validator(mode='after')
    def validate_model(self):
        # Check first message is user or system
        first_role = self.messages[0]['role']
        if first_role not in ('user', 'system'):
            raise ValueError("First message must be 'user' or 'system'")
        return self


# Valid request
request = APIRequest(
    max_tokens=500,
    temperature=0.5,
    messages=[{"role": "user", "content": "Hello"}]
)

# Invalid - will raise ValidationError
try:
    bad_request = APIRequest(
        max_tokens=10000,  # > 4096
        messages=[]
    )
except Exception as e:
    print(f"Validation error: {e}")
```

## Exercise

**Task:** Create a Pydantic-based system for defining and validating LLM tool calls:

1. Define a `Tool` model with name, description, and parameters schema
2. Define a `ToolCall` model for parsing tool use responses
3. Create a `ToolResult` model for tool execution results
4. Write a function to validate tool calls against tool definitions

**Requirements:**
- Tools must have non-empty name and description
- ToolCall must reference a valid tool name
- ToolResult must indicate success/failure

### Hints

<details>
<summary>Hint 1: Tool definition model</summary>

```python
class Tool(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    input_schema: dict  # JSON Schema

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError("Name must be alphanumeric with underscores")
        return v
```
</details>

<details>
<summary>Hint 2: ToolCall model</summary>

```python
class ToolCall(BaseModel):
    id: str
    name: str
    input: dict

    def validate_against_tool(self, tool: Tool) -> bool:
        # Check name matches
        # Optionally validate input against schema
        pass
```
</details>

<details>
<summary>Hint 3: ToolResult model</summary>

```python
class ToolResult(BaseModel):
    tool_use_id: str
    success: bool
    output: str | dict | None = None
    error: str | None = None

    @model_validator(mode='after')
    def check_output_or_error(self):
        if self.success and self.output is None:
            raise ValueError("Successful result must have output")
        if not self.success and self.error is None:
            raise ValueError("Failed result must have error")
        return self
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Use Field for Documentation and Validation

```python
class Config(BaseModel):
    api_key: str = Field(min_length=10, description="Anthropic API key")
    max_tokens: int = Field(default=1024, ge=1, le=100000)
    temperature: float = Field(default=0.7, ge=0, le=2)
```

### 2. Generate JSON Schema from Models

```python
# For tool definitions
schema = MyModel.model_json_schema()

# Exclude defaults, titles for cleaner schema
schema = MyModel.model_json_schema(mode='serialization')
```

### 3. Use Literal for Enums

```python
from typing import Literal

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    # Instead of: role: str
```

### 4. Nested Models for Complex Structures

```python
class ContentBlock(BaseModel):
    type: str
    text: str | None = None

class Response(BaseModel):
    content: list[ContentBlock]  # Auto-validated nested
```

### 5. Custom Serialization

```python
class APIKey(BaseModel):
    key: str

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data['key'] = data['key'][:8] + '...'  # Mask key
        return data
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `Optional[str] = None` without default | Required field | Add `= None` |
| Mutable default | Shared state | Use `Field(default_factory=list)` |
| Not handling validation errors | Crash on bad input | Catch `ValidationError` |
| Over-complex nested models | Hard to maintain | Keep models focused |
| Missing `@classmethod` on validators | Validator not called | Add decorator |

## LLM API Connection

Type hints and Pydantic are used throughout:

```python
# Module 3: Tool definitions
tools = [pydantic_to_tool_schema(MyTool, "my_tool", "...")]

# Module 4: RAG document schemas
class Document(BaseModel):
    content: str
    metadata: dict
    embedding: list[float]

# Module 7: Agent state
class AgentState(BaseModel):
    messages: list[Message]
    tools_called: list[ToolCall]
    memory: dict

# Module 8: API request validation
@app.post("/generate")
async def generate(request: GenerateRequest):  # Pydantic validates
    ...
```

## Next Section

[Section 7: Generators & Streaming →](../07-generators-streaming/)
