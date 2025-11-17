#!/usr/bin/env python3
"""
Performance Comparison: Claude vs OpenAI

This script compares performance metrics:
- Token efficiency
- Response time
- Streaming performance
- Cost per task
- Throughput

Usage:
    python performance_comparison.py
"""

import os
import time
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv
import statistics

load_dotenv()

claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def benchmark_response_time(provider: str, iterations: int = 5):
    """Benchmark response time for multiple requests."""
    print(f"\n📊 Benchmarking {provider} ({iterations} iterations)...")

    times = []
    tokens_in = []
    tokens_out = []

    prompt = "Explain Python list comprehensions in one sentence."

    for i in range(iterations):
        print(f"  Iteration {i+1}/{iterations}...", end=" ", flush=True)

        start_time = time.time()

        if provider == "Claude":
            message = claude_client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            duration = time.time() - start_time
            tokens_in.append(message.usage.input_tokens)
            tokens_out.append(message.usage.output_tokens)

        elif provider == "OpenAI":
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            duration = time.time() - start_time
            tokens_in.append(response.usage.prompt_tokens)
            tokens_out.append(response.usage.completion_tokens)

        times.append(duration)
        print(f"{duration:.2f}s")

        time.sleep(0.5)  # Rate limiting

    # Calculate statistics
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0

    avg_tokens_in = statistics.mean(tokens_in)
    avg_tokens_out = statistics.mean(tokens_out)

    return {
        "provider": provider,
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "std_dev": std_dev,
        "avg_tokens_in": avg_tokens_in,
        "avg_tokens_out": avg_tokens_out
    }

