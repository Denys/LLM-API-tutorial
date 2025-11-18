"""Basic environment configuration for LLM APIs.

Run: python config_basic.py
Requires: .env file with ANTHROPIC_API_KEY
"""

from dotenv import load_dotenv
import os

# Load .env file (looks in current dir, then parents)
load_dotenv()

# Required variable - fail fast if missing
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError(
        "ANTHROPIC_API_KEY not set.\n"
        "Create a .env file with: ANTHROPIC_API_KEY=sk-ant-..."
    )

# Optional with defaults
model = os.getenv("MODEL", "claude-sonnet-4-20250514")
max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
temperature = float(os.getenv("TEMPERATURE", "0.7"))

# Display configuration (safe - doesn't expose full key)
print("Configuration loaded:")
print(f"  Model: {model}")
print(f"  Max tokens: {max_tokens}")
print(f"  Temperature: {temperature}")
print(f"  API key: {api_key[:10]}...{api_key[-4:]}")
