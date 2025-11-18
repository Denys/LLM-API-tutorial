# Section 3: HTTP Fundamentals

**Duration:** 20 minutes | **Difficulty:** Beginner-Intermediate

## Why This Matters for LLM APIs

The Anthropic SDK handles HTTP for you, but understanding the underlying protocol helps you:
- Debug connection issues
- Implement custom retry logic
- Work with rate limits
- Build raw API integrations
- Understand error responses

## Concepts

### HTTP Request Structure

```
POST /v1/messages HTTP/1.1
Host: api.anthropic.com
Content-Type: application/json
X-API-Key: sk-ant-...
anthropic-version: 2023-06-01

{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
}
```

### Key Components

| Component | Description | LLM API Usage |
|-----------|-------------|---------------|
| Method | GET, POST, etc. | POST for completions |
| Headers | Metadata | Auth, content type, version |
| Body | Request payload | Model, messages, parameters |
| Status Code | Response status | 200 OK, 429 rate limit, etc. |

### Common Status Codes

| Code | Meaning | LLM API Context |
|------|---------|-----------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Bad API key |
| 429 | Too Many Requests | Rate limited |
| 500 | Server Error | Retry with backoff |
| 529 | Overloaded | API overloaded, retry |

## Examples

### Basic Request with httpx

```python
# examples/http_basic.py
"""Basic HTTP request to Claude API using httpx."""

import httpx
import json
from dotenv import load_dotenv
import os

load_dotenv()

# API configuration
API_URL = "https://api.anthropic.com/v1/messages"
API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Required headers
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
    "anthropic-version": "2023-06-01"
}

# Request body
payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 100,
    "messages": [
        {"role": "user", "content": "Say hello in exactly 5 words."}
    ]
}

# Make request
response = httpx.post(API_URL, headers=headers, json=payload)

# Check status
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse: {data['content'][0]['text']}")
    print(f"Tokens: {data['usage']['input_tokens']} in, {data['usage']['output_tokens']} out")
else:
    print(f"Error: {response.text}")
```

### Handling Response Headers

```python
# examples/response_headers.py
"""Extract useful information from response headers."""

import httpx

def analyze_response(response: httpx.Response) -> dict:
    """Extract useful metadata from API response.

    Args:
        response: httpx Response object.

    Returns:
        Dictionary with extracted metadata.
    """
    return {
        "status": response.status_code,
        "request_id": response.headers.get("request-id"),
        "rate_limit": {
            "limit": response.headers.get("x-ratelimit-limit-requests"),
            "remaining": response.headers.get("x-ratelimit-remaining-requests"),
            "reset": response.headers.get("x-ratelimit-reset-requests"),
        },
        "content_type": response.headers.get("content-type"),
        "response_time_ms": response.elapsed.total_seconds() * 1000
    }

# Usage:
# response = httpx.post(url, headers=headers, json=payload)
# metadata = analyze_response(response)
# print(f"Request ID: {metadata['request_id']}")
# print(f"Rate limit remaining: {metadata['rate_limit']['remaining']}")
```

### Timeout and Connection Handling

```python
# examples/timeout_handling.py
"""Configure timeouts for LLM API calls."""

import httpx

# Create client with timeouts
client = httpx.Client(
    timeout=httpx.Timeout(
        connect=5.0,    # Time to establish connection
        read=60.0,      # Time to receive response (LLMs can be slow)
        write=10.0,     # Time to send request
        pool=5.0        # Time to get connection from pool
    )
)

# Or simple timeout (same for all)
client = httpx.Client(timeout=30.0)

# Per-request timeout override
response = client.post(
    url,
    headers=headers,
    json=payload,
    timeout=120.0  # Override for this request only
)

# Always close client when done
client.close()

# Or use context manager
with httpx.Client(timeout=30.0) as client:
    response = client.post(url, headers=headers, json=payload)
```

### Raw vs SDK Comparison

