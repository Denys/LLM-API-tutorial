# Module 2: Token Optimization & Cost Management

**Duration:** 2 hours
**Difficulty:** Intermediate
**Prerequisites:** Module 1 completed

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Count tokens accurately in your prompts
- ✅ Calculate API costs precisely
- ✅ Implement prompt caching to reduce costs by 90%
- ✅ Use streaming for better user experience
- ✅ Write efficient prompts that minimize token usage
- ✅ Build a token budget system
- ✅ Apply advanced prompt engineering techniques

## Overview

Every API call costs money based on token usage. This module teaches you how to optimize costs while maintaining quality. You'll learn to use Claude efficiently, making your applications economical and scalable.

### Cost Breakdown (as of 2025)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Cache Write | Cache Read |
|-------|----------------------|------------------------|-------------|------------|
| Haiku | $0.25 | $1.25 | $0.30 | $0.03 |
| Sonnet | $3.00 | $15.00 | $3.75 | $0.30 |
| Opus | $15.00 | $75.00 | $18.75 | $1.50 |

**Key insight:** Cache reads are 10x cheaper than regular input!

---

## Understanding Tokens

### What is a Token?

A token is a unit of text that Claude processes. Roughly:
- **1 token ≈ 4 characters** in English
- **1 token ≈ ¾ of a word**
- **100 tokens ≈ 75 words**

**Examples:**
```
"Hello" = 1 token
"Hello, world!" = 4 tokens
"The quick brown fox" = 4 tokens
"OpenAI" = 3 tokens (Open, AI, space)
```

### Why Tokens Matter

```python
# Example: Same meaning, different costs

# ❌ Inefficient (100 tokens)
prompt = """
Please analyze the following text and provide
a detailed summary of the main points discussed
in the document, including key themes, important
details, and any conclusions that can be drawn.
"""

# ✅ Efficient (20 tokens)
prompt = "Summarize the main points, themes, and conclusions:"

# Cost savings: 80% reduction!
```

---

## Exercise 2.1: Token Counting

### Manual Token Counting

**Python:**
```python
import tiktoken

def count_tokens(text: str, model: str = "claude-3-5-sonnet-20241022") -> int:
    """
    Count tokens in text using tiktoken.
    Claude uses a similar tokenizer to GPT models.
    """
    # Use cl100k_base encoding (close approximation for Claude)
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    return len(tokens)

# Examples
print(count_tokens("Hello, world!"))  # ~4 tokens
print(count_tokens("The quick brown fox jumps over the lazy dog."))  # ~10 tokens
```

**JavaScript:**
```javascript
import { encode } from 'gpt-tokenizer';

function countTokens(text) {
  const tokens = encode(text);
  return tokens.length;
}

console.log(countTokens("Hello, world!"));  // ~4 tokens
console.log(countTokens("The quick brown fox jumps over the lazy dog."));  // ~10 tokens
```

### Token Counter Tool

See `examples/token_counter.py` for a complete implementation with:
- File and text input support
- Batch processing
- Cost estimation
- Detailed breakdown

**Try it:**
```bash
python examples/token_counter.py "Your text here"
python examples/token_counter.py --file document.txt
```

---

## Exercise 2.2: Cost Calculation

### Building a Cost Calculator

**Python:**
```python
class CostCalculator:
    """Calculate Claude API costs with precision."""

    PRICING = {
        "claude-3-5-haiku-20241022": {
            "input": 0.25,    # per 1M tokens
            "output": 1.25,
            "cache_write": 0.30,
            "cache_read": 0.03
        },
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00,
            "cache_write": 3.75,
            "cache_read": 0.30
        }
    }

    def calculate_cost(self, usage, model: str, cache_read_tokens: int = 0) -> dict:
        """Calculate total cost from usage object."""
        pricing = self.PRICING.get(model, self.PRICING["claude-3-5-haiku-20241022"])

        # Standard costs
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]

        # Cache costs (if applicable)
        cache_cost = 0
        if cache_read_tokens > 0:
            regular_input_tokens = usage.input_tokens - cache_read_tokens
            regular_cost = (regular_input_tokens / 1_000_000) * pricing["input"]
            cached_cost = (cache_read_tokens / 1_000_000) * pricing["cache_read"]
            input_cost = regular_cost + cached_cost
            cache_cost = cached_cost

        total_cost = input_cost + output_cost

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "cache_cost": cache_cost,
            "total_cost": total_cost,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read_tokens": cache_read_tokens
        }

    def estimate_monthly_cost(self, avg_requests_per_day: int,
                             avg_tokens_per_request: int,
                             model: str = "claude-3-5-haiku-20241022") -> dict:
        """Estimate monthly costs based on usage patterns."""
        pricing = self.PRICING[model]

        # Daily calculations
        daily_tokens = avg_requests_per_day * avg_tokens_per_request
        daily_cost = (daily_tokens / 1_000_000) * (pricing["input"] + pricing["output"])

        # Monthly projections
        monthly_requests = avg_requests_per_day * 30
        monthly_tokens = daily_tokens * 30
        monthly_cost = daily_cost * 30

        return {
            "monthly_requests": monthly_requests,
            "monthly_tokens": monthly_tokens,
            "monthly_cost": monthly_cost,
            "daily_cost": daily_cost
        }
```

