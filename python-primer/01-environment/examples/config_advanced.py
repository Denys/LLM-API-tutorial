"""Production-ready configuration pattern using dataclasses.

Run: python config_advanced.py
Requires: .env file with ANTHROPIC_API_KEY
"""

from dotenv import load_dotenv
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM API client."""

    api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: int = 30
    base_url: Optional[str] = None

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "LLMConfig":
        """Load configuration from environment variables.

        Args:
            env_file: Path to .env file. None for default lookup.

        Returns:
            Configured LLMConfig instance.

        Raises:
            ValueError: If required variables are missing.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in .env file or environment."
            )

        return cls(
            api_key=api_key,
            model=os.getenv("MODEL", cls.model),
            max_tokens=int(os.getenv("MAX_TOKENS", str(cls.max_tokens))),
            temperature=float(os.getenv("TEMPERATURE", str(cls.temperature))),
            timeout=int(os.getenv("TIMEOUT", str(cls.timeout))),
            base_url=os.getenv("BASE_URL"),
        )

    def __repr__(self) -> str:
        """Safe repr that doesn't expose full API key."""
        return (
            f"LLMConfig(model={self.model!r}, "
            f"max_tokens={self.max_tokens}, "
            f"temperature={self.temperature}, "
            f"api_key='{self.api_key[:8]}...')"
        )

    def to_client_kwargs(self) -> dict:
        """Convert to kwargs for Anthropic client.

        Returns:
            Dictionary suitable for Anthropic() constructor.
        """
        kwargs = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        if self.timeout:
            kwargs["timeout"] = self.timeout
        return kwargs


if __name__ == "__main__":
    # Load and display configuration
    config = LLMConfig.from_env()
    print(f"Loaded: {config}")
    print(f"\nClient kwargs: { {k: v if k != 'api_key' else '***' for k, v in config.to_client_kwargs().items()} }")

    # Example usage with Anthropic client:
    # from anthropic import Anthropic
    # client = Anthropic(**config.to_client_kwargs())
    # response = client.messages.create(
    #     model=config.model,
    #     max_tokens=config.max_tokens,
    #     messages=[{"role": "user", "content": "Hello!"}]
    # )
