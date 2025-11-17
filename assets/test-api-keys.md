# Test API Keys Guide

## ⚠️ IMPORTANT: Never commit real API keys!

This guide shows you how to properly manage API keys for testing and development.

## Setting Up Test Environment

### 1. Create `.env` File (Never Commit!)

```bash
# .env (add to .gitignore!)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: For RAG modules
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VOYAGE_API_KEY=pa-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: For databases
PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PINECONE_ENVIRONMENT=us-west1-gcp
```

### 2. Create `.env.example` (Safe to Commit)

```bash
# .env.example (template)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
VOYAGE_API_KEY=your_voyage_api_key_here
```

### 3. Verify `.gitignore`

```bash
# Ensure these are in .gitignore:
.env
.env.local
.env.*.local
*.key
secrets/
credentials/
```

## Getting API Keys

### Anthropic Claude API

1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Click "Create Key"
5. Copy and save securely
6. Add to `.env` file

**Free Credits:** New accounts receive $5 in free credits

### OpenAI (Optional - for embeddings)

1. Visit [platform.openai.com](https://platform.openai.com/)
2. Create account
3. Go to API Keys section
4. Create new secret key
5. Save immediately (cannot view again!)

### Voyage AI (Optional - for embeddings)

1. Visit [voyage.ai](https://www.voyageai.com/)
2. Sign up
3. Get API key from dashboard
4. Good for RAG/embeddings work

## Testing API Keys

### Python Test

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Test if key is loaded
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    print("✅ API key loaded successfully")
    print(f"Key starts with: {api_key[:10]}...")
else:
    print("❌ API key not found!")
```

### JavaScript Test

```javascript
import dotenv from 'dotenv';

dotenv.config();

const apiKey = process.env.ANTHROPIC_API_KEY;
if (apiKey) {
  console.log('✅ API key loaded successfully');
  console.log(`Key starts with: ${apiKey.substring(0, 10)}...`);
} else {
  console.log('❌ API key not found!');
}
```

### Quick Validation Script

```bash
#!/bin/bash
# validate-keys.sh

echo "Validating API keys..."

if [ -f .env ]; then
    echo "✅ .env file found"

    if grep -q "ANTHROPIC_API_KEY=sk-ant-" .env; then
        echo "✅ Anthropic API key format looks correct"
    else
        echo "⚠️  Anthropic API key may be invalid"
    fi
else
    echo "❌ .env file not found!"
    echo "Run: cp .env.example .env"
fi
```

## Security Best Practices

### DO ✅

1. **Use environment variables**
   ```python
   api_key = os.getenv("ANTHROPIC_API_KEY")
   ```

2. **Add .env to .gitignore**
   ```bash
   echo ".env" >> .gitignore
   ```

3. **Use different keys for dev/prod**
   ```bash
   # .env.development
   ANTHROPIC_API_KEY=dev_key_here

   # .env.production
   ANTHROPIC_API_KEY=prod_key_here
   ```

4. **Rotate keys regularly**
   - Create new keys every 90 days
   - Delete old keys immediately

5. **Set spending limits**
   - Configure in Anthropic console
   - Monitor usage regularly

6. **Use key management services**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault

### DON'T ❌

1. **Never hardcode keys**
   ```python
   # ❌ BAD!
   client = Anthropic(api_key="sk-ant-api03-...")
   ```

2. **Never commit keys to git**
   ```bash
   # Check before committing:
   git diff .env  # Should not be tracked!
   ```

3. **Never share keys**
   - Not in Slack, Discord, email
   - Not in screenshots
   - Not in documentation

4. **Never log keys**
   ```python
   # ❌ BAD!
   print(f"Using key: {api_key}")

   # ✅ GOOD
   print(f"Using key: {api_key[:10]}...")
   ```

## If You Accidentally Expose a Key

### Immediate Actions:

1. **Revoke the key immediately**
   - Go to Anthropic console
   - Delete the exposed key
   - Create a new one

2. **Check usage**
   - Review API usage logs
   - Look for unauthorized calls

3. **Update .env**
   - Replace with new key
   - Test application

4. **If committed to Git:**
   ```bash
   # Remove from history (use with caution!)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push
   git push origin --force --all
   ```

## Cost Management

### Monitor Usage

```python
# Track costs in your application
def track_api_call(usage):
    input_cost = (usage.input_tokens / 1_000_000) * 0.25
    output_cost = (usage.output_tokens / 1_000_000) * 1.25
    total = input_cost + output_cost

    # Log or store
    print(f"Cost: ${total:.6f}")
    return total
```

### Set Budgets

1. Anthropic Console → Settings → Usage Limits
2. Set monthly budget
3. Enable email alerts

### Use Cheaper Models for Testing

```python
# Development/Testing
model = "claude-3-5-haiku-20241022"  # Cheapest

# Production/Complex tasks
model = "claude-3-5-sonnet-20241022"  # Balanced
```

## Team Development

### For Teams:

1. **Everyone uses their own key**
   ```bash
   # Each developer has their own .env
   ANTHROPIC_API_KEY=<developer_personal_key>
   ```

2. **Shared dev key (optional)**
   ```bash
   # Use key management service
   # Rotate frequently
   # Monitor usage by developer
   ```

3. **Production keys**
   ```bash
   # Store in secure vault
   # Access only via CI/CD
   # Never on developer machines
   ```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
- name: Run tests
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: pytest tests/
```

### Setting up secrets:
1. GitHub repo → Settings → Secrets
2. Add `ANTHROPIC_API_KEY`
3. Use in workflows

## Useful Scripts

### Generate .env from template

```bash
#!/bin/bash
# setup-env.sh

if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env from template"
    echo "⚠️  Please add your API keys to .env"
else
    echo "⚠️  .env already exists"
fi
```

### Check for exposed keys

```bash
#!/bin/bash
# check-secrets.sh

# Check if any files contain API keys
if git grep -E "sk-ant-|sk-[a-zA-Z0-9]{48}" HEAD; then
    echo "❌ WARNING: API keys found in git history!"
    exit 1
else
    echo "✅ No API keys found in git"
fi
```

## Resources

- [Anthropic API Docs](https://docs.anthropic.com/)
- [API Key Best Practices](https://docs.anthropic.com/claude/reference/api-keys)
- [Environment Variables Guide](https://12factor.net/config)

---

**Remember:** Treat API keys like passwords. Never share, never commit, always secure!
