#!/usr/bin/env python3
"""
Claude vs OpenAI Provider Comparison

This script compares Claude and OpenAI APIs side-by-side:
- Response quality and style
- Token usage and cost
- Response time
- API structure differences

Usage:
    python compare_providers.py
"""

import os
import time
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken

load_dotenv()

# Initialize clients
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def claude_request(prompt: str, model="claude-3-5-haiku-20241022", max_tokens=500):
    """Make a Claude API request and measure performance."""
    start_time = time.time()

    message = claude_client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )

    end_time = time.time()
    duration = end_time - start_time

    # Extract response
    response_text = message.content[0].text

    # Calculate cost (Haiku pricing)
    input_cost = (message.usage.input_tokens / 1_000_000) * 0.25
    output_cost = (message.usage.output_tokens / 1_000_000) * 1.25
    total_cost = input_cost + output_cost

    return {
        "provider": "Claude (Haiku)",
        "model": model,
        "response": response_text,
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
        "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
        "cost": total_cost,
        "duration": duration
    }

def openai_request(prompt: str, model="gpt-3.5-turbo", max_tokens=500):
    """Make an OpenAI API request and measure performance."""
    start_time = time.time()

    response = openai_client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )

    end_time = time.time()
    duration = end_time - start_time

    # Extract response
    response_text = response.choices[0].message.content

    # Calculate cost
    if "gpt-4" in model:
        input_rate, output_rate = 10.00, 30.00
    else:  # gpt-3.5-turbo
        input_rate, output_rate = 0.50, 1.50

    input_cost = (response.usage.prompt_tokens / 1_000_000) * input_rate
    output_cost = (response.usage.completion_tokens / 1_000_000) * output_rate
    total_cost = input_cost + output_cost

    return {
        "provider": "OpenAI",
        "model": model,
        "response": response_text,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "cost": total_cost,
        "duration": duration
    }

def compare_responses(prompt: str, description: str = ""):
    """Compare Claude and OpenAI responses side-by-side."""
    print_section(f"Test: {description}")
    print(f"Prompt: {prompt}\n")

    # Claude response
    print("🔵 Claude (Haiku) Response:")
    print("-" * 80)
    claude_result = claude_request(prompt)
    print(claude_result["response"])
    print("-" * 80)

    time.sleep(1)  # Rate limiting

    # OpenAI response
    print("\n🟢 OpenAI (GPT-3.5) Response:")
    print("-" * 80)
    openai_result = openai_request(prompt)
    print(openai_result["response"])
    print("-" * 80)

    # Comparison table
    print("\n📊 Comparison:")
    print(f"{'Metric':<20} {'Claude (Haiku)':<25} {'OpenAI (GPT-3.5)':<25}")
    print("-" * 70)
    print(f"{'Input tokens':<20} {claude_result['input_tokens']:<25} {openai_result['input_tokens']:<25}")
    print(f"{'Output tokens':<20} {claude_result['output_tokens']:<25} {openai_result['output_tokens']:<25}")
    print(f"{'Total tokens':<20} {claude_result['total_tokens']:<25} {openai_result['total_tokens']:<25}")
    print(f"{'Cost':<20} ${claude_result['cost']:<24.6f} ${openai_result['cost']:<24.6f}")
    print(f"{'Duration':<20} {claude_result['duration']:<24.2f}s {openai_result['duration']:<24.2f}s")

    # Winner
    if claude_result['cost'] < openai_result['cost']:
        print(f"\n💰 Most cost-effective: Claude (${claude_result['cost']:.6f})")
    else:
        print(f"\n💰 Most cost-effective: OpenAI (${openai_result['cost']:.6f})")

    if claude_result['duration'] < openai_result['duration']:
        print(f"⚡ Fastest: Claude ({claude_result['duration']:.2f}s)")
    else:
        print(f"⚡ Fastest: OpenAI ({openai_result['duration']:.2f}s)")

    return claude_result, openai_result

def test_api_structure():
    """Show the differences in API structure."""
    print_section("API Structure Comparison")

    print("🔵 Claude API Structure:")
    print("-" * 80)
    print("""
# Claude uses 'messages.create()' with clear separation
message = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

# Access response
text = message.content[0].text

# Token usage
input_tokens = message.usage.input_tokens
output_tokens = message.usage.output_tokens
""")

    print("\n🟢 OpenAI API Structure:")
    print("-" * 80)
    print("""
# OpenAI uses 'chat.completions.create()'
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

# Access response
text = response.choices[0].message.content

# Token usage
prompt_tokens = response.usage.prompt_tokens
completion_tokens = response.usage.completion_tokens
""")

    print("\n📝 Key Differences:")
    print("-" * 80)
    print("1. Method names:")
    print("   • Claude: messages.create()")
    print("   • OpenAI: chat.completions.create()")
    print()
    print("2. Response structure:")
    print("   • Claude: message.content[0].text")
    print("   • OpenAI: response.choices[0].message.content")
    print()
    print("3. Token naming:")
    print("   • Claude: input_tokens / output_tokens")
    print("   • OpenAI: prompt_tokens / completion_tokens")
    print()
    print("4. Model naming:")
    print("   • Claude: claude-3-5-haiku-20241022")
    print("   • OpenAI: gpt-3.5-turbo, gpt-4-turbo-preview")

