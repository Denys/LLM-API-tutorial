#!/usr/bin/env python3
"""
Your first OpenAI API call!

This script demonstrates:
- Loading environment variables
- Creating an OpenAI client
- Making a simple API call with GPT-4
- Displaying the response and token usage

Usage:
    python hello_openai.py
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def main():
    print("🤖 Making your first OpenAI API call...\n")

    # Create a message
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Say hello and introduce yourself in one sentence!"
            }
        ]
    )

    # Extract the response text
    response_text = response.choices[0].message.content

    # Display results
    print("=" * 60)
    print("GPT-4's Response:")
    print("=" * 60)
    print(response_text)
    print("\n" + "=" * 60)
    print("📊 Token Usage:")
    print("=" * 60)
    print(f"  Input tokens:  {response.usage.prompt_tokens}")
    print(f"  Output tokens: {response.usage.completion_tokens}")
    print(f"  Total tokens:  {response.usage.total_tokens}")

    # Calculate approximate cost (GPT-4-turbo pricing as of 2025)
    input_cost = (response.usage.prompt_tokens / 1_000_000) * 10.00
    output_cost = (response.usage.completion_tokens / 1_000_000) * 30.00
    total_cost = input_cost + output_cost

    print(f"\n💰 Approximate cost: ${total_cost:.6f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
