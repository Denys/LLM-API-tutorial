#!/usr/bin/env python3
"""
Google Gemini CLI Interface

Interactive and direct query interface for Google's Gemini models.

Features:
- Text generation
- Multimodal (text + images)
- Conversation history
- Streaming support

Usage:
    # Direct query
    python gemini_cli.py "Explain MOSFET operation"

    # Interactive mode
    python gemini_cli.py

    # With image
    python gemini_cli.py --image circuit.png "Analyze this circuit"
"""

import os
import sys
from pathlib import Path
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiCLI:
    """CLI interface for Google Gemini."""

    def __init__(self, model_name: str = "gemini-pro"):
        # Configure API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        self.chat_session = None

    def generate(self, prompt: str, stream: bool = False) -> str:
        """Generate response for a prompt."""
        if stream:
            response = self.model.generate_content(prompt, stream=True)
            full_text = ""
            for chunk in response:
                text = chunk.text
                print(text, end="", flush=True)
                full_text += text
            print()  # New line after streaming
            return full_text
        else:
            response = self.model.generate_content(prompt)
            return response.text

    def generate_with_image(self, prompt: str, image_path: str) -> str:
        """Generate response with image input."""
        import PIL.Image

        # Switch to vision model if needed
        if "vision" not in self.model_name:
            self.model = genai.GenerativeModel('gemini-pro-vision')

        # Load image
        img = PIL.Image.open(image_path)

        # Generate response
        response = self.model.generate_content([prompt, img])
        return response.text

    def start_chat(self):
        """Start an interactive chat session."""
        if self.chat_session is None:
            self.chat_session = self.model.start_chat(history=[])
        return self.chat_session

    def send_message(self, message: str, stream: bool = False) -> str:
        """Send message in chat session."""
        session = self.start_chat()

        if stream:
            response = session.send_message(message, stream=True)
            full_text = ""
            for chunk in response:
                text = chunk.text
                print(text, end="", flush=True)
                full_text += text
            print()
            return full_text
        else:
            response = session.send_message(message)
            return response.text

    def clear_history(self):
        """Clear chat history."""
        self.chat_session = None
        print("🗑️  Chat history cleared")

    def show_history(self):
        """Show chat history."""
        if not self.chat_session or not self.chat_session.history:
            print("No conversation history")
            return

        print("\n" + "=" * 60)
        print("💬 Conversation History")
        print("=" * 60)

        for i, message in enumerate(self.chat_session.history):
            role = "You" if message.role == "user" else "Gemini"
            text = message.parts[0].text if message.parts else ""
            print(f"\n{role}: {text[:100]}{'...' if len(text) > 100 else ''}")

        print("=" * 60 + "\n")

    def interactive(self):
        """Run interactive mode."""
        print("\n" + "🌟 " + "=" * 56 + " 🌟")
        print("    GOOGLE GEMINI INTERACTIVE CLI")
        print("🌟 " + "=" * 56 + " 🌟")
        print(f"\nModel: {self.model_name}")
        print("Commands: /help, /history, /clear, /quit\n")

        while True:
            try:
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    if user_input.lower() in ["/quit", "/exit", "/q"]:
                        print("\nGoodbye! 🌟\n")
                        break

                    elif user_input.lower() == "/help":
                        self.show_help()

                    elif user_input.lower() == "/history":
                        self.show_history()

                    elif user_input.lower() == "/clear":
                        self.clear_history()

                    elif user_input.lower() == "/stream":
                        print("Streaming mode (responses will stream in real-time)")

                    else:
                        print(f"Unknown command: {user_input}")
                        print("Type /help for available commands")

                    continue

                # Send message
                print("\n🌟 Gemini: ", end="", flush=True)
                response = self.send_message(user_input, stream=True)

            except KeyboardInterrupt:
                print("\n\nGoodbye! 🌟\n")
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")

    def show_help(self):
        """Show help message."""
        print("\n" + "=" * 60)
        print("📚 Gemini CLI Commands")
        print("=" * 60)
        print("/help      - Show this help message")
        print("/history   - Show conversation history")
        print("/clear     - Clear conversation history")
        print("/quit      - Exit (or Ctrl+C)")
        print("\nFeatures:")
        print("• Streaming responses by default")
        print("• Persistent conversation history")
        print("• Multimodal support (use --image flag)")
        print("=" * 60 + "\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Google Gemini CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python gemini_cli.py

  # Direct query
  python gemini_cli.py "Explain how buck converters work"

  # Analyze image
  python gemini_cli.py --image circuit.png "What is this circuit?"

  # Use different model
  python gemini_cli.py --model gemini-pro-vision
        """
    )

    parser.add_argument("query", nargs="*", help="Query to send to Gemini")
    parser.add_argument("--image", help="Path to image for multimodal query")
    parser.add_argument("--model", default="gemini-pro",
                        choices=["gemini-pro", "gemini-pro-vision"],
                        help="Model to use")
    parser.add_argument("--stream", action="store_true",
                        help="Enable streaming output")

    args = parser.parse_args()

    try:
        # Create CLI instance
        cli = GeminiCLI(model_name=args.model)

        # Direct query mode
        if args.query or args.image:
            query_text = " ".join(args.query) if args.query else "Describe this image"

            if args.image:
                # Multimodal query
                print(f"🖼️  Analyzing image: {args.image}")
                print(f"❓ Query: {query_text}\n")
                response = cli.generate_with_image(query_text, args.image)
                print(f"🌟 Gemini:\n{response}")
            else:
                # Text-only query
                response = cli.generate(query_text, stream=args.stream)
                if not args.stream:
                    print(response)

        # Interactive mode
        else:
            cli.interactive()

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print("\nMake sure you have:", file=sys.stderr)
        print("  1. Set GOOGLE_API_KEY in .env", file=sys.stderr)
        print("  2. pip install google-generativeai", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
