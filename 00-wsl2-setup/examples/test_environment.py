#!/usr/bin/env python3
"""
Test script to verify your WSL2 environment is properly configured.
Run this after completing Module 0 setup.
"""

import sys
import os
import platform

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_item(name, condition, details=""):
    """Check and print status of an item."""
    status = f"{GREEN}✓ PASS{RESET}" if condition else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {name}")
    if details:
        print(f"       {details}")
    return condition

def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}WSL2 Environment Test{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    all_passed = True

    # Check Python version
    py_version = sys.version_info
    version_ok = py_version.major == 3 and py_version.minor >= 9
    all_passed &= check_item(
        "Python Version",
        version_ok,
        f"Found: Python {py_version.major}.{py_version.minor}.{py_version.micro}"
    )

    # Check if running in WSL
    is_wsl = 'microsoft' in platform.uname().release.lower()
    all_passed &= check_item(
        "Running in WSL",
        is_wsl,
        f"System: {platform.system()} {platform.release()}"
    )

    # Check essential packages
    packages = {
        'anthropic': 'Anthropic SDK',
        'dotenv': 'python-dotenv',
        'tiktoken': 'tiktoken',
    }

    print(f"\n{YELLOW}Checking Python Packages:{RESET}")
    for package, name in packages.items():
        try:
            __import__(package)
            all_passed &= check_item(name, True)
        except ImportError:
            all_passed &= check_item(name, False, f"Install with: pip install {package}")

    # Check environment variables
    print(f"\n{YELLOW}Checking Environment Variables:{RESET}")
    api_key = os.getenv('ANTHROPIC_API_KEY')
    all_passed &= check_item(
        "ANTHROPIC_API_KEY",
        api_key is not None and len(api_key) > 0,
        "Set with: export ANTHROPIC_API_KEY='your-key'"
    )

    # Check virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    check_item(
        "Virtual Environment",
        in_venv,
        "Active" if in_venv else "Not active (optional but recommended)"
    )

    # Check common CLI tools
    print(f"\n{YELLOW}Checking CLI Tools:{RESET}")
    tools = ['git', 'curl', 'jq', 'rg', 'fdfind']
    for tool in tools:
        available = os.system(f'which {tool} > /dev/null 2>&1') == 0
        check_item(f"{tool}", available, f"Install with: sudo apt install {tool}")

    # Test Anthropic SDK
    if api_key:
        print(f"\n{YELLOW}Testing Anthropic API Connection:{RESET}")
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            # Make a minimal API call
            message = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=20,
                messages=[{"role": "user", "content": "Say 'OK' and nothing else"}]
            )

            response_text = message.content[0].text
            api_working = 'ok' in response_text.lower()

            all_passed &= check_item(
                "API Connection",
                api_working,
                f"Response: {response_text} | Tokens: {message.usage.input_tokens + message.usage.output_tokens}"
            )
        except Exception as e:
            all_passed &= check_item("API Connection", False, f"Error: {str(e)}")

    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_passed:
        print(f"{GREEN}✓ All checks passed! Your environment is ready.{RESET}")
    else:
        print(f"{YELLOW}⚠ Some checks failed. Review the output above.{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Recommendations
    print(f"{YELLOW}Recommendations:{RESET}")
    print("1. Always work in ~/projects for best performance")
    print("2. Use virtual environments for each project")
    print("3. Set ANTHROPIC_API_KEY in ~/.bashrc for persistence")
    print("4. Install VS Code with Remote-WSL extension")
    print("\nNext: Start with Module 1 - Claude API Basics")
    print()

if __name__ == "__main__":
    main()
