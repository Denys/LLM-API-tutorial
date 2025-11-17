#!/usr/bin/env python3
"""
Token Counter - Count tokens and estimate costs

This tool helps you:
- Count tokens in text or files
- Estimate API costs before making calls
- Understand token usage patterns
- Optimize prompts for cost

Usage:
    python token_counter.py "Your text here"
    python token_counter.py --file document.txt
    python token_counter.py --file doc.txt --model sonnet
"""

import argparse
import sys
import tiktoken
from pathlib import Path

# Model pricing (per 1M tokens)
PRICING = {
    "haiku": {
        "name": "claude-3-5-haiku-20241022",
        "input": 0.25,
        "output": 1.25
    },
    "sonnet": {
        "name": "claude-3-5-sonnet-20241022",
        "input": 3.00,
        "output": 15.00
    },
    "opus": {
        "name": "claude-3-opus-20240229",
        "input": 15.00,
        "output": 75.00
    }
}

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)

def estimate_cost(token_count: int, model: str = "haiku", io_type: str = "input") -> float:
    """Estimate cost for given token count."""
    model_info = PRICING.get(model, PRICING["haiku"])
    rate = model_info[io_type]
    return (token_count / 1_000_000) * rate

def analyze_text(text: str, model: str = "haiku") -> dict:
    """Analyze text and return detailed statistics."""
    token_count = count_tokens(text)
    char_count = len(text)
    word_count = len(text.split())

    # Cost estimates (assuming equal input/output)
    input_cost = estimate_cost(token_count, model, "input")
    output_cost = estimate_cost(token_count, model, "output")
    total_cost = input_cost + output_cost

    return {
        "text_length": char_count,
        "word_count": word_count,
        "token_count": token_count,
        "tokens_per_word": token_count / word_count if word_count > 0 else 0,
        "chars_per_token": char_count / token_count if token_count > 0 else 0,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "model": PRICING[model]["name"]
    }

def print_analysis(stats: dict):
    """Print analysis results in a formatted way."""
    print("\n" + "=" * 70)
    print("📊 TOKEN ANALYSIS")
    print("=" * 70)
    print(f"Model: {stats['model']}")
    print()
    print(f"📝 Text Statistics:")
    print(f"  Characters:     {stats['text_length']:,}")
    print(f"  Words:          {stats['word_count']:,}")
    print(f"  Tokens:         {stats['token_count']:,}")
    print()
    print(f"📏 Ratios:")
    print(f"  Tokens/Word:    {stats['tokens_per_word']:.2f}")
    print(f"  Chars/Token:    {stats['chars_per_token']:.2f}")
    print()
    print(f"💰 Cost Estimates:")
    print(f"  Input cost:     ${stats['input_cost']:.6f}")
    print(f"  Output cost:    ${stats['output_cost']:.6f}")
    print(f"  Total (I+O):    ${stats['total_cost']:.6f}")
    print("=" * 70)
    print()

def compare_models(text: str):
    """Compare token costs across different models."""
    token_count = count_tokens(text)

    print("\n" + "=" * 70)
    print("🔍 MODEL COMPARISON")
    print("=" * 70)
    print(f"Token count: {token_count:,}\n")
    print(f"{'Model':<15} {'Input Cost':<15} {'Output Cost':<15} {'Total Cost':<15}")
    print("-" * 70)

    for model_key in ["haiku", "sonnet", "opus"]:
        model_info = PRICING[model_key]
        input_cost = estimate_cost(token_count, model_key, "input")
        output_cost = estimate_cost(token_count, model_key, "output")
        total_cost = input_cost + output_cost

        print(f"{model_key.capitalize():<15} ${input_cost:<14.6f} ${output_cost:<14.6f} ${total_cost:<14.6f}")

    print("=" * 70)
    print()

def batch_analysis(texts: list[str], model: str = "haiku"):
    """Analyze multiple texts and provide summary."""
    total_tokens = 0
    total_cost = 0

    print("\n" + "=" * 70)
    print("📚 BATCH ANALYSIS")
    print("=" * 70)
    print(f"Analyzing {len(texts)} texts...\n")

    for i, text in enumerate(texts, 1):
        stats = analyze_text(text, model)
        total_tokens += stats['token_count']
        total_cost += stats['total_cost']
        print(f"Text {i}: {stats['token_count']:,} tokens (${stats['total_cost']:.6f})")

    avg_tokens = total_tokens / len(texts)
    avg_cost = total_cost / len(texts)

    print()
    print(f"Summary:")
    print(f"  Total tokens:   {total_tokens:,}")
    print(f"  Average tokens: {avg_tokens:,.1f}")
    print(f"  Total cost:     ${total_cost:.6f}")
    print(f"  Average cost:   ${avg_cost:.6f}")
    print("=" * 70)
    print()

def main():
    parser = argparse.ArgumentParser(
        description="Count tokens and estimate costs for Claude API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python token_counter.py "Hello, world!"
  python token_counter.py --file document.txt
  python token_counter.py --file doc.txt --model sonnet
  python token_counter.py --compare "Your text here"
        """
    )

    parser.add_argument(
        "text",
        nargs="?",
        help="Text to analyze (or use --file)"
    )
    parser.add_argument(
        "-f", "--file",
        type=Path,
        help="Read text from file"
    )
    parser.add_argument(
        "-m", "--model",
        choices=["haiku", "sonnet", "opus"],
        default="haiku",
        help="Model for cost estimation (default: haiku)"
    )
    parser.add_argument(
        "-c", "--compare",
        action="store_true",
        help="Compare costs across all models"
    )

    args = parser.parse_args()

    # Get text from argument or file
    if args.file:
        if not args.file.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        text = args.file.read_text(encoding="utf-8")
        print(f"📄 Reading from: {args.file}")
    elif args.text:
        text = args.text
    else:
        print("❌ Please provide text or use --file option")
        parser.print_help()
        sys.exit(1)

    # Perform analysis
    if args.compare:
        compare_models(text)
    else:
        stats = analyze_text(text, args.model)
        print_analysis(stats)

    # Helpful tips
    print("💡 Tips:")
    print("  • 1 token ≈ 4 characters ≈ ¾ of a word")
    print("  • Use Haiku for simple tasks (cheapest)")
    print("  • Use prompt caching for repeated content (90% savings)")
    print("  • Keep prompts concise to minimize costs")
    print()

if __name__ == "__main__":
    main()
