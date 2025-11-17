# Module 6: CLI Integration - Claude Code, Codex & Gemini

**Duration:** 2-3 hours
**Difficulty:** Intermediate
**Prerequisites:** Modules 1-2 completed (Modules 3-5 optional but recommended)

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Install and configure Claude Code CLI
- ✅ Use OpenAI CLI for code generation (Codex)
- ✅ Integrate Google Gemini CLI
- ✅ Compare capabilities of different AI CLIs
- ✅ Create unified CLI workflows
- ✅ Build custom CLI tools for power electronics
- ✅ Automate engineering tasks with AI CLIs
- ✅ Configure CLI environments for team use

## What are AI CLIs?

**AI Command-Line Interfaces** allow you to interact with AI models directly from your terminal. They're ideal for:

- **Developer workflows**: Integrate AI into existing toolchains
- **Automation**: Scripting and batch processing
- **Quick queries**: Fast access without opening browsers
- **Terminal-native**: Works in SSH, tmux, screen sessions
- **CI/CD integration**: Use AI in deployment pipelines

---

## CLI Comparison Overview

| Feature | Claude Code CLI | OpenAI CLI | Gemini CLI |
|---------|----------------|------------|------------|
| **Provider** | Anthropic | OpenAI | Google |
| **Installation** | npm/standalone | pip | gcloud SDK |
| **Configuration** | API key file | Environment var | gcloud auth |
| **Interactive Mode** | ✅ Yes | ⚠️ Limited | ✅ Yes |
| **Streaming** | ✅ Yes | ✅ Yes | ✅ Yes |
| **File Upload** | ✅ Yes | ❌ No | ✅ Yes |
| **Code Execution** | ✅ Yes | ❌ No | ⚠️ Limited |
| **Project Context** | ✅ Yes | ❌ No | ⚠️ Limited |
| **Cost** | Pay-per-token | Pay-per-token | Free tier + paid |
| **Best For** | Coding, analysis | Code generation | General purpose |

---

## Part 1: Claude Code CLI

### Installation

**Option 1: npm (recommended)**
```bash
npm install -g @anthropic-ai/claude-code
```

**Option 2: Standalone binary**
```bash
# macOS/Linux
curl -fsSL https://claude.ai/download/cli | sh

# Or download from releases
# https://github.com/anthropics/claude-code/releases
```

**Verify installation:**
```bash
claude --version
```

### Configuration

**Set API Key:**
```bash
# Set environment variable
export ANTHROPIC_API_KEY="your-api-key"

# Or configure via CLI
claude configure

# Or in config file
mkdir -p ~/.config/claude
echo "ANTHROPIC_API_KEY=your-api-key" > ~/.config/claude/config
```

**Configuration file:** `~/.config/claude/config`
```ini
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096
ANTHROPIC_TEMPERATURE=1.0
```

### Basic Usage

**1. Simple Query**
```bash
claude "Explain how a buck converter works"
```

**2. Interactive Mode**
```bash
claude

# Now in interactive mode
> What is the Rds(on) of IRF540N?
> Calculate LED resistor for 5V supply, 2V LED, 20mA
> exit
```

**3. File Input**
```bash
# Analyze a circuit schematic
claude --file circuit.png "What issues do you see in this circuit?"

# Code review
claude --file main.py "Review this code for bugs"
```

**4. Project Context**
```bash
# Claude Code can see your project files
cd /path/to/project
claude "Find all TODO comments in this codebase"
claude "Refactor the authentication module"
```

**5. Code Execution**
```bash
# Claude can run code with confirmation
claude "Write and run a Python script to calculate 12V to 5V buck converter components"
```

### Advanced Features

**Streaming Output:**
```bash
# Real-time streaming (default)
claude "Generate a 100-line Python script for data analysis"
```

**Custom System Prompts:**
```bash
claude --system "You are a power electronics expert" \
       "Design a 3A buck converter"
```

**Output to File:**
```bash
claude "Write a complete MOSFET selection guide" > mosfet_guide.md
```

**Pipe Input:**
```bash
cat circuit.txt | claude "Analyze this circuit and suggest improvements"
```

**Non-Interactive (Scripting):**
```bash
#!/bin/bash
# Automated circuit analysis
for circuit in circuits/*.txt; do
  claude --file "$circuit" "Calculate efficiency" >> results.txt
done
```

---

## Part 2: OpenAI CLI (Codex)

### Installation

