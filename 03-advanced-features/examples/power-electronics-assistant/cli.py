#!/usr/bin/env python3
"""
Power Electronics Assistant - Interactive CLI

Interactive command-line interface for the Power Electronics Assistant.

Features:
- Interactive chat with Claude/OpenAI
- Tool use visualization
- Conversation history
- Cost tracking
- Save/load conversations
- Multi-provider support

Usage:
    python cli.py
    python cli.py --provider openai
    python cli.py --model claude-3-5-haiku-20241022
"""

import sys
import argparse
from typing import Optional
from assistant import PowerElectronicsAssistant


class CLI:
    """Interactive CLI for Power Electronics Assistant."""

    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """Initialize CLI with assistant."""
        self.assistant = PowerElectronicsAssistant(provider=provider, model=model)
        self.running = True

    def print_welcome(self):
        """Print welcome message."""
        print("\n" + "🔌 " + "=" * 76 + " 🔌")
        print("    POWER ELECTRONICS ASSISTANT - Interactive CLI")
        print("🔌 " + "=" * 76 + " 🔌")
        print(f"\nProvider: {self.assistant.provider.upper()}")
        print(f"Model:    {self.assistant.model}")
        print("\nI can help you with:")
        print("  • Resistor power calculations")
        print("  • Capacitor value calculations")
        print("  • MOSFET component selection")
        print("  • Thermal analysis")
        print("  • LED current limiting")
        print("  • Buck converter design")
        print("\n" + "=" * 80)
        print("Commands:")
        print("  /help    - Show this help message")
        print("  /stats   - Show conversation statistics")
        print("  /clear   - Clear conversation history")
        print("  /save    - Save conversation to file")
        print("  /load    - Load conversation from file")
        print("  /example - Show example queries")
        print("  /quit    - Exit the assistant")
        print("=" * 80 + "\n")

    def print_help(self):
        """Print help message."""
        print("\n" + "=" * 80)
        print("📚 HELP - Available Commands")
        print("=" * 80)
        print("\n/help    - Show this help message")
        print("/stats   - Display conversation statistics (tokens, cost, tool uses)")
        print("/clear   - Clear conversation history and start fresh")
        print("/save    - Save current conversation to JSON file")
        print("/load    - Load a saved conversation from JSON file")
        print("/example - Display example queries you can ask")
        print("/quit    - Exit the assistant\n")

        print("=" * 80)
        print("💡 Usage Tips")
        print("=" * 80)
        print("\nAsk natural language questions like:")
        print('  • "Calculate resistor for 20mA LED at 5V"')
        print('  • "Select MOSFET for 24V 5A motor controller"')
        print('  • "Design buck converter 12V to 5V at 2A"')
        print('  • "Calculate thermal resistance for 5W dissipation"')
        print()

    def print_examples(self):
        """Print example queries."""
        print("\n" + "=" * 80)
        print("💡 EXAMPLE QUERIES")
        print("=" * 80)

        examples = [
            {
                "category": "LED Circuits",
                "queries": [
                    "Calculate the resistor needed for a blue LED (3.2V, 20mA) with a 9V supply",
                    "I have a 12V supply and want to power a red LED at 15mA. What resistor?"
                ]
            },
            {
                "category": "MOSFET Selection",
                "queries": [
                    "Select a MOSFET for switching a 12V 3A load",
                    "I need a MOSFET for a 48V motor controller handling 10A"
                ]
            },
            {
                "category": "Resistor Power",
                "queries": [
                    "What power rating do I need for a 100Ω resistor with 12V across it?",
                    "Calculate power dissipation in a 10kΩ resistor with 5mA current"
                ]
            },
            {
                "category": "Capacitor Design",
                "queries": [
                    "Calculate filter capacitor for 1A load, 50mV ripple at 100kHz",
                    "What capacitor do I need for a 2A load with 20mV ripple at 50kHz?"
                ]
            },
            {
                "category": "Buck Converter",
                "queries": [
                    "Design a buck converter: 24V input, 5V output, 3A load, 100kHz switching",
                    "Help me design a 12V to 3.3V buck converter for 1.5A at 200kHz"
                ]
            },
            {
                "category": "Thermal Analysis",
                "queries": [
                    "Calculate heatsink requirements for 10W dissipation, 85°C max junction temp",
                    "Thermal analysis for 5W component with 50°C/W junction-to-case resistance"
                ]
            }
        ]

        for example in examples:
            print(f"\n📁 {example['category']}:")
            for i, query in enumerate(example['queries'], 1):
                print(f"   {i}. \"{query}\"")

        print("\n" + "=" * 80)
        print("Just type any of these queries (or similar ones) to get started!")
        print("=" * 80 + "\n")

    def print_stats(self):
        """Print conversation statistics."""
        stats = self.assistant.get_stats()

        print("\n" + "=" * 80)
        print("📊 CONVERSATION STATISTICS")
        print("=" * 80)
        print(f"\nProvider:        {stats['provider'].upper()}")
        print(f"Model:           {stats['model']}")
        print(f"Messages:        {stats['messages']}")
        print(f"Input tokens:    {stats['input_tokens']:,}")
        print(f"Output tokens:   {stats['output_tokens']:,}")
        print(f"Total tokens:    {stats['total_tokens']:,}")
        print(f"Tool uses:       {stats['tool_uses']}")
        print(f"Estimated cost:  ${stats['estimated_cost']:.6f}")

        # Cost breakdown
        if stats['provider'] == "claude":
            input_cost = (stats['input_tokens'] / 1_000_000) * 3.00
            output_cost = (stats['output_tokens'] / 1_000_000) * 15.00
        else:
            input_cost = (stats['input_tokens'] / 1_000_000) * 10.00
            output_cost = (stats['output_tokens'] / 1_000_000) * 30.00

        print(f"\nCost breakdown:")
        print(f"  Input:  ${input_cost:.6f}")
        print(f"  Output: ${output_cost:.6f}")

        print("=" * 80 + "\n")

    def save_conversation(self):
        """Save conversation with user input."""
        filename = input("Enter filename (e.g., conversation.json): ").strip()
        if not filename:
            filename = "conversation.json"

        if not filename.endswith('.json'):
            filename += '.json'

        try:
            self.assistant.save_conversation(filename)
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")

    def load_conversation(self):
        """Load conversation with user input."""
        filename = input("Enter filename to load: ").strip()

        try:
            self.assistant.load_conversation(filename)
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except Exception as e:
            print(f"❌ Error loading conversation: {e}")

    def handle_command(self, command: str) -> bool:
        """
        Handle special commands.

        Returns:
            True if command was handled, False otherwise
        """
        command = command.lower().strip()

        if command in ['/quit', '/exit', '/q']:
            print("\n👋 Thank you for using the Power Electronics Assistant!")
            self.print_stats()
            self.running = False
            return True

        elif command == '/help':
            self.print_help()
            return True

        elif command == '/stats':
            self.print_stats()
            return True

        elif command == '/clear':
            self.assistant.clear_history()
            return True

        elif command == '/save':
            self.save_conversation()
            return True

        elif command == '/load':
            self.load_conversation()
            return True

        elif command == '/example':
            self.print_examples()
            return True

        return False

    def run(self):
        """Run the interactive CLI."""
        self.print_welcome()

        while self.running:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                    continue

                # Send to assistant
                print("\n🤔 Assistant thinking...", end="", flush=True)
                result = self.assistant.chat(user_input)
                print("\r" + " " * 30 + "\r", end="")  # Clear "thinking" message

                # Display response
                print(f"🤖 Assistant:\n{result['response']}\n")

                # Show tool use count if any tools were used
                if result['tool_uses'] > 0:
                    print(f"[Used {result['tool_uses']} tool(s)]")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self.print_stats()
                break

            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Type /help for assistance or /quit to exit.\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Power Electronics Assistant - Interactive CLI"
    )
    parser.add_argument(
        "--provider",
        choices=["claude", "openai"],
        default="claude",
        help="AI provider (default: claude)"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model name (optional, uses defaults if not specified)"
    )

    args = parser.parse_args()

    # Check for API keys
    import os
    from dotenv import load_dotenv
    load_dotenv()

    if args.provider == "claude" and not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("Please set it in your .env file")
        sys.exit(1)

    if args.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Please set it in your .env file")
        sys.exit(1)

    # Run CLI
    try:
        cli = CLI(provider=args.provider, model=args.model)
        cli.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
