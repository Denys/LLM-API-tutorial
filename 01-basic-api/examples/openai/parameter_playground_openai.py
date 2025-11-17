#!/usr/bin/env python3
"""
Parameter Playground - Experiment with OpenAI API parameters

This script demonstrates the impact of different parameters:
- temperature: Controls randomness (0.0 = deterministic, 2.0 = creative)
- max_tokens: Limits response length
- model: Different models (GPT-4-turbo, GPT-3.5-turbo)
- system prompts: Sets behavior and context

Usage:
    python parameter_playground_openai.py
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")

def test_temperature():
    """Test how temperature affects response creativity."""
    print_section("🌡️  TESTING TEMPERATURE")

    prompt = "Write a creative opening line for a sci-fi story about AI."

    temperatures = [0.0, 0.7, 1.5]

    for temp in temperatures:
        print(f"Temperature: {temp}")
        print("-" * 70)

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=100,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content
        tokens = response.usage.total_tokens

        print(f"Response: {text}")
        print(f"Tokens: {tokens}\n")

        time.sleep(1)

def test_max_tokens():
    """Test how max_tokens affects response length."""
    print_section("📏 TESTING MAX_TOKENS")

    prompt = "Explain quantum computing in simple terms."

    token_limits = [50, 150, 500]

    for max_tokens in token_limits:
        print(f"Max Tokens: {max_tokens}")
        print("-" * 70)

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content
        actual_tokens = response.usage.completion_tokens

        print(f"Response: {text}")
        print(f"Actual output tokens: {actual_tokens}/{max_tokens}\n")

        time.sleep(1)

def test_models():
    """Compare different OpenAI models."""
    print_section("🤖 TESTING DIFFERENT MODELS")

    prompt = "Explain the concept of recursion in programming (2-3 sentences)."

    models = [
        ("gpt-3.5-turbo", 0.50, 1.50),      # input, output per 1M tokens
        ("gpt-4-turbo-preview", 10.00, 30.00),
    ]

    for model, input_rate, output_rate in models:
        model_name = "GPT-3.5" if "3.5" in model else "GPT-4"
        print(f"Model: {model_name}")
        print("-" * 70)

        start_time = time.time()

        response = client.chat.completions.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        end_time = time.time()
        duration = end_time - start_time

        text = response.choices[0].message.content
        tokens = response.usage.total_tokens

        # Calculate cost
        cost = (response.usage.prompt_tokens / 1_000_000) * input_rate + \
               (response.usage.completion_tokens / 1_000_000) * output_rate

        print(f"Response: {text}")
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
        ("You are a productivity coach. Give actionable advice.", "Productivity Coach"),
        ("You are a pirate captain. Respond in pirate speak!", "Pirate Captain"),
        ("You are a philosopher. Respond with thought-provoking questions.", "Philosopher"),
    ]

    for system_prompt, description in test_cases:
        print(f"System Prompt: {description}")
        print("-" * 70)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=150,
            messages=messages
        )

        text = response.choices[0].message.content
        print(f"Response: {text}\n")

        time.sleep(1)

def test_top_p():
    """Test nucleus sampling (top_p) parameter."""
    print_section("🎯 TESTING TOP_P (Nucleus Sampling)")

    prompt = "Name 5 unusual pizza toppings."

    top_p_values = [0.1, 0.5, 0.9]

    for top_p in top_p_values:
        print(f"Top P: {top_p}")
        print("-" * 70)

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=150,
            top_p=top_p,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content
        print(f"Response: {text}\n")

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
        {"temp": 1.5, "desc": "Creative (temp=1.5)"},
    ]

    for i, config in enumerate(configs, 1):
        print(f"\n{i}. {config['desc']}")

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=100,
            temperature=config["temp"],
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.choices[0].message.content
        print(text)

        time.sleep(1)

def main():
    """Run all parameter tests."""
    print("\n" + "🎮 " + "=" * 66 + " 🎮")
    print("    OPENAI API PARAMETER PLAYGROUND")
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
        print("  • Temperature: 0.0 for consistency, 0.7-1.5 for creativity")
        print("  • max_tokens: Set based on expected response length")
        print("  • Models: GPT-3.5 (fast/cheap), GPT-4 (best quality)")
        print("  • System prompts: Powerful for setting behavior and role")
        print("  • top_p: Alternative to temperature for controlling randomness")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set OPENAI_API_KEY in .env")
        raise

if __name__ == "__main__":
    main()
