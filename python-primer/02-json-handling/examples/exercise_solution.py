"""Exercise Solution: Conversation Formatter.

Formats and validates conversation messages with metadata.

Run: python exercise_solution.py
"""

import json
from collections import Counter


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 characters per token).

    Args:
        text: Input text.

    Returns:
        Estimated token count.
    """
    return len(text) // 4 + 1


def validate_message(msg: dict, index: int) -> None:
    """Validate a single message dictionary.

    Args:
        msg: Message dictionary to validate.
        index: Message index for error reporting.

    Raises:
        ValueError: If message is invalid.
    """
    if not isinstance(msg, dict):
        raise ValueError(f"Message {index}: Expected dict, got {type(msg).__name__}")

    if "role" not in msg:
        raise ValueError(f"Message {index}: Missing 'role' field")

    if "content" not in msg:
        raise ValueError(f"Message {index}: Missing 'content' field")

    valid_roles = ("user", "assistant", "system")
    if msg["role"] not in valid_roles:
        raise ValueError(
            f"Message {index}: Invalid role '{msg['role']}'. "
            f"Must be one of: {valid_roles}"
        )

    if not isinstance(msg["content"], str):
        raise ValueError(
            f"Message {index}: 'content' must be string, "
            f"got {type(msg['content']).__name__}"
        )


def format_conversation(messages: list[dict]) -> dict:
    """Format and validate conversation with metadata.

    Args:
        messages: List of message dictionaries with 'role' and 'content'.

    Returns:
        Formatted conversation with metadata.

    Raises:
        ValueError: If any message is invalid.
    """
    if not messages:
        raise ValueError("Messages list cannot be empty")

    # Validate all messages
    for i, msg in enumerate(messages):
        validate_message(msg, i)

    # Calculate metadata
    total_tokens = sum(estimate_tokens(msg["content"]) for msg in messages)
    role_counts = dict(Counter(msg["role"] for msg in messages))

    return {
        "messages": messages,
        "metadata": {
            "message_count": len(messages),
            "estimated_tokens": total_tokens,
            "roles": role_counts
        }
    }


if __name__ == "__main__":
    # Test with sample conversation
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "user", "content": "What's the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."}
    ]

    try:
        result = format_conversation(messages)
        print("Formatted conversation:")
        print(json.dumps(result, indent=2))
    except ValueError as e:
        print(f"Validation error: {e}")

    # Test with invalid message
    print("\n--- Testing validation ---")
    invalid_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "invalid_role", "content": "Test"}  # Invalid role
    ]

    try:
        format_conversation(invalid_messages)
    except ValueError as e:
        print(f"Caught expected error: {e}")
