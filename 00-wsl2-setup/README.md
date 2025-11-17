# Module 0: WSL2 & Python Setup for LLM Development

**Duration:** 1-2 hours
**Difficulty:** Beginner-Friendly
**Platform:** Windows 11 (with WSL2)

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Install and configure WSL2 on Windows 11
- ✅ Navigate Linux file systems confidently
- ✅ Use essential Linux commands
- ✅ Set up Python for LLM development
- ✅ Install and configure CLI agents (Claude Code, etc.)
- ✅ Manage development environments efficiently
- ✅ Use pro tips and tricks for productivity

## Table of Contents

1. [Why WSL2?](#why-wsl2)
2. [Installing WSL2](#installing-wsl2)
3. [Essential Linux Commands](#essential-linux-commands)
4. [File System Navigation](#file-system-navigation)
5. [Python Setup for LLMs](#python-setup-for-llms)
6. [CLI Tools for AI Development](#cli-tools-for-ai-development)
7. [Pro Tips & Tricks](#pro-tips--tricks)
8. [Troubleshooting](#troubleshooting)

---

## Why WSL2?

### The Problem with Native Windows for AI Development

❌ **Native Windows Issues:**
- Many Python packages assume Linux
- Path differences (`\` vs `/`)
- Permissions and security models differ
- CLI tools built for Unix/Linux
- Performance overhead with virtualization
- Inconsistent behavior across environments

✅ **WSL2 Advantages:**
- Real Linux kernel running on Windows
- Near-native Linux performance
- Direct access to Windows files
- No dual-boot or VMs needed
- GPU passthrough support (for ML)
- Seamless integration with Windows apps

### What is WSL2?

WSL2 = **Windows Subsystem for Linux, Version 2**

```
┌──────────────────────────────────────────┐
│         Windows 11                       │
│  ┌────────────────────────────────────┐  │
│  │  Your Windows Apps                 │  │
│  │  (VS Code, Browser, etc.)          │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │  WSL2 (Linux Kernel)               │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │ Ubuntu/Debian                │  │  │
│  │  │ Python, Claude Code CLI      │  │  │
│  │  │ Node.js, Git, etc.           │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## Installing WSL2

### Method 1: One-Command Install (Easiest)

**Requirements:**
- Windows 11 or Windows 10 version 2004+ (Build 19041+)
- Administrator access

**Steps:**

1. **Open PowerShell as Administrator**
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Run the install command:**
   ```powershell
   wsl --install
   ```

3. **Restart your computer**

4. **First Launch:**
   - Ubuntu will auto-launch
   - Create your Linux username (lowercase recommended)
   - Create a password (you won't see it while typing - this is normal!)
   - Remember these credentials!

5. **Update packages:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

**That's it! You now have WSL2 with Ubuntu.**

---

### Method 2: Manual Install (If Method 1 Fails)

<details>
<summary>Click to expand manual installation steps</summary>

**Step 1: Enable WSL**
```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

**Step 2: Enable Virtual Machine Platform**
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**Step 3: Restart Computer**

**Step 4: Download WSL2 Kernel Update**
- Visit: https://aka.ms/wsl2kernel
- Download and install the update package

**Step 5: Set WSL2 as Default**
```powershell
wsl --set-default-version 2
```

**Step 6: Install Ubuntu**
```powershell
wsl --install -d Ubuntu
```

</details>

---

### Verify Installation

```powershell
# In PowerShell, check installed distributions
wsl --list --verbose

# Expected output:
#   NAME      STATE           VERSION
# * Ubuntu    Running         2

# Check WSL version
wsl --version

# Enter your Ubuntu environment
wsl
```

**Success Indicators:**
- ✅ Ubuntu listed with VERSION 2
- ✅ Can run `wsl` and get a Linux shell
- ✅ Username and password working

---

## Essential Linux Commands

### File System Basics

```bash
# Print Working Directory - where am I?
pwd

# List files and directories
ls                  # Simple list
ls -l              # Detailed list (permissions, size, date)
ls -la             # Include hidden files (start with .)
ls -lh             # Human-readable sizes (KB, MB, GB)

# Change directory
cd ~               # Go to home directory
cd ..              # Go up one level
cd /               # Go to root directory
cd -               # Go to previous directory
cd Documents       # Go to Documents folder

# Create directory
mkdir my_project
mkdir -p path/to/nested/dir  # Create nested directories

# Remove directory
rmdir empty_dir              # Remove empty directory
rm -r directory_name         # Remove directory and contents
rm -rf directory_name        # Force remove (careful!)

# Create empty file
touch filename.txt

# Copy files
cp source.txt destination.txt
cp -r source_dir/ dest_dir/   # Copy directory recursively

# Move/Rename files
mv oldname.txt newname.txt
mv file.txt /path/to/destination/

# Delete files
rm filename.txt
rm -i filename.txt   # Interactive (asks confirmation)
```

### Viewing File Contents

```bash
# View entire file
cat file.txt

# View with line numbers
cat -n file.txt

# View first 10 lines
head file.txt
head -n 20 file.txt  # First 20 lines

# View last 10 lines
tail file.txt
tail -f logfile.txt  # Follow (live updates)

# Page through file
less file.txt        # Press 'q' to quit, space to page down
more file.txt

# Search in file
grep "search_term" file.txt
grep -i "case_insensitive" file.txt
grep -r "search_in_dir" /path/to/directory/
```

### File Permissions

```bash
# View permissions
ls -l file.txt
# Output: -rw-r--r-- 1 user group 1234 Jan 1 12:00 file.txt
#         │││││││││
#         │││││││└└─ Other: read, read, -
#         ││││││└─── Group: read, read, -
#         │││└└└──── User:  read, write, -
#         ││└──────── Number of links
#         │└───────── File type (- = file, d = directory)

# Change permissions
chmod +x script.sh           # Make executable
chmod 755 script.sh          # rwxr-xr-x
chmod 644 file.txt           # rw-r--r--

# Change owner
sudo chown username file.txt
sudo chown username:group file.txt
```

### Process Management

```bash
# List running processes
ps aux
ps aux | grep python

# Top running processes (interactive)
top
htop  # Better version (install: sudo apt install htop)

# Kill process
kill PID
kill -9 PID      # Force kill

# Find process by name and kill
pkill python
pkill -f "program_name"
```

### Package Management (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Upgrade all packages
sudo apt upgrade
sudo apt upgrade -y  # Auto-yes to prompts

# Install package
sudo apt install package_name
sudo apt install python3 git curl wget

# Remove package
sudo apt remove package_name
sudo apt autoremove  # Remove unused dependencies

# Search for package
apt search keyword

# Show package info
apt show package_name
```

### System Information

```bash
# Current user
whoami

# System info
uname -a

# Disk space
df -h

# Directory size
du -sh directory_name
du -h --max-depth=1  # Size of subdirectories

# Memory usage
free -h

# OS version
lsb_release -a
cat /etc/os-release
```

### Pro Command Tips

```bash
# Command history
history
history | grep python  # Search history
!123                  # Run command #123 from history
!!                    # Run last command
sudo !!              # Run last command with sudo

# Aliases (add to ~/.bashrc)
alias ll='ls -lah'
alias ..='cd ..'
alias python='python3'

# Pipe commands
ls -l | grep ".txt"           # Filter output
cat file.txt | wc -l          # Count lines
history | tail -20            # Last 20 commands

# Redirect output
command > output.txt          # Overwrite file
command >> output.txt         # Append to file
command 2> errors.txt         # Redirect errors
command &> all.txt            # Redirect all output

# Run in background
command &
nohup long_running_command &  # Keep running after logout

# Multiple commands
command1 && command2          # Run cmd2 only if cmd1 succeeds
command1 || command2          # Run cmd2 only if cmd1 fails
command1 ; command2           # Run both regardless
```

---

## File System Navigation

### Understanding the Linux File System

```
/                    Root directory (NOT C:\)
├── home/            User home directories
│   └── yourusername/    Your home directory (also ~)
│       ├── projects/
│       ├── Documents/
│       └── .bashrc      Hidden config files start with .
├── mnt/             Mounted drives
│   ├── c/           Your Windows C:\ drive
│   ├── d/           Your Windows D:\ drive
│   └── ...
├── usr/             User programs
├── etc/             System configuration
├── var/             Variable data (logs, etc.)
└── tmp/             Temporary files
```

### WSL2 File System Integration

**Two File Systems:**

1. **Linux File System (Fast)** ⚡
   ```bash
   cd ~
   cd ~/projects
   # Files stored in Linux VM
   # Path: \\wsl$\Ubuntu\home\yourusername
   ```

2. **Windows File System (Slower)** 🐌
   ```bash
   cd /mnt/c/Users/YourName
   cd /mnt/c/Users/YourName/Documents
   # Files stored on Windows
   # Path: C:\Users\YourName
   ```

**Performance Rules:**
```bash
# ✅ DO: Work in Linux filesystem
cd ~/projects
git clone https://github.com/...

# ❌ DON'T: Work in Windows filesystem via /mnt/c
cd /mnt/c/Users/YourName/projects  # SLOW!
```

### Accessing Files Between Systems

**From Windows → Linux:**
```
File Explorer address bar:
\\wsl$\Ubuntu\home\yourusername

Or:
\\wsl$\Ubuntu-22.04\home\yourusername
```

**From Linux → Windows:**
```bash
# Access C:\ drive
cd /mnt/c

# Access D:\ drive
cd /mnt/d

# Access your Windows user folder
cd /mnt/c/Users/$USER
```

**Pro Tip: Create Symbolic Links**
```bash
# Link Windows Documents to Linux home
ln -s /mnt/c/Users/YourName/Documents ~/WindowsDocs

# Now access via:
cd ~/WindowsDocs
```

### Example: Organizing Your Projects

```bash
# Create a projects directory in Linux (FAST)
cd ~
mkdir -p projects/llm-tutorials
mkdir -p projects/experiments
mkdir -p projects/production

# Check your structure
tree -L 2 projects/
# projects/
# ├── llm-tutorials/
# ├── experiments/
# └── production/

# Clone repositories here
cd ~/projects/llm-tutorials
git clone https://github.com/yourusername/LLM-API-tutorial.git
```

---

## Python Setup for LLMs

### Installing Python 3.11

**Why Python 3.11?**
- Latest stable version with best performance
- Required by many modern LLM libraries
- Better error messages
- Faster than older versions

```bash
# Update package list
sudo apt update

# Install Python 3.11 and essentials
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y python3-pip
sudo apt install -y build-essential libssl-dev libffi-dev

# Install Python development headers (needed for some packages)
sudo apt install -y python3-dev

# Set Python 3.11 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Verify installation
python --version     # Should show Python 3.11.x
python3 --version
pip --version
```

### Setting Up Virtual Environments

**Why Virtual Environments?**
- Isolate project dependencies
- Avoid version conflicts
- Easy to reproduce environments
- Clean project structure

```bash
# Navigate to your project
cd ~/projects/LLM-API-tutorial

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt changes to show (venv)
# (venv) username@hostname:~/projects/LLM-API-tutorial$

# Install packages (only in this venv)
pip install anthropic python-dotenv

# Deactivate when done
deactivate
```

**Pro Tip: Auto-activate venv**
```bash
# Add to your project's directory
echo 'source venv/bin/activate' > .envrc

# Or use direnv (auto-activate on cd)
sudo apt install direnv
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
echo 'source venv/bin/activate' > .envrc
direnv allow .
```

### Installing Common LLM Packages

```bash
# Activate your venv first!
source venv/bin/activate

# Core packages
pip install anthropic              # Claude API
pip install openai                 # OpenAI API
pip install google-generativeai    # Gemini API

# LLM frameworks
pip install langchain              # LangChain
pip install llama-index            # LlamaIndex

# Vector databases
pip install chromadb               # ChromaDB
pip install pinecone-client        # Pinecone
pip install weaviate-client        # Weaviate

# Utilities
pip install python-dotenv          # Environment variables
pip install tiktoken               # Token counting
pip install rich                   # Beautiful terminal output

# Save your dependencies
pip freeze > requirements.txt

# Later, install from requirements
pip install -r requirements.txt
```

### Python Configuration

**Create ~/.pythonrc for interactive shell:**
```python
# ~/.pythonrc
import sys
import os

# Enable tab completion
try:
    import readline
    import rlcompleter
    readline.parse_and_bind("tab: complete")
except ImportError:
    pass

# Print Python version on start
print(f"Python {sys.version}")
print("Tab completion enabled")
```

**Add to ~/.bashrc:**
```bash
export PYTHONSTARTUP=~/.pythonrc
```

### Example: Test Python Setup

```python
# test_llm_setup.py
import sys
import anthropic
import dotenv
from rich import print as rprint

rprint("[green]✅ Python version:[/green]", sys.version)
rprint("[green]✅ Anthropic SDK:[/green]", anthropic.__version__)
rprint("[green]✅ python-dotenv:[/green]", dotenv.__version__)
rprint("\n[bold green]🎉 All packages installed successfully![/bold green]")
```

Run it:
```bash
python test_llm_setup.py
```

---

## CLI Tools for AI Development

### Installing Claude Code CLI

```bash
# Method 1: Using npm (recommended)
npm install -g @anthropic-ai/claude-code

# Verify installation
claude-code --version

# Initialize in your project
cd ~/projects/LLM-API-tutorial
claude-code init
```

**Configuration:**
```bash
# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Or add to ~/.bashrc
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Installing Other AI CLI Tools

**GitHub Copilot CLI:**
```bash
gh extension install github/gh-copilot
gh copilot --version
```

**Gemini CLI (unofficial):**
```bash
pip install google-generativeai
# Create a wrapper script (see examples/gemini_cli.py)
```

### Essential Development Tools

```bash
# Git (version control)
sudo apt install git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# curl (HTTP requests)
sudo apt install curl

# jq (JSON processor)
sudo apt install jq

# httpie (better curl)
sudo apt install httpie

# tmux (terminal multiplexer)
sudo apt install tmux

# fd (better find)
sudo apt install fd-find

# ripgrep (better grep)
sudo apt install ripgrep

# bat (better cat)
sudo apt install bat

# fzf (fuzzy finder)
sudo apt install fzf
```

### Using tmux for Multiple Sessions

```bash
# Start tmux
tmux

# tmux keyboard shortcuts (prefix: Ctrl+b)
Ctrl+b c          # New window
Ctrl+b n          # Next window
Ctrl+b p          # Previous window
Ctrl+b %          # Split vertically
Ctrl+b "          # Split horizontally
Ctrl+b arrow      # Navigate panes
Ctrl+b d          # Detach (keeps running)

# Reattach to session
tmux attach

# List sessions
tmux ls
```

**Use case for LLM development:**
```bash
# Window 1: Run your Python app
python app.py

# Window 2: Watch logs
tail -f logs/app.log

# Window 3: Interactive Python shell
python

# Window 4: File editing
vim script.py
```

---

## Pro Tips & Tricks

### Shell Customization

**Install Zsh and Oh-My-Zsh (Better than Bash):**
```bash
# Install Zsh
sudo apt install zsh

# Install Oh-My-Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Set as default shell
chsh -s $(which zsh)

# Restart terminal
```

**Useful Oh-My-Zsh plugins** (edit ~/.zshrc):
```bash
plugins=(
  git
  python
  pip
  docker
  colored-man-pages
  zsh-autosuggestions
  zsh-syntax-highlighting
)
```

### Bash/Zsh Aliases for LLM Dev

```bash
# Add to ~/.bashrc or ~/.zshrc

# Quick navigation
alias proj='cd ~/projects'
alias llm='cd ~/projects/LLM-API-tutorial'

# Python shortcuts
alias py='python'
alias ipy='ipython'
alias venv='source venv/bin/activate'
alias mkvenv='python -m venv venv && source venv/bin/activate'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph --all'

# API testing
alias test-api='python -m pytest tests/'
alias run-dev='python app.py --debug'

# Token counting
alias count-tokens='python -c "import tiktoken; enc = tiktoken.get_encoding(\"cl100k_base\"); import sys; print(len(enc.encode(sys.stdin.read())))"'

# Usage: echo "Hello world" | count-tokens
```

### Environment Variables Management

**Use direnv for per-project environments:**
```bash
# Install direnv
sudo apt install direnv

# Add to ~/.bashrc or ~/.zshrc
eval "$(direnv hook bash)"  # or zsh

# In your project directory
cd ~/projects/LLM-API-tutorial
cat > .envrc << 'EOF'
# Auto-activate virtual environment
source venv/bin/activate

# Load .env file
dotenv_if_exists

# Project-specific environment variables
export PYTHONPATH="$PWD/src:$PYTHONPATH"
export LOG_LEVEL=DEBUG
EOF

# Allow direnv for this directory
direnv allow

# Now entering the directory auto-activates everything!
```

### Fast File Finding

```bash
# Using fd (modern find)
fd "*.py"                    # Find all Python files
fd "test" ~/projects         # Find files/dirs named test
fd -e txt                    # Find all .txt files

# Using ripgrep (modern grep)
rg "def main" --type py      # Search in Python files
rg "TODO" -g "*.py"          # Search TODOs in Python files
rg "api_key" --hidden        # Search in hidden files too

# Using fzf (fuzzy finder)
# Ctrl+r                     # Fuzzy search command history
# Ctrl+t                     # Fuzzy find files
# Alt+c                      # Fuzzy cd into directory

# Find and edit file
vim $(fd test.py | fzf)
```

### Quick Python Snippets

**Count tokens in a file:**
```bash
# Create a utility script
cat > ~/bin/count-tokens << 'EOF'
#!/usr/bin/env python3
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
export PATH="$HOME/bin:$PATH"  # Add to ~/.bashrc

# Usage
count-tokens myfile.txt
cat myfile.txt | count-tokens
```

**Quick Claude API test:**
```bash
# Create quick-ask script
cat > ~/bin/quick-ask << 'EOF'
#!/usr/bin/env python3
import os
import sys
from anthropic import Anthropic

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

# Usage
quick-ask "What is Python?"
echo "Explain async/await" | quick-ask
```

### VS Code + WSL2 Integration

**Install VS Code Extensions:**
1. Open VS Code on Windows
2. Install "Remote - WSL" extension
3. In WSL terminal:
   ```bash
   cd ~/projects/LLM-API-tutorial
   code .
   ```

**Recommended extensions for LLM development:**
- Python (Microsoft)
- Pylance
- Python Debugger
- Jupyter
- GitLens
- Thunder Client (API testing)
- Error Lens
- Better Comments

**VS Code settings for Python** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### Performance Optimization

**Check what's using resources:**
```bash
# CPU usage
top
htop  # Better visualization

# Memory usage
free -h
ps aux --sort=-%mem | head -n 10  # Top memory users

# Disk I/O
iotop  # Requires sudo

# WSL2 memory usage (from PowerShell)
wsl --list --verbose
```

**Limit WSL2 memory** (create `C:\Users\YourName\.wslconfig`):
```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
```

---

## Troubleshooting

### Common Issues & Solutions

**Issue: "command not found" after installation**
```bash
# Reload your shell configuration
source ~/.bashrc  # or ~/.zshrc

# Check if program is installed
which python
which pip

# Check PATH
echo $PATH
```

**Issue: Permission denied**
```bash
# Wrong: Using sudo with pip
sudo pip install package  # DON'T DO THIS

# Right: Use pip in virtual environment
source venv/bin/activate
pip install package

# For system packages, use apt
sudo apt install python3-package
```

**Issue: "Cannot activate virtual environment"**
```bash
# Make sure venv was created correctly
python -m venv venv

# Use full path
source ./venv/bin/activate

# Check if venv directory exists
ls -la venv/
```

**Issue: Slow performance in /mnt/c**
```bash
# Move your project to Linux filesystem
mv /mnt/c/Users/YourName/project ~/projects/project
cd ~/projects/project

# Much faster now!
```

**Issue: Can't access localhost from Windows**
```bash
# In Windows, use hostname instead of localhost
# Get your WSL IP
ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'

# Or enable localhostForwarding (Windows 11)
# It should work automatically, but if not:
# Add to C:\Users\YourName\.wslconfig:
[wsl2]
localhostForwarding=true
```

**Issue: Git credentials not working**
```bash
# Use Git Credential Manager
git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"

# Or use SSH keys
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub  # Add to GitHub
```

**Issue: Python package build fails**
```bash
# Install build dependencies
sudo apt install -y build-essential python3-dev libssl-dev libffi-dev

# For specific packages:
# For pandas/numpy
sudo apt install -y python3-numpy python3-pandas

# For Pillow (images)
sudo apt install -y libjpeg-dev zlib1g-dev

# For psycopg2 (PostgreSQL)
sudo apt install -y libpq-dev
```

---

## Quick Reference Card

```bash
# WSL Management (PowerShell)
wsl --list --verbose          # List distributions
wsl --shutdown               # Shut down WSL
wsl --terminate Ubuntu       # Stop specific distro
wsl --export Ubuntu backup.tar    # Backup
wsl --import Ubuntu2 C:\path backup.tar  # Restore

# Essential Commands
pwd                          # Where am I?
ls -lah                      # List files (detailed)
cd ~/projects                # Change directory
mkdir -p path/to/dir         # Create directories
rm -rf directory             # Remove directory
cp -r source dest            # Copy
mv source dest               # Move/rename

# Python
python -m venv venv          # Create venv
source venv/bin/activate     # Activate venv
pip install package          # Install package
pip freeze > requirements.txt # Save dependencies
python script.py             # Run script

# File Viewing
cat file.txt                 # Show file
less file.txt                # Page through (q to quit)
head -n 20 file.txt          # First 20 lines
tail -f logfile.txt          # Follow log file
grep "search" file.txt       # Search in file

# Process Management
ps aux | grep python         # Find Python processes
kill PID                     # Stop process
pkill python                 # Kill all Python
top                          # Monitor processes

# File System
\\wsl$\Ubuntu\home\username  # Access from Windows
/mnt/c/Users/YourName        # Access Windows from Linux
```

---

## Next Steps

✅ WSL2 installed and configured
✅ Essential Linux commands mastered
✅ Python environment ready
✅ CLI tools installed
✅ Pro tips learned

**You're ready to start building with LLMs!**

→ Continue to [Module 1: Foundation - Getting Started with Claude API](../01-basic-api/README.md)

---

## Additional Resources

- [Official WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Ubuntu Documentation](https://help.ubuntu.com/)
- [Python Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)
- [Oh My Zsh Documentation](https://github.com/ohmyzsh/ohmyzsh)
- [tmux Cheat Sheet](https://tmuxcheatsheet.com/)

---

**Questions?** Open an issue or check the [FAQ](../FAQ.md)
