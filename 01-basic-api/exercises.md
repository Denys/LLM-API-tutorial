# Module 1: Exercises

Hands-on challenges to reinforce your learning. Solutions are provided in the `solutions/` directory, but try to solve them yourself first!

## Exercise 1: Model Comparison Tool

**Difficulty:** Easy
**Time:** 15 minutes

Build a tool that sends the same prompt to all three Claude models and compares:
- Response quality
- Response time
- Token usage
- Cost

**Requirements:**
1. Accept a prompt as input
2. Send it to Haiku, Sonnet, and Opus
3. Display all three responses
4. Show performance metrics
5. Calculate the cost for each

**Starter Code:**
```python
def compare_models(prompt: str):
    # TODO: Implement model comparison
    pass

# Test with:
# compare_models("Explain machine learning in 3 sentences")
```

**Bonus:**
- Add a "winner" selection based on cost/quality ratio
- Save results to a JSON file
- Create a visualization

---

## Exercise 2: Smart Chatbot

**Difficulty:** Medium
**Time:** 30 minutes

Build an enhanced chatbot with these features:
1. Conversation history with timestamps
2. Ability to save/load conversations
3. Token usage tracking
4. Cost estimation
5. Configurable model and temperature

**Requirements:**
```python
class SmartChatbot:
    def __init__(self, model="claude-3-5-haiku-20241022", temperature=0.7):
        # TODO: Initialize

    def chat(self, message: str) -> str:
        # TODO: Send message and get response

    def get_conversation_stats(self):
        # TODO: Return total tokens, cost, message count

    def save_conversation(self, filename: str):
        # TODO: Save to JSON

    def load_conversation(self, filename: str):
        # TODO: Load from JSON
```

**Test Cases:**
```python
bot = SmartChatbot()
bot.chat("Hello!")
bot.chat("What's 2+2?")
bot.chat("Why?")
stats = bot.get_conversation_stats()
print(stats)  # Should show tokens and cost
bot.save_conversation("chat.json")
```

---

## Exercise 3: Role-Playing Assistant

**Difficulty:** Easy
**Time:** 20 minutes

Create different AI personalities using system prompts:

1. **Code Reviewer** - Reviews code and suggests improvements
2. **Creative Writer** - Writes creative stories (high temperature)
3. **Analyst** - Provides data-driven analysis (low temperature)
4. **Translator** - Translates between languages
5. **Tutor** - Teaches concepts with examples

**Requirements:**
```python
class RolePlayingAssistant:
    ROLES = {
        "code_reviewer": "You are an expert code reviewer...",
        "creative_writer": "You are a creative writer...",
        # TODO: Add more roles
    }

    def __init__(self, role: str):
        # TODO: Set system prompt and temperature

    def respond(self, message: str) -> str:
        # TODO: Generate response in character
```

**Test:**
```python
reviewer = RolePlayingAssistant("code_reviewer")
response = reviewer.respond("def calc(x,y): return x+y")
print(response)  # Should provide code review
```

---

## Exercise 4: Token Budget Manager

**Difficulty:** Medium
**Time:** 25 minutes

Build a wrapper that enforces token budgets:

**Features:**
1. Set maximum tokens per request
2. Set maximum total tokens per session
3. Warn when approaching limit
4. Refuse requests that exceed budget
5. Provide budget status

**Requirements:**
```python
class TokenBudgetManager:
    def __init__(self, max_tokens_per_request=1000, max_total_tokens=10000):
        # TODO: Initialize

    def create_message(self, messages: list, **kwargs):
        # TODO: Check budget, make request, track usage

    def get_budget_status(self):
        # TODO: Return remaining budget
```

**Test:**
```python
manager = TokenBudgetManager(max_total_tokens=5000)
for i in range(10):
    try:
        response = manager.create_message([
            {"role": "user", "content": f"Count to {i}"}
        ])
        print(manager.get_budget_status())
    except Exception as e:
        print(f"Budget exceeded: {e}")
```

---

## Exercise 5: Response Quality Tester

**Difficulty:** Hard
**Time:** 40 minutes

Test how different parameters affect response quality:

**What to test:**
1. Temperature (0.0, 0.3, 0.5, 0.7, 1.0)
2. Max tokens (50, 100, 500, 1000)
3. Top_p values
4. Different models

**Requirements:**
1. Run the same prompt with different parameters
2. Collect responses
3. Calculate variance in responses (for temperature)
4. Measure response length vs max_tokens
5. Generate a report

**Output:**
```
Parameter Testing Report
========================

Prompt: "Write a haiku about coding"

Temperature Analysis:
- 0.0: [consistent response every time]
- 0.5: [moderate variation]
- 1.0: [high variation]

Max Tokens Analysis:
- 50: [response characteristics]
- 100: [response characteristics]
...
```

---

## Exercise 6: CLI Chat Interface

**Difficulty:** Medium
**Time:** 30 minutes

Build a command-line chat interface with:

**Features:**
- `/help` - Show available commands
- `/clear` - Clear conversation
- `/save <filename>` - Save conversation
- `/load <filename>` - Load conversation
- `/model <name>` - Switch models
- `/temp <value>` - Change temperature
- `/stats` - Show statistics
- `/quit` - Exit

**Example Session:**
```
> /help
Available commands:
  /help - Show this help
  /clear - Clear conversation
  ...

> Hello Claude
Claude: Hi! How can I help you today?

> /stats
Messages: 2
Tokens: 45 (input: 20, output: 25)
Cost: $0.000056

> /temp 0.9
Temperature set to 0.9

> Tell me a joke
Claude: [creative joke with high temperature]

> /quit
Goodbye!
```

---

## Challenge Projects

### Project A: Multi-Model Consensus

Build a system that:
1. Sends the same question to multiple models
2. Compares their answers
3. Identifies consensus or disagreement
4. Reports confidence levels

**Use case:** Fact-checking, decision support

### Project B: Adaptive Model Selector

Build a system that:
1. Analyzes the user's question
2. Automatically selects the best model
3. Chooses optimal parameters
4. Minimizes cost while maintaining quality

**Logic:**
- Simple questions → Haiku
- Complex reasoning → Sonnet
- Creative tasks → High temperature
- Analytical tasks → Low temperature

### Project C: Conversation Analyzer

Build a tool that:
1. Loads conversation history
2. Analyzes patterns (topics, sentiment, length)
3. Generates insights
4. Visualizes conversation flow

---

## Solutions

Solutions are available in `solutions/` directory:
- `solution_01_model_comparison.py`
- `solution_02_smart_chatbot.py`
- `solution_03_role_playing.py`
- `solution_04_budget_manager.py`
- `solution_05_quality_tester.py`
- `solution_06_cli_chat.py`

**Try solving them yourself first!** 💪

---

## Self-Grading Rubric

Rate yourself on each exercise:

- ⭐ Attempted but incomplete
- ⭐⭐ Working but basic implementation
- ⭐⭐⭐ Fully working with good practices
- ⭐⭐⭐⭐ Includes error handling and edge cases
- ⭐⭐⭐⭐⭐ Optimized, documented, production-ready

**Goal:** At least ⭐⭐⭐ on all exercises before moving to Module 2

---

## Need Help?

- Review the [Module 1 README](README.md)
- Check the [Quick Reference](../QUICK_REFERENCE.md)
- Look at example code
- Ask in GitHub Discussions

---

**Ready for more?** Continue to [Module 2: Token Optimization](../02-optimization/README.md)
