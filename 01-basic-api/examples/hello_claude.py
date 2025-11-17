#!/usr/bin/env python3
"""
Your first Claude API call!

This script demonstrates:
- Loading environment variables
- Creating an Anthropic client
- Making a simple API call
- Displaying the response and token usage

Usage:
    python hello_claude.py
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def main():
    print("🤖 Making your first Claude API call...\n")

    # Create a message
    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Say hello and introduce yourself in one sentence!"
            }
        ]
    )

    # Extract the response text
    response_text = message.content[0].text

    # Display results
    print("=" * 60)
    print("Claude's Response:")
    print("=" * 60)
    print(response_text)
    print("\n" + "=" * 60)
    print("📊 Token Usage:")
    print("=" * 60)
    print(f"  Input tokens:  {message.usage.input_tokens}")
    print(f"  Output tokens: {message.usage.output_tokens}")
    print(f"  Total tokens:  {message.usage.input_tokens + message.usage.output_tokens}")

    # Calculate approximate cost (Haiku pricing as of 2025)
    input_cost = (message.usage.input_tokens / 1_000_000) * 0.25
    output_cost = (message.usage.output_tokens / 1_000_000) * 1.25
    total_cost = input_cost + output_cost

    print(f"\n💰 Approximate cost: ${total_cost:.6f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
