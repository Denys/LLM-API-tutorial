#!/usr/bin/env python3
"""
Interactive OpenAI CLI Session

Provides an interactive command-line interface for OpenAI's GPT models.

Features:
- Conversation history
- Model selection
- Token and cost tracking
- Command shortcuts

Usage:
    python interactive_openai.py
    python interactive_openai.py --model gpt-4-turbo
"""

import os
import sys
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class InteractiveOpenAI:
    """Interactive OpenAI CLI session manager."""

    def __init__(self, model: str = "gpt-4-turbo"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.conversation: List[Dict] = []
        self.total_tokens = 0
        self.total_cost = 0.0

    def chat(self, message: str) -> str:
        """Send message and get response."""
        # Add user message to conversation
        self.conversation.append({"role": "user", "content": message})

        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.conversation
        )

        # Extract response
        assistant_message = response.choices[0].message.content

        # Add to conversation history
        self.conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Track usage
        if response.usage:
            self.total_tokens += response.usage.total_tokens

            # Calculate cost
            if "gpt-4" in self.model:
                input_cost = (response.usage.prompt_tokens / 1_000_000) * 10.00
                output_cost = (response.usage.completion_tokens / 1_000_000) * 30.00
            else:  # gpt-3.5-turbo
                input_cost = (response.usage.prompt_tokens / 1_000_000) * 0.50
                output_cost = (response.usage.completion_tokens / 1_000_000) * 1.50

            self.total_cost += input_cost + output_cost

        return assistant_message

    def clear_history(self):
        """Clear conversation history."""
        self.conversation = []
        print("🗑️  Conversation history cleared")

    def show_stats(self):
        """Show session statistics."""
        print("\n" + "=" * 60)
        print("📊 Session Statistics")
        print("=" * 60)
        print(f"Model:           {self.model}")
        print(f"Messages:        {len(self.conversation)}")
        print(f"Total Tokens:    {self.total_tokens:,}")
        print(f"Estimated Cost:  ${self.total_cost:.4f}")
        print("=" * 60 + "\n")

    def help(self):
        """Show help message."""
        print("\n" + "=" * 60)
        print("📚 Commands")
        print("=" * 60)
        print("/help     - Show this help message")
        print("/clear    - Clear conversation history")
        print("/stats    - Show session statistics")
        print("/model    - Change model")
        print("/system   - Set system message")
        print("/quit     - Exit (or Ctrl+C)")
        print("=" * 60 + "\n")

    def change_model(self, new_model: str = None):
        """Change the model."""
        if not new_model:
            print("\nAvailable models:")
            print("  • gpt-4-turbo (recommended)")
            print("  • gpt-4")
            print("  • gpt-3.5-turbo (cheaper)")
            new_model = input("\nEnter model name: ").strip()

        self.model = new_model
        print(f"✅ Model changed to: {new_model}")

    def set_system_message(self):
        """Set or update system message."""
        print("\nEnter system message (empty line to finish):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)

        system_message = "\n".join(lines)

        # Remove old system message if exists
        self.conversation = [
            msg for msg in self.conversation
            if msg["role"] != "system"
        ]

        # Add new system message at the beginning
        if system_message:
            self.conversation.insert(0, {
                "role": "system",
                "content": system_message
            })
            print("✅ System message set")

    def run(self):
        """Run interactive session."""
        print("\n" + "🤖 " + "=" * 56 + " 🤖")
        print("    OPENAI INTERACTIVE CLI")
        print("🤖 " + "=" * 56 + " 🤖")
        print(f"\nModel: {self.model}")
        print("Type /help for commands, /quit to exit\n")

        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    command = user_input.lower()

                    if command in ["/quit", "/exit", "/q"]:
                        self.show_stats()
                        print("Goodbye! 👋\n")
                        break

                    elif command == "/help":
                        self.help()

                    elif command == "/clear":
                        self.clear_history()

                    elif command == "/stats":
                        self.show_stats()

                    elif command == "/model":
                        self.change_model()

                    elif command == "/system":
                        self.set_system_message()

                    else:
                        print(f"❌ Unknown command: {user_input}")
                        print("Type /help for available commands")

                    continue

                # Send to OpenAI
                print("\n🤖 Assistant: ", end="", flush=True)
                response = self.chat(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.show_stats()
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Interactive OpenAI CLI")
    parser.add_argument("--model", default="gpt-4-turbo",
                        help="Model to use (default: gpt-4-turbo)")
    parser.add_argument("--system", help="System message")

    args = parser.parse_args()

    # Create session
    session = InteractiveOpenAI(model=args.model)

    # Set system message if provided
    if args.system:
        session.conversation.insert(0, {
            "role": "system",
            "content": args.system
        })

    # Run interactive session
    session.run()


if __name__ == "__main__":
    main()
