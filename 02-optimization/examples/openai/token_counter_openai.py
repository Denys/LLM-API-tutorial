#!/usr/bin/env python3
"""
Token Counter for OpenAI - Track and optimize token usage

This script demonstrates:
- Counting tokens with tiktoken (OpenAI's tokenizer)
- Understanding GPT-4 vs GPT-3.5 token usage
- Cost calculation for OpenAI models
- Token optimization strategies
- Comparing message sizes

Usage:
    python token_counter_openai.py
"""

import os
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TokenCounter:
    """Track and analyze OpenAI token usage."""

    def __init__(self, model="gpt-4-turbo-preview"):
        self.model = model

        # Get the correct encoding for the model
        if "gpt-4" in model:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        elif "gpt-3.5" in model:
            self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        else:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        tokens = self.encoding.encode(text)
        return len(tokens)

    def count_message_tokens(self, messages: list) -> int:
        """Count tokens in a list of messages.

        OpenAI adds tokens for message formatting:
        - 3 tokens per message (role/content structure)
        - 1 token per name field
        - 3 tokens for assistant reply priming
        """
        num_tokens = 0

        for message in messages:
            # Every message has structure overhead
            num_tokens += 3  # role, content, and formatting

            # Count content tokens
            num_tokens += self.count_tokens(message["content"])

            # Count role tokens
            num_tokens += self.count_tokens(message["role"])

        # Add tokens for assistant reply priming
        num_tokens += 3

        return num_tokens

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> dict:
        """Calculate cost based on model pricing."""

        # Pricing per 1M tokens (as of 2025)
        pricing = {
            "gpt-4-turbo-preview": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        }

        # Determine pricing for current model
        if "gpt-4-turbo" in self.model:
            rates = pricing["gpt-4-turbo-preview"]
        elif "gpt-4" in self.model:
            rates = pricing["gpt-4"]
        else:
            rates = pricing["gpt-3.5-turbo"]

        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        total_cost = input_cost + output_cost

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "input_rate": rates["input"],
            "output_rate": rates["output"]
        }

def demo_basic_counting():
    """Demonstrate basic token counting."""
    print("\n" + "=" * 70)
    print("📊 BASIC TOKEN COUNTING")
    print("=" * 70)

    counter = TokenCounter()

    test_strings = [
        "Hello, world!",
        "The quick brown fox jumps over the lazy dog.",
        "Artificial intelligence is transforming technology.",
        "GPT-4 is a large language model created by OpenAI using deep learning.",
    ]

    for text in test_strings:
        token_count = counter.count_tokens(text)
        chars = len(text)
        ratio = chars / token_count if token_count > 0 else 0

        print(f"\nText: {text}")
        print(f"  Tokens: {token_count}")
        print(f"  Characters: {chars}")
        print(f"  Chars per token: {ratio:.2f}")

def demo_message_counting():
    """Demonstrate message token counting."""
    print("\n" + "=" * 70)
    print("💬 MESSAGE TOKEN COUNTING")
    print("=" * 70)

    counter = TokenCounter()

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a high-level programming language."},
        {"role": "user", "content": "Can you give me an example?"},
    ]

    print("\nConversation:")
    for msg in messages:
        print(f"  {msg['role']}: {msg['content']}")

    estimated_tokens = counter.count_message_tokens(messages)

    print(f"\nEstimated input tokens: {estimated_tokens}")
    print("  (includes formatting overhead)")

def demo_cost_calculation():
    """Demonstrate cost calculation."""
    print("\n" + "=" * 70)
    print("💰 COST CALCULATION")
    print("=" * 70)

    models = ["gpt-3.5-turbo", "gpt-4-turbo-preview"]

    # Sample usage
    input_tokens = 1000
    output_tokens = 500

    print(f"\nScenario: {input_tokens} input tokens, {output_tokens} output tokens\n")

    for model in models:
        counter = TokenCounter(model=model)
        cost_info = counter.estimate_cost(input_tokens, output_tokens)

        model_name = "GPT-3.5" if "3.5" in model else "GPT-4"

        print(f"{model_name}:")
        print(f"  Input:  ${cost_info['input_cost']:.6f}")
        print(f"  Output: ${cost_info['output_cost']:.6f}")
        print(f"  Total:  ${cost_info['total_cost']:.6f}")
        print()

