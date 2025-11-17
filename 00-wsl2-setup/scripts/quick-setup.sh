#!/bin/bash
# Quick Setup Script for WSL2 LLM Development Environment
# Usage: bash quick-setup.sh

set -e  # Exit on error

echo "🚀 WSL2 LLM Development Environment Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if running in WSL
if ! grep -qi microsoft /proc/version; then
    print_error "This script must be run in WSL2"
    exit 1
fi

print_status "Running in WSL2"

# Update system
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_status "System updated"

# Install Python 3.11
print_info "Installing Python 3.11..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# Set Python 3.11 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

print_status "Python $(python --version) installed"

# Install essential development tools
print_info "Installing development tools..."
sudo apt install -y \
    git \
    curl \
    wget \
    htop \
    tmux \
    jq \
    unzip \
    software-properties-common

print_status "Development tools installed"

# Install modern CLI tools
print_info "Installing modern CLI tools..."
sudo apt install -y ripgrep fd-find bat fzf

print_status "CLI tools installed"

# Install Node.js via nvm
print_info "Installing Node.js..."
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install --lts
    nvm use --lts
    print_status "Node.js $(node --version) installed"
else
    print_status "Node.js already installed"
fi

# Create projects directory
print_info "Creating projects directory..."
mkdir -p ~/projects/llm-tutorials
mkdir -p ~/projects/experiments
mkdir -p ~/bin

print_status "Project directories created"

# Install Python packages for LLM development
print_info "Installing Python packages for LLM development..."
pip install --upgrade pip
pip install anthropic openai python-dotenv tiktoken rich ipython

print_status "Python packages installed"

# Create useful aliases
print_info "Adding useful aliases to ~/.bashrc..."
cat >> ~/.bashrc << 'EOF'

# LLM Development Aliases
alias proj='cd ~/projects'
alias llm='cd ~/projects/llm-tutorials'
alias py='python'
alias venv='source venv/bin/activate'
alias mkvenv='python -m venv venv && source venv/bin/activate'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph --all'

# Modern CLI tools
alias cat='batcat'
alias find='fdfind'

EOF

print_status "Aliases added to ~/.bashrc"

# Create utility scripts
print_info "Creating utility scripts..."

# Token counter script
cat > ~/bin/count-tokens << 'EOF'
#!/usr/bin/env python3
"""Count tokens in text using tiktoken."""
import sys
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")
text = sys.stdin.read() if not sys.stdin.isatty() else open(sys.argv[1]).read()
tokens = enc.encode(text)

print(f"Tokens: {len(tokens)}")
print(f"Characters: {len(text)}")
print(f"Words: {len(text.split())}")
EOF

chmod +x ~/bin/count-tokens

# Quick Claude ask script
cat > ~/bin/quick-ask << 'EOF'
#!/usr/bin/env python3
"""Quick CLI for asking Claude questions."""
import os
import sys
from anthropic import Anthropic

if not os.getenv("ANTHROPIC_API_KEY"):
    print("Error: ANTHROPIC_API_KEY not set")
    sys.exit(1)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()

message = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": question}]
)

print(message.content[0].text)
EOF

chmod +x ~/bin/quick-ask

# Add ~/bin to PATH if not already there
if ! grep -q 'export PATH="$HOME/bin:$PATH"' ~/.bashrc; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
fi

print_status "Utility scripts created in ~/bin"

# Git configuration
print_info "Configuring Git..."
read -p "Enter your Git username: " git_username
read -p "Enter your Git email: " git_email

git config --global user.name "$git_username"
git config --global user.email "$git_email"
git config --global init.defaultBranch main
git config --global core.editor "nano"

print_status "Git configured"

# Create .pythonrc for enhanced Python REPL
cat > ~/.pythonrc << 'EOF'
# Python interactive shell configuration
import sys
import os

# Enable tab completion
try:
    import readline
    import rlcompleter
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass

# Colorful prompt
sys.ps1 = '\033[1;32m>>> \033[0m'
sys.ps2 = '\033[1;33m... \033[0m'

print(f"Python {sys.version.split()[0]} | Tab completion enabled")
EOF

if ! grep -q 'export PYTHONSTARTUP=' ~/.bashrc; then
    echo 'export PYTHONSTARTUP=~/.pythonrc' >> ~/.bashrc
fi

print_status "Enhanced Python REPL configured"

# Final message
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart your terminal or run: source ~/.bashrc"
echo "2. Set your ANTHROPIC_API_KEY:"
echo "   export ANTHROPIC_API_KEY='your-key-here'"
echo "3. Add it to ~/.bashrc to make it permanent"
echo "4. Clone the LLM tutorial repository:"
echo "   cd ~/projects/llm-tutorials"
echo "   git clone <repository-url>"
echo ""
echo "Useful commands installed:"
echo "  - count-tokens: Count tokens in text"
echo "  - quick-ask: Ask Claude a quick question"
echo ""
echo "Try: echo 'Hello world' | count-tokens"
echo ""
