#!/usr/bin/env python3
"""
Prompt Caching Demo - See 90% cost savings in action!

This script demonstrates prompt caching by:
1. Making requests with cached system prompts
2. Showing cache hits and misses
3. Calculating cost savings
4. Comparing cached vs non-cached approaches

Usage:
    python prompt_caching_demo.py
"""

import os
import time
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Large system prompt that we'll cache
EXPERT_SYSTEM_PROMPT = """You are an expert Python developer with 20 years of experience.

Your expertise includes:
- Python 3.x best practices and PEP 8 style guide
- Object-oriented and functional programming patterns
- Async programming with asyncio
- Popular frameworks: Django, Flask, FastAPI
- Data science libraries: NumPy, Pandas, scikit-learn
- Testing with pytest and unittest
- Performance optimization and profiling
- Security best practices
- Package management and virtual environments

When answering questions:
1. Provide clear, concise explanations
2. Include working code examples
3. Explain the reasoning behind your recommendations
4. Mention potential pitfalls or edge cases
5. Suggest best practices and alternatives when relevant

Always prioritize code readability, maintainability, and Pythonic solutions.
"""

def calculate_cost(usage, model="sonnet", cache_read_tokens=0):
    """Calculate cost including cache savings."""
    if model == "sonnet":
        input_rate = 3.00
        output_rate = 15.00
        cache_read_rate = 0.30
    else:
        input_rate = 0.25
        output_rate = 1.25
        cache_read_rate = 0.03

    # Regular input tokens
    regular_input = usage.input_tokens - cache_read_tokens
    regular_cost = (regular_input / 1_000_000) * input_rate

    # Cached tokens (much cheaper!)
    cache_cost = (cache_read_tokens / 1_000_000) * cache_read_rate

    # Output tokens
    output_cost = (usage.output_tokens / 1_000_000) * output_rate

    total_cost = regular_cost + cache_cost + output_cost

    return {
        "regular_input_cost": regular_cost,
        "cache_cost": cache_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }

def demo_without_caching():
    """Make requests WITHOUT caching - expensive!"""
    print("\n" + "=" * 70)
    print("❌ WITHOUT CACHING (Expensive)")
    print("=" * 70)

    questions = [
        "Explain list comprehensions",
        "What are decorators?",
        "How does async/await work?"
    ]

    total_cost = 0

    for i, question in enumerate(questions, 1):
        print(f"\nRequest {i}: {question}")
        print("-" * 70)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            system=EXPERT_SYSTEM_PROMPT,  # NO CACHING!
            messages=[{"role": "user", "content": question}]
        )

        cost_info = calculate_cost(message.usage)

        print(f"Input tokens:  {message.usage.input_tokens}")
        print(f"Output tokens: {message.usage.output_tokens}")
        print(f"Cost: ${cost_info['total_cost']:.6f}")

        total_cost += cost_info['total_cost']
        time.sleep(1)  # Respect rate limits

    print("\n" + "=" * 70)
    print(f"💸 TOTAL COST WITHOUT CACHING: ${total_cost:.6f}")
    print("=" * 70)

    return total_cost