def test_pricing_comparison():
    """Compare pricing across models."""
    print_section("Pricing Comparison (per 1M tokens)")

    print(f"{'Model':<30} {'Input':<15} {'Output':<15} {'Context':<15}")
    print("-" * 75)

    # Claude models
    print("🔵 CLAUDE:")
    print(f"{'  Haiku':<30} {'$0.25':<15} {'$1.25':<15} {'200K':<15}")
    print(f"{'  Sonnet':<30} {'$3.00':<15} {'$15.00':<15} {'200K':<15}")
    print(f"{'  Opus':<30} {'$15.00':<15} {'$75.00':<15} {'200K':<15}")

    print()

    # OpenAI models
    print("🟢 OPENAI:")
    print(f"{'  GPT-3.5-turbo':<30} {'$0.50':<15} {'$1.50':<15} {'16K':<15}")
    print(f"{'  GPT-4-turbo':<30} {'$10.00':<15} {'$30.00':<15} {'128K':<15}")
    print(f"{'  GPT-4':<30} {'$30.00':<15} {'$60.00':<15} {'8K':<15}")

    print("\n💡 Cost Analysis:")
    print("-" * 75)
    print("Most affordable:   Claude Haiku ($0.25/$1.25)")
    print("Best value:        Claude Haiku or GPT-3.5-turbo")
    print("Premium quality:   Claude Opus or GPT-4")
    print("Longest context:   Claude models (200K tokens)")

def test_special_features():
    """Compare special features between providers."""
    print_section("Special Features Comparison")

    features = [
        ("Prompt Caching", "✅ Yes (90% discount)", "❌ No"),
        ("Context Window", "✅ 200K tokens", "⚠️  128K max (GPT-4-turbo)"),
        ("Vision API", "✅ Yes", "✅ Yes"),
        ("Function Calling", "✅ Yes (Tool Use)", "✅ Yes (Function Calling)"),
        ("Streaming", "✅ Yes", "✅ Yes"),
        ("JSON Mode", "✅ Yes", "✅ Yes"),
        ("System Messages", "✅ Separate parameter", "✅ In messages array"),
        ("Fine-tuning", "❌ No", "✅ Yes"),
    ]

    print(f"{'Feature':<25} {'Claude':<30} {'OpenAI':<30}")
    print("-" * 85)

    for feature, claude, openai in features:
        print(f"{feature:<25} {claude:<30} {openai:<30}")

def main():
    """Run all comparison tests."""
    print("\n" + "🆚 " + "=" * 76 + " 🆚")
    print("    CLAUDE VS OPENAI: COMPREHENSIVE COMPARISON")
    print("🆚 " + "=" * 76 + " 🆚")

    try:
        # Test 1: API Structure
        test_api_structure()

        # Test 2: Pricing
        test_pricing_comparison()

        # Test 3: Special Features
        test_special_features()

        # Test 4: Real comparison
        compare_responses(
            "Explain what machine learning is in 2-3 sentences.",
            "Simple Explanation"
        )

        time.sleep(2)

        compare_responses(
            "Write a Python function that calculates the Fibonacci sequence.",
            "Code Generation"
        )

        time.sleep(2)

        compare_responses(
            "What are the pros and cons of renewable energy?",
            "Analytical Thinking"
        )

        # Summary
        print_section("Summary & Recommendations")
        print("""
✅ Use CLAUDE when:
  • You need prompt caching (90% cost savings on repeated prompts)
  • Working with very long contexts (up to 200K tokens)
  • Cost is a primary concern (Haiku is most affordable)
  • You want clear, structured API responses
  • Building chatbots with consistent system prompts

✅ Use OPENAI when:
  • You need fine-tuned models for specific tasks
  • Ecosystem integration with OpenAI tools
  • Familiar with GPT API patterns
  • Using GPT-4 for complex reasoning
  • One-off queries (no caching benefit)

💡 Best Practice:
  • Use Claude Haiku for most tasks (fast, cheap)
  • Use Claude Sonnet for complex reasoning
  • Use GPT-3.5-turbo as OpenAI alternative to Haiku
  • Use GPT-4-turbo when you need OpenAI's best model
  • Implement multi-provider support for flexibility
        """)

        print("=" * 80)
        print("✅ Comparison complete!")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set both API keys in .env:")
        print("  - ANTHROPIC_API_KEY")
        print("  - OPENAI_API_KEY")
        raise

if __name__ == "__main__":
    main()
