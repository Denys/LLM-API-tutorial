# Setup Guide

This guide will help you set up your development environment for the Claude API tutorial.

## Step 1: Get Your Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. **Save it securely** - you won't be able to see it again!

### Free Credits

New accounts receive free credits to get started. Check your console for current balance.

### Cost Estimation

For this entire tutorial:
- **Estimated cost:** $2-5 if you run every exercise
- Most exercises use Claude Haiku (lowest cost tier)
- Token optimization is taught throughout

## Step 2: Choose Your Language

This tutorial provides examples in both Python and JavaScript/TypeScript. Choose one or learn both!

### Option A: Python Setup

**Requirements:**
- Python 3.9 or higher

**Installation:**

```bash
# Check Python version
python --version  # Should be 3.9+

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Create requirements.txt:**

```bash
cat > requirements.txt << EOF
anthropic>=0.34.0
python-dotenv>=1.0.0
httpx>=0.25.0
pydantic>=2.0.0
tiktoken>=0.5.0
chromadb>=0.4.0
numpy>=1.24.0
fastapi>=0.104.0
uvicorn>=0.24.0
pytest>=7.4.0
rich>=13.0.0
EOF

# Install
pip install -r requirements.txt
```

### Option B: Node.js Setup

**Requirements:**
- Node.js 18 or higher

**Installation:**

```bash
# Check Node version
node --version  # Should be 18+

# Initialize project (if needed)
npm init -y

# Install dependencies
npm install @anthropic-ai/sdk dotenv axios zod
npm install -D typescript @types/node tsx
```

**Create package.json:**

```bash
cat > package.json << EOF
{
  "name": "llm-api-tutorial",
  "version": "1.0.0",
  "description": "Claude API Tutorial: From Zero to Hero",
  "type": "module",
  "scripts": {
    "dev": "tsx watch",
    "build": "tsc",
    "test": "node --test"
  },
  "dependencies": {
    "@anthropic-ai/sdk": "^0.27.0",
    "dotenv": "^16.3.1",
    "axios": "^1.6.0",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "typescript": "^5.3.0",
    "tsx": "^4.7.0"
  }
}
EOF

npm install
```

## Step 3: Configure Environment Variables

**Create .env file:**

```bash
# Copy the example file
cp .env.example .env

# Edit with your API key
# On macOS/Linux:
nano .env
# On Windows:
notepad .env
```

**Add your API key to .env:**

```bash
# Anthropic API
ANTHROPIC_API_KEY=your_api_key_here

# Optional: Model preferences
DEFAULT_MODEL=claude-3-5-sonnet-20241022
HAIKU_MODEL=claude-3-5-haiku-20241022

# Optional: Token limits
MAX_TOKENS=4096

# Optional: For RAG modules (add later)
# OPENAI_API_KEY=your_openai_key_for_embeddings
# VOYAGE_API_KEY=your_voyage_key
```

**Create .env.example (template):**

```bash
cat > .env.example << EOF
# Anthropic API Key (required)
ANTHROPIC_API_KEY=your_api_key_here

# Model Configuration
DEFAULT_MODEL=claude-3-5-sonnet-20241022
HAIKU_MODEL=claude-3-5-haiku-20241022

# Token Limits
MAX_TOKENS=4096

# Optional: For RAG/embeddings modules
# OPENAI_API_KEY=
# VOYAGE_API_KEY=
EOF
```

**Important:** Add .env to .gitignore!

```bash
echo ".env" >> .gitignore
echo "venv/" >> .gitignore
echo "node_modules/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

## Step 4: Verify Installation

### Python Verification

Create and run a test script:

```python
# test_setup.py
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Check API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY not found in .env file")
    exit(1)

print("✅ API key loaded")

# Test API connection
try:
    client = Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=50,
        messages=[{"role": "user", "content": "Say 'Setup successful!' and nothing else."}]
    )
    print(f"✅ API connection successful!")
    print(f"📝 Claude says: {message.content[0].text}")
    print(f"💰 Tokens used: {message.usage.input_tokens + message.usage.output_tokens}")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n🎉 All setup complete! Ready to start the tutorial.")
```

