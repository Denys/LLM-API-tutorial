"""Exercise Solution: Async Batch Processor.

Process multiple prompts in parallel with concurrency control.

Run: python exercise_solution.py
Requires: .env file with ANTHROPIC_API_KEY
"""

import asyncio
import time
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()


async def batch_process(
    prompts: list[str],
    max_concurrent: int = 5,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 100
) -> list[dict]:
    """Process prompts in parallel with concurrency limit.

    Args:
        prompts: List of user prompts.
        max_concurrent: Maximum concurrent API calls.
        model: Model to use.
        max_tokens: Max tokens per response.

    Returns:
        List of result dictionaries with:
        - prompt: Original prompt
        - response: Response text (or None on error)
        - tokens: Dict with input/output tokens (or None)
        - error: Error message (or None on success)
    """
    client = AsyncAnthropic()
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(prompt: str) -> dict:
        """Process a single prompt with error handling."""
        async with semaphore:
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )

                return {
                    "prompt": prompt,
                    "response": response.content[0].text,
                    "tokens": {
                        "input": response.usage.input_tokens,
                        "output": response.usage.output_tokens
                    },
                    "error": None
                }

            except Exception as e:
                return {
                    "prompt": prompt,
                    "response": None,
                    "tokens": None,
                    "error": str(e)
                }

    # Create tasks and gather results
    tasks = [process_one(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)

    return results


def summarize_results(results: list[dict]) -> dict:
    """Summarize batch processing results.

    Args:
        results: List of result dictionaries.

    Returns:
        Summary with counts and token totals.
    """
    successful = [r for r in results if r["error"] is None]
    failed = [r for r in results if r["error"] is not None]

    total_input_tokens = sum(
        r["tokens"]["input"] for r in successful
    )
    total_output_tokens = sum(
        r["tokens"]["output"] for r in successful
    )

    return {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "errors": [r["error"] for r in failed] if failed else None
    }


async def main():
    """Demo the batch processor."""
    prompts = [
        "What is a resistor? (1 sentence)",
        "What is a capacitor? (1 sentence)",
        "What is an inductor? (1 sentence)",
        "What is a diode? (1 sentence)",
        "What is a transistor? (1 sentence)",
        "What is an op-amp? (1 sentence)",
        "What is a MOSFET? (1 sentence)",
        "What is a thyristor? (1 sentence)",
    ]

    print(f"Processing {len(prompts)} prompts...")
    print(f"Concurrency limit: 3\n")

    start = time.time()
    results = await batch_process(prompts, max_concurrent=3)
    elapsed = time.time() - start

    # Display results
    for result in results:
        if result["error"]:
            print(f"ERROR: {result['prompt'][:30]}...")
            print(f"  {result['error']}\n")
        else:
            component = result["prompt"].split()[3].rstrip("?")
            print(f"{component}: {result['response']}")
            print(f"  Tokens: {result['tokens']['input']} in, {result['tokens']['output']} out\n")

    # Summary
    summary = summarize_results(results)
    print("=" * 50)
    print(f"Summary:")
    print(f"  Processed: {summary['successful']}/{summary['total']}")
    print(f"  Total tokens: {summary['total_input_tokens']} in, {summary['total_output_tokens']} out")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  (Sequential estimate: ~{len(prompts) * 2}s)")


if __name__ == "__main__":
    asyncio.run(main())
