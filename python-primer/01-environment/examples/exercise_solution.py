"""Exercise Solution: LLM Configuration System.

This solution demonstrates:
1. Loading required and optional config from environment
2. Type conversion with validation
3. Safe display of sensitive values

Run: python exercise_solution.py
Requires: .env file (copy from .env.example)
"""

from dotenv import load_dotenv
import os
from dataclasses import dataclass


def mask_key(key: str, prefix_len: int = 8, suffix_len: int = 4) -> str:
    """Mask sensitive key for safe display.

    Args:
        key: The sensitive string to mask.
        prefix_len: Characters to show at start.
        suffix_len: Characters to show at end.

    Returns:
        Masked string like "sk-ant-a...xyz9"
    """
    if len(key) > prefix_len + suffix_len:
        return f"{key[:prefix_len]}...{key[-suffix_len:]}"
    return "***"


@dataclass
class AppConfig:
    """Application configuration with validation."""

    api_key: str
    model: str
    max_tokens: int
    temperature: float
    rate_limit: int  # requests per minute

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Load and validate configuration from environment.

        Returns:
            Validated AppConfig instance.

        Raises:
            ValueError: If required vars missing or validation fails.
        """
        load_dotenv()

        # Required: API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required.\n"
                "Copy .env.example to .env and add your key."
            )

        # Optional with defaults
        model = os.getenv("MODEL", "claude-sonnet-4-20250514")

        # Parse and validate max_tokens
        try:
            max_tokens = int(os.getenv("MAX_TOKENS", "2048"))
        except ValueError:
            raise ValueError(
                f"MAX_TOKENS must be integer, got: {os.getenv('MAX_TOKENS')}"
            )

        # Parse and validate temperature
        try:
            temperature = float(os.getenv("TEMPERATURE", "0.5"))
        except ValueError:
            raise ValueError(
                f"TEMPERATURE must be float, got: {os.getenv('TEMPERATURE')}"
            )

        if not 0 <= temperature <= 1:
            raise ValueError(
                f"TEMPERATURE must be between 0 and 1, got: {temperature}"
            )

        # Parse rate limit (supports "10" or "10/min" format)
        rate_str = os.getenv("RATE_LIMIT", "10")
        try:
            rate_limit = int(rate_str.split("/")[0])
        except ValueError:
            raise ValueError(
                f"RATE_LIMIT must be integer or 'N/min', got: {rate_str}"
            )

        return cls(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            rate_limit=rate_limit,
        )

    def print_summary(self) -> None:
        """Print configuration summary with masked API key."""
        print("=" * 50)
        print("LLM Application Configuration")
        print("=" * 50)
        print(f"  API Key:     {mask_key(self.api_key)}")
        print(f"  Model:       {self.model}")
        print(f"  Max Tokens:  {self.max_tokens}")
        print(f"  Temperature: {self.temperature}")
        print(f"  Rate Limit:  {self.rate_limit} req/min")
        print("=" * 50)


# .env.example content (create this file):
ENV_EXAMPLE = """# LLM Application Configuration
# Copy this file to .env and fill in your values

# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (defaults shown)
MODEL=claude-sonnet-4-20250514
MAX_TOKENS=2048
TEMPERATURE=0.5
RATE_LIMIT=10
"""


if __name__ == "__main__":
    # Create .env.example if it doesn't exist
    if not os.path.exists(".env.example"):
        with open(".env.example", "w") as f:
            f.write(ENV_EXAMPLE)
        print("Created .env.example template")

    # Load and display configuration
    try:
        config = AppConfig.from_env()
        config.print_summary()
        print("\nConfiguration loaded successfully!")
    except ValueError as e:
        print(f"Configuration error: {e}")
        exit(1)
