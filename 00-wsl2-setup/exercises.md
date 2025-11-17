# Module 0: WSL2 Exercises

Hands-on exercises to master WSL2, Linux commands, and Python setup for LLM development.

## Exercise 1: WSL2 Installation & Verification

**Difficulty:** Easy
**Time:** 15 minutes

**Tasks:**
1. Install WSL2 on Windows 11
2. Verify installation with `wsl --list --verbose`
3. Update Ubuntu packages
4. Create a Linux username and password

**Verification:**
```bash
# Check WSL version
wsl --version

# Check Ubuntu version
lsb_release -a

# Check kernel version
uname -r

# Should see "microsoft" in output
uname -r | grep microsoft
```

**Success Criteria:**
- [ ] WSL2 version 2 running
- [ ] Ubuntu installed and accessible
- [ ] All packages updated
- [ ] Can enter WSL with `wsl` command

---

## Exercise 2: Linux Command Mastery

**Difficulty:** Easy
**Time:** 30 minutes

**Tasks:**

1. **File Navigation:**
   ```bash
   # Create this directory structure:
   ~/projects/
   ├── llm-tutorials/
   │   ├── module1/
   │   └── module2/
   ├── experiments/
   └── utils/

   # Navigate between directories using cd, ls, pwd
   ```

2. **File Operations:**
   ```bash
   # Create 5 text files in different ways
   touch file1.txt
   echo "content" > file2.txt
   cat > file3.txt << EOF
   Multiple
   Lines
   EOF

   # Copy, move, and rename files
   # Delete specific files
   ```

3. **Search Operations:**
   ```bash
   # Create test files
   echo "Hello World" > test1.txt
   echo "Hello Python" > test2.txt
   echo "Goodbye World" > test3.txt

   # Find files containing "Hello"
   # Count lines in all txt files
   # Find files modified in last hour
   ```

**Challenge:**
Create a bash script that:
- Creates a project structure
- Generates a README.md with current date
- Makes the script executable

---

## Exercise 3: Python Environment Setup

**Difficulty:** Medium
**Time:** 30 minutes

**Tasks:**

1. **Install Python 3.11:**
   ```bash
   # Install Python 3.11
   # Set as default
   # Verify with python --version
   ```

2. **Create Virtual Environment:**
   ```bash
   mkdir ~/test-project
   cd ~/test-project

   # Create venv
   # Activate it
   # Install packages: anthropic, rich, python-dotenv
   # Create requirements.txt
   # Deactivate and reactivate
   ```

3. **Test Python Setup:**
   ```python
   # Create test_setup.py that:
   # - Prints Python version
   # - Lists installed packages
   # - Tests package imports
   # - Shows system information
   ```

**Verification Script:**
```python
#!/usr/bin/env python3
import sys
import platform

print(f"Python: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"In venv: {hasattr(sys, 'real_prefix')}")

# Try importing LLM packages
try:
    import anthropic
    print("✓ anthropic installed")
except ImportError:
    print("✗ anthropic missing")
```

---

## Exercise 4: File System Integration

**Difficulty:** Medium
**Time:** 20 minutes

**Tasks:**

1. **Windows ↔ Linux Navigation:**
   ```bash
   # From Linux, navigate to Windows Documents
   # Create a file there from WSL
   # View it in Windows File Explorer

   # From Windows, access WSL files using \\wsl$
   # Bookmark the location
   ```

2. **Performance Test:**
   ```bash
   # Test file operations in both locations

   # In Linux filesystem (fast)
   cd ~/projects
   time (for i in {1..1000}; do touch file$i.txt; done)
   rm file*.txt

   # In Windows filesystem (slow)
   cd /mnt/c/Users/YourName/temp
   time (for i in {1..1000}; do touch file$i.txt; done)
   rm file*.txt

   # Compare times!
   ```

3. **Create Symbolic Links:**
   ```bash
   # Link Windows directories to Linux home
   ln -s /mnt/c/Users/YourName/Documents ~/WindowsDocs
   ln -s /mnt/c/Users/YourName/Downloads ~/WindowsDownloads

   # Test access
   ls ~/WindowsDocs
   ```

**Pro Tip Challenge:**
Create a script that automatically creates useful symbolic links and a .wslconfig file with optimal settings.

---

## Exercise 5: CLI Tools Installation

**Difficulty:** Easy
**Time:** 25 minutes

**Tasks:**

1. **Install Essential Tools:**
   ```bash
   # Install: git, curl, wget, htop, tmux
   # Configure git with your name and email
   # Test each tool
   ```

2. **Install Modern Alternatives:**
   ```bash
   # Install: ripgrep, fd, bat, fzf
   # Create aliases:
   alias cat='batcat'
   alias find='fdfind'
   alias grep='rg'
   ```

3. **Node.js Setup:**
   ```bash
   # Install nvm
   # Install latest LTS Node.js
   # Install global packages: npm, typescript
   # Verify installation
   ```

**Verification:**
```bash
# Create verification script
cat > verify-tools.sh << 'EOF'
#!/bin/bash
tools="git curl wget htop tmux rg fdfind batcat fzf node npm"
for tool in $tools; do
    if command -v $tool &> /dev/null; then
        echo "✓ $tool"
    else
        echo "✗ $tool - missing"
    fi
done
EOF

chmod +x verify-tools.sh
./verify-tools.sh
```

---

## Exercise 6: Productivity Boosters

**Difficulty:** Medium
**Time:** 30 minutes

**Tasks:**

1. **Create Custom Aliases:**
   ```bash
   # Add to ~/.bashrc:
   # - Navigation shortcuts
   # - Git shortcuts
   # - Python shortcuts
   # - Project-specific shortcuts
   ```