**Usage:**
```python
calculator = CostCalculator()

# After API call
cost_breakdown = calculator.calculate_cost(message.usage, "claude-3-5-haiku-20241022")
print(f"Total cost: ${cost_breakdown['total_cost']:.6f}")

# Monthly estimate
estimate = calculator.estimate_monthly_cost(
    avg_requests_per_day=1000,
    avg_tokens_per_request=500,
    model="claude-3-5-haiku-20241022"
)
print(f"Estimated monthly cost: ${estimate['monthly_cost']:.2f}")
```

---

## Exercise 2.3: Prompt Caching

### What is Prompt Caching?

Prompt caching allows you to reuse parts of your prompt across multiple requests, reducing costs by up to 90% for cached content.

**How it works:**
```
┌─────────────────────────────────────┐
│  First Request (Cache MISS)         │
│  ─────────────────────────────────  │
│  System: "You are helpful" (cached) │  ← Costs normal rate
│  User: "What is Python?"            │  ← Costs normal rate
│  ─────────────────────────────────  │
│  Total: Normal cost                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Second Request (Cache HIT)         │
│  ─────────────────────────────────  │
│  System: "You are helpful" (cached) │  ← 90% cheaper!
│  User: "What is JavaScript?"        │  ← Costs normal rate
│  ─────────────────────────────────  │
│  Total: Much cheaper!               │
└─────────────────────────────────────┘
```

### Implementing Prompt Caching

**Python:**
```python
from anthropic import Anthropic

client = Anthropic()

# Cache the system prompt (stays same across requests)
def create_cached_message(user_prompt: str):
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": """You are an expert Python programmer with 20 years of experience.
                You provide clear, concise explanations with code examples.
                You follow PEP 8 style guide and best practices.""",
                "cache_control": {"type": "ephemeral"}  # ← Cache this!
            }
        ],
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    return message

# First call: Cache MISS (full cost)
response1 = create_cached_message("Explain list comprehensions")
print(f"Cache read tokens: {response1.usage.cache_read_input_tokens}")  # 0

# Second call: Cache HIT (90% cheaper for cached part!)
response2 = create_cached_message("Explain decorators")
print(f"Cache read tokens: {response2.usage.cache_read_input_tokens}")  # ~50
```

### Cache Best Practices

✅ **DO:**
- Cache large, static content (system prompts, documentation)
- Cache content that repeats across requests
- Use cache for conversation context in chatbots
- Cache RAG document context

❌ **DON'T:**
- Cache small prompts (not cost-effective)
- Cache frequently changing content
- Assume cache will always be available (TTL: 5 minutes)

### Advanced Caching: Multi-Block

```python
# Cache multiple blocks separately
system = [
    {
        "type": "text",
        "text": "You are a helpful assistant.",
    },
    {
        "type": "text",
        "text": large_company_documentation,  # 10,000 tokens
        "cache_control": {"type": "ephemeral"}  # Cache this
    },
    {
        "type": "text",
        "text": conversation_history,  # 5,000 tokens
        "cache_control": {"type": "ephemeral"}  # Cache this too
    }
]
```

---

## Exercise 2.4: Streaming Responses

### Why Stream?

**Benefits:**
- ⚡ **Faster perceived response time** - Users see output immediately
- 🔄 **Better UX** - Real-time feedback, like ChatGPT
- 📊 **Process as you receive** - Start working with partial responses
- 💰 **Same cost** - No additional charges for streaming

### Implementing Streaming

**Python:**
```python
from anthropic import Anthropic

client = Anthropic()

def stream_response(prompt: str):
    """Stream Claude's response token by token."""
    with client.messages.stream(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print()  # New line after complete response

# Usage
stream_response("Tell me a short story about a robot")
```

