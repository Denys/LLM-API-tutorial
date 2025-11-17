#!/usr/bin/env python3
"""
Interactive chat with OpenAI - Multi-turn conversation

This script demonstrates:
- Maintaining conversation history
- Multi-turn interactions with GPT-4
- Context awareness
- Interactive CLI interface
- Token tracking across conversation

Usage:
    python chat_openai.py
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatSession:
    def __init__(self, model="gpt-4-turbo-preview", max_tokens=1024):
        self.model = model
        self.max_tokens = max_tokens
        self.conversation = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.message_count = 0

    def send_message(self, user_message):
        """Send a message and get OpenAI's response."""
        # Add user message to conversation history
        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        # Get OpenAI's response
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=self.conversation
        )

        # Extract assistant's message
        assistant_message = response.choices[0].message.content

        # Add assistant's response to conversation history
        self.conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Track usage
        self.total_prompt_tokens += response.usage.prompt_tokens
        self.total_completion_tokens += response.usage.completion_tokens
        self.message_count += 1

        return assistant_message, response.usage

    def get_stats(self):
        """Get conversation statistics."""
        total_tokens = self.total_prompt_tokens + self.total_completion_tokens

        # GPT-4-turbo pricing
        input_cost = (self.total_prompt_tokens / 1_000_000) * 10.00
        output_cost = (self.total_completion_tokens / 1_000_000) * 30.00
        total_cost = input_cost + output_cost

        return {
            "messages": self.message_count,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": total_cost
        }

    def clear_history(self):
        """Clear conversation history."""
        self.conversation = []
        print("🗑️  Conversation history cleared!")

def print_stats(stats):
    """Print conversation statistics."""
    print("\n" + "=" * 60)
    print("📊 Conversation Statistics:")
    print("=" * 60)
    print(f"  Messages:        {stats['messages']}")
    print(f"  Prompt tokens:   {stats['prompt_tokens']}")
    print(f"  Completion tokens: {stats['completion_tokens']}")
    print(f"  Total tokens:    {stats['total_tokens']}")
    print(f"  Cost estimate:   ${stats['estimated_cost']:.6f}")
    print("=" * 60 + "\n")

def main():
    print("🤖 OpenAI Chat - Interactive Conversation")
    print("=" * 60)
    print("Commands:")
    print("  /stats  - Show conversation statistics")
    print("  /clear  - Clear conversation history")
    print("  /quit   - Exit chat")
    print("=" * 60 + "\n")

    session = ChatSession()

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['/quit', '/exit', '/q']:
                print("\n👋 Goodbye!")
                break

            if user_input.lower() == '/stats':
                print_stats(session.get_stats())
                continue

            if user_input.lower() == '/clear':
                session.clear_history()
                continue

            # Send message to OpenAI
            response, usage = session.send_message(user_input)

            # Display response
            print(f"\nGPT-4: {response}")
            print(f"[Tokens: {usage.prompt_tokens} in, {usage.completion_tokens} out]\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

    # Show final stats
    if session.message_count > 0:
        print("\n📊 Final Statistics:")
        print_stats(session.get_stats())

if __name__ == "__main__":
    main()
