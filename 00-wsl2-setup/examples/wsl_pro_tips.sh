#!/bin/bash
# WSL2 Pro Tips and Tricks - Interactive Demo
# Run: bash wsl_pro_tips.sh

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   WSL2 Pro Tips & Tricks Demo         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

# Tip 1: Fast navigation
echo -e "${GREEN}[Tip 1] Fast Directory Navigation${NC}"
echo "Instead of: cd /path/to/long/directory"
echo "Use CDPATH:"
cat << 'EOF'
# Add to ~/.bashrc:
export CDPATH=".:~:~/projects:~/projects/llm-tutorials"

# Now you can:
cd LLM-API-tutorial  # from anywhere!
EOF
echo ""

# Tip 2: Aliases
echo -e "${GREEN}[Tip 2] Powerful Aliases${NC}"
cat << 'EOF'
# Add to ~/.bashrc:
alias ..='cd ..'
alias ...='cd ../..'
alias ll='ls -lah'
alias ports='netstat -tuln'
alias myip='curl ifconfig.me'

# Project-specific
alias llm='cd ~/projects/LLM-API-tutorial && source venv/bin/activate'
EOF
echo ""

# Tip 3: History search
echo -e "${GREEN}[Tip 3] Better History Search${NC}"
echo "Press Ctrl+R and start typing to fuzzy search command history"
echo "Add to ~/.inputrc:"
cat << 'EOF'
"\e[A": history-search-backward
"\e[B": history-search-forward
EOF
echo "Now arrow keys search history based on what you've typed!"
echo ""

# Tip 4: Multiple commands
echo -e "${GREEN}[Tip 4] Command Chaining${NC}"
cat << 'EOF'
# Run if previous succeeds
cd project && source venv/bin/activate && python app.py

# Run regardless
cd project ; ls ; pwd

# Run if previous fails
command1 || command2

# Run in parallel
command1 & command2 & wait
EOF
echo ""

# Tip 5: Quick file operations
echo -e "${GREEN}[Tip 5] Quick File Operations${NC}"
cat << 'EOF'
# Create and edit file
vim +"{content}" filename

# Edit last modified file
vim $(ls -t | head -1)

# Find and edit
vim $(fdfind test.py)

# Batch rename
for f in *.txt; do mv "$f" "${f%.txt}.md"; done
EOF
echo ""

# Tip 6: Clipboard integration
echo -e "${GREEN}[Tip 6] Clipboard Integration${NC}"
cat << 'EOF'
# Copy to Windows clipboard
echo "Hello" | clip.exe

# Pipe command output
cat file.txt | clip.exe

# Create alias
alias pbcopy='clip.exe'
alias pbpaste='powershell.exe Get-Clipboard'
EOF
echo ""

# Tip 7: Process monitoring
echo -e "${GREEN}[Tip 7] Process Monitoring${NC}"
cat << 'EOF'
# Watch command output (updates every 2s)
watch -n 2 'ps aux | grep python'

# Monitor file changes
tail -f logfile.txt | grep ERROR

# Find process using port
lsof -i :8000
netstat -tuln | grep 8000
EOF
echo ""

# Tip 8: Quick Python snippets
echo -e "${GREEN}[Tip 8] Quick Python One-Liners${NC}"
cat << 'EOF'
# Start HTTP server
python -m http.server 8000

# Pretty print JSON
cat data.json | python -m json.tool

# Run module as script
python -m pip list
python -m pytest tests/

# Quick calculations
python -c "print(sum(range(100)))"

# Interactive shell with imports
python -i -c "from anthropic import Anthropic; client = Anthropic()"
EOF
echo ""

# Tip 9: Git shortcuts
echo -e "${GREEN}[Tip 9] Git Pro Tips${NC}"
cat << 'EOF'
# Git aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --oneline --graph --all'

# Usage:
git co main
git ci -m "message"
git visual
EOF
echo ""

# Tip 10: Environment management
echo -e "${GREEN}[Tip 10] Environment Management${NC}"
cat << 'EOF'
# Install pyenv for multiple Python versions
curl https://pyenv.run | bash

# Install specific Python version
pyenv install 3.11.0
pyenv global 3.11.0

# Project-specific Python
cd my_project
pyenv local 3.11.0  # Creates .python-version file
EOF
echo ""

# Tip 11: Quick API testing
echo -e "${GREEN}[Tip 11] Quick API Testing${NC}"
cat << 'EOF'
# Using curl
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-haiku-20241022","max_tokens":100,...}'

# Using httpie (better)
http POST https://api.anthropic.com/v1/messages \
  x-api-key:$ANTHROPIC_API_KEY \
  model=claude-3-5-haiku-20241022 \
  max_tokens:=100

# Save to file
http ... > response.json
EOF
echo ""

# Tip 12: Background jobs
echo -e "${GREEN}[Tip 12] Background Jobs${NC}"
cat << 'EOF'
# Run in background
long_running_command &

# List jobs
jobs

# Bring to foreground
fg %1

# Send to background
Ctrl+Z
bg

# Keep running after logout
nohup long_command &
disown
EOF
echo ""

# Tip 13: Quick disk space check
echo -e "${GREEN}[Tip 13] Disk Space Management${NC}"
echo "Current disk usage:"
df -h | grep -E "Filesystem|/dev/sdc"
echo ""
echo "Largest directories in current path:"
du -h --max-depth=1 2>/dev/null | sort -hr | head -10
echo ""

# Tip 14: Performance tips
echo -e "${GREEN}[Tip 14] Performance Optimization${NC}"
cat << 'EOF'
# Work in Linux filesystem (fast)
~/projects/  ✓ FAST

# Avoid Windows filesystem (slow)
/mnt/c/Users/...  ✗ SLOW

# Check file system type
df -T .

# WSL memory management (create ~/.wslconfig on Windows)
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
EOF
echo ""

# Tip 15: Dotfiles management
echo -e "${GREEN}[Tip 15] Dotfiles Management${NC}"
cat << 'EOF'
# Backup important configs
mkdir ~/dotfiles
cp ~/.bashrc ~/dotfiles/
cp ~/.vimrc ~/dotfiles/
cp ~/.gitconfig ~/dotfiles/

# Or use Git
cd ~
git init
git add .bashrc .vimrc .gitconfig
git commit -m "Initial dotfiles"
git remote add origin <your-repo>
git push

# On new machine
git clone <your-dotfiles-repo> ~/dotfiles
ln -s ~/dotfiles/.bashrc ~/.bashrc
EOF
echo ""

# Demo complete
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Demo Complete!                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}Try these tips in your daily workflow!${NC}"
echo "For more tips, check out: https://github.com/rothgar/awesome-wsl"
echo ""
