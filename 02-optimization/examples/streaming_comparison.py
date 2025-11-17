#!/usr/bin/env python3
"""
Streaming vs Non-Streaming Comparison

This script demonstrates the differences between:
1. Traditional (non-streaming) API calls
2. Streaming API calls

Shows:
- Time to first token
- Perceived response time
- User experience differences
- Implementation patterns

Usage:
    python streaming_comparison.py
"""

import os
import time
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def non_streaming_request(prompt: str):
    """Traditional non-streaming request."""
    print("\n" + "=" * 70)
    print("⏳ NON-STREAMING REQUEST")
    print("=" * 70)
    print(f"Prompt: {prompt}\n")

    start_time = time.time()
    print("Waiting for complete response...", end="", flush=True)

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    end_time = time.time()
    duration = end_time - start_time

    print(f" Done! ({duration:.2f}s)\n")
    print("Response:")
    print("-" * 70)
    print(message.content[0].text)
    print("-" * 70)
    print(f"\n⏱️  Total time: {duration:.2f}s")
    print(f"📊 Tokens: {message.usage.input_tokens} in, {message.usage.output_tokens} out")

    return duration, message.usage

def streaming_request(prompt: str):
    """Streaming request with real-time output."""
    print("\n" + "=" * 70)
    print("⚡ STREAMING REQUEST")
    print("=" * 70)
    print(f"Prompt: {prompt}\n")

    start_time = time.time()
    first_token_time = None
    token_count = 0

    print("Response:")
    print("-" * 70)

    with client.messages.stream(
        model="claude-3-5-haiku-20241022",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            if first_token_time is None:
                first_token_time = time.time()
                time_to_first = first_token_time - start_time
                print(f"\n[⚡ First token received in {time_to_first:.2f}s]\n", flush=True)

            print(text, end="", flush=True)
            token_count += 1

    end_time = time.time()
    total_duration = end_time - start_time

    # Get final message for usage stats
    final_message = stream.get_final_message()

    print("\n" + "-" * 70)
    print(f"\n⏱️  Time to first token: {time_to_first:.2f}s")
    print(f"⏱️  Total time: {total_duration:.2f}s")
    print(f"📊 Tokens: {final_message.usage.input_tokens} in, {final_message.usage.output_tokens} out")

    return total_duration, time_to_first, final_message.usage

def side_by_side_comparison():
    """Compare both methods side by side."""
    prompt = "Explain how neural networks work in 3-4 sentences."

    print("\n" + "🔄 " + "=" * 66 + " 🔄")
    print("    SIDE-BY-SIDE COMPARISON: STREAMING VS NON-STREAMING")
    print("🔄 " + "=" * 66 + " 🔄")

    # Non-streaming
    non_stream_duration, non_stream_usage = non_streaming_request(prompt)

    time.sleep(2)  # Pause between requests

    # Streaming
    stream_duration, time_to_first, stream_usage = streaming_request(prompt)

    # Comparison
    print("\n" + "=" * 70)
    print("📊 COMPARISON SUMMARY")
    print("=" * 70)
    print(f"\n{'Metric':<35} {'Non-Streaming':<17} {'Streaming':<17}")
    print("-" * 70)
    print(f"{'Time to first token':<35} {non_stream_duration:>15.2f}s  {time_to_first:>15.2f}s")
    print(f"{'Total response time':<35} {non_stream_duration:>15.2f}s  {stream_duration:>15.2f}s")
    print(f"{'Input tokens':<35} {non_stream_usage.input_tokens:>17}  {stream_usage.input_tokens:>17}")
    print(f"{'Output tokens':<35} {non_stream_usage.output_tokens:>17}  {stream_usage.output_tokens:>17}")

    # Cost is the same!
    cost_non_stream = (non_stream_usage.input_tokens / 1_000_000) * 0.25 + \
                      (non_stream_usage.output_tokens / 1_000_000) * 1.25
    cost_stream = (stream_usage.input_tokens / 1_000_000) * 0.25 + \
                  (stream_usage.output_tokens / 1_000_000) * 1.25

    print(f"{'Cost':<35} ${cost_non_stream:>16.6f}  ${cost_stream:>16.6f}")

    print("\n" + "=" * 70)

    # Calculate improvement
    if time_to_first < non_stream_duration:
        improvement = ((non_stream_duration - time_to_first) / non_stream_duration) * 100
        print(f"⚡ Streaming feels {improvement:.0f}% faster!")
        print(f"   (User sees output {time_to_first:.2f}s earlier)")
    print()

def demonstrate_use_cases():
    """Show practical use cases for streaming."""
    print("\n" + "=" * 70)
    print("💼 STREAMING USE CASES")
    print("=" * 70)

    print("\n1️⃣  Long-form content generation")
    print("   Perfect for: Stories, essays, documentation")
    print("   Benefit: Users see content immediately, can stop if needed\n")

    with client.messages.stream(
        model="claude-3-5-haiku-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": "Write a short paragraph about the ocean."}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            time.sleep(0.02)  # Simulate typing effect

    print("\n\n" + "-" * 70)

    print("\n2️⃣  Interactive chat applications")
    print("   Perfect for: Chatbots, assistants")
    print("   Benefit: Natural conversation flow\n")

    # Simulate chat
    messages = ["Hi!", "What's the weather like?"]

    for msg in messages:
        print(f"User: {msg}")
        print("Claude: ", end="", flush=True)

        with client.messages.stream(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": msg}]
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                time.sleep(0.01)

        print("\n")

    print("-" * 70)

    print("\n3️⃣  Real-time processing")
    print("   Perfect for: Sentiment analysis, keyword extraction")
    print("   Benefit: Can process output as it arrives\n")

    keywords_found = []

    with client.messages.stream(
        model="claude-3-5-haiku-20241022",
        max_tokens=200,
        messages=[{"role": "user", "content": "List 5 keywords about AI: machine learning, neural networks..."}]
    ) as stream:
        buffer = ""
        for text in stream.text_stream:
            print(text, end="", flush=True)
            buffer += text

            # Extract keywords in real-time
            if "," in buffer or "." in buffer or "\n" in buffer:
                # Simple keyword extraction
                words = buffer.replace(",", " ").replace(".", " ").replace("\n", " ").split()
                for word in words:
                    if len(word) > 3 and word.lower() not in ["this", "that", "with"]:
                        if word not in keywords_found:
                            keywords_found.append(word)
                buffer = ""

    print(f"\n\nKeywords extracted in real-time: {', '.join(keywords_found[:5])}")
    print()

def main():
    """Run all demonstrations."""
    print("\n⚡ STREAMING API DEMONSTRATION")
    print("See the difference between streaming and non-streaming!")

    try:
        # Main comparison
        side_by_side_comparison()

        # Use cases
        demonstrate_use_cases()

        # Final tips
        print("\n" + "=" * 70)
        print("💡 BEST PRACTICES")
        print("=" * 70)
        print("\nUse STREAMING when:")
        print("  ✅ Building chat interfaces")
        print("  ✅ Generating long-form content")
        print("  ✅ User experience is priority")
        print("  ✅ Processing output in real-time")

        print("\nUse NON-STREAMING when:")
        print("  ✅ Batch processing")
        print("  ✅ Background tasks")
        print("  ✅ Need complete response before proceeding")
        print("  ✅ Simpler error handling needed")

        print("\nKey Points:")
        print("  • Streaming and non-streaming cost the SAME")
        print("  • Streaming feels much faster to users")
        print("  • Use streaming for better UX in interactive apps")
        print("  • Both approaches produce identical results")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set ANTHROPIC_API_KEY in .env")

if __name__ == "__main__":
    main()