def demo_real_api_call():
    """Make a real API call and track tokens."""
    print("\n" + "=" * 70)
    print("🔬 REAL API CALL TOKEN TRACKING")
    print("=" * 70)

    counter = TokenCounter()

    messages = [
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "Explain quantum computing in 2 sentences."}
    ]

    # Estimate before API call
    estimated_input = counter.count_message_tokens(messages)

    print("\nBefore API call:")
    print(f"  Estimated input tokens: {estimated_input}")

    # Make API call
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=100,
        messages=messages
    )

    # Get actual usage
    actual_input = response.usage.prompt_tokens
    actual_output = response.usage.completion_tokens
    total = response.usage.total_tokens

    print("\nAfter API call:")
    print(f"  Actual input tokens:  {actual_input}")
    print(f"  Output tokens:        {actual_output}")
    print(f"  Total tokens:         {total}")
    print(f"  Estimation accuracy:  {(estimated_input/actual_input)*100:.1f}%")

    # Calculate cost
    cost_info = counter.estimate_cost(actual_input, actual_output)

    print(f"\nCost:")
    print(f"  ${cost_info['total_cost']:.6f}")

    print(f"\nResponse:")
    print(f"  {response.choices[0].message.content}")

def demo_optimization_strategies():
    """Show token optimization strategies."""
    print("\n" + "=" * 70)
    print("⚡ TOKEN OPTIMIZATION STRATEGIES")
    print("=" * 70)

    counter = TokenCounter()

    # Strategy 1: Concise prompts
    print("\n1️⃣  Use Concise Prompts")

    verbose = "I would like you to please help me by explaining the concept of recursion in programming. Could you provide a detailed explanation?"
    concise = "Explain recursion in programming."

    verbose_tokens = counter.count_tokens(verbose)
    concise_tokens = counter.count_tokens(concise)
    saved = verbose_tokens - concise_tokens

    print(f"  Verbose:  {verbose_tokens} tokens")
    print(f"  Concise:  {concise_tokens} tokens")
    print(f"  Saved:    {saved} tokens ({(saved/verbose_tokens)*100:.0f}%)")

    # Strategy 2: System message reuse
    print("\n2️⃣  Reuse System Messages")
    print("  • Set system message once per conversation")
    print("  • Avoid repeating instructions in each message")
    print("  • Note: OpenAI doesn't have prompt caching (unlike Claude)")

    # Strategy 3: Use cheaper models when possible
    print("\n3️⃣  Choose Appropriate Model")

    sample_tokens = (500, 200)  # input, output

    for model in ["gpt-3.5-turbo", "gpt-4-turbo-preview"]:
        counter_model = TokenCounter(model=model)
        cost = counter_model.estimate_cost(*sample_tokens)
        model_name = "GPT-3.5" if "3.5" in model else "GPT-4"
        print(f"  {model_name:10} ${cost['total_cost']:.6f}")

    # Strategy 4: Set max_tokens appropriately
    print("\n4️⃣  Set max_tokens Appropriately")
    print("  • Don't set unnecessarily high max_tokens")
    print("  • Estimate response length and add buffer")
    print("  • Example: For 2-3 sentences, use max_tokens=100")

    # Strategy 5: Monitor usage
    print("\n5️⃣  Monitor Usage")
    print("  • Track tokens per request")
    print("  • Set budgets and alerts")
    print("  • Log usage for analysis")

def compare_encoding():
    """Compare different encoding methods."""
    print("\n" + "=" * 70)
    print("🔤 TOKEN ENCODING COMPARISON")
    print("=" * 70)

    text = "Hello! This is a test of token encoding. 你好！こんにちは！"

    encodings = ["gpt2", "cl100k_base", "p50k_base"]

    print(f"\nText: {text}\n")

    for encoding_name in encodings:
        try:
            encoding = tiktoken.get_encoding(encoding_name)
            tokens = encoding.encode(text)
            token_count = len(tokens)

            print(f"{encoding_name:15} {token_count:3} tokens")

            # Show first few tokens
            token_preview = " ".join([str(t) for t in tokens[:5]])
            print(f"{'':15} First tokens: {token_preview}...")
            print()
        except Exception as e:
            print(f"{encoding_name:15} Error: {e}\n")

def main():
    """Run all token counting demonstrations."""
    print("\n💎 " + "=" * 66 + " 💎")
    print("    OPENAI TOKEN COUNTER & OPTIMIZATION GUIDE")
    print("💎 " + "=" * 66 + " 💎")

    try:
        demo_basic_counting()
        demo_message_counting()
        demo_cost_calculation()
        demo_real_api_call()
        demo_optimization_strategies()
        compare_encoding()

        print("\n" + "=" * 70)
        print("✅ All demonstrations completed!")
        print("=" * 70)

        print("\n💡 Key Takeaways:")
        print("  • Use tiktoken to count tokens accurately")
        print("  • Message formatting adds ~3 tokens per message")
        print("  • GPT-3.5 is 20x cheaper than GPT-4")
        print("  • Concise prompts save tokens and money")
        print("  • Always set appropriate max_tokens limits")
        print("  • Track usage with response.usage object")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set OPENAI_API_KEY in .env")
        raise

if __name__ == "__main__":
    main()