**JavaScript:**
```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

async function streamResponse(prompt) {
  const stream = await client.messages.create({
    model: 'claude-3-5-haiku-20241022',
    max_tokens: 1024,
    messages: [{ role: 'user', content: prompt }],
    stream: true
  });

  for await (const event of stream) {
    if (event.type === 'content_block_delta') {
      process.stdout.write(event.delta.text);
    }
  }

  console.log();  // New line
}

// Usage
await streamResponse('Tell me a short story about a robot');
```

### Advanced Streaming with Processing

```python
def stream_with_processing(prompt: str):
    """Stream and process response in real-time."""
    full_response = []

    with client.messages.stream(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            # Display to user
            print(text, end="", flush=True)

            # Collect for processing
            full_response.append(text)

            # Real-time processing (e.g., sentiment analysis)
            # analyze_sentiment(text)

    # Final message
    final_message = stream.get_final_message()
    print(f"\n\nTokens used: {final_message.usage.input_tokens + final_message.usage.output_tokens}")

    return "".join(full_response)
```

---

## Exercise 2.5: Prompt Engineering for Efficiency

### Concise Prompting

**Before (verbose):**
```python
prompt = """
I would like you to please provide me with a comprehensive
and detailed explanation of what the Python programming
language is, including information about its history, its
main features and characteristics, and some of the primary
use cases where it is commonly applied.
"""
# ~50 tokens
```

**After (concise):**
```python
prompt = "Explain Python: history, key features, and common use cases."
# ~12 tokens - 76% reduction!
```

### Structured Prompts with XML

```python
# Use XML tags for clarity and token efficiency
prompt = """
<document>
{long_document_text}
</document>

<question>
What are the main themes?
</question>

<instructions>
- List 3-5 themes
- Provide brief examples
- Keep under 200 words
</instructions>
"""
```

### Few-Shot Learning

```python
# Show examples instead of long explanations
prompt = """
Extract email addresses.

Examples:
"Contact john@example.com" → john@example.com
"Email: alice@test.org" → alice@test.org

Now extract from: {user_text}
"""
```

---

## Exercise 2.6: Budget Management

### Token Budget System

**Python:**
```python
class TokenBudget:
    """Manage token usage with budgets and alerts."""

    def __init__(self, daily_budget_tokens: int, cost_per_million: float = 1.0):
        self.daily_budget = daily_budget_tokens
        self.used_today = 0
        self.cost_per_million = cost_per_million
        self.requests_today = 0

    def check_budget(self, estimated_tokens: int) -> bool:
        """Check if request fits within budget."""
        if self.used_today + estimated_tokens > self.daily_budget:
            remaining = self.daily_budget - self.used_today
            print(f"⚠️  Budget exceeded! Remaining: {remaining} tokens")
            return False
        return True

    def record_usage(self, input_tokens: int, output_tokens: int):
        """Record token usage from API response."""
        total = input_tokens + output_tokens
        self.used_today += total
        self.requests_today += 1

        # Alert at thresholds
        usage_percent = (self.used_today / self.daily_budget) * 100
        if usage_percent >= 90:
            print(f"🚨 90% of daily budget used!")
        elif usage_percent >= 75:
            print(f"⚠️  75% of daily budget used")

    def get_stats(self) -> dict:
        """Get current usage statistics."""
        remaining = self.daily_budget - self.used_today
        cost_today = (self.used_today / 1_000_000) * self.cost_per_million

        return {
            "used": self.used_today,
            "remaining": remaining,
            "budget": self.daily_budget,
            "percent_used": (self.used_today / self.daily_budget) * 100,
            "requests": self.requests_today,
            "cost_today": cost_today
        }
```

**Usage:**
```python
# Set daily budget
budget = TokenBudget(daily_budget_tokens=100_000, cost_per_million=1.25)

# Before request
if not budget.check_budget(estimated_tokens=5000):
    print("Request denied - budget exceeded")
    exit()

# After request
message = client.messages.create(...)
budget.record_usage(message.usage.input_tokens, message.usage.output_tokens)

# Check stats
stats = budget.get_stats()
print(f"Used: {stats['percent_used']:.1f}%")
print(f"Cost today: ${stats['cost_today']:.4f}")
```

---

## Pro Tips & Tricks

### 1. Model Selection Strategy

```python
def choose_model(task_complexity: str, budget: str) -> str:
    """Smart model selection based on task and budget."""

    if budget == "minimal":
        return "claude-3-5-haiku-20241022"

    if task_complexity == "simple":
        return "claude-3-5-haiku-20241022"  # Fast and cheap
    elif task_complexity == "moderate":
        return "claude-3-5-sonnet-20241022"  # Balanced
    else:  # complex
        if budget == "unlimited":
            return "claude-3-opus-20240229"  # Best quality
        else:
            return "claude-3-5-sonnet-20241022"  # Best value
```

