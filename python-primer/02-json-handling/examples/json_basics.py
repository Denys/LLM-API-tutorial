"""Basic JSON operations for LLM APIs.

Run: python json_basics.py
"""

import json

# Typical API response (as string - simulating raw HTTP response)
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
print(f"Total cost estimate: ${(input_tokens * 3 + output_tokens * 15) / 1_000_000:.6f}")

# Serialize back to JSON string
print("\n--- Re-serialized (compact) ---")
print(json.dumps(response, separators=(',', ':')))

print("\n--- Re-serialized (pretty) ---")
print(json.dumps(response, indent=2))
