"""Exercise Solution: LLM Decorator Suite.

Decorators for rate limiting and cost tracking.

Run: python exercise_solution.py
Requires: .env file with ANTHROPIC_API_KEY
"""

import time
from functools import wraps
from anthropic import Anthropic, RateLimitError, APITimeoutError
from dotenv import load_dotenv

load_dotenv()


# Pricing per 1M tokens (input, output)
MODEL_COSTS = {
    "sonnet": (3.0, 15.0),
    "opus": (15.0, 75.0),
    "haiku": (0.25, 1.25),
}


def rate_limit(calls_per_minute: int = 10):
    """Rate limit decorator.

    Args:
        calls_per_minute: Maximum calls allowed per minute.

    Returns:
        Decorator function.
    """
    call_times = []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_times
            now = time.time()

            # Remove timestamps older than 1 minute
            call_times = [t for t in call_times if now - t < 60]

            # Wait if at limit
            if len(call_times) >= calls_per_minute:
                sleep_time = 60 - (now - call_times[0])
                if sleep_time > 0:
                    print(f"Rate limit reached. Waiting {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    call_times = call_times[1:]  # Remove oldest

            result = func(*args, **kwargs)
            call_times.append(time.time())

            return result
        return wrapper
    return decorator


def track_cost(model: str = "sonnet"):
    """Cost tracking decorator.

    Args:
        model: Model name for pricing.

    Returns:
        Decorator function.
    """
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0

    input_cost_per_m, output_cost_per_m = MODEL_COSTS.get(model, (3.0, 15.0))

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal total_cost, total_input_tokens, total_output_tokens

            result = func(*args, **kwargs)

            # Extract token counts from result
            # Assumes function returns (response_text, usage_dict) or has .usage
            if isinstance(result, tuple) and len(result) == 2:
                text, usage = result
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
            else:
                # Assume just text returned
                return result

            # Calculate cost
            cost = (input_tokens * input_cost_per_m +
                   output_tokens * output_cost_per_m) / 1_000_000

            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_cost += cost

            print(f"  Cost: ${cost:.6f} | Total: ${total_cost:.6f}")

            return text

        # Expose stats
        wrapper.get_stats = lambda: {
            "total_cost": total_cost,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
        }

        return wrapper
    return decorator


def retry(max_attempts: int = 3, base_delay: float = 1.0):
    """Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts.
        base_delay: Initial delay between retries.

    Returns:
        Decorator function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, APITimeoutError) as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        print(f"  Retry {attempt + 1}/{max_attempts - 1} in {delay}s...")
                        time.sleep(delay)

            raise last_error

        return wrapper
    return decorator


def timer(func):
    """Timer decorator."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"  Time: {elapsed:.2f}s")
        return result
    return wrapper


# Combined usage
@track_cost(model="sonnet")
@rate_limit(calls_per_minute=10)
@timer
@retry(max_attempts=3)
def call_claude(prompt: str) -> tuple[str, dict]:
    """Make Claude API call with all decorators.

    Returns:
        Tuple of (response_text, usage_dict).
    """
    client = Anthropic()

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    return (
        response.content[0].text,
        {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
    )


if __name__ == "__main__":
    prompts = [
        "What is a resistor?",
        "What is a capacitor?",
        "What is an inductor?",
    ]

    print("Making API calls with decorator suite:\n")

    for i, prompt in enumerate(prompts, 1):
        print(f"Call {i}: {prompt}")
        result = call_claude(prompt)
        print(f"  Response: {result[:50]}...\n")

    # Get cumulative stats
    stats = call_claude.get_stats()
    print("=" * 50)
    print(f"Session Summary:")
    print(f"  Total input tokens: {stats['total_input_tokens']}")
    print(f"  Total output tokens: {stats['total_output_tokens']}")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