```bash
pip install openai
```

The OpenAI Python package includes a CLI interface.

### Configuration

**Set API Key:**
```bash
export OPENAI_API_KEY="your-api-key"

# Or in shell config (.bashrc, .zshrc)
echo 'export OPENAI_API_KEY="your-api-key"' >> ~/.bashrc
```

### Basic Usage

**1. Chat Completions (GPT-4):**
```bash
# Using OpenAI CLI directly
openai api chat.completions.create \
  -m gpt-4-turbo \
  -g user "Explain MOSFET gate drive requirements"
```

**2. Code Generation:**
```bash
# Generate code with GPT-4
openai api chat.completions.create \
  -m gpt-4-turbo \
  -g system "You are an expert Python developer" \
  -g user "Write a function to calculate buck converter components"
```

**3. Improved CLI Wrapper**

The official OpenAI CLI is limited. Create a better wrapper:

**File:** `scripts/openai-chat` (see examples/codex/)
```bash
#!/bin/bash
# Better OpenAI CLI wrapper

python3 << 'EOF'
import openai
import sys

openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": " ".join(sys.argv[1:])}]
)

print(response.choices[0].message.content)
EOF
```

**Usage:**
```bash
chmod +x scripts/openai-chat
./openai-chat "Design a buck converter for 12V to 5V"
```

### Interactive OpenAI Session

**File:** `examples/codex/interactive_openai.py`

```python
#!/usr/bin/env python3
"""Interactive OpenAI CLI session."""

import os
import sys
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat(message: str, model: str = "gpt-4-turbo"):
    """Send message to OpenAI."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

def main():
    print("OpenAI CLI (type 'exit' to quit)")
    print("=" * 50)

    while True:
        try:
            prompt = input("\n> ")
            if prompt.lower() in ['exit', 'quit']:
                break

            response = chat(prompt)
            print(f"\n{response}")

        except KeyboardInterrupt:
            break

    print("\nGoodbye!")

if __name__ == "__main__":
    main()
```

---

## Part 3: Google Gemini CLI

### Installation

**Option 1: Using Google Cloud SDK**
```bash
# Install gcloud
curl https://sdk.cloud.google.com | bash

# Initialize
gcloud init

# Install Gemini support
gcloud components install alpha
```

**Option 2: Using Python SDK**
```bash
pip install google-generativeai
```

### Configuration

**Authenticate:**
```bash
# Using gcloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Or using API key
export GOOGLE_API_KEY="your-api-key"
```

### Basic Usage with gcloud

```bash
# Text generation
gcloud alpha ai models predict \
  --model=gemini-pro \
  --prompt="Explain buck converter operation"

# Multimodal (text + image)
gcloud alpha ai models predict \
  --model=gemini-pro-vision \
  --prompt="Analyze this circuit schematic" \
  --image=circuit.png
```

### Python CLI Wrapper for Gemini

**File:** `examples/gemini/gemini_cli.py`

```python
#!/usr/bin/env python3
"""Gemini CLI interface."""

import os
import sys
import google.generativeai as genai

# Configure API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def chat(message: str, model_name: str = "gemini-pro"):
    """Send message to Gemini."""
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(message)
    return response.text

def chat_with_image(message: str, image_path: str):
    """Multimodal chat with image."""
    import PIL.Image

    model = genai.GenerativeModel('gemini-pro-vision')
    img = PIL.Image.open(image_path)

    response = model.generate_content([message, img])
    return response.text

def interactive():
    """Interactive session."""
    print("Gemini CLI (type 'exit' to quit)")
    print("=" * 50)

    model = genai.GenerativeModel('gemini-pro')
    chat_session = model.start_chat(history=[])

    while True:
        try:
            prompt = input("\n> ")
            if prompt.lower() in ['exit', 'quit']:
                break

            response = chat_session.send_message(prompt)
            print(f"\n{response.text}")

        except KeyboardInterrupt:
            break

    print("\nGoodbye!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Direct query
        result = chat(" ".join(sys.argv[1:]))
        print(result)
    else:
        # Interactive mode
        interactive()
```

**Usage:**
```bash
chmod +x examples/gemini/gemini_cli.py

# Direct query
./gemini_cli.py "Calculate LED resistor for 5V, 2V LED, 20mA"

# Interactive mode
./gemini_cli.py
```

---

## Part 4: Unified CLI Wrapper

### Multi-Provider CLI

Create a unified interface for all three providers:

