"""Exercise Solution: Streaming Response Analyzer.

Stream and analyze Claude responses in real-time.

Run: python exercise_solution.py
Requires: .env file with ANTHROPIC_API_KEY
"""

import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


def extract_numbers(text: str) -> list[float]:
    """Extract all numbers from text.

    Args:
        text: Input text.

    Returns:
        List of numbers found.
    """
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(x) for x in matches]


def stream_and_analyze(prompt: str) -> dict:
    """Stream response and analyze content.

    Args:
        prompt: User message.

    Returns:
        Analysis results dictionary.
    """
    client = Anthropic()

    # Accumulators
    full_response = ""
    word_count = 0
    word_buffer = ""

    print(f"Prompt: {prompt}\n")
    print("Response: ", end="")

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            # Display in real-time
            print(text, end="", flush=True)

            # Accumulate full response
            full_response += text

            # Count words incrementally
            word_buffer += text
            words = word_buffer.split()

            if word_buffer.endswith((' ', '\n', '\t')):
                # Buffer ends with whitespace - all words complete
                word_count += len(words)
                word_buffer = ""
            elif words:
                # Last word might be incomplete
                word_count += len(words) - 1
                word_buffer = words[-1]

        # Count remaining buffer
        if word_buffer.strip():
            word_count += 1

        # Get final message for token counts
        final = stream.get_final_message()

    # Extract numbers from complete response
    numbers_found = extract_numbers(full_response)

    # Remove duplicates while preserving order
    seen = set()
    unique_numbers = []
    for num in numbers_found:
        if num not in seen:
            seen.add(num)
            unique_numbers.append(num)

    print("\n")

    return {
        "response": full_response,
        "word_count": word_count,
        "numbers_found": unique_numbers,
        "tokens_in": final.usage.input_tokens,
        "tokens_out": final.usage.output_tokens
    }


if __name__ == "__main__":
    # Test with a prompt that includes numbers
    result = stream_and_analyze(
        "List 3 common resistor values with their typical applications. "
        "Include specific resistance values in ohms."
    )

    print("Analysis Results:")
    print(f"  Word count: {result['word_count']}")
    print(f"  Numbers found: {result['numbers_found']}")
    print(f"  Tokens: {result['tokens_in']} in, {result['tokens_out']} out")

    # Cost estimate (Claude Sonnet pricing)
    cost = (result['tokens_in'] * 3 + result['tokens_out'] * 15) / 1_000_000
    print(f"  Estimated cost: ${cost:.6f}")
