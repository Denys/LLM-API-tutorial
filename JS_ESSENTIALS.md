# JavaScript Essentials for Beginners

**Duration:** 30-45 minutes
**Prerequisites:** Basic programming concepts

## Quick Start: Why This Guide?

This tutorial uses **both Python and JavaScript** for examples. This guide helps you:
- Understand JavaScript basics quickly
- Know when to use Python vs JavaScript
- Follow along with JavaScript examples in this tutorial

## Python vs JavaScript: When to Use Each?

### 🐍 Use Python When:

✅ **Data Science & ML** - Better libraries (numpy, pandas, scikit-learn)
✅ **Scripts & Automation** - Simpler syntax for quick scripts
✅ **Backend APIs** - Great frameworks (FastAPI, Django)
✅ **You're a beginner** - Easier to learn first
✅ **Scientific Computing** - Industry standard

**Example Use Cases:**
- Data analysis and visualization
- Machine learning models
- Web scraping
- System administration
- RAG pipelines with embeddings

### 🟨 Use JavaScript When:

✅ **Web Frontend** - Only language browsers understand natively
✅ **Full-Stack Apps** - Same language frontend & backend (Node.js)
✅ **Real-Time Apps** - WebSockets, event-driven architecture
✅ **Mobile Apps** - React Native, Ionic
✅ **You need async** - Built-in async/await, event loop

**Example Use Cases:**
- Interactive web applications
- Real-time chat applications
- Browser extensions
- Serverless functions (AWS Lambda, Cloudflare Workers)
- Desktop apps (Electron)

### 🎯 For This Tutorial:

**Both work equally well for Claude API!** Choose based on:
- Your existing knowledge
- Your project requirements
- Your team's preference

**Quick Recommendation:**
- **Beginners:** Start with Python (easier syntax)
- **Web developers:** Use JavaScript (integrate with frontend)
- **Want both:** Examples are side-by-side!

---

## JavaScript Essentials

### 1. Variables and Constants

**JavaScript:**
```javascript
// Modern JavaScript uses let and const (not var!)
let name = "Claude";           // Can be reassigned
const age = 2;                 // Cannot be reassigned
const apiKey = "sk-ant-...";   // Use const for values that won't change

// ❌ Old way (don't use):
var oldWay = "avoid this";
```

**Python equivalent:**
```python
name = "Claude"        # Variables can be reassigned
age = 2
API_KEY = "sk-ant-..."  # Convention: CAPS for constants
```

**Key Differences:**
- JavaScript: Use `let` for variables, `const` for constants
- Python: All are variables; CAPS is just a convention

---

### 2. String Operations

**JavaScript:**
```javascript
// Template literals (use backticks)
const model = "claude-3-5-sonnet-20241022";
const message = `Using model: ${model}`;  // ✅ Modern way

// String concatenation (old way)
const oldMessage = "Using model: " + model;  // ❌ Avoid

// Multi-line strings
const prompt = `
  You are a helpful assistant.
  Please be concise.
`;

// Common methods
const text = "Hello World";
text.toLowerCase();          // "hello world"
text.toUpperCase();          // "HELLO WORLD"
text.includes("World");      // true
text.split(" ");             // ["Hello", "World"]
```

**Python equivalent:**
```python
# f-strings (Python 3.6+)
model = "claude-3-5-sonnet-20241022"
message = f"Using model: {model}"  # Modern way

# Multi-line strings
prompt = """
  You are a helpful assistant.
  Please be concise.
"""

# Common methods
text = "Hello World"
text.lower()              # "hello world"
text.upper()              # "HELLO WORLD"
"World" in text           # True
text.split(" ")           # ["Hello", "World"]
```

---

### 3. Arrays and Objects

**JavaScript:**
```javascript
// Arrays (like Python lists)
const models = ["haiku", "sonnet", "opus"];
models.push("new-model");        // Add to end
models[0];                       // "haiku"
models.length;                   // 4
models.map(m => m.toUpperCase()); // Transform each item
models.filter(m => m.length > 5); // Filter items

// Objects (like Python dicts)
const config = {
  model: "claude-3-5-sonnet-20241022",
  maxTokens: 1024,
  temperature: 0.7
};

// Access properties
config.model;              // Dot notation
config["maxTokens"];       // Bracket notation

// Add new property
config.systemPrompt = "You are helpful";

// Destructuring (unpack values)
const { model, maxTokens } = config;
```

**Python equivalent:**
```python
# Lists
models = ["haiku", "sonnet", "opus"]
models.append("new-model")        # Add to end
models[0]                         # "haiku"
len(models)                       # 4
[m.upper() for m in models]       # List comprehension
[m for m in models if len(m) > 5] # Filter

# Dictionaries
config = {
    "model": "claude-3-5-sonnet-20241022",
    "maxTokens": 1024,
    "temperature": 0.7
}

# Access
config["model"]
config.get("maxTokens")

# Add new key
config["systemPrompt"] = "You are helpful"

# Unpack
model = config["model"]
max_tokens = config["maxTokens"]
```

---

### 4. Functions

