# Quick Start Guide - AI CLI Tools

## Installation

```bash
cd 06-cli-integration

# Install dependencies
pip install -r requirements.txt

# Run setup script
bash scripts/setup.sh
```

## Configuration

**1. Set API Keys in `.env`:**
```bash
# Create .env file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=your-key-here
EOF
```

**2. Get API Keys:**
- **Claude**: https://console.anthropic.com/
- **OpenAI**: https://platform.openai.com/api-keys
- **Gemini**: https://makersuite.google.com/app/apikey

## Usage Examples

### Unified AI CLI

```bash
# Direct queries
python examples/unified/ai_cli.py claude "Explain MOSFET operation"
python examples/unified/ai_cli.py openai "Design a buck converter"
python examples/unified/ai_cli.py gemini "Calculate LED resistor"

# Interactive mode
python examples/unified/ai_cli.py --interactive claude

# Compare providers
python examples/unified/ai_cli.py --compare "What is a buck converter?"
```

### Power Electronics CLI

```bash
# Calculations
python examples/unified/power_cli.py calc resistor voltage=5 current=0.1
python examples/unified/power_cli.py calc led supply_voltage=9 led_forward_voltage=3.2
python examples/unified/power_cli.py calc buck vin=12 vout=5 iout=3

# Design with AI
python examples/unified/power_cli.py design buck "12V to 5V, 3A, 100kHz"

# Component search
python examples/unified/power_cli.py component "MOSFET for 24V 10A"
```

### Individual CLIs

**OpenAI:**
```bash
python examples/codex/interactive_openai.py
python examples/codex/interactive_openai.py --model gpt-3.5-turbo
```

**Gemini:**
```bash
# Direct query
python examples/gemini/gemini_cli.py "Explain how capacitors work"

# Interactive mode
python examples/gemini/gemini_cli.py

# With image (vision)
python examples/gemini/gemini_cli.py --image circuit.png "Analyze this circuit"
```

## Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# AI CLI shortcuts
alias ask='python /path/to/06-cli-integration/examples/unified/ai_cli.py claude'
alias gpt='python /path/to/06-cli-integration/examples/unified/ai_cli.py openai'
alias gemini='python /path/to/06-cli-integration/examples/gemini/gemini_cli.py'
alias power='python /path/to/06-cli-integration/examples/unified/power_cli.py'

# Quick calculations
alias calc-resistor='power calc resistor'
alias calc-led='power calc led'
alias calc-buck='power calc buck'
```

## Troubleshooting

**"API key not found"**
- Make sure .env file is in the current directory or parent directory
- Verify API key is set correctly in .env

**"Module not found"**
- Run: `pip install -r requirements.txt`
- Make sure you're in the right directory

**"Permission denied"**
- Run: `chmod +x examples/**/*.py`

**Gemini not working**
- Install: `pip install google-generativeai pillow`
- Set GOOGLE_API_KEY in .env

## Tips

1. **Use streaming for better UX** (enabled by default in unified CLI)

2. **Interactive mode is best for conversations**
   ```bash
   python examples/unified/ai_cli.py --interactive claude
   ```

3. **Switch providers in interactive mode**
   ```
   > /switch openai
   > /switch gemini
   ```

4. **Compare providers for important queries**
   ```bash
   python examples/unified/ai_cli.py --compare "your important question"
   ```

5. **Use specific models for cost optimization**
   ```bash
   # Cheaper (GPT-3.5)
   python examples/unified/ai_cli.py openai --model gpt-3.5-turbo "query"

   # Faster (Claude Haiku)
   python examples/unified/ai_cli.py claude --model claude-3-5-haiku-20241022 "query"
   ```

## Next Steps

- Read the full README.md for detailed information
- Try the power electronics examples
- Create custom shell functions for your workflow
- Integrate CLIs into your development process

## Support

For issues or questions:
- Check the main README.md
- Review example scripts
- Open a GitHub issue