Run it:
```bash
python test_setup.py
```

### Node.js Verification

Create and run a test script:

```javascript
// test-setup.js
import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

dotenv.config();

// Check API key
const apiKey = process.env.ANTHROPIC_API_KEY;
if (!apiKey) {
  console.log('❌ ANTHROPIC_API_KEY not found in .env file');
  process.exit(1);
}

console.log('✅ API key loaded');

// Test API connection
const client = new Anthropic({ apiKey });

try {
  const message = await client.messages.create({
    model: 'claude-3-5-haiku-20241022',
    max_tokens: 50,
    messages: [{ role: 'user', content: "Say 'Setup successful!' and nothing else." }]
  });

  console.log('✅ API connection successful!');
  console.log(`📝 Claude says: ${message.content[0].text}`);
  console.log(`💰 Tokens used: ${message.usage.input_tokens + message.usage.output_tokens}`);
} catch (error) {
  console.log(`❌ Error: ${error.message}`);
  process.exit(1);
}

console.log('\n🎉 All setup complete! Ready to start the tutorial.');
```

Run it:
```bash
node test-setup.js
```

## Step 5: Additional Tools (Optional)

### Claude Code CLI (for Module 6)

Install Claude Code CLI for AI-assisted development:

```bash
# Installation instructions vary by platform
# Visit: https://docs.anthropic.com/claude/docs/claude-code
```

### Docker (for Module 8)

For deployment modules, install Docker:

- **macOS/Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux:** Follow [official instructions](https://docs.docker.com/engine/install/)

Verify:
```bash
docker --version
```

### Vector Databases (for Module 4 - RAG)

You'll set these up in Module 4, but here are quick install commands:

```bash
# ChromaDB (easiest)
pip install chromadb

# FAISS (Facebook AI)
pip install faiss-cpu

# Pinecone (cloud-based)
pip install pinecone-client
```

### MCP Tools (for Module 5)

You'll set up MCP in Module 5. No pre-installation needed.

## Step 6: Code Editor Setup

We recommend **VS Code** with these extensions:

- Python (Microsoft)
- Pylance (Microsoft)
- ESLint (for JavaScript/TypeScript)
- Prettier (code formatting)
- Claude Dev (optional, for AI assistance)

## Troubleshooting

### "Module not found" errors

**Python:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Node.js:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### API Key Issues

1. Verify your .env file exists and contains the key
2. Check that you loaded dotenv: `load_dotenv()` in Python or `dotenv.config()` in JS
3. Ensure no extra spaces or quotes around the API key
4. Verify the key is active in Anthropic console

### Rate Limiting

If you see rate limit errors:
- You may be on free tier limits
- Wait a few seconds between requests
- Implement exponential backoff (covered in Module 8)

### Import Errors

**Python:** Make sure you're using Python 3.9+
```bash
python --version
```

**Node.js:** Ensure package.json has `"type": "module"` for ES modules

## Budget Planning

To minimize costs during learning:

1. **Use Haiku** for practice (cheapest model)
2. **Set token limits** - `max_tokens=1024` is enough for most exercises
3. **Use prompt caching** (taught in Module 2)
4. **Monitor usage** in Anthropic console
5. **Estimated costs:**
   - Module 1-3: $0.50
   - Module 4 (RAG): $1.00
   - Module 5-7: $1.00
   - Module 8-9: $1.00
   - **Total: ~$3.50**

## Next Steps

✅ Environment set up
✅ API key configured
✅ Test script successful

**You're ready to start learning!**

→ Begin with [Module 1: Foundation](01-basic-api/README.md)

## Getting Help

- **Issues:** Check the troubleshooting section above
- **Questions:** Open a GitHub issue
- **Documentation:** [Anthropic Docs](https://docs.anthropic.com)

---

**Having trouble?** Don't hesitate to open an issue with:
- Your operating system
- Python/Node version
- Error messages
- What you've tried
