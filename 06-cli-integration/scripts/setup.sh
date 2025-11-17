#!/bin/bash
#
# Setup script for AI CLI tools
#
# Usage: bash setup.sh
#

set -e

echo "=================================="
echo "  AI CLI Tools Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Install Python dependencies
echo ""
echo "Installing Python packages..."
pip3 install -r requirements.txt

# Create config directory
echo ""
echo "Creating configuration directory..."
mkdir -p ~/.config/ai-cli
cp config/ai-cli.conf ~/.config/ai-cli.conf

# Setup API keys
echo ""
echo "=================================="
echo "  API Key Configuration"
echo "=================================="
echo ""
echo "You need to set up API keys for the providers you want to use."
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# AI Provider API Keys
# Uncomment and fill in the keys you need

# Anthropic Claude
#ANTHROPIC_API_KEY=sk-ant-your-key-here

# OpenAI
#OPENAI_API_KEY=sk-your-key-here

# Google Gemini
#GOOGLE_API_KEY=your-key-here
EOF
    echo "✅ Created .env file"
    echo "   Please edit .env and add your API keys"
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x examples/codex/interactive_openai.py
chmod +x examples/gemini/gemini_cli.py
chmod +x examples/unified/ai_cli.py
chmod +x examples/unified/power_cli.py

# Create symlinks (optional)
echo ""
read -p "Create symlinks in ~/bin for easy access? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p ~/bin

    ln -sf "$(pwd)/examples/unified/ai_cli.py" ~/bin/ai-cli
    ln -sf "$(pwd)/examples/unified/power_cli.py" ~/bin/power-cli
    ln -sf "$(pwd)/examples/codex/interactive_openai.py" ~/bin/openai-cli
    ln -sf "$(pwd)/examples/gemini/gemini_cli.py" ~/bin/gemini-cli

    echo "✅ Created symlinks in ~/bin"
    echo "   Make sure ~/bin is in your PATH"
    echo "   Add to ~/.bashrc or ~/.zshrc:"
    echo '   export PATH="$HOME/bin:$PATH"'
fi

echo ""
echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Test the CLI tools:"
echo "   python examples/unified/ai_cli.py --help"
echo "   python examples/unified/power_cli.py --help"
echo ""
echo "Quick test:"
echo '   python examples/unified/ai_cli.py claude "Hello!"'
echo ""
