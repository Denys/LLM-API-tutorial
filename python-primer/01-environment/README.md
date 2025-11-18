# Section 1: Environment & Configuration

**Duration:** 15 minutes | **Difficulty:** Beginner

## Why This Matters for LLM APIs

Every LLM API requires authentication. Hardcoding API keys is a security disaster and makes switching between dev/prod environments painful. This section covers patterns you'll use in every module.

## Concepts

### Environment Variables

Environment variables are key-value pairs available to your process:

```bash
# Set in terminal (temporary)
export ANTHROPIC_API_KEY="sk-ant-..."

# Or in .env file (persistent, gitignored)
ANTHROPIC_API_KEY=sk-ant-...
```

### The python-dotenv Pattern

```python
from dotenv import load_dotenv
import os

# Load .env file into environment
load_dotenv()

# Access variables (with optional default)
api_key = os.getenv("ANTHROPIC_API_KEY")
max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
```

### Why .env Files?

1. **Security:** Keep secrets out of code (gitignore .env)
2. **Flexibility:** Different values for dev/staging/prod
3. **Collaboration:** Each developer has their own keys
4. **12-Factor App:** Industry standard for config

## Examples

### Basic Usage

```python
# examples/config_basic.py
"""Basic environment configuration for LLM APIs."""

from dotenv import load_dotenv
import os

# Load .env file (looks in current dir, then parents)
load_dotenv()

# Required variable - fail fast if missing
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set. Create a .env file.")

# Optional with default
model = os.getenv("MODEL", "claude-sonnet-4-20250514")
max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
temperature = float(os.getenv("TEMPERATURE", "0.7"))

print(f"Config loaded:")
print(f"  Model: {model}")
print(f"  Max tokens: {max_tokens}")
print(f"  Temperature: {temperature}")
print(f"  API key: {api_key[:10]}...{api_key[-4:]}")  # Partial reveal for debugging
```

### Advanced: Config Class

```python
# examples/config_advanced.py
"""Production-ready configuration pattern."""

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
            max_tokens=int(os.getenv("MAX_TOKENS", cls.max_tokens)),
            temperature=float(os.getenv("TEMPERATURE", cls.temperature)),
            timeout=int(os.getenv("TIMEOUT", cls.timeout)),
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


# Usage
if __name__ == "__main__":
    config = LLMConfig.from_env()
    print(config)

    # Use with Anthropic client
    # from anthropic import Anthropic
    # client = Anthropic(api_key=config.api_key)
```

### Multiple Environments

```python
# examples/multi_env.py
"""Handle multiple environments (dev/staging/prod)."""

from dotenv import load_dotenv
import os

def load_environment(env_name: str = None) -> dict:
    """Load environment-specific configuration.

    Args:
        env_name: Environment name (dev/staging/prod).
                  Auto-detected from ENV variable if not provided.

    Returns:
        Configuration dictionary.
    """
    # Determine environment
    env = env_name or os.getenv("ENV", "dev")

    # Load base .env first, then environment-specific
    load_dotenv(".env")  # Common settings
    load_dotenv(f".env.{env}", override=True)  # Environment overrides

    return {
        "env": env,
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "model": os.getenv("MODEL"),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }


# File structure:
# .env          - ANTHROPIC_API_KEY=sk-ant-dev-...
# .env.prod     - ANTHROPIC_API_KEY=sk-ant-prod-...
#                 MODEL=claude-sonnet-4-20250514
# .env.staging  - ANTHROPIC_API_KEY=sk-ant-staging-...
```

## Exercise

**Task:** Create a configuration system for an LLM application that:

1. Loads API key from environment (required)
2. Supports these optional settings with defaults:
   - `MODEL` (default: "claude-sonnet-4-20250514")
   - `MAX_TOKENS` (default: 2048)
   - `TEMPERATURE` (default: 0.5)
   - `RATE_LIMIT` (default: 10 requests/minute)
3. Validates that temperature is between 0 and 1
4. Prints a configuration summary (without exposing full API key)

**Create these files:**
- `.env.example` - Template showing required variables
- `config.py` - Your configuration module

**Test with:**
```bash
# Create .env from example
cp .env.example .env
# Edit .env with your values
python config.py
```

### Hints

<details>
<summary>Hint 1: Structure</summary>

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Get values
api_key = os.getenv("ANTHROPIC_API_KEY")
# ... more variables

# Validate
if not api_key:
    raise ValueError("...")

temperature = float(os.getenv("TEMPERATURE", "0.5"))
if not 0 <= temperature <= 1:
    raise ValueError("...")
```
</details>

<details>
<summary>Hint 2: Rate limit parsing</summary>

```python
# RATE_LIMIT might be "10" or "10/min"
rate_str = os.getenv("RATE_LIMIT", "10")
rate_limit = int(rate_str.split("/")[0])
```
</details>

<details>
<summary>Hint 3: Safe key display</summary>

```python
def mask_key(key: str) -> str:
    """Show first 8 and last 4 characters."""
    if len(key) > 12:
        return f"{key[:8]}...{key[-4:]}"
    return "***"
```
</details>

### Solution

See [examples/exercise_solution.py](./examples/exercise_solution.py)

## Pro Tips

### 1. Fail Fast on Missing Required Config

```python
# Bad - silent failure, hard to debug
api_key = os.getenv("API_KEY", "")

# Good - immediate, clear error
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable is required")
```

### 2. Use Type Conversion with Validation

```python
# Bad - crashes with unhelpful error if invalid
max_tokens = int(os.getenv("MAX_TOKENS", "1024"))

# Good - clear error message
try:
    max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
except ValueError:
    raise ValueError(f"MAX_TOKENS must be integer, got: {os.getenv('MAX_TOKENS')}")
```

### 3. Never Log Full API Keys

```python
# Terrible - key in logs/error reports
print(f"Using key: {api_key}")
logger.info(f"Config: {config}")

# Good - partial reveal for debugging
print(f"Using key: {api_key[:8]}...")
logger.info(f"Config: {config.safe_repr()}")
```

### 4. .gitignore Pattern

```gitignore
# .gitignore
.env
.env.*
!.env.example
```

### 5. Pydantic Settings (Production Pattern)

For production apps, consider `pydantic-settings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    anthropic_api_key: str
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 1024

    class Config:
        env_file = ".env"

settings = Settings()  # Auto-loads from env
```

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| Committing .env | API key exposed | Add to .gitignore |
| No .env.example | Team doesn't know what to set | Create template |
| Hardcoded defaults for secrets | Accidental prod usage | Require explicit set |
| Not loading dotenv | Variables are None | Call `load_dotenv()` first |

## LLM API Connection

This pattern appears in every module:

```python
# Module 1: Basic API
from dotenv import load_dotenv
import os
from anthropic import Anthropic

load_dotenv()
client = Anthropic()  # Auto-reads ANTHROPIC_API_KEY

# Module 4: RAG
voyage_key = os.getenv("VOYAGE_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

# Module 7: Agents (multiple providers)
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
```

## Next Section

[Section 2: JSON & Data Handling →](../02-json-handling/)
