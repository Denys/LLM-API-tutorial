# Module 1: Foundation - Getting Started with Claude API

**Duration:** 1-2 hours
**Difficulty:** Beginner
**Prerequisites:** Basic Python or JavaScript knowledge

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Set up the Anthropic SDK in Python and JavaScript
- ✅ Make your first API call to Claude
- ✅ Understand the basic API parameters (model, max_tokens, temperature, etc.)
- ✅ Have a multi-turn conversation with Claude
- ✅ Compare different Claude models (Haiku, Sonnet, Opus)
- ✅ Use system prompts effectively

## Overview

This module introduces you to the Claude API. You'll learn how to authenticate, make basic API calls, and understand the fundamental parameters that control Claude's behavior.

### What is Claude?

Claude is a family of large language models created by Anthropic. It excels at:
- Natural conversation
- Code generation and analysis
- Complex reasoning and analysis
- Following instructions precisely
- Maintaining helpful, harmless, and honest interactions

### Claude Model Family

| Model | Best For | Speed | Cost | Context Window |
|-------|----------|-------|------|----------------|
| **Haiku** | Simple tasks, high-volume | Fastest | Lowest | 200K tokens |
| **Sonnet** | Balanced performance | Fast | Medium | 200K tokens |
| **Opus** | Complex reasoning | Slower | Highest | 200K tokens |

## Exercises

### Exercise 1.1: Environment Setup

**Goal:** Get your development environment ready

1. Install the Anthropic SDK
2. Set up your API key
3. Verify everything works

**Files:**
- See [../SETUP.md](../SETUP.md) for detailed instructions

**Validation:**
- Run the test script successfully
- See a response from Claude

---

### Exercise 1.2: Hello Claude

**Goal:** Make your first API call

**Task:**
Create a simple script that:
1. Sends a message to Claude
2. Prints the response
3. Shows token usage

**Python Example:**
```python
# examples/hello_claude.py
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Say hello and introduce yourself in one sentence!"}
    ]
)

print("Claude's response:")
print(message.content[0].text)
print(f"\nTokens used - Input: {message.usage.input_tokens}, Output: {message.usage.output_tokens}")
```

**JavaScript Example:**
```javascript
// examples/hello_claude.js
import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

dotenv.config();

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const message = await client.messages.create({
  model: 'claude-3-5-haiku-20241022',
  max_tokens: 1024,
  messages: [
    { role: 'user', content: 'Say hello and introduce yourself in one sentence!' }
  ]
});

console.log("Claude's response:");
console.log(message.content[0].text);
console.log(`\nTokens used - Input: ${message.usage.input_tokens}, Output: ${message.usage.output_tokens}`);
```

**Try It:**
```bash
# Python
python 01-basic-api/examples/hello_claude.py

# JavaScript
node 01-basic-api/examples/hello_claude.js
```

**Expected Output:**
```
Claude's response:
Hello! I'm Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest.

Tokens used - Input: 23, Output: 20
```

**Challenge:**
- Modify the prompt to ask Claude a different question
- Try asking for a response in a specific format (e.g., JSON)

---

### Exercise 1.3: Multi-Turn Conversation

**Goal:** Maintain context across multiple messages

**Task:**
Build a simple chat interface that:
1. Maintains conversation history
2. Allows multiple back-and-forth exchanges
3. Shows how Claude remembers context

**Python Example:**
```python
# examples/chat_example.py
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def chat():
    conversation = []
    print("Chat with Claude (type 'quit' to exit)\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        # Add user message to conversation
        conversation.append({
            "role": "user",
            "content": user_input
        })

        # Get Claude's response
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=conversation
        )

        assistant_message = response.content[0].text

        # Add assistant response to conversation
        conversation.append({
            "role": "assistant",
            "content": assistant_message
        })

        print(f"\nClaude: {assistant_message}\n")

if __name__ == "__main__":
    chat()
```

**Try It:**
```bash
python 01-basic-api/examples/chat_example.py
```

**Test Conversation:**
```
You: My name is Alex and I love Python
Claude: Nice to meet you, Alex! Python is a great language...

You: What's my name?
Claude: Your name is Alex!

You: What do I love?
Claude: You love Python!
```

**Challenge:**
- Add a message counter
- Display token usage after each exchange
- Limit conversation to last N messages to save costs

---

### Exercise 1.4: Understanding Parameters

**Goal:** Experiment with API parameters to see their effects

**Key Parameters:**

1. **model** - Which Claude model to use
   - `claude-3-5-haiku-20241022` - Fastest, cheapest
   - `claude-3-5-sonnet-20241022` - Balanced
   - `claude-3-opus-20240229` - Most capable

