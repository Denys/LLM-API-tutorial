# Track A, Section 3: Packaging & Distribution

**Duration:** 45-60 minutes | **Level:** Intermediate

## Why This Matters for LLM APIs

Package your LLM tools so they can be:
- **Installed** with `pip install your-package`
- **Shared** via PyPI or private registry
- **Versioned** properly for production
- **CLI-enabled** with entry points

## Concepts

### Modern Python Packaging

```
my-llm-client/
├── pyproject.toml        # Project config (replaces setup.py)
├── src/
│   └── my_llm_client/
│       ├── __init__.py
│       ├── client.py
│       └── cli.py
├── tests/
│   └── test_client.py
└── README.md
```

### pyproject.toml Structure

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-llm-client"
version = "0.1.0"
description = "My LLM client library"
dependencies = [
    "anthropic>=0.34.0",
]

[project.scripts]
my-llm = "my_llm_client.cli:main"
```

## Examples

### Complete Package Structure

```python
# src/my_llm_client/__init__.py
"""My LLM Client - A simple interface for Claude."""

from .client import LLMClient
from .config import Config

__version__ = "0.1.0"
__all__ = ["LLMClient", "Config"]
```

```python
# src/my_llm_client/client.py
"""Main client implementation."""

from anthropic import Anthropic
from .config import Config


class LLMClient:
    """Simple LLM client."""

    def __init__(self, config: Config = None):
        self.config = config or Config.from_env()
        self._client = Anthropic(api_key=self.config.api_key)

    def chat(self, prompt: str) -> str:
        """Send a message and get response."""
        response = self._client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
```

```python
# src/my_llm_client/cli.py
"""Command-line interface."""

import argparse
from .client import LLMClient


def main():
    parser = argparse.ArgumentParser(description="Chat with Claude")
    parser.add_argument("prompt", help="Message to send")
    parser.add_argument("--model", default="claude-sonnet-4-20250514")
    args = parser.parse_args()

    client = LLMClient()
    response = client.chat(args.prompt)
    print(response)


if __name__ == "__main__":
    main()
```

### Complete pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-llm-client"
version = "0.1.0"
description = "A simple, production-ready Claude API client"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "anthropic>=0.34.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]

[project.scripts]
my-llm = "my_llm_client.cli:main"

[project.urls]
Homepage = "https://github.com/user/my-llm-client"
Documentation = "https://github.com/user/my-llm-client#readme"
Repository = "https://github.com/user/my-llm-client"

[tool.hatch.build.targets.wheel]
packages = ["src/my_llm_client"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.black]
line-length = 88

[tool.mypy]
python_version = "3.9"
strict = true
```

---

## Exercises

### Simple: Create Basic Package

**Task:** Create a minimal package structure:
1. Create directory structure with `src/` layout
2. Write a simple `pyproject.toml`
3. Install locally with `pip install -e .`

<details>
<summary>Solution</summary>

```bash
mkdir -p my-package/src/my_package
cd my-package

# Create __init__.py
echo 'VERSION = "0.1.0"' > src/my_package/__init__.py

# Create pyproject.toml
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
dependencies = []

[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]
EOF

# Install in editable mode
pip install -e .

# Test
python -c "from my_package import VERSION; print(VERSION)"
```
</details>

---

### Intermediate: Add CLI Entry Point

**Task:** Add a command-line interface:
1. Create a `cli.py` with argument parsing
2. Configure entry point in `pyproject.toml`
3. Install and test the command

<details>
<summary>Solution</summary>

```python
# src/my_package/cli.py
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Name to greet")
    parser.add_argument("--shout", action="store_true")
    args = parser.parse_args()

    message = f"Hello, {args.name}!"
    if args.shout:
        message = message.upper()
    print(message)

if __name__ == "__main__":
    main()
```

```toml
# pyproject.toml
[project.scripts]
greet = "my_package.cli:main"
```

```bash
pip install -e .
greet World
greet World --shout
```
</details>

---

### Advanced: Full Distribution Package

**Task:** Create a complete, publishable package:
1. Full `pyproject.toml` with metadata
2. Optional dependencies for dev/test
3. Type hints and mypy configuration
4. Build and verify the package

<details>
<summary>Solution</summary>

```bash
# Build the package
pip install build
python -m build

# Check the built package
pip install twine
twine check dist/*

# Install from built wheel
pip install dist/*.whl

# Publish to TestPyPI (optional)
twine upload --repository testpypi dist/*
```

See full `pyproject.toml` in Examples section above.
</details>

---

## Pro Tips

### 1. Use `src/` Layout

Prevents accidental imports from local directory instead of installed package.

### 2. Dynamic Versioning

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
path = "src/my_package/__init__.py"
```

### 3. Entry Points for Plugins

```toml
[project.entry-points."llm_providers"]
claude = "my_package.providers:ClaudeProvider"
```

### 4. Development Installation

```bash
pip install -e ".[dev]"  # Install with dev dependencies
```

### 5. Version Constraints

```toml
dependencies = [
    "anthropic>=0.34.0,<1.0.0",  # Min and max
    "pydantic~=2.0",             # Compatible release
]
```

---

## Building & Publishing

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

---

## Track A Complete!

You've learned:
- OOP patterns for extensible LLM clients
- Testing with mocks and fixtures
- Packaging for distribution

Continue to [Track B: Data Science](../../track-b-data-science/) or [Track C: Web Integration](../../track-c-web-integration/).
