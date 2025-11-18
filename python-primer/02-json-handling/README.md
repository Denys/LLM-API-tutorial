# Section 2: JSON & Data Handling

**Duration:** 20 minutes | **Difficulty:** Beginner

## Why This Matters for LLM APIs

Every LLM API request and response is JSON. You'll parse responses, build structured prompts, handle nested tool calls, and serialize data for caching. This is unavoidable.

## Concepts

### JSON ↔ Python Mapping

| JSON Type | Python Type |
|-----------|-------------|
| `object` | `dict` |
| `array` | `list` |
| `string` | `str` |
| `number` | `int` / `float` |
| `true/false` | `True` / `False` |
| `null` | `None` |

### Core Operations

```python
import json

# Parse JSON string → Python object
data = json.loads('{"model": "claude-3", "tokens": 100}')

# Serialize Python object → JSON string
text = json.dumps(data)

# Pretty print with indentation
text = json.dumps(data, indent=2)

# File operations
with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

with open("data.json", "r") as f:
    data = json.load(f)
```

## Examples

### Basic Parsing

```python
# examples/json_basics.py
"""Basic JSON operations for LLM APIs."""

import json

# Typical API response (as string)
response_text = '''
{
    "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": "Hello! How can I help you today?"
        }
    ],
    "model": "claude-sonnet-4-20250514",
    "stop_reason": "end_turn",
    "usage": {
        "input_tokens": 12,
        "output_tokens": 15
    }
}
'''

# Parse into Python dict
response = json.loads(response_text)

# Access nested data
message_text = response["content"][0]["text"]
model = response["model"]
input_tokens = response["usage"]["input_tokens"]
output_tokens = response["usage"]["output_tokens"]

print(f"Model: {model}")
print(f"Response: {message_text}")
print(f"Tokens: {input_tokens} in, {output_tokens} out")
```

### Nested Structures (Tool Calls)

```python
# examples/nested_structures.py
"""Handling nested JSON in tool/function calls."""

import json

# Tool call response from Claude
tool_response = '''
{
    "content": [
        {
            "type": "tool_use",
            "id": "toolu_01A09q90qw90lq917835lq9",
            "name": "get_weather",
            "input": {
                "location": "San Francisco",
                "unit": "celsius"
            }
        }
    ],
    "stop_reason": "tool_use"
}
'''

response = json.loads(tool_response)

# Extract tool call details
for block in response["content"]:
    if block["type"] == "tool_use":
        tool_name = block["name"]
        tool_id = block["id"]
        tool_input = block["input"]

        print(f"Tool: {tool_name}")
        print(f"ID: {tool_id}")
        print(f"Input: {json.dumps(tool_input, indent=2)}")

        # Process specific tool
        if tool_name == "get_weather":
            location = tool_input["location"]
            unit = tool_input.get("unit", "fahrenheit")  # Safe access with default
            print(f"\nFetching weather for {location} in {unit}...")
```

### Building Request Bodies

```python
# examples/request_building.py
"""Building JSON request bodies for Claude API."""

import json

def build_message_request(
    user_message: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 1024,
    system: str = None,
    temperature: float = None,
) -> dict:
    """Build a Claude API request body.

    Args:
        user_message: The user's input message.
        model: Model identifier.
        max_tokens: Maximum response tokens.
        system: Optional system prompt.
        temperature: Optional temperature (0-1).

    Returns:
        Request body as dictionary.
    """
    request = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": user_message}
        ]
    }

    # Only add optional fields if provided
    if system:
        request["system"] = system
    if temperature is not None:
        request["temperature"] = temperature

    return request


# Build request
request = build_message_request(
    user_message="Explain capacitor ESR in 2 sentences.",
    system="You are an electronics expert. Be concise.",
    temperature=0.3
)

# Pretty print for debugging
print("Request body:")
print(json.dumps(request, indent=2))

# For actual API call, you'd use:
# response = httpx.post(url, json=request, headers=headers)
```

### Safe Access Patterns

```python
# examples/safe_access.py
"""Safe JSON access patterns to avoid KeyError."""

import json

# Response might have missing fields
response = {
    "content": [{"type": "text", "text": "Hello"}],
    "usage": {"input_tokens": 10}
    # Note: output_tokens might be missing
}

# BAD - raises KeyError if missing
# output_tokens = response["usage"]["output_tokens"]

# GOOD - use .get() with default
output_tokens = response.get("usage", {}).get("output_tokens", 0)
print(f"Output tokens: {output_tokens}")

# GOOD - check before access
if "output_tokens" in response.get("usage", {}):
    output_tokens = response["usage"]["output_tokens"]
else:
    output_tokens = 0

# For deeply nested optional data
def safe_get(data: dict, *keys, default=None):
    """Safely navigate nested dict structure.

    Args:
        data: The dictionary to navigate.
        *keys: Sequence of keys to follow.
        default: Value if path doesn't exist.

    Returns:
        Value at path or default.

    Example:
        safe_get(response, "usage", "output_tokens", default=0)
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
        if data is None:
            return default
    return data


# Usage
output_tokens = safe_get(response, "usage", "output_tokens", default=0)
cache_tokens = safe_get(response, "usage", "cache_read_input_tokens", default=0)
```