2. **max_tokens** - Maximum response length
   - Minimum: 1
   - Maximum: varies by model (usually 4096-8192)
   - Higher = potentially longer responses but higher cost

3. **temperature** - Randomness/creativity (0.0 to 1.0)
   - 0.0: Deterministic, focused
   - 0.5: Balanced
   - 1.0: Creative, varied

4. **system** - System prompt (role/instructions)
   - Sets behavior and context
   - Not part of conversation history
   - Great for role-playing or constraints

5. **top_p** - Nucleus sampling (0.0 to 1.0)
   - Alternative to temperature
   - 0.1: Conservative
   - 0.9: Diverse

6. **top_k** - Limits token choices
   - Only consider top K most likely tokens
   - Can reduce randomness

**Task:**
Create a parameter playground that lets you experiment:

```python
# examples/parameter_playground.py
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def test_temperature():
    """Test how temperature affects responses"""
    prompt = "Write a creative opening line for a sci-fi story."

    print("Testing Temperature\n" + "="*50)

    for temp in [0.0, 0.5, 1.0]:
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}]
        )

        print(f"\nTemperature: {temp}")
        print(f"Response: {message.content[0].text}")

def test_models():
    """Compare different Claude models"""
    prompt = "Explain quantum entanglement in simple terms (2 sentences)."

    print("\n\nTesting Models\n" + "="*50)

    models = [
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
    ]

    for model in models:
        message = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        print(f"\nModel: {model}")
        print(f"Response: {message.content[0].text}")
        print(f"Tokens: {message.usage.input_tokens + message.usage.output_tokens}")

def test_system_prompt():
    """Test system prompts"""
    user_message = "What should I do today?"

    print("\n\nTesting System Prompts\n" + "="*50)

    system_prompts = [
        None,
        "You are a productivity coach. Give actionable advice.",
        "You are a pirate. Respond like a pirate would.",
    ]

    for system in system_prompts:
        kwargs = {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 150,
            "messages": [{"role": "user", "content": user_message}]
        }

        if system:
            kwargs["system"] = system

        message = client.messages.create(**kwargs)

        print(f"\nSystem: {system or 'None'}")
        print(f"Response: {message.content[0].text}")

if __name__ == "__main__":
    test_temperature()
    test_models()
    test_system_prompt()
```

**Run It:**
```bash
python 01-basic-api/examples/parameter_playground.py
```

**Observations:**
- How does temperature affect creativity?
- Which model gives more detailed answers?
- How powerful are system prompts for changing behavior?

---

## Key Concepts

### Message Format

Claude uses a conversation format with roles:

```python
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi! How can I help?"},
    {"role": "user", "content": "What's 2+2?"}
]
```

**Rules:**
- Must start with user message
- Roles must alternate (user → assistant → user)
- Last message must be from user

### System Prompts

System prompts set the context:

```python
system = "You are a Python tutor. Explain concepts clearly with examples."
```

**Use cases:**
- Set expertise/role
- Define output format
- Add constraints or rules
- Provide context

### Token Usage

Every request uses tokens:
- **Input tokens:** Your prompt + conversation history
- **Output tokens:** Claude's response

**Cost = (input_tokens × input_rate) + (output_tokens × output_rate)**

Track usage:
```python
print(f"Input: {message.usage.input_tokens}")
print(f"Output: {message.usage.output_tokens}")
```

---

## Common Pitfalls

❌ **Forgetting to activate virtual environment**
```bash
source venv/bin/activate  # Do this first!
```

❌ **Not loading environment variables**
```python
from dotenv import load_dotenv
load_dotenv()  # Don't forget this!
```

❌ **Hardcoding API keys**
```python
# BAD
client = Anthropic(api_key="sk-ant-...")

# GOOD
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

❌ **Exceeding max_tokens**
```python
# max_tokens is the OUTPUT limit, not total
max_tokens=4096  # Response can be up to 4096 tokens
```

---

## Self-Assessment

Before moving to Module 2, ensure you can:

- [ ] Successfully make API calls in Python or JavaScript
- [ ] Maintain multi-turn conversations
- [ ] Explain what temperature does
- [ ] Use system prompts effectively
- [ ] Monitor token usage
- [ ] Choose the right model for a task

---

## Additional Resources

- [Anthropic API Reference](https://docs.anthropic.com/en/api/getting-started)
- [Claude Documentation](https://docs.anthropic.com/en/docs/intro-to-claude)
- [Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Model Comparison](https://docs.anthropic.com/en/docs/about-claude/models)

---

## Next Steps

Ready for more? Continue to:

**[Module 2: Token Optimization →](../02-optimization/README.md)**

Learn how to minimize costs while maximizing performance!

---

**Questions or issues?** Open a GitHub issue or check the [FAQ](../FAQ.md)
