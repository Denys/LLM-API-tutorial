# Contributing to Claude API Tutorial

Thank you for your interest in contributing! This tutorial aims to be the most comprehensive resource for learning Claude API development.

## How to Contribute

### Reporting Issues

Found a bug or have a suggestion?

1. Check if the issue already exists
2. Open a new issue with:
   - Clear title and description
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Your environment (OS, Python/Node version)
   - Code samples if applicable

### Suggesting Enhancements

Have an idea for improvement?

1. Open an issue tagged with `enhancement`
2. Describe the feature and its benefits
3. Provide examples or mockups if possible
4. Explain how it fits into the tutorial structure

### Contributing Code

#### Before You Start

1. Check existing issues and PRs
2. For major changes, open an issue first to discuss
3. Fork the repository
4. Create a feature branch: `git checkout -b feature/your-feature-name`

#### Code Guidelines

**Python:**
- Follow PEP 8 style guide
- Use type hints
- Add docstrings to functions
- Format with Black: `black .`
- Lint with flake8: `flake8 .`

**JavaScript/TypeScript:**
- Use ES6+ features
- Add JSDoc comments
- Format with Prettier: `npm run format`
- Lint with ESLint: `npm run lint`

**General:**
- Keep code simple and educational
- Add comments explaining complex logic
- Include error handling
- Optimize for learning, not just performance

#### Tutorial Content Guidelines

**New Exercises:**
- Clear learning objective
- Step-by-step instructions
- Working example code
- Expected output
- Common pitfalls section
- Self-assessment questions

**Code Examples:**
- Must be tested and working
- Include cost estimates (tokens)
- Add inline comments for clarity
- Follow best practices
- Handle errors gracefully

**Documentation:**
- Use clear, simple language
- Provide context and rationale
- Include visual aids when helpful
- Link to relevant resources
- Update table of contents

#### Module Structure

Each module should contain:

```
XX-module-name/
├── README.md           # Overview and concepts
├── exercises.md        # Hands-on challenges
├── examples/          # Working code examples
│   ├── example1.py
│   └── example1.js
├── solutions/         # Exercise solutions
│   ├── solution1.py
│   └── solution1.js
└── assets/           # Images, diagrams, data
```

#### Commit Guidelines

Use conventional commits:

```
feat: Add streaming example to Module 2
fix: Correct token counting in optimization module
docs: Update RAG module README
test: Add tests for agent memory system
chore: Update dependencies
```

### Pull Request Process

1. **Update your fork:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Test your changes:**
   ```bash
   # Python
   pytest
   python -m black --check .

   # JavaScript
   npm test
   npm run lint
   ```

3. **Update documentation:**
   - Add/update README sections
   - Update TUTORIAL_PLAN.md if needed
   - Add examples to relevant exercises.md

4. **Create Pull Request:**
   - Clear title describing the change
   - Reference related issues
   - Describe what changed and why
   - Include screenshots for UI changes
   - List any breaking changes

5. **PR Review:**
   - Address reviewer feedback
   - Keep discussion focused and professional
   - Update as requested

### Adding New Modules

Proposing a new module?

1. Open an issue first with:
   - Module topic and rationale
   - Learning objectives
   - Prerequisite modules
   - Estimated time
   - Draft outline

2. Wait for approval before investing significant time

3. Follow the module structure template

### Improving Existing Content

Small improvements are always welcome:

- Fix typos or grammar
- Clarify confusing explanations
- Add helpful comments
- Improve code examples
- Update outdated information

**No issue needed for:**
- Typo fixes
- Grammar improvements
- Broken link fixes
- Comment additions

Just submit a PR!

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

**Positive behavior:**
- Be respectful and inclusive
- Welcome newcomers
- Give and receive constructive feedback gracefully
- Focus on what's best for the community
- Show empathy

**Unacceptable behavior:**
- Harassment or discrimination
- Trolling or insulting comments
- Political or off-topic discussions
- Publishing others' private information
- Unprofessional conduct

### Enforcement

Violations may result in:
1. Warning
2. Temporary ban
3. Permanent ban

Report issues to: [maintainer email]

## Development Setup

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/LLM-API-tutorial.git
cd LLM-API-tutorial

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/LLM-API-tutorial.git

# Install dependencies
pip install -r requirements.txt  # Python
npm install                       # Node.js

# Set up pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Testing Changes

```bash
# Run tests
pytest                  # Python
npm test               # Node.js

# Check formatting
black --check .        # Python
npm run format         # JavaScript

# Verify examples work
python 01-basic-api/examples/hello_claude.py
node 01-basic-api/examples/hello-claude.js
```

### Building Documentation

```bash
# Generate table of contents (if you have the tool)
markdown-toc -i README.md

# Check links
markdown-link-check **/*.md
```

## Recognition

Contributors will be:
- Listed in README acknowledgments
- Credited in relevant module sections
- Recognized in release notes

## Questions?

- Open an issue with the `question` label
- Join our community discussions
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make this tutorial better!** 🙏

Every contribution, no matter how small, makes a difference.