def benchmark_streaming_performance():
    """Compare streaming performance."""
    print_section("Streaming Performance Comparison")

    prompt = "Write a 100-word paragraph about renewable energy."

    # Claude streaming
    print("🔵 Claude Streaming:")
    print("-" * 80)

    start_time = time.time()
    first_token_time_claude = None
    claude_response = ""

    with claude_client.messages.stream(
        model="claude-3-5-haiku-20241022",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            if first_token_time_claude is None:
                first_token_time_claude = time.time() - start_time
            claude_response += text

    claude_total_time = time.time() - start_time

    print(f"Time to first token: {first_token_time_claude:.2f}s")
    print(f"Total time:          {claude_total_time:.2f}s")
    print(f"Response length:     {len(claude_response)} chars")

    time.sleep(2)

    # OpenAI streaming
    print("\n🟢 OpenAI Streaming:")
    print("-" * 80)

    start_time = time.time()
    first_token_time_openai = None
    openai_response = ""

    stream = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            if first_token_time_openai is None:
                first_token_time_openai = time.time() - start_time
            openai_response += chunk.choices[0].delta.content

    openai_total_time = time.time() - start_time

    print(f"Time to first token: {first_token_time_openai:.2f}s")
    print(f"Total time:          {openai_total_time:.2f}s")
    print(f"Response length:     {len(openai_response)} chars")

    # Comparison
    print("\n📊 Streaming Comparison:")
    print("-" * 80)
    print(f"{'Metric':<25} {'Claude':<20} {'OpenAI':<20}")
    print("-" * 65)
    print(f"{'Time to first token':<25} {first_token_time_claude:<19.2f}s {first_token_time_openai:<19.2f}s")
    print(f"{'Total time':<25} {claude_total_time:<19.2f}s {openai_total_time:<19.2f}s")

    if first_token_time_claude < first_token_time_openai:
        improvement = ((first_token_time_openai - first_token_time_claude) / first_token_time_openai) * 100
        print(f"\n⚡ Claude streaming is {improvement:.0f}% faster to first token!")
    else:
        improvement = ((first_token_time_claude - first_token_time_openai) / first_token_time_claude) * 100
        print(f"\n⚡ OpenAI streaming is {improvement:.0f}% faster to first token!")

def benchmark_token_efficiency():
    """Compare token efficiency for same task."""
    print_section("Token Efficiency Comparison")

    test_cases = [
        "What is Python?",
        "Explain machine learning in simple terms.",
        "Write a function to sort a list of numbers.",
        "What are the benefits of using virtual environments?",
    ]

    results = []

    for i, prompt in enumerate(test_cases, 1):
        print(f"\nTest {i}: {prompt}")
        print("-" * 80)

        # Claude
        claude_msg = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        time.sleep(1)

        # OpenAI
        openai_resp = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        # Compare
        claude_total = claude_msg.usage.input_tokens + claude_msg.usage.output_tokens
        openai_total = openai_resp.usage.prompt_tokens + openai_resp.usage.completion_tokens

        print(f"Claude:  {claude_msg.usage.input_tokens:3d} in + {claude_msg.usage.output_tokens:3d} out = {claude_total:3d} total")
        print(f"OpenAI:  {openai_resp.usage.prompt_tokens:3d} in + {openai_resp.usage.completion_tokens:3d} out = {openai_total:3d} total")

        diff = abs(claude_total - openai_total)
        print(f"Difference: {diff} tokens")

        results.append({
            "prompt": prompt,
            "claude_total": claude_total,
            "openai_total": openai_total,
            "diff": diff
        })

    # Summary
    avg_claude = statistics.mean([r["claude_total"] for r in results])
    avg_openai = statistics.mean([r["openai_total"] for r in results])

    print("\n📊 Average Token Usage:")
    print(f"  Claude:  {avg_claude:.1f} tokens")
    print(f"  OpenAI:  {avg_openai:.1f} tokens")
    print(f"  Difference: {abs(avg_claude - avg_openai):.1f} tokens")

def benchmark_cost_per_task():
    """Compare cost for different task types."""
    print_section("Cost Per Task Comparison")

    tasks = [
        {
            "name": "Simple Q&A",
            "prompt": "What is Python?",
            "max_tokens": 100
        },
        {
            "name": "Code Generation",
            "prompt": "Write a Python function to calculate factorial recursively.",
            "max_tokens": 200
        },
        {
            "name": "Analysis",
            "prompt": "Analyze the pros and cons of using microservices architecture.",
            "max_tokens": 500
        }
    ]

    for task in tasks:
        print(f"\n📝 Task: {task['name']}")
        print("-" * 80)

        # Claude
        claude_msg = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=task["max_tokens"],
            messages=[{"role": "user", "content": task["prompt"]}]
        )

        claude_cost = (claude_msg.usage.input_tokens / 1_000_000) * 0.25 + \
                      (claude_msg.usage.output_tokens / 1_000_000) * 1.25

        time.sleep(1)

        # OpenAI
        openai_resp = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            max_tokens=task["max_tokens"],
            messages=[{"role": "user", "content": task["prompt"]}]
        )

        openai_cost = (openai_resp.usage.prompt_tokens / 1_000_000) * 0.50 + \
                      (openai_resp.usage.completion_tokens / 1_000_000) * 1.50

        # Compare
        print(f"Claude (Haiku):     ${claude_cost:.6f}")
        print(f"OpenAI (GPT-3.5):   ${openai_cost:.6f}")

        if claude_cost < openai_cost:
            savings = ((openai_cost - claude_cost) / openai_cost) * 100
            print(f"💰 Claude is {savings:.1f}% cheaper")
        else:
            savings = ((claude_cost - openai_cost) / claude_cost) * 100
            print(f"💰 OpenAI is {savings:.1f}% cheaper")

