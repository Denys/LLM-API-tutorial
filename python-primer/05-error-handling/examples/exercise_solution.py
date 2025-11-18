"""Exercise Solution: Robust API Caller.

Implements retry logic with backoff and comprehensive error handling.

Run: python exercise_solution.py
Requires: .env file with ANTHROPIC_API_KEY
"""

import time
import random
import logging
from anthropic import (
    Anthropic,
    RateLimitError,
    APITimeoutError,
    InternalServerError,
    AuthenticationError,
    BadRequestError,
    APIError
)
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Classify errors
RETRYABLE_ERRORS = (RateLimitError, APITimeoutError, InternalServerError)
NON_RETRYABLE_ERRORS = (AuthenticationError, BadRequestError)


def robust_call(
    prompt: str,
    max_retries: int = 3,
    total_timeout: float = 120.0,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> dict:
    """Make API call with comprehensive error handling.

    Args:
        prompt: User message.
        max_retries: Maximum retry attempts.
        total_timeout: Total time budget in seconds.
        base_delay: Initial retry delay.
        max_delay: Maximum retry delay.

    Returns:
        Result dictionary with:
        - success: Whether call succeeded
        - response: Response text (or None)
        - attempts: Number of attempts made
        - error: Error message (or None)
        - elapsed: Total time taken
    """
    client = Anthropic()
    start_time = time.time()
    last_error = None
    attempts = 0

    while attempts <= max_retries:
        # Check total timeout
        elapsed = time.time() - start_time
        if elapsed >= total_timeout:
            logger.warning(f"Total timeout ({total_timeout}s) exceeded")
            return {
                "success": False,
                "response": None,
                "attempts": attempts,
                "error": f"Total timeout exceeded ({elapsed:.1f}s)",
                "elapsed": elapsed
            }

        attempts += 1
        logger.info(f"Attempt {attempts}/{max_retries + 1}")

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )

            elapsed = time.time() - start_time
            logger.info(f"Success on attempt {attempts} ({elapsed:.2f}s)")

            return {
                "success": True,
                "response": response.content[0].text,
                "attempts": attempts,
                "error": None,
                "elapsed": elapsed,
                "tokens": {
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens
                }
            }

        except NON_RETRYABLE_ERRORS as e:
            # Don't retry these
            elapsed = time.time() - start_time
            error_msg = f"{type(e).__name__}: {e.message}"
            logger.error(f"Non-retryable error: {error_msg}")

            return {
                "success": False,
                "response": None,
                "attempts": attempts,
                "error": error_msg,
                "elapsed": elapsed
            }

        except RETRYABLE_ERRORS as e:
            last_error = e
            error_type = type(e).__name__

            if attempts > max_retries:
                break

            # Calculate backoff delay
            delay = min(base_delay * (2 ** (attempts - 1)), max_delay)

            # Check if we have time for another retry
            elapsed = time.time() - start_time
            if elapsed + delay >= total_timeout:
                logger.warning("Not enough time for another retry")
                break

            # Add jitter (10% of delay)
            jitter = random.uniform(0, delay * 0.1)
            total_delay = delay + jitter

            # Special handling for rate limit
            if isinstance(e, RateLimitError):
                retry_after = e.response.headers.get('retry-after')
                if retry_after:
                    total_delay = min(float(retry_after), max_delay)

            logger.warning(
                f"Retryable error ({error_type}). "
                f"Waiting {total_delay:.1f}s before retry..."
            )
            time.sleep(total_delay)

        except APIError as e:
            # Unknown API error - treat as non-retryable
            elapsed = time.time() - start_time
            error_msg = f"Unexpected API error: {e.message}"
            logger.error(error_msg)

            return {
                "success": False,
                "response": None,
                "attempts": attempts,
                "error": error_msg,
                "elapsed": elapsed
            }

    # All retries exhausted
    elapsed = time.time() - start_time
    error_msg = f"All {attempts} attempts failed. Last: {type(last_error).__name__}"
    logger.error(error_msg)

    return {
        "success": False,
        "response": None,
        "attempts": attempts,
        "error": error_msg,
        "elapsed": elapsed
    }


if __name__ == "__main__":
    print("Testing robust_call...\n")

    result = robust_call(
        "What is the speed of light? (1 sentence)",
        max_retries=3,
        total_timeout=60.0
    )

    print("\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Attempts: {result['attempts']}")
    print(f"  Elapsed: {result['elapsed']:.2f}s")

    if result['success']:
        print(f"  Response: {result['response']}")
        print(f"  Tokens: {result['tokens']}")
    else:
        print(f"  Error: {result['error']}")
