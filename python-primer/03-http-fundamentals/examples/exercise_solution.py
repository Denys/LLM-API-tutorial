"""Exercise Solution: API Health Checker.

Checks Claude API health and returns status report.

Run: python exercise_solution.py
Requires: .env file with ANTHROPIC_API_KEY
"""

import httpx
import time
from dotenv import load_dotenv
import os


def check_api_health(timeout: float = 30.0) -> dict:
    """Check Claude API health status.

    Args:
        timeout: Request timeout in seconds.

    Returns:
        Health status report dictionary.
    """
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "healthy": False,
            "error": "missing_api_key",
            "message": "ANTHROPIC_API_KEY not set"
        }

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
        "anthropic-version": "2023-06-01"
    }

    # Minimal payload for health check
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 5,
        "messages": [{"role": "user", "content": "Hi"}]
    }

    start_time = time.time()

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        elapsed_ms = (time.time() - start_time) * 1000

        # Extract rate limit info
        rate_limit_remaining = response.headers.get(
            "x-ratelimit-remaining-requests"
        )
        if rate_limit_remaining:
            rate_limit_remaining = int(rate_limit_remaining)

        request_id = response.headers.get("request-id")

        # Handle different status codes
        if response.status_code == 200:
            return {
                "healthy": True,
                "response_time_ms": round(elapsed_ms, 2),
                "rate_limit_remaining": rate_limit_remaining,
                "model_responding": True,
                "request_id": request_id
            }

        elif response.status_code == 401:
            return {
                "healthy": False,
                "error": "auth_failed",
                "response_time_ms": round(elapsed_ms, 2),
                "request_id": request_id,
                "message": "Invalid API key"
            }

        elif response.status_code == 429:
            return {
                "healthy": False,
                "error": "rate_limited",
                "response_time_ms": round(elapsed_ms, 2),
                "rate_limit_remaining": 0,
                "request_id": request_id,
                "message": "Rate limit exceeded"
            }

        elif response.status_code >= 500:
            return {
                "healthy": False,
                "error": "server_error",
                "status_code": response.status_code,
                "response_time_ms": round(elapsed_ms, 2),
                "request_id": request_id,
                "message": "API server error"
            }

        else:
            return {
                "healthy": False,
                "error": "unexpected_status",
                "status_code": response.status_code,
                "response_time_ms": round(elapsed_ms, 2),
                "request_id": request_id,
                "message": response.text[:200]
            }

    except httpx.TimeoutException:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "healthy": False,
            "error": "timeout",
            "response_time_ms": round(elapsed_ms, 2),
            "message": f"Request timed out after {timeout}s"
        }

    except httpx.ConnectError as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "healthy": False,
            "error": "connection_failed",
            "response_time_ms": round(elapsed_ms, 2),
            "message": str(e)
        }


if __name__ == "__main__":
    import json

    print("Checking Claude API health...\n")
    result = check_api_health()
    print(json.dumps(result, indent=2))

    if result.get("healthy"):
        print("\n✓ API is healthy")
    else:
        print(f"\n✗ API check failed: {result.get('error')}")
