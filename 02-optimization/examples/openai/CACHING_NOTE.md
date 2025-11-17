# Prompt Caching: Claude vs OpenAI

## Important Difference

**Claude (Anthropic)** has built-in **Prompt Caching** support that can reduce costs by up to 90%!

**OpenAI** does **NOT** have an equivalent prompt caching feature as of 2025.

## What is Prompt Caching (Claude)?

Claude allows you to mark portions of your prompt (like system messages or large contexts) to be cached for 5 minutes:

```python
# Claude with caching
cached_system = [
    {
        "type": "text",
        "text": LARGE_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}  # ← Cache this!
    }
]

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=cached_system,
    messages=[{"role": "user", "content": "Question"}]
)

# First request: Normal cost
# Subsequent requests (within 5 min): 90% discount on cached tokens!
```

## OpenAI Alternative Strategies

Since OpenAI doesn't have prompt caching, here are optimization strategies:

### 1. **Keep System Messages Concise**

```python
# ❌ Verbose system message (costs repeat on every call)
system = """You are an expert Python developer with 20 years of experience.
Your expertise includes Python 3.x, async programming, Django, Flask...
[500+ tokens of instructions]"""

# ✅ Concise system message
system = "You are a Python expert. Provide clear, working code examples."
```

### 2. **Use GPT-3.5-turbo for Simple Tasks**

GPT-3.5-turbo is **20x cheaper** than GPT-4:

```python
# Cost comparison for 1000 input + 500 output tokens:
# GPT-3.5-turbo: $0.00125
# GPT-4-turbo:   $0.025
# Claude Haiku:  $0.00088 (without caching)
# Claude Haiku:  $0.00009 (with caching - 90% off!)
```

### 3. **Batch Similar Requests**

Instead of multiple separate calls:

```python
# ❌ Multiple calls (repeats system message cost)
for question in questions:
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )
```

Batch them together:

```python
# ✅ Single call with all questions
combined_prompt = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])

response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Answer these questions:\n{combined_prompt}"}
    ]
)
```

### 4. **Store Context in Conversation History**

For multi-turn conversations, build up context naturally:

```python
conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
]

# First turn
conversation.append({"role": "user", "content": "I'm working on a Python project."})
response = client.chat.completions.create(model="gpt-4", messages=conversation)
conversation.append({"role": "assistant", "content": response.choices[0].message.content})

# Second turn - context already in conversation
conversation.append({"role": "user", "content": "How do I add logging?"})
response = client.chat.completions.create(model="gpt-4", messages=conversation)
```

### 5. **Use Fine-Tuning for Repeated Patterns**

If you have specific, repeated use cases, consider fine-tuning:

```python
# Fine-tune GPT-3.5-turbo with your specific instructions
# Then use shorter prompts in production

# Before fine-tuning:
# "You are an expert in X. Always format responses as Y. Use style Z. [200 tokens]"

# After fine-tuning:
# "Analyze this code." [3 tokens]
```

## Cost Comparison Example

Scenario: **10 API calls** with a **500-token system prompt** and **200-token responses**

| Provider | Feature | Cost |
|----------|---------|------|
| **Claude Haiku** | With caching | $0.00094 |
| **Claude Haiku** | Without caching | $0.00875 |
| **GPT-3.5-turbo** | No caching | $0.01250 |
| **GPT-4-turbo** | No caching | $0.25000 |

**Claude with caching is 265x cheaper than GPT-4 for repeated prompts!**

## When to Use Claude vs OpenAI

### Use **Claude** when:
- ✅ You have large, repeated system prompts
- ✅ Building chatbots with consistent instructions
- ✅ Processing many documents with same analysis prompt
- ✅ Cost optimization is critical
- ✅ You need longer context windows (200K tokens)

### Use **OpenAI** when:
- ✅ You need function calling (more mature)
- ✅ You prefer GPT-4's specific capabilities
- ✅ Integration with OpenAI ecosystem
- ✅ Simple, one-off requests (no caching benefit)
- ✅ Using fine-tuned models

## Summary

| Feature | Claude | OpenAI |
|---------|--------|--------|
| **Prompt Caching** | ✅ Yes (90% discount) | ❌ No |
| **Cache Duration** | 5 minutes | N/A |
| **Best Use Case** | Repeated prompts | One-off queries |
| **Optimization Strategy** | Cache large contexts | Use concise prompts |
| **Cost (Haiku)** | $0.25/$1.25 per 1M | N/A |
| **Cost (GPT-3.5)** | N/A | $0.50/$1.50 per 1M |
| **Cost (GPT-4)** | N/A | $10/$30 per 1M |

## Code Examples

See the examples in this directory:

- **`prompt_caching_demo.py`** - Claude caching demonstration (in parent directory)
- **`token_counter_openai.py`** - OpenAI token optimization
- **`streaming_openai.py`** - OpenAI streaming (same cost as non-streaming)

## Key Takeaway

**If you're making repeated API calls with large system prompts, Claude's prompt caching can save you 90% on costs. OpenAI doesn't have this feature, so optimize by keeping prompts concise and using cheaper models when possible.**