**File:** `examples/unified/ai_cli.py`

```python
#!/usr/bin/env python3
"""
Unified AI CLI - Works with Claude, OpenAI, and Gemini

Usage:
    ai-cli claude "your query"
    ai-cli openai "your query"
    ai-cli gemini "your query"
    ai-cli --interactive claude
"""

import os
import sys
import argparse
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai

class UnifiedAI:
    """Unified interface for multiple AI providers."""

    def __init__(self):
        # Initialize clients
        self.claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def query_claude(self, message: str) -> str:
        """Query Claude."""
        response = self.claude.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

    def query_openai(self, message: str) -> str:
        """Query OpenAI."""
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content

    def query_gemini(self, message: str) -> str:
        """Query Gemini."""
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(message)
        return response.text

    def query(self, provider: str, message: str) -> str:
        """Query specified provider."""
        if provider == "claude":
            return self.query_claude(message)
        elif provider == "openai":
            return self.query_openai(message)
        elif provider == "gemini":
            return self.query_gemini(message)
        else:
            raise ValueError(f"Unknown provider: {provider}")

# Command-line interface
def main():
    parser = argparse.ArgumentParser(description="Unified AI CLI")
    parser.add_argument("provider", choices=["claude", "openai", "gemini"])
    parser.add_argument("query", nargs="*", help="Query to send to AI")
    parser.add_argument("-i", "--interactive", action="store_true")

    args = parser.parse_args()

    ai = UnifiedAI()

    if args.interactive:
        # Interactive mode
        print(f"{args.provider.upper()} Interactive Mode")
        print("=" * 50)
        while True:
            try:
                query = input("\n> ")
                if query.lower() in ['exit', 'quit']:
                    break
                response = ai.query(args.provider, query)
                print(f"\n{response}")
            except KeyboardInterrupt:
                break
    else:
        # Single query
        if not args.query:
            print("Error: Provide a query or use --interactive")
            sys.exit(1)

        query = " ".join(args.query)
        response = ai.query(args.provider, query)
        print(response)

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
chmod +x examples/unified/ai_cli.py

# Direct queries
./ai_cli.py claude "Explain MOSFET operation"
./ai_cli.py openai "Design a buck converter"
./ai_cli.py gemini "Calculate LED resistor"

# Interactive mode
./ai_cli.py --interactive claude
```

---

## Part 5: Power Electronics CLI Assistant

### Specialized CLI for Engineers

**File:** `examples/unified/power_cli.py`

```python
#!/usr/bin/env python3
"""
Power Electronics CLI Assistant

Integrates AI with power electronics tools.

Commands:
    power calc <calculation>
    power design <circuit-type>
    power analyze <file>
    power simulate <circuit>
"""

import sys
import argparse
from typing import Dict

# Import from previous modules
sys.path.append("../../03-advanced-features/examples/power-electronics-assistant")
from tools import PowerElectronicsTools

class PowerCLI:
    """CLI for power electronics engineering."""

    def __init__(self, ai_provider: str = "claude"):
        self.ai_provider = ai_provider
        self.tools = PowerElectronicsTools()

    def calculate(self, calc_type: str, **params):
        """Run calculation."""
        if calc_type == "resistor":
            return self.tools.calculate_resistor_power(**params)
        elif calc_type == "led":
            return self.tools.calculate_led_resistor(**params)
        elif calc_type == "buck":
            return self.tools.design_buck_converter(**params)
        else:
            return {"error": f"Unknown calculation: {calc_type}"}

    def design(self, circuit_type: str, specs: Dict):
        """Design circuit with AI assistance."""
        # Use AI to help with design
        from unified_ai import UnifiedAI
        ai = UnifiedAI()

        prompt = f"""Design a {circuit_type} circuit with these specifications:
{specs}

Provide:
1. Component values
2. Calculations
3. Design considerations
"""
        return ai.query(self.ai_provider, prompt)

# See complete implementation in examples/unified/power_cli.py
```

---

## CLI Workflows & Automation

### 1. Automated Code Review

```bash
#!/bin/bash
# review_code.sh - Automated code review

for file in src/*.py; do
  echo "Reviewing $file..."
  claude --file "$file" "Review this code for bugs and improvements" \
    > "reviews/$(basename $file .py)_review.md"
done
```

### 2. Documentation Generation

```bash
#!/bin/bash
# generate_docs.sh

claude "Generate API documentation for this project" \
  --include "src/**/*.py" \
  > docs/api.md
```