```python
# examples/raw_vs_sdk.py
"""Compare raw HTTP vs SDK usage."""

import httpx
import json
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

user_message = "What is 2+2?"

# ========== RAW HTTP ==========
def call_api_raw(message: str) -> str:
    """Make API call using raw HTTP."""
    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": os.getenv("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01"
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 100,
            "messages": [{"role": "user", "content": message}]
        }
    )
    response.raise_for_status()  # Raise exception for 4xx/5xx
    return response.json()["content"][0]["text"]


# ========== SDK ==========
def call_api_sdk(message: str) -> str:
    """Make API call using Anthropic SDK."""
    client = Anthropic()  # Auto-reads API key from env
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": message}]
    )
    return response.content[0].text


# The SDK handles:
# - Header construction
# - JSON serialization/deserialization
# - Error handling and retries
# - Response type conversion
# - Streaming support

if __name__ == "__main__":
    print("Raw HTTP:", call_api_raw(user_message))
    print("SDK:", call_api_sdk(user_message))
```

## Exercise

**Task:** Build a simple API health checker that:

1. Makes a minimal API call (short prompt, low max_tokens)
2. Measures response time
3. Extracts rate limit info from headers
4. Returns a health status report

**Required output:**
```python
{
    "healthy": True,
    "response_time_ms": 342.5,
    "rate_limit_remaining": 985,
    "model_responding": True,
    "request_id": "req_..."
}
```

**Handle these error cases:**
- Timeout → `healthy: False, error: "timeout"`
- Rate limited → `healthy: False, error: "rate_limited"`
- Auth error → `healthy: False, error: "auth_failed"`

### Hints

<details>
<summary>Hint 1: Minimal request</summary>

```python
payload = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 5,
    "messages": [{"role": "user", "content": "Hi"}]
}
```
</details>

<details>
<summary>Hint 2: Measure time</summary>

```python
import time
start = time.time()
response = httpx.post(...)
elapsed_ms = (time.time() - start) * 1000
# Or use response.elapsed.total_seconds() * 1000
```
</details>

<details>
<summary>Hint 3: Handle specific status codes</summary>

```python
if response.status_code == 200:
    return {"healthy": True, ...}
elif response.status_code == 429:
    return {"healthy": False, "error": "rate_limited"}
elif response.status_code == 401:
    return {"healthy": False, "error": "auth_failed"}
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Use httpx Over requests

```python
# httpx advantages:
# - Async support (httpx.AsyncClient)
# - HTTP/2 support
# - Better timeout handling
# - Type hints throughout

import httpx
# Instead of: import requests
```

### 2. Connection Pooling for Multiple Requests

```python
# BAD - new connection per request
for prompt in prompts:
    response = httpx.post(url, ...)

# GOOD - reuse connections
with httpx.Client() as client:
    for prompt in prompts:
        response = client.post(url, ...)
```

### 3. Log Request IDs for Debugging

```python
response = client.post(url, headers=headers, json=payload)
request_id = response.headers.get("request-id")
logger.info(f"API call {request_id}: {response.status_code}")

# When reporting issues to Anthropic, include request_id
```

### 4. Respect Rate Limit Headers

```python
remaining = int(response.headers.get("x-ratelimit-remaining-requests", 100))
if remaining < 10:
    logger.warning(f"Rate limit low: {remaining} remaining")
```

### 5. Handle Streaming Responses

```python
# For streaming, use iter_lines or iter_bytes
with httpx.stream("POST", url, headers=headers, json=payload) as response:
    for line in response.iter_lines():
        if line:
            event = json.loads(line.removeprefix("data: "))
            print(event)
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Missing `anthropic-version` header | 400 error | Always include version header |
| Short timeout for LLM | Timeout errors | Use 60-120s for read timeout |
| Not closing client | Connection leak | Use context manager or close() |
| Ignoring rate limit headers | Get blocked | Monitor and back off |
| Not checking status code | Silent failures | Always check before parsing |

## LLM API Connection

Understanding HTTP helps with:

```python
# Module 1: Debug why requests fail
# "Why am I getting 401?" → Check API key header

# Module 5: MCP server implementation
# Build HTTP endpoints that Claude calls

# Module 7: Agent external API calls
# Make HTTP calls to weather, search, etc.

# Module 8: Production monitoring
# Log response times, track rate limits
```

## Next Section

[Section 4: Async/Await Essentials →](../04-async-await/)