def benchmark_with_caching():
    """Demonstrate Claude's caching advantage."""
    print_section("Prompt Caching Performance (Claude Only)")

    large_system_prompt = """You are an expert Python developer with deep knowledge of:
- Python 3.x best practices and PEP 8 guidelines
- Object-oriented and functional programming patterns
- Async programming with asyncio and multiprocessing
- Popular frameworks like Django, Flask, FastAPI
- Data science libraries: NumPy, Pandas, scikit-learn
- Testing with pytest, unittest, and mocking
- Performance optimization and profiling
- Security best practices and common vulnerabilities
- Package management with pip, poetry, and conda
- Virtual environments and dependency management

When answering questions, provide clear explanations with working code examples."""

    # Cached system prompt
    cached_system = [
        {
            "type": "text",
            "text": large_system_prompt,
            "cache_control": {"type": "ephemeral"}
        }
    ]

    questions = [
        "What are decorators?",
        "Explain list comprehensions.",
        "How does async/await work?"
    ]

    print("Note: OpenAI doesn't support prompt caching\n")
    print("Making 3 requests with large system prompt...\n")

    total_cost_cached = 0
    total_cost_uncached = 0

    for i, question in enumerate(questions, 1):
        # With caching
        message = claude_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            system=cached_system,
            messages=[{"role": "user", "content": question}]
        )

        cache_read = getattr(message.usage, 'cache_read_input_tokens', 0)
        cache_creation = getattr(message.usage, 'cache_creation_input_tokens', 0)

        # Calculate cost with cache
        regular_input = message.usage.input_tokens - cache_read
        cost_cached = (regular_input / 1_000_000) * 0.25 + \
                     (cache_read / 1_000_000) * 0.03 + \
                     (message.usage.output_tokens / 1_000_000) * 1.25

        # Calculate what it would cost without cache
        cost_uncached = (message.usage.input_tokens / 1_000_000) * 0.25 + \
                       (message.usage.output_tokens / 1_000_000) * 1.25

        total_cost_cached += cost_cached
        total_cost_uncached += cost_uncached

        status = "CACHE HIT" if cache_read > 0 else "CACHE MISS"
        print(f"Request {i} ({status}):")
        print(f"  Question: {question}")
        print(f"  Cached tokens: {cache_read}")
        print(f"  Cost with cache:    ${cost_cached:.6f}")
        print(f"  Cost without cache: ${cost_uncached:.6f}")
        print(f"  Saved: ${cost_uncached - cost_cached:.6f}\n")

        time.sleep(1)

    # Summary
    savings = total_cost_uncached - total_cost_cached
    percent_saved = (savings / total_cost_uncached) * 100

    print("=" * 80)
    print(f"Total cost WITH caching:    ${total_cost_cached:.6f}")
    print(f"Total cost WITHOUT caching: ${total_cost_uncached:.6f}")
    print(f"💰 Total saved: ${savings:.6f} ({percent_saved:.0f}%)")
    print("=" * 80)
    print("\n⚠️  OpenAI does not have prompt caching - all requests are full price!")

def main():
    """Run all performance benchmarks."""
    print("\n" + "⚡ " + "=" * 76 + " ⚡")
    print("    PERFORMANCE COMPARISON: CLAUDE VS OPENAI")
    print("⚡ " + "=" * 76 + " ⚡")

    try:
        # Benchmark 1: Response time
        print_section("Response Time Benchmark")
        claude_results = benchmark_response_time("Claude", iterations=5)
        openai_results = benchmark_response_time("OpenAI", iterations=5)

        print("\n📊 Response Time Summary:")
        print("-" * 80)
        print(f"{'Provider':<15} {'Avg':<10} {'Min':<10} {'Max':<10} {'Std Dev':<10}")
        print("-" * 80)
        print(f"{'Claude':<15} {claude_results['avg_time']:<9.2f}s {claude_results['min_time']:<9.2f}s {claude_results['max_time']:<9.2f}s {claude_results['std_dev']:<9.2f}s")
        print(f"{'OpenAI':<15} {openai_results['avg_time']:<9.2f}s {openai_results['min_time']:<9.2f}s {openai_results['max_time']:<9.2f}s {openai_results['std_dev']:<9.2f}s")

        # Benchmark 2: Streaming
        benchmark_streaming_performance()

        # Benchmark 3: Token efficiency
        benchmark_token_efficiency()

        # Benchmark 4: Cost per task
        benchmark_cost_per_task()

        # Benchmark 5: Caching advantage
        benchmark_with_caching()

        # Final summary
        print_section("Performance Summary")
        print("""
📊 Key Findings:

SPEED:
  • Both providers have similar response times
  • Streaming provides faster time-to-first-token for both
  • Performance varies by region and time of day

TOKEN EFFICIENCY:
  • Token counts are very similar between providers
  • Minor differences due to different tokenizers
  • Output length is model-dependent, not provider-dependent

COST:
  • Claude Haiku: Most cost-effective ($0.25/$1.25 per 1M)
  • GPT-3.5-turbo: Competitive alternative ($0.50/$1.50 per 1M)
  • Claude's caching: 90% savings on repeated prompts!
  • OpenAI: No caching feature

BEST PRACTICES:
  ✅ Use Claude Haiku for cost-sensitive applications
  ✅ Use prompt caching for chatbots (Claude only)
  ✅ Use streaming for better user experience (both)
  ✅ Use GPT-3.5 as budget OpenAI alternative
  ✅ Monitor token usage and costs continuously
        """)

        print("=" * 80)
        print("✅ Performance benchmarks complete!")
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
