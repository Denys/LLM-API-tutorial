#!/usr/bin/env python3
"""
Streaming with OpenAI - Real-time response generation

This script demonstrates:
- Streaming vs non-streaming API calls
- Time to first token
- User experience improvements
- Cost comparison (same cost!)
- Implementation patterns

Usage:
    python streaming_openai.py
"""

import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def non_streaming_request(prompt: str):
    """Traditional non-streaming request."""
    print("\n" + "=" * 70)
    print("⏳ NON-STREAMING REQUEST")
    print("=" * 70)
    print(f"Prompt: {prompt}\n")

    start_time = time.time()
    print("Waiting for complete response...", end="", flush=True)

    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    end_time = time.time()
    duration = end_time - start_time

    print(f" Done! ({duration:.2f}s)\n")
    print("Response:")
    print("-" * 70)
    print(response.choices[0].message.content)
    print("-" * 70)
    print(f"\n⏱️  Total time: {duration:.2f}s")
    print(f"📊 Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")

    return duration, response.usage

def streaming_request(prompt: str):
    """Streaming request with real-time output."""
    print("\n" + "=" * 70)
    print("⚡ STREAMING REQUEST")
    print("=" * 70)
    print(f"Prompt: {prompt}\n")

    start_time = time.time()
    first_token_time = None
    full_response = ""

    print("Response:")
    print("-" * 70)

    # OpenAI streaming API
    stream = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
        stream=True  # Enable streaming
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content

            if first_token_time is None:
                first_token_time = time.time()
                time_to_first = first_token_time - start_time
                print(f"\n[⚡ First token received in {time_to_first:.2f}s]\n", flush=True)

            print(content, end="", flush=True)
            full_response += content

    end_time = time.time()
    total_duration = end_time - start_time

    print("\n" + "-" * 70)

    # Note: OpenAI streaming doesn't return usage in chunks
    # We'll estimate token count
    import tiktoken
    encoding = tiktoken.encoding_for_model("gpt-4")

    prompt_tokens = len(encoding.encode(prompt)) + 10  # +10 for message formatting
    completion_tokens = len(encoding.encode(full_response))

    print(f"\n⏱️  Time to first token: {time_to_first:.2f}s")
    print(f"⏱️  Total time: {total_duration:.2f}s")
    print(f"📊 Estimated tokens: {prompt_tokens} in, {completion_tokens} out")

    return total_duration, time_to_first, (prompt_tokens, completion_tokens)

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
    stream_duration, time_to_first, stream_tokens = streaming_request(prompt)

    # Comparison
    print("\n" + "=" * 70)
    print("📊 COMPARISON SUMMARY")
    print("=" * 70)
    print(f"\n{'Metric':<35} {'Non-Streaming':<17} {'Streaming':<17}")
    print("-" * 70)
    print(f"{'Time to first token':<35} {non_stream_duration:>15.2f}s  {time_to_first:>15.2f}s")
    print(f"{'Total response time':<35} {non_stream_duration:>15.2f}s  {stream_duration:>15.2f}s")
    print(f"{'Input tokens':<35} {non_stream_usage.prompt_tokens:>17}  {stream_tokens[0]:>17}")
    print(f"{'Output tokens':<35} {non_stream_usage.completion_tokens:>17}  {stream_tokens[1]:>17}")

    # Cost is the same!
    cost_non_stream = (non_stream_usage.prompt_tokens / 1_000_000) * 10.00 + \
                      (non_stream_usage.completion_tokens / 1_000_000) * 30.00
    cost_stream = (stream_tokens[0] / 1_000_000) * 10.00 + \
                  (stream_tokens[1] / 1_000_000) * 30.00

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

    stream = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=300,
        messages=[{"role": "user", "content": "Write a short paragraph about the ocean."}],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)
            time.sleep(0.02)  # Simulate typing effect

    print("\n\n" + "-" * 70)

    print("\n2️⃣  Interactive chat applications")
    print("   Perfect for: Chatbots, assistants")
    print("   Benefit: Natural conversation flow\n")

    # Simulate chat
    messages_list = ["Hi!", "What's Python?"]

    for msg in messages_list:
        print(f"User: {msg}")
        print("GPT-4: ", end="", flush=True)

        stream = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=100,
            messages=[{"role": "user", "content": msg}],
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="", flush=True)
                time.sleep(0.01)

        print("\n")

    print("-" * 70)

    print("\n3️⃣  Real-time processing")
    print("   Perfect for: Sentiment analysis, keyword extraction")
    print("   Benefit: Can process output as it arrives\n")

    keywords_found = []

    stream = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=200,
        messages=[{"role": "user", "content": "List 5 keywords about AI: machine learning, neural networks..."}],
        stream=True
    )

    buffer = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            buffer += content

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

def demonstrate_advanced_streaming():
    """Show advanced streaming patterns."""
    print("\n" + "=" * 70)
    print("🚀 ADVANCED STREAMING PATTERNS")
    print("=" * 70)

    print("\n1️⃣  Function Calling with Streaming")
    print("   Note: OpenAI can stream function calls too!\n")

    # Define a simple function
    functions = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state, e.g., San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    ]

    print("Asking: What's the weather in San Francisco?")
    print("Response: ", end="", flush=True)

    stream = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        max_tokens=200,
        messages=[{"role": "user", "content": "What's the weather in San Francisco?"}],
        functions=functions,
        stream=True
    )

    function_call_detected = False
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="", flush=True)

        # Check for function call
        if hasattr(chunk.choices[0].delta, 'function_call') and chunk.choices[0].delta.function_call:
            if not function_call_detected:
                print("\n[Function call detected!]", flush=True)
                function_call_detected = True

    print("\n")

    print("\n2️⃣  Streaming with Temperature Control")
    print("   Lower temperature = more consistent streaming\n")

    temperatures = [0.0, 1.0]

    for temp in temperatures:
        print(f"Temperature {temp}:")
        print("  ", end="", flush=True)

        stream = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=50,
            temperature=temp,
            messages=[{"role": "user", "content": "Say 'Hello, World!' creatively."}],
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="", flush=True)

        print("\n")

def main():
    """Run all streaming demonstrations."""
    print("\n⚡ OPENAI STREAMING API DEMONSTRATION")
    print("See the difference between streaming and non-streaming!")

    try:
        # Main comparison
        side_by_side_comparison()

        # Use cases
        demonstrate_use_cases()

        # Advanced patterns
        demonstrate_advanced_streaming()

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
        print("  • OpenAI streaming: iterate over chunks, check delta.content")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set OPENAI_API_KEY in .env")

if __name__ == "__main__":
    main()
