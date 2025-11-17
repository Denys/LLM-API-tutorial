#!/usr/bin/env python3
"""
Interactive chat with Claude - Multi-turn conversation

This script demonstrates:
- Maintaining conversation history
- Multi-turn interactions
- Context awareness
- Interactive CLI interface
- Token tracking across conversation

Usage:
    python chat_conversation.py
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class ChatSession:
    def __init__(self, model="claude-3-5-haiku-20241022", max_tokens=1024):
        self.model = model
        self.max_tokens = max_tokens
        self.conversation = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.message_count = 0

    def send_message(self, user_message):
        """Send a message and get Claude's response."""
        # Add user message to conversation history
        self.conversation.append({
            "role": "user",
            "content": user_message
        })

        # Get Claude's response
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=self.conversation
        )

        # Extract assistant's message
        assistant_message = response.content[0].text

        # Add assistant's response to conversation history
        self.conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Track usage
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens
        self.message_count += 1

        return assistant_message, response.usage

    def get_stats(self):
        """Get conversation statistics."""
        total_tokens = self.total_input_tokens + self.total_output_tokens
        input_cost = (self.total_input_tokens / 1_000_000) * 0.25
        output_cost = (self.total_output_tokens / 1_000_000) * 1.25
        total_cost = input_cost + output_cost

        return {
            "messages": self.message_count,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
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
    print(f"  Messages:      {stats['messages']}")
    print(f"  Input tokens:  {stats['input_tokens']}")
    print(f"  Output tokens: {stats['output_tokens']}")
    print(f"  Total tokens:  {stats['total_tokens']}")
    print(f"  Cost estimate: ${stats['estimated_cost']:.6f}")
    print("=" * 60 + "\n")

def main():
    print("🤖 Claude Chat - Interactive Conversation")
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

            # Send message to Claude
            response, usage = session.send_message(user_input)

            # Display Claude's response
            print(f"\nClaude: {response}")
            print(f"[Tokens: {usage.input_tokens} in, {usage.output_tokens} out]\n")

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