### 3. Circuit Analysis Pipeline

```bash
#!/bin/bash
# analyze_circuits.sh

for schematic in schematics/*.png; do
  claude --file "$schematic" \
    "Analyze this circuit and identify any issues" \
    >> circuit_analysis.txt
done
```

### 4. Batch Component Research

```bash
#!/bin/bash
# research_components.sh

while IFS= read -r part; do
  echo "Researching $part..."
  claude "Find specifications for $part MOSFET" >> components.txt
done < part_list.txt
```

---

## CLI Configuration Management

### Team Configuration

**File:** `.ai-cli-config`
```yaml
default_provider: claude
providers:
  claude:
    model: claude-3-5-sonnet-20241022
    max_tokens: 4096
    temperature: 1.0
  openai:
    model: gpt-4-turbo
    max_tokens: 4096
  gemini:
    model: gemini-pro

system_prompts:
  power_electronics: |
    You are an expert power electronics engineer.
    Provide detailed, accurate answers with calculations.
    Always include safety considerations.

  code_review: |
    You are an experienced software architect.
    Focus on code quality, performance, and security.

aliases:
  calc: "power calc"
  design: "power design"
  review: "claude --system code_review"
```

---

## Comparison: Which CLI to Use?

### Use **Claude Code CLI** when:
- ✅ You need project-aware coding assistance
- ✅ Interactive coding sessions
- ✅ File analysis and code review
- ✅ Long-form technical writing
- ✅ Complex reasoning tasks

### Use **OpenAI CLI** when:
- ✅ Quick code generation
- ✅ Simple queries
- ✅ Integration with existing OpenAI workflows
- ✅ Cost-effective for simple tasks (GPT-3.5)

### Use **Gemini CLI** when:
- ✅ Multimodal analysis (text + images)
- ✅ Free tier for testing
- ✅ Google Cloud ecosystem
- ✅ Vision tasks (circuit image analysis)

---

## Tips & Best Practices

### Performance

1. **Use Streaming**: Get results faster
   ```bash
   claude --stream "long query..."
   ```

2. **Optimize Token Usage**: Be concise
   ```bash
   # ❌ Verbose
   claude "I would like you to please help me understand..."

   # ✅ Concise
   claude "Explain MOSFET gate drive"
   ```

3. **Cache System Prompts**: Reuse contexts
   ```bash
   export CLAUDE_SYSTEM="You are a power electronics expert"
   claude "Design buck converter"  # Uses cached system prompt
   ```

### Security

1. **Protect API Keys**: Never commit to git
   ```bash
   echo '.env' >> .gitignore
   echo '.ai-cli-config' >> .gitignore
   ```

2. **Use Environment Files**:
   ```bash
   # .env (git-ignored)
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=...
   ```

3. **Limit Permissions**: Use restricted API keys
   - Read-only keys for analysis
   - Separate keys per project/team

### Productivity

1. **Shell Aliases**:
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   alias ask='claude'
   alias code='claude --file'
   alias explain='claude "Explain: "'
   ```

2. **Custom Functions**:
   ```bash
   # Quick component lookup
   component() {
     claude "Find specifications for $1 component"
   }

   # Circuit analysis
   analyze() {
     claude --file "$1" "Analyze this circuit"
   }
   ```

3. **Integration with Editor**:
   ```vim
   " Vim integration
   vnoremap <leader>a :!claude<CR>
   ```

---

## Self-Assessment

Before completing this module, ensure you can:

- [ ] Install and configure Claude Code CLI
- [ ] Set up OpenAI CLI with custom wrappers
- [ ] Install and use Gemini CLI
- [ ] Create unified CLI interfaces
- [ ] Automate tasks with AI CLIs
- [ ] Configure CLI tools for team use
- [ ] Choose appropriate CLI for different tasks
- [ ] Integrate CLIs into development workflows

---

## Additional Resources

- [Claude Code CLI Documentation](https://docs.anthropic.com/claude/docs/cli)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Google Gemini Documentation](https://ai.google.dev/docs)
- [AI CLI Best Practices](https://github.com/awesome-ai-cli)

---

## Next Steps

Ready for multi-agent systems? Continue to:

**[Module 7: Agents & Multi-Agent Systems →](../07-agents/README.md)**

Learn about building autonomous agent systems for complex engineering tasks!

---

**Questions or issues?** Open a GitHub issue or check the examples.