**JavaScript:**
```javascript
// Traditional function
function greet(name) {
  return `Hello, ${name}!`;
}

// Arrow function (modern, concise)
const greet = (name) => {
  return `Hello, ${name}!`;
};

// Arrow function (one-liner, implicit return)
const greet = (name) => `Hello, ${name}!`;

// Async function (for API calls)
async function callClaude(prompt) {
  const response = await client.messages.create({
    model: "claude-3-5-haiku-20241022",
    max_tokens: 1024,
    messages: [{ role: "user", content: prompt }]
  });
  return response.content[0].text;
}

// Using async arrow function
const callClaude = async (prompt) => {
  const response = await client.messages.create({
    model: "claude-3-5-haiku-20241022",
    max_tokens: 1024,
    messages: [{ role: "user", content: prompt }]
  });
  return response.content[0].text;
};
```

**Python equivalent:**
```python
# Regular function
def greet(name):
    return f"Hello, {name}!"

# Lambda (one-liner)
greet = lambda name: f"Hello, {name}!"

# Async function (for API calls)
async def call_claude(prompt):
    response = await client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

**Key Difference:**
- JavaScript: `async/await` is more common
- Python: Can use sync or async

---

### 5. Async/Await (Important for APIs!)

**JavaScript:**
```javascript
// ✅ Modern way (async/await)
async function main() {
  try {
    const response = await client.messages.create({
      model: "claude-3-5-haiku-20241022",
      max_tokens: 1024,
      messages: [{ role: "user", content: "Hello!" }]
    });
    console.log(response.content[0].text);
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();

// ❌ Old way (promises with .then)
client.messages.create({...})
  .then(response => console.log(response))
  .catch(error => console.error(error));
```

**Python equivalent:**
```python
# Sync way (simpler, most examples use this)
def main():
    try:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print(response.content[0].text)
    except Exception as error:
        print(f"Error: {error}")

main()

# Async way (for concurrent requests)
async def main():
    try:
        response = await client.messages.create(...)
        print(response.content[0].text)
    except Exception as error:
        print(f"Error: {error}")

asyncio.run(main())
```

---

### 6. Error Handling

**JavaScript:**
```javascript
// Try-catch
try {
  const response = await callAPI();
  console.log(response);
} catch (error) {
  console.error("Error:", error.message);
  console.error("Stack:", error.stack);
} finally {
  console.log("Cleanup");
}

// Handling specific errors
try {
  await client.messages.create({...});
} catch (error) {
  if (error.status === 401) {
    console.error("Invalid API key");
  } else if (error.status === 429) {
    console.error("Rate limited");
  } else {
    console.error("Unknown error:", error);
  }
}
```

**Python equivalent:**
```python
# Try-except
try:
    response = call_api()
    print(response)
except Exception as error:
    print(f"Error: {error}")
finally:
    print("Cleanup")

# Handling specific errors
from anthropic import APIError, RateLimitError

try:
    client.messages.create(...)
except RateLimitError:
    print("Rate limited")
except APIError as error:
    print(f"API error: {error}")
```

---

### 7. Imports and Modules

**JavaScript (ES6 Modules):**
```javascript
// Import specific items
import { Anthropic } from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

// Import everything
import * as fs from 'fs';

// Import with alias
import { something as alias } from 'module';

// Default export
import Anthropic from '@anthropic-ai/sdk';

// Load environment variables
dotenv.config();
const apiKey = process.env.ANTHROPIC_API_KEY;
```

**JavaScript (CommonJS - older):**
```javascript
// ❌ Old way (avoid in new projects)
const Anthropic = require('@anthropic-ai/sdk');
const dotenv = require('dotenv');
```

**Python equivalent:**
```python
# Import specific items
from anthropic import Anthropic
from dotenv import load_dotenv

# Import everything
import os

# Import with alias
import anthropic as ai

# Load environment variables
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")
```

**Important for this tutorial:**
- Always use ES6 modules (`import/export`)
- Set `"type": "module"` in package.json

---

### 8. Common Patterns for Claude API

**Pattern 1: Basic API Call**

**JavaScript:**
```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const message = await client.messages.create({
  model: 'claude-3-5-haiku-20241022',
  max_tokens: 1024,
  messages: [
    { role: 'user', content: 'Hello!' }
  ]
});

console.log(message.content[0].text);
```

**Python:**
```python
from anthropic import Anthropic
import os

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

message = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(message.content[0].text)
```

**Pattern 2: Streaming**

**JavaScript:**
```javascript
const stream = await client.messages.create({
  model: 'claude-3-5-haiku-20241022',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true
});

for await (const event of stream) {
  if (event.type === 'content_block_delta') {
    process.stdout.write(event.delta.text);
  }
}
```

**Python:**
```python
with client.messages.stream(
    model="claude-3-5-haiku-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

## Quick Comparison Cheat Sheet

| Feature | JavaScript | Python |
|---------|-----------|--------|
| **Variables** | `let`, `const` | Just assign |
| **Strings** | Backticks: \`${var}\` | f-strings: `f"{var}"` |
| **Arrays** | `[1, 2, 3]` | `[1, 2, 3]` |
| **Objects/Dicts** | `{key: value}` | `{"key": value}` |
| **Functions** | `() => {}` or `function()` | `def func():` |
| **Async** | `async/await` (built-in) | `async/await` (with asyncio) |
| **True/False** | `true/false` | `True/False` |
| **Null** | `null`, `undefined` | `None` |
| **Print** | `console.log()` | `print()` |
| **Comments** | `//` or `/* */` | `#` |
| **Env vars** | `process.env.VAR` | `os.getenv("VAR")` |

---

## JavaScript Setup Checklist

If you're using JavaScript in this tutorial:

```bash
# 1. Install Node.js (if not already)
node --version  # Should be 18+

# 2. Initialize project
npm init -y

# 3. Set to ES6 modules
# Add to package.json: "type": "module"

# 4. Install dependencies
npm install @anthropic-ai/sdk dotenv

# 5. Create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# 6. Create your first script
cat > hello.js << 'EOF'
import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

dotenv.config();

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const message = await client.messages.create({
  model: 'claude-3-5-haiku-20241022',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(message.content[0].text);
EOF

# 7. Run it!
node hello.js
```

---

## Common JavaScript Gotchas

### 1. Always use `const` or `let`, never `var`

```javascript
// ❌ BAD
var x = 10;

// ✅ GOOD
const x = 10;  // Won't change
let y = 20;    // Might change
```

### 2. Use arrow functions for callbacks

```javascript
// ❌ VERBOSE
array.map(function(item) {
  return item * 2;
});

// ✅ CONCISE
array.map(item => item * 2);
```

### 3. Use template literals, not concatenation

```javascript
// ❌ BAD
const message = "Hello, " + name + "!";

// ✅ GOOD
const message = `Hello, ${name}!`;
```

### 4. Use async/await, not .then()

```javascript
// ❌ OLD WAY
api.call().then(response => {
  console.log(response);
}).catch(error => {
  console.error(error);
});

// ✅ MODERN WAY
try {
  const response = await api.call();
  console.log(response);
} catch (error) {
  console.error(error);
}
```

### 5. Don't forget `await`!

```javascript
// ❌ WRONG (returns a Promise, not the value)
const response = client.messages.create({...});

// ✅ CORRECT
const response = await client.messages.create({...});
```

---

## Pro Tips for This Tutorial

### Tip 1: Use Top-Level Await

Modern Node.js (18+) supports await at top level:

```javascript
// ✅ Can use await directly in .js files
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({...});
const message = await client.messages.create({...});

// No need to wrap in async function!
```

### Tip 2: Destructuring for Cleaner Code

```javascript
// Instead of:
const text = message.content[0].text;
const tokens = message.usage.input_tokens;

// Use:
const { content, usage } = message;
const text = content[0].text;
const tokens = usage.input_tokens;

// Or even:
const { content: [{ text }], usage: { input_tokens } } = message;
```

### Tip 3: Use Optional Chaining

```javascript
// Instead of:
const text = message && message.content && message.content[0] && message.content[0].text;

// Use:
const text = message?.content?.[0]?.text;
```

### Tip 4: Default Parameters

```javascript
// Set defaults for optional parameters
async function callClaude(prompt, model = 'claude-3-5-haiku-20241022', maxTokens = 1024) {
  return await client.messages.create({
    model,
    max_tokens: maxTokens,
    messages: [{ role: 'user', content: prompt }]
  });
}

// Call with defaults
await callClaude("Hello!");

// Override defaults
await callClaude("Hello!", "claude-3-5-sonnet-20241022", 2048);
```

---

## Practice Exercise

Create a simple Claude chatbot in JavaScript:

```javascript
import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';
import * as readline from 'readline';

dotenv.config();

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const conversation = [];

async function chat(userMessage) {
  conversation.push({
    role: 'user',
    content: userMessage
  });

  const response = await client.messages.create({
    model: 'claude-3-5-haiku-20241022',
    max_tokens: 1024,
    messages: conversation
  });

  const assistantMessage = response.content[0].text;
  conversation.push({
    role: 'assistant',
    content: assistantMessage
  });

  return assistantMessage;
}

async function main() {
  console.log("Chat with Claude (type 'quit' to exit)\n");

  const askQuestion = () => {
    rl.question('You: ', async (input) => {
      if (input.toLowerCase() === 'quit') {
        console.log('Goodbye!');
        rl.close();
        return;
      }

      const response = await chat(input);
      console.log(`\nClaude: ${response}\n`);
      askQuestion();
    });
  };

  askQuestion();
}

main();
```

**Challenge:** Convert this to Python!

---

## Next Steps

Now that you understand JavaScript basics:

1. ✅ Follow along with JavaScript examples in the tutorial
2. ✅ Try converting Python examples to JavaScript (great practice!)
3. ✅ Use whichever language you're more comfortable with
4. ✅ Mix and match based on your project needs

**Ready to start?** → [Module 1: Foundation - Getting Started with Claude API](../01-basic-api/README.md)

---

## Additional Resources

- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [JavaScript.info](https://javascript.info/) - Modern JavaScript tutorial
- [Node.js Documentation](https://nodejs.org/docs/)
- [ES6 Features](http://es6-features.org/)