### 2. Batch Processing for Efficiency

```python
def batch_process(items: list, batch_size: int = 10):
    """Process multiple items in fewer API calls."""

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        # Combine multiple requests into one
        prompt = "Analyze these items:\n\n"
        for idx, item in enumerate(batch, 1):
            prompt += f"{idx}. {item}\n"

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse batch response
        # process_batch_response(response)
```

### 3. Prompt Templates for Reusability

```python
TEMPLATES = {
    "summarize": "Summarize in {max_words} words:\n\n{text}",
    "translate": "Translate to {language}:\n\n{text}",
    "code_review": "Review this {language} code:\n\n```{language}\n{code}\n```",
    "extract_data": """
    Extract {data_type} from the text.
    Return as JSON with these fields: {fields}

    Text: {text}
    """
}

def use_template(template_name: str, **kwargs) -> str:
    """Fill template with provided values."""
    return TEMPLATES[template_name].format(**kwargs)

# Usage
prompt = use_template(
    "summarize",
    max_words=100,
    text="Long document here..."
)
```

### 4. Compression Techniques

```python
# Instead of sending full document multiple times
# Send once with caching, then reference

# First request (cache document)
message1 = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[{
        "type": "text",
        "text": f"Document:\n\n{large_document}",
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[{"role": "user", "content": "Summarize the main points"}]
)

# Subsequent requests (cached!)
message2 = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[{
        "type": "text",
        "text": f"Document:\n\n{large_document}",
        "cache_control": {"type": "ephemeral"}
    }],
    messages=[{"role": "user", "content": "What are the conclusions?"}]
)
# ← Document tokens now 90% cheaper!
```

---

## Common Pitfalls

### ❌ Pitfall 1: Over-engineering Prompts

```python
# BAD: Too verbose
prompt = """
Please carefully analyze the following text and provide
me with a very detailed and comprehensive summary that
includes all of the most important points...
"""

# GOOD: Clear and concise
prompt = "Summarize the key points:"
```

### ❌ Pitfall 2: Ignoring Cache Opportunities

```python
# BAD: Recalculate everything each time
for question in questions:
    response = client.messages.create(
        system=long_instructions,  # Not cached!
        messages=[{"role": "user", "content": question}]
    )

# GOOD: Cache static content
system_cached = [{
    "type": "text",
    "text": long_instructions,
    "cache_control": {"type": "ephemeral"}
}]

for question in questions:
    response = client.messages.create(
        system=system_cached,  # Cached after first call!
        messages=[{"role": "user", "content": question}]
    )
```

### ❌ Pitfall 3: Not Monitoring Costs

```python
# BAD: No tracking
response = client.messages.create(...)

# GOOD: Always track
response = client.messages.create(...)
cost = calculate_cost(response.usage)
log_cost(cost)  # Store for analysis
alert_if_threshold_exceeded(cost)
```

---

## Real-World Examples

### Example 1: Cost-Optimized Chatbot

See `examples/optimized_chatbot.py` for complete implementation featuring:
- Prompt caching for system instructions
- Conversation summarization to manage history
- Token budget enforcement
- Streaming responses
- Cost tracking and reporting

### Example 2: Batch Document Analyzer

See `examples/batch_analyzer.py` showing:
- Processing multiple documents efficiently
- Smart batching to reduce API calls
- Progress tracking
- Cost comparison (batch vs individual)

### Example 3: Budget-Aware Application

See `examples/budget_app.py` demonstrating:
- Daily/monthly budget management
- Automatic model selection based on remaining budget
- Usage alerts and reporting
- Cost optimization strategies

---

## Self-Assessment

Before moving to Module 3, ensure you can:

- [ ] Count tokens in prompts accurately
- [ ] Calculate API costs for different models
- [ ] Implement prompt caching effectively
- [ ] Use streaming for better UX
- [ ] Write concise, efficient prompts
- [ ] Set up budget management
- [ ] Choose the right model for the task
- [ ] Apply prompt engineering techniques

---

## Additional Resources

- [Anthropic Prompt Caching Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Token Counting Best Practices](https://docs.anthropic.com/en/docs/build-with-claude/token-counting)
- [Streaming API Documentation](https://docs.anthropic.com/en/api/messages-streaming)
- [Cost Optimization Tips](https://docs.anthropic.com/en/docs/build-with-claude/cost-optimization)

---

## Next Steps

Ready to explore advanced features? Continue to:

**[Module 3: Advanced Features - Vision & Tools →](../03-advanced-features/README.md)**

Learn about multimodal AI, function calling, and tool integration!

---

**Questions or issues?** Open a GitHub issue or check the tutorials.