2. **Set Up Oh-My-Zsh:**
   ```bash
   # Install zsh
   # Install Oh-My-Zsh
   # Configure plugins: git, python, docker
   # Choose a theme
   # Add custom aliases
   ```

3. **Create Utility Scripts:**
   Create these scripts in ~/bin:

   - `newproject` - Creates a new Python project with venv
   - `activate-venv` - Finds and activates nearest venv
   - `cleanup-pyc` - Remove all .pyc and __pycache__
   - `ports` - Show all listening ports

   Example:
   ```bash
   # ~/bin/newproject
   #!/bin/bash
   mkdir -p "$1"
   cd "$1"
   python -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   touch README.md .gitignore
   echo "venv/" >> .gitignore
   git init
   ```

4. **Configure VS Code:**
   - Install Remote-WSL extension
   - Open project from WSL: `code .`
   - Install Python extensions
   - Configure settings.json

---

## Exercise 7: LLM Development Environment

**Difficulty:** Hard
**Time:** 45 minutes

**Complete Environment Setup:**

1. **Project Structure:**
   ```bash
   ~/projects/my-llm-app/
   ├── .env
   ├── .env.example
   ├── .gitignore
   ├── requirements.txt
   ├── README.md
   ├── src/
   │   ├── __init__.py
   │   └── main.py
   ├── tests/
   │   └── test_main.py
   └── venv/
   ```

2. **Configuration:**
   - Set up .env with API keys
   - Create .gitignore with proper exclusions
   - Write requirements.txt with all dependencies
   - Configure logging

3. **Utility Functions:**
   Create `src/utils.py` with:
   - Token counter function
   - Cost calculator
   - API key validator
   - Environment checker

4. **Test Setup:**
   ```python
   # tests/test_environment.py
   import os
   import sys
   import pytest

   def test_python_version():
       assert sys.version_info >= (3, 9)

   def test_api_key():
       assert os.getenv('ANTHROPIC_API_KEY') is not None

   def test_imports():
       import anthropic
       import dotenv
       import tiktoken
   ```

5. **Run Complete Test:**
   ```bash
   cd ~/projects/my-llm-app
   source venv/bin/activate
   pytest tests/
   python src/main.py
   ```

**Bonus Challenge:**
Create a Makefile that automates:
- Environment setup
- Dependency installation
- Running tests
- Cleaning up
- Starting the app

---

## Exercise 8: Pro Tips Implementation

**Difficulty:** Medium
**Time:** 30 minutes

**Implement These Pro Tips:**

1. **Enhanced History:**
   ```bash
   # Add to ~/.bashrc
   export HISTSIZE=10000
   export HISTFILESIZE=10000
   export HISTCONTROL=ignoredups:erasedups
   shopt -s histappend
   PROMPT_COMMAND="history -a; $PROMPT_COMMAND"
   ```

2. **Quick Directory Jumping:**
   ```bash
   # Install and configure autojump or z
   sudo apt install autojump

   # After visiting directories, jump with:
   j projects
   j llm
   ```

3. **Git Enhancements:**
   ```bash
   # Beautiful git log
   git config --global alias.lg "log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"

   # Use: git lg
   ```

4. **Clipboard Integration:**
   ```bash
   # Copy file contents to Windows clipboard
   cat myfile.txt | clip.exe

   # Get from clipboard
   powershell.exe Get-Clipboard > fromclipboard.txt
   ```

---

## Challenge Projects

### Challenge 1: Development Environment Manager

Create a tool that:
- Detects and lists all Python projects
- Shows which have virtual environments
- Can activate any project's venv
- Displays dependencies
- Checks for outdated packages

### Challenge 2: WSL Configuration Wizard

Create an interactive script that:
- Checks current WSL configuration
- Asks user preferences
- Generates optimal .wslconfig
- Sets up recommended aliases
- Installs chosen tools
- Creates project structure

### Challenge 3: API Key Manager

Build a secure tool that:
- Stores multiple API keys encrypted
- Loads appropriate keys per project
- Validates keys before use
- Rotates keys on schedule
- Logs key usage

---

## Self-Assessment Checklist

Before moving to Module 1, you should be able to:

**WSL2 Basics:**
- [ ] Install and configure WSL2
- [ ] Switch between PowerShell and WSL
- [ ] Access files between Windows and Linux
- [ ] Understand performance implications

**Linux Commands:**
- [ ] Navigate file system confidently
- [ ] Create, move, copy, delete files/folders
- [ ] Use grep, find, sed for text processing
- [ ] Manage processes and permissions
- [ ] Install packages with apt

**Python Setup:**
- [ ] Install Python 3.11+
- [ ] Create and activate virtual environments
- [ ] Install packages with pip
- [ ] Use requirements.txt
- [ ] Run Python scripts

**Development Tools:**
- [ ] Use git for version control
- [ ] Edit files with vim/nano/VS Code
- [ ] Use tmux for multiple terminals
- [ ] Install Node.js packages
- [ ] Test APIs with curl/httpie

**Pro Skills:**
- [ ] Create and use aliases
- [ ] Write simple bash scripts
- [ ] Use symbolic links
- [ ] Configure .bashrc/.zshrc
- [ ] Integrate VS Code with WSL

---

## Solutions

Solutions for exercises are in `solutions/` directory. Try completing them yourself first!

**Files:**
- `solution_01_verification.sh`
- `solution_02_commands.sh`
- `solution_03_python_setup.sh`
- `solution_05_tools_install.sh`
- `solution_06_productivity.sh`
- `solution_07_llm_project/`

---

## Need Help?

- Review the [Module 0 README](README.md)
- Check [WSL2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- See [examples/](examples/) directory for reference
- Open a GitHub issue

---

**Ready?** Continue to [Module 1: Claude API Foundation](../01-basic-api/README.md)
