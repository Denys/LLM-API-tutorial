#!/usr/bin/env python3
"""
Unified AI CLI - Works with Claude, OpenAI, and Gemini

Single interface for multiple AI providers.

Usage:
    # Direct queries
    ai-cli claude "your query"
    ai-cli openai "your query"
    ai-cli gemini "your query"

    # Interactive mode
    ai-cli --interactive claude
    ai-cli --interactive openai
    ai-cli --interactive gemini

    # Compare providers
    ai-cli --compare "Explain MOSFET operation"

    # With specific models
    ai-cli claude --model claude-3-5-haiku-20241022 "query"
    ai-cli openai --model gpt-3.5-turbo "query"
"""

import os
import sys
import argparse
from typing import Optional, List, Dict
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

load_dotenv()


class UnifiedAI:
    """Unified interface for multiple AI providers."""

    def __init__(self):
        """Initialize all available providers."""
        # Claude
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        if self.claude_key:
            self.claude = Anthropic(api_key=self.claude_key)
        else:
            self.claude = None

        # OpenAI
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
        else:
            self.openai_client = None

        # Gemini
        self.gemini_key = os.getenv("GOOGLE_API_KEY")
        if self.gemini_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_key)
            self.gemini_available = True
        else:
            self.gemini_available = False

        # Conversation histories
        self.conversations = {
            "claude": [],
            "openai": [],
            "gemini": None  # Gemini uses chat session
        }

    def query_claude(self, message: str, model: str = "claude-3-5-sonnet-20241022",
                     stream: bool = False) -> str:
        """Query Claude."""
        if not self.claude:
            return "❌ Claude API key not configured"

        # Add to conversation
        self.conversations["claude"].append({
            "role": "user",
            "content": message
        })

        # Query API
        if stream:
            full_response = ""
            with self.claude.messages.stream(
                model=model,
                max_tokens=2048,
                messages=self.conversations["claude"]
            ) as stream:
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    full_response += text
            print()  # New line after streaming

            # Add to history
            self.conversations["claude"].append({
                "role": "assistant",
                "content": full_response
            })

            return full_response

        else:
            response = self.claude.messages.create(
                model=model,
                max_tokens=2048,
                messages=self.conversations["claude"]
            )

            assistant_message = response.content[0].text

            # Add to history
            self.conversations["claude"].append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

    def query_openai(self, message: str, model: str = "gpt-4-turbo",
                     stream: bool = False) -> str:
        """Query OpenAI."""
        if not self.openai_client:
            return "❌ OpenAI API key not configured"

        # Add to conversation
        self.conversations["openai"].append({
            "role": "user",
            "content": message
        })

        # Query API
        if stream:
            full_response = ""
            stream_response = self.openai_client.chat.completions.create(
                model=model,
                messages=self.conversations["openai"],
                stream=True
            )

            for chunk in stream_response:
                if chunk.choices[0].delta.content is not None:
                    text = chunk.choices[0].delta.content
                    print(text, end="", flush=True)
                    full_response += text
            print()  # New line

            # Add to history
            self.conversations["openai"].append({
                "role": "assistant",
                "content": full_response
            })

            return full_response

        else:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=self.conversations["openai"]
            )

            assistant_message = response.choices[0].message.content

            # Add to history
            self.conversations["openai"].append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message

    def query_gemini(self, message: str, model: str = "gemini-pro",
                     stream: bool = False) -> str:
        """Query Gemini."""
        if not self.gemini_available:
            return "❌ Gemini not available (install google-generativeai)"

        # Initialize chat session if needed
        if self.conversations["gemini"] is None:
            gemini_model = genai.GenerativeModel(model)
            self.conversations["gemini"] = gemini_model.start_chat(history=[])

        # Send message
        if stream:
            response = self.conversations["gemini"].send_message(message, stream=True)
            full_text = ""
            for chunk in response:
                text = chunk.text
                print(text, end="", flush=True)
                full_text += text
            print()
            return full_text
        else:
            response = self.conversations["gemini"].send_message(message)
            return response.text

    def query(self, provider: str, message: str, model: Optional[str] = None,
              stream: bool = False) -> str:
        """Query specified provider."""
        if provider == "claude":
            return self.query_claude(
                message,
                model or "claude-3-5-sonnet-20241022",
                stream
            )
        elif provider == "openai":
            return self.query_openai(
                message,
                model or "gpt-4-turbo",
                stream
            )
        elif provider == "gemini":
            return self.query_gemini(
                message,
                model or "gemini-pro",
                stream
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def compare(self, message: str):
        """Compare responses from all providers."""
        print("\n" + "🔄 " + "=" * 74 + " 🔄")
        print("    COMPARING PROVIDERS")
        print("🔄 " + "=" * 74 + " 🔄")
        print(f"\nQuery: {message}\n")

        # Claude
        print("─" * 80)
        print("🔵 CLAUDE (Sonnet):")
        print("─" * 80)
        claude_response = self.query_claude(message)
        print(claude_response)

        # OpenAI
        print("\n" + "─" * 80)
        print("🟢 OPENAI (GPT-4):")
        print("─" * 80)
        openai_response = self.query_openai(message)
        print(openai_response)

        # Gemini
        if self.gemini_available:
            print("\n" + "─" * 80)
            print("🌟 GEMINI (Pro):")
            print("─" * 80)
            gemini_response = self.query_gemini(message)
            print(gemini_response)

        print("\n" + "=" * 80 + "\n")

    def interactive(self, provider: str, model: Optional[str] = None,
                    stream: bool = True):
        """Run interactive session."""
        print(f"\n{'🔵' if provider=='claude' else '🟢' if provider=='openai' else '🌟'} {provider.upper()} Interactive Mode")
        print("=" * 60)
        print("Commands: /help, /clear, /quit, /switch <provider>")
        print("=" * 60 + "\n")

        current_provider = provider

        while True:
            try:
                user_input = input(f"\n💬 You ({current_provider}): ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if user_input.lower() in ["/quit", "/exit", "/q"]:
                        print("\nGoodbye! 👋\n")
                        break

                    elif user_input.lower() == "/help":
                        self.show_help()

                    elif user_input.lower() == "/clear":
                        self.conversations[current_provider] = []
                        if current_provider == "gemini":
                            self.conversations["gemini"] = None
                        print("🗑️  History cleared")

                    elif user_input.lower().startswith("/switch"):
                        parts = user_input.split()
                        if len(parts) > 1:
                            new_provider = parts[1].lower()
                            if new_provider in ["claude", "openai", "gemini"]:
                                current_provider = new_provider
                                print(f"✅ Switched to {current_provider}")
                            else:
                                print(f"❌ Unknown provider: {new_provider}")
                        else:
                            print("Usage: /switch <claude|openai|gemini>")

                    else:
                        print(f"❌ Unknown command: {user_input}")

                    continue

                # Send message
                emoji = "🔵" if current_provider == "claude" else "🟢" if current_provider == "openai" else "🌟"
                print(f"\n{emoji} {current_provider.capitalize()}: ", end="", flush=True)

                response = self.query(current_provider, user_input, model, stream)

                if not stream:
                    print(response)

            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋\n")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")

    def show_help(self):
        """Show help message."""
        print("\n" + "=" * 60)
        print("📚 Unified AI CLI Help")
        print("=" * 60)
        print("\nCommands:")
        print("  /help              - Show this help")
        print("  /clear             - Clear conversation history")
        print("  /switch <provider> - Switch AI provider")
        print("  /quit              - Exit")
        print("\nProviders:")
        print("  • claude  - Anthropic Claude")
        print("  • openai  - OpenAI GPT models")
        print("  • gemini  - Google Gemini")
        print("=" * 60 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified AI CLI - Claude, OpenAI, Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Direct queries
  ai-cli claude "Explain MOSFET operation"
  ai-cli openai "Design a buck converter"
  ai-cli gemini "Calculate LED resistor"

  # Interactive mode
  ai-cli --interactive claude
  ai-cli -i openai

  # Compare providers
  ai-cli --compare "What is a buck converter?"

  # Specific models
  ai-cli claude --model claude-3-5-haiku-20241022 "query"
  ai-cli openai --model gpt-3.5-turbo "query"
        """
    )

    parser.add_argument("provider", nargs="?",
                        choices=["claude", "openai", "gemini"],
                        help="AI provider to use")
    parser.add_argument("query", nargs="*", help="Query to send")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Interactive mode")
    parser.add_argument("--compare", metavar="QUERY",
                        help="Compare response from all providers")
    parser.add_argument("--model", help="Specific model to use")
    parser.add_argument("--stream", action="store_true", default=True,
                        help="Enable streaming (default)")
    parser.add_argument("--no-stream", dest="stream", action="store_false",
                        help="Disable streaming")

    args = parser.parse_args()

    # Create unified AI instance
    ai = UnifiedAI()

    try:
        # Compare mode
        if args.compare:
            ai.compare(args.compare)
            return

        # Interactive mode
        if args.interactive:
            if not args.provider:
                print("Error: Specify provider for interactive mode")
                print("Usage: ai-cli --interactive <claude|openai|gemini>")
                sys.exit(1)

            ai.interactive(args.provider, args.model, args.stream)
            return

        # Direct query mode
        if not args.provider:
            parser.print_help()
            sys.exit(1)

        if not args.query:
            print("Error: Provide a query or use --interactive")
            sys.exit(1)

        query_text = " ".join(args.query)
        response = ai.query(args.provider, query_text, args.model, args.stream)

        if not args.stream:
            print(response)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