### Serializing for Cache/Storage

```python
# examples/serialization.py
"""Serializing conversations for caching."""

import json
from datetime import datetime

# Conversation history
conversation = {
    "id": "conv_123",
    "created_at": datetime.now().isoformat(),
    "messages": [
        {"role": "user", "content": "What is a MOSFET?"},
        {"role": "assistant", "content": "A MOSFET is..."},
        {"role": "user", "content": "What about gate charge?"},
    ],
    "metadata": {
        "total_tokens": 450,
        "model": "claude-sonnet-4-20250514"
    }
}

# Save to file
with open("conversation.json", "w") as f:
    json.dump(conversation, f, indent=2)

# Load from file
with open("conversation.json", "r") as f:
    loaded = json.load(f)

print(f"Loaded conversation {loaded['id']} with {len(loaded['messages'])} messages")

# Compact serialization for storage/transmission
compact = json.dumps(conversation, separators=(',', ':'))
print(f"\nCompact size: {len(compact)} bytes")
print(f"Pretty size: {len(json.dumps(conversation, indent=2))} bytes")
```

## Exercise

**Task:** Build a conversation formatter that:

1. Takes a list of message dictionaries (role + content)
2. Validates each message has required fields
3. Calculates estimated token count (~4 chars per token)
4. Returns formatted JSON with metadata

**Input format:**
```python
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "What's 2+2?"}
]
```

**Output format:**
```json
{
    "messages": [...],
    "metadata": {
        "message_count": 3,
        "estimated_tokens": 42,
        "roles": {"user": 2, "assistant": 1}
    }
}
```

### Hints

<details>
<summary>Hint 1: Validation</summary>

```python
def validate_message(msg):
    if "role" not in msg:
        raise ValueError("Message missing 'role'")
    if "content" not in msg:
        raise ValueError("Message missing 'content'")
    if msg["role"] not in ("user", "assistant", "system"):
        raise ValueError(f"Invalid role: {msg['role']}")
```
</details>

<details>
<summary>Hint 2: Token estimation</summary>

```python
def estimate_tokens(text: str) -> int:
    """Rough estimate: ~4 characters per token."""
    return len(text) // 4 + 1
```
</details>

<details>
<summary>Hint 3: Counting roles</summary>

```python
from collections import Counter
roles = Counter(msg["role"] for msg in messages)
# roles = {"user": 2, "assistant": 1}
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Always Use `json.dumps()` for Request Bodies

```python
# BAD - manual string building (escape issues)
body = '{"model": "' + model + '", "messages": [...]}'

# GOOD - json.dumps handles escaping
body = json.dumps({"model": model, "messages": messages})
```

### 2. Handle Unicode Properly

```python
# Ensure non-ASCII characters are preserved
json.dumps({"text": "Ω resistor"}, ensure_ascii=False)
# '{"text": "Ω resistor"}'

# Default escapes them (larger payload)
json.dumps({"text": "Ω resistor"})
# '{"text": "\\u03a9 resistor"}'
```

### 3. Custom Serialization for Non-JSON Types

```python
from datetime import datetime

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

data = {"timestamp": datetime.now()}
json.dumps(data, cls=CustomEncoder)
```

### 4. Validate Before Parsing

```python
def safe_parse(text: str) -> dict | None:
    """Parse JSON with error handling."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON at position {e.pos}: {e.msg}")
        return None
```

### 5. Use `pprint` for Debugging

```python
from pprint import pprint

# Better than print() for nested structures
pprint(response, width=80, depth=3)
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| `json.loads(dict)` | loads() expects string | Use dict directly or dumps() first |
| Single quotes in JSON | Invalid JSON syntax | JSON requires double quotes |
| Accessing missing keys | KeyError crash | Use .get() with default |
| Trailing commas | Invalid JSON | Remove trailing commas |
| `datetime` in dict | Not JSON serializable | Convert to .isoformat() |

## LLM API Connection

JSON handling appears constantly:

```python
# Module 1: Parse API response
response = client.messages.create(...)
content = response.content[0].text  # SDK parses JSON for you

# Module 3: Tool calling
for block in response.content:
    if block.type == "tool_use":
        args = block.input  # Already parsed dict

# Module 4: RAG metadata
metadata = json.loads(chunk["metadata"])
source = metadata.get("source", "unknown")

# Module 7: Agent state
state = json.dumps(agent.get_state())
# ... later ...
agent.restore_state(json.loads(state))
```

## Next Section

[Section 3: HTTP Fundamentals →](../03-http-fundamentals/)
