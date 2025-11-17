# Quick Start Guide - Module 7: Agents

Get started with autonomous AI agents in 5 minutes!

## Prerequisites

- Python 3.8+
- Anthropic API key (required)
- OpenAI API key (optional, for multi-provider examples)

## Installation

### 1. Install Dependencies

```bash
cd 07-agents
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Copy template
cp .env.template .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Add your keys:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
OPENAI_API_KEY=sk-your-actual-key-here  # Optional
```

## Run Examples

### Single Agent Examples

**Basic autonomous agent:**
```bash
python examples/single-agent/basic_agent.py
```

This demonstrates:
- Agent perceive-reason-act-observe loop
- Tool usage for calculations
- Autonomous task completion

**Agent with memory:**
```bash
python examples/single-agent/agent_with_memory.py
```

This demonstrates:
- Short-term memory (conversation context)
- Long-term memory (persistent knowledge)
- Memory search and recall

**Multi-provider agent:**
```bash
python examples/single-agent/multi_provider_agent.py
```

This demonstrates:
- Using both Claude and OpenAI
- Provider comparison
- Provider-agnostic design

### Multi-Agent Examples

**Communication patterns:**
```bash
python examples/multi-agent/communication_demo.py
```

This demonstrates:
- Request-Response: Direct agent-to-agent queries
- Broadcast: One-to-many messaging
- Pub-Sub: Topic-based communication

**Collaborative agents:**
```bash
python examples/multi-agent/collaborative_agents.py
```

This demonstrates:
- Multiple specialized agents
- Sequential collaboration
- Context sharing between agents

### Orchestration Examples

**Agent orchestration:**
```bash
python examples/orchestration/orchestrator.py
```

This demonstrates:
- Sequential execution
- Parallel execution
- Hierarchical supervisor-worker pattern

### Power Design System

**Complete multi-agent design system:**
```bash
python examples/power-design/power_multi_agent_system.py
```

This demonstrates:
- 9 specialized agents working together
- Complex workflow orchestration
- Professional design documentation
- Real-world application

## Example Output Locations

All examples save outputs to `outputs/` directories within their folders:

```
examples/
├── single-agent/outputs/
│   └── led_resistor_design.txt
├── multi-agent/outputs/
│   └── collaborative_design_report.txt
└── power-design/outputs/
    ├── buck_converter_design.json
    └── buck_converter_design.txt
```

## Quick Reference

### Agent Architecture

```
┌─────────────────────────────────┐
│     Perceive (Input/Task)       │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│  Reason (AI Model Decision)     │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│      Act (Execute Tools)        │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   Observe (Process Results)     │
└────────────┬────────────────────┘
             │
             └──────────► Loop until complete
```

### Orchestration Patterns

| Pattern      | Use Case                          | Example                     |
|--------------|-----------------------------------|-----------------------------|
| Sequential   | Steps depend on previous results  | Design → Analyze → Optimize |
| Parallel     | Independent tasks                 | Multiple analyses at once   |
| Hierarchical | Supervisor coordinates workers    | Manager + specialist team   |
| Conditional  | Task selection based on criteria  | If X then do Y              |

## Common Tasks

### Create a Basic Agent

```python
from anthropic import Anthropic

class MyAgent:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def run(self, task: str):
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=MY_TOOLS,
            messages=[{"role": "user", "content": task}]
        )
        # Process response and handle tools...
```

### Add Memory to Agent

```python
class MemoryAgent:
    def __init__(self):
        self.memory = []  # Short-term memory
        self.knowledge_base = []  # Long-term memory

    def remember(self, fact):
        self.knowledge_base.append(fact)
        self._save_to_disk()

    def recall(self, query):
        # Search knowledge base
        return relevant_memories
```

### Create Multi-Agent System

```python
agents = {
    "designer": Agent("Designer", "Circuit design"),
    "analyzer": Agent("Analyzer", "Performance analysis"),
}

# Sequential workflow
design = agents["designer"].run(task)
analysis = agents["analyzer"].run(f"Analyze: {design}")
```

## Troubleshooting

### API Key Errors

```
Error: ANTHROPIC_API_KEY not found
```

**Solution:** Check your `.env` file exists and contains valid API key.

### Import Errors

```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution:** Install requirements:
```bash
pip install -r requirements.txt
```

### Memory Errors

```
FileNotFoundError: memory directory not found
```

**Solution:** Memory directories are created automatically, but ensure write permissions.

## Next Steps

1. ✅ Run all examples to see different agent patterns
2. 📖 Read the full [README.md](README.md) for detailed explanations
3. 🔧 Modify examples to solve your specific problems
4. 🏗️ Build your own multi-agent systems

## Resources

- **Full Documentation:** [README.md](README.md)
- **Anthropic Docs:** https://docs.anthropic.com
- **OpenAI Docs:** https://platform.openai.com/docs
- **Tool Use Guide:** Module 3 (Advanced Features)
- **RAG Guide:** Module 4 (for agent knowledge bases)

## Tips

1. **Start Simple:** Begin with basic_agent.py before moving to complex systems
2. **Test Incrementally:** Test each agent individually before integration
3. **Monitor Costs:** Agents make multiple API calls - track token usage
4. **Use Haiku for Testing:** Use claude-3-5-haiku-20241022 for faster, cheaper testing
5. **Save Outputs:** All examples save outputs - review them to understand agent behavior

---

**Ready to build autonomous AI systems? Run your first agent:**

```bash
python examples/single-agent/basic_agent.py
```
