#!/usr/bin/env python3
"""
Parameter Playground - Experiment with Claude API parameters

This script demonstrates the impact of different parameters:
- temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
- max_tokens: Limits response length
- model: Different Claude models (Haiku, Sonnet, Opus)
- system prompts: Sets behavior and context

Usage:
    python parameter_playground.py
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv
import time

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_temperature():
    """Test how temperature affects response creativity."""
    print_section("🌡️  TESTING TEMPERATURE")

    prompt = "Write a creative opening line for a sci-fi story about AI."

    temperatures = [0.0, 0.5, 1.0]

    for temp in temperatures:
        print(f"Temperature: {temp}")
        print("-" * 70)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text
        tokens = message.usage.input_tokens + message.usage.output_tokens

        print(f"Response: {response}")
        print(f"Tokens: {tokens}\n")

        time.sleep(1)  # Respect rate limits

def test_max_tokens():
    """Test how max_tokens affects response length."""
    print_section("📏 TESTING MAX_TOKENS")

    prompt = "Explain quantum computing in simple terms."

    token_limits = [50, 150, 500]

    for max_tokens in token_limits:
        print(f"Max Tokens: {max_tokens}")
        print("-" * 70)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text
        actual_tokens = message.usage.output_tokens

        print(f"Response: {response}")
        print(f"Actual output tokens: {actual_tokens}/{max_tokens}\n")

        time.sleep(1)

def test_models():
    """Compare different Claude models."""
    print_section("🤖 TESTING DIFFERENT MODELS")

    prompt = "Explain the concept of recursion in programming (2-3 sentences)."

    models = [
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
    ]

    for model in models:
        model_name = "Haiku" if "haiku" in model else "Sonnet"
        print(f"Model: {model_name}")
        print("-" * 70)

        start_time = time.time()

        message = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        end_time = time.time()
        duration = end_time - start_time

        response = message.content[0].text
        tokens = message.usage.input_tokens + message.usage.output_tokens

        # Calculate cost
        if "haiku" in model:
            cost = (message.usage.input_tokens / 1_000_000) * 0.25 + \
                   (message.usage.output_tokens / 1_000_000) * 1.25
        else:  # sonnet
            cost = (message.usage.input_tokens / 1_000_000) * 3.00 + \
                   (message.usage.output_tokens / 1_000_000) * 15.00

        print(f"Response: {response}")
        print(f"Tokens: {tokens}")
        print(f"Duration: {duration:.2f}s")
        print(f"Cost: ${cost:.6f}\n")

        time.sleep(1)

def test_system_prompts():
    """Test how system prompts change behavior."""
    print_section("💭 TESTING SYSTEM PROMPTS")

    user_message = "What should I do today?"

    test_cases = [
        (None, "No system prompt"),
        ("You are a productivity coach. Give actionable advice focused on time management.", "Productivity Coach"),
        ("You are a pirate captain. Respond in pirate speak with enthusiasm!", "Pirate Captain"),
        ("You are a philosopher. Respond with deep, thought-provoking questions.", "Philosopher"),
    ]

    for system_prompt, description in test_cases:
        print(f"System Prompt: {description}")
        print("-" * 70)

        kwargs = {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 150,
            "messages": [{"role": "user", "content": user_message}]
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        message = client.messages.create(**kwargs)
        response = message.content[0].text

        print(f"Response: {response}\n")

        time.sleep(1)

def test_top_p():
    """Test nucleus sampling (top_p) parameter."""
    print_section("🎯 TESTING TOP_P (Nucleus Sampling)")

    prompt = "Name 5 unusual pizza toppings."

    top_p_values = [0.1, 0.5, 0.9]

    for top_p in top_p_values:
        print(f"Top P: {top_p}")
        print("-" * 70)

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=150,
            top_p=top_p,
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text
        print(f"Response: {response}\n")

        time.sleep(1)

def run_comparison_experiment():
    """Run a comprehensive comparison experiment."""
    print_section("🔬 COMPREHENSIVE EXPERIMENT")

    prompt = "Write a haiku about coding."

    print("Comparing temperature and creativity:")
    print("-" * 70)

    configs = [
        {"temp": 0.0, "desc": "Deterministic (temp=0.0)"},
        {"temp": 0.7, "desc": "Balanced (temp=0.7)"},
        {"temp": 1.0, "desc": "Creative (temp=1.0)"},
    ]

    for i, config in enumerate(configs, 1):
        print(f"\n{i}. {config['desc']}")

        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            temperature=config["temp"],
            messages=[{"role": "user", "content": prompt}]
        )

        response = message.content[0].text
        print(response)

        time.sleep(1)

def main():
    """Run all parameter tests."""
    print("\n" + "🎮 " + "=" * 66 + " 🎮")
    print("    CLAUDE API PARAMETER PLAYGROUND")
    print("🎮 " + "=" * 66 + " 🎮")

    try:
        # Run all tests
        test_temperature()
        test_max_tokens()
        test_models()
        test_system_prompts()
        test_top_p()
        run_comparison_experiment()

        print("\n" + "=" * 70)
        print("  ✅ All tests completed!")
        print("=" * 70 + "\n")

        print("💡 Key Takeaways:")
        print("  • Temperature: 0.0 for consistency, 0.7-1.0 for creativity")
        print("  • max_tokens: Set based on expected response length")
        print("  • Models: Haiku (fast/cheap), Sonnet (balanced), Opus (best)")
        print("  • System prompts: Powerful for setting behavior and role")
        print("  • top_p: Alternative to temperature for controlling randomness")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