def demo_with_caching():
    """Make requests WITH caching - much cheaper!"""
    print("\n" + "=" * 70)
    print("✅ WITH CACHING (Cost-Effective)")
    print("=" * 70)

    questions = [
        "Explain list comprehensions",
        "What are decorators?",
        "How does async/await work?"
    ]

    # System prompt with caching enabled
    cached_system = [
        {
            "type": "text",
            "text": EXPERT_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}  # ← CACHE THIS!
        }
    ]

    total_cost = 0
    cache_savings = 0

    for i, question in enumerate(questions, 1):
        print(f"\nRequest {i}: {question}")
        print("-" * 70)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            system=cached_system,  # CACHED SYSTEM PROMPT!
            messages=[{"role": "user", "content": question}]
        )

        # Check cache usage
        cache_read_tokens = getattr(message.usage, 'cache_read_input_tokens', 0)
        cache_creation_tokens = getattr(message.usage, 'cache_creation_input_tokens', 0)

        if cache_read_tokens > 0:
            print(f"🎯 Cache HIT! Saved {cache_read_tokens} tokens")
        if cache_creation_tokens > 0:
            print(f"📝 Cache created: {cache_creation_tokens} tokens")

        cost_info = calculate_cost(message.usage, cache_read_tokens=cache_read_tokens)

        print(f"Input tokens:  {message.usage.input_tokens}")
        print(f"  Cached:      {cache_read_tokens}")
        print(f"  Regular:     {message.usage.input_tokens - cache_read_tokens}")
        print(f"Output tokens: {message.usage.output_tokens}")
        print(f"Cost: ${cost_info['total_cost']:.6f}")

        if cache_read_tokens > 0:
            # Calculate what it would have cost without cache
            full_cost = calculate_cost(message.usage, cache_read_tokens=0)
            saved = full_cost['total_cost'] - cost_info['total_cost']
            cache_savings += saved
            print(f"  Saved: ${saved:.6f} (vs non-cached)")

        total_cost += cost_info['total_cost']
        time.sleep(1)

    print("\n" + "=" * 70)
    print(f"💰 TOTAL COST WITH CACHING: ${total_cost:.6f}")
    if cache_savings > 0:
        print(f"🎉 CACHE SAVINGS: ${cache_savings:.6f}")
    print("=" * 70)

    return total_cost, cache_savings

def demo_conversation_caching():
    """Demonstrate caching with conversation history."""
    print("\n" + "=" * 70)
    print("💬 CONVERSATION WITH CACHING")
    print("=" * 70)
    print("This shows caching in a multi-turn conversation")
    print()

    conversation = []

    # Cached system prompt
    cached_system = [
        {
            "type": "text",
            "text": EXPERT_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }
    ]

    questions = [
        "What is a Python decorator?",
        "Can you show me an example?",
        "How would I use it with arguments?"
    ]

    total_cost = 0

    for i, question in enumerate(questions, 1):
        print(f"\nTurn {i}:")
        print(f"User: {question}")

        # Add user message
        conversation.append({"role": "user", "content": question})

        # Make request
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            system=cached_system,
            messages=conversation
        )

        # Add assistant response to conversation
        conversation.append({
            "role": "assistant",
            "content": message.content[0].text
        })

        # Show response
        response_preview = message.content[0].text[:100] + "..."
        print(f"Claude: {response_preview}")

        # Show cache stats
        cache_read = getattr(message.usage, 'cache_read_input_tokens', 0)
        print(f"\nTokens: {message.usage.input_tokens} in, {message.usage.output_tokens} out")
        print(f"Cached: {cache_read} tokens")

        cost_info = calculate_cost(message.usage, cache_read_tokens=cache_read)
        print(f"Cost: ${cost_info['total_cost']:.6f}")

        total_cost += cost_info['total_cost']
        time.sleep(1)

    print("\n" + "=" * 70)
    print(f"💰 Total conversation cost: ${total_cost:.6f}")
    print("=" * 70)

def main():
    """Run all caching demonstrations."""
    print("\n🎯 PROMPT CACHING DEMONSTRATION")
    print("This demo shows how prompt caching can reduce costs by up to 90%!")
    print()

    try:
        # Demo 1: Without caching
        cost_without = demo_without_caching()

        # Demo 2: With caching
        cost_with, savings = demo_with_caching()

        # Demo 3: Conversation caching
        demo_conversation_caching()

        # Final summary
        print("\n" + "=" * 70)
        print("📊 FINAL SUMMARY")
        print("=" * 70)
        print(f"Cost without caching: ${cost_without:.6f}")
        print(f"Cost with caching:    ${cost_with:.6f}")
        print(f"Total saved:          ${cost_without - cost_with:.6f}")

        if cost_without > 0:
            percent_saved = ((cost_without - cost_with) / cost_without) * 100
            print(f"Percentage saved:     {percent_saved:.1f}%")

        print("\n💡 Key Takeaways:")
        print("  • Cache large, static content (system prompts, docs)")
        print("  • Cache is valid for 5 minutes")
        print("  • First request creates cache (normal cost)")
        print("  • Subsequent requests use cache (90% cheaper!)")
        print("  • Perfect for chatbots and repeated queries")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. You have set ANTHROPIC_API_KEY in .env")
        print("  2. You have API credits available")
        print("  3. You're using a model that supports caching")

if __name__ == "__main__":
    main()
