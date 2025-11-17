# Module 7: Agents - Autonomous AI Systems & Multi-Agent Workflows

**Duration:** 4-5 hours
**Difficulty:** Advanced
**Prerequisites:** Modules 1-3 completed (Modules 4-6 highly recommended)

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Understand autonomous AI agents and their architecture
- ✅ Create single-purpose agents with goals and tools
- ✅ Build multi-agent systems with specialized roles
- ✅ Implement agent communication protocols
- ✅ Design agent orchestration patterns
- ✅ Create a power electronics multi-agent design system
- ✅ Handle agent failures and error recovery
- ✅ Optimize agent performance and cost

## What are AI Agents?

**AI Agents** are autonomous systems that:
1. **Perceive** their environment (inputs, tools, data)
2. **Reason** about goals and plans
3. **Act** by using tools and making decisions
4. **Learn** from results and iterate

Unlike simple LLM calls, agents can:
- Work autonomously toward goals
- Use multiple tools in sequence
- Make decisions based on intermediate results
- Handle complex, multi-step tasks
- Collaborate with other agents

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS AGENT                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    AGENT LOOP                         │   │
│  │                                                       │   │
│  │  1. PERCEIVE  ──→  2. REASON  ──→  3. ACT           │   │
│  │       ↑                                    │          │   │
│  │       │                                    │          │   │
│  │       └────────────  4. OBSERVE  ←─────────┘          │   │
│  │                                                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   MEMORY    │  │    TOOLS    │  │   GOALS     │         │
│  │             │  │             │  │             │         │
│  │ • History   │  │ • Calculate │  │ • Task      │         │
│  │ • Context   │  │ • Search    │  │ • Success   │         │
│  │ • Learning  │  │ • Analyze   │  │ • Metrics   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Perception**: Understanding the current state
2. **Reasoning**: Planning actions to achieve goals
3. **Action**: Executing tools and making decisions
4. **Memory**: Maintaining context and learning
5. **Tools**: Available capabilities and functions
6. **Goals**: Success criteria and objectives

---

## Single Agent vs Multi-Agent

### Single Agent
```
User Goal → Agent → Tools → Result
```

**Use when:**
- Task is well-defined and focused
- Single perspective is sufficient
- Tools are straightforward

**Example:** "Calculate buck converter components"

### Multi-Agent System
```
User Goal → Orchestrator
              ↓
         ┌────┴────┬──────────┐
         ↓         ↓          ↓
    Agent 1    Agent 2    Agent 3
    (Design)   (Verify)   (Optimize)
         ↓         ↓          ↓
         └────┬────┴──────────┘
              ↓
           Result
```

**Use when:**
- Task requires multiple perspectives
- Specialized expertise needed
- Parallel processing beneficial
- Verification and validation required

**Example:** "Design, verify, and optimize a complete power supply"

---

## Exercise 7.1: Basic Autonomous Agent

### Simple Agent Pattern

**Python:**
```python
from anthropic import Anthropic
from typing import List, Dict, Any

class SimpleAgent:
    """Basic autonomous agent."""

    def __init__(self, name: str, goal: str, tools: List[Dict]):
        self.name = name
        self.goal = goal
        self.tools = tools
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.memory = []  # Conversation history

    def run(self, task: str, max_iterations: int = 10):
        """Run agent to accomplish task."""
        print(f"🤖 {self.name} starting...")
        print(f"   Goal: {self.goal}")
        print(f"   Task: {task}\n")

        # Add task to memory
        self.memory.append({
            "role": "user",
            "content": f"Goal: {self.goal}\n\nTask: {task}"
        })

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"── Iteration {iteration} ──")

            # Reason and act
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                tools=self.tools,
                messages=self.memory
            )

            # Check if done
            if response.stop_reason == "end_turn":
                # Extract final answer
                final_text = response.content[0].text
                print(f"\n✅ {self.name} completed!")
                print(f"   Result: {final_text}")
                return final_text

            # Handle tool use
            if response.stop_reason == "tool_use":
                self._handle_tools(response)

            # Add to memory
            self.memory.append({
                "role": "assistant",
                "content": response.content
            })

        print(f"\n⚠️  Max iterations reached")
        return None

    def _handle_tools(self, response):
        """Handle tool execution."""
        tool_results = []

        for content in response.content:
            if content.type == "tool_use":
                print(f"   🔧 Using: {content.name}")

                # Execute tool
                result = self._execute_tool(content.name, content.input)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content.id,
                    "content": json.dumps(result)
                })

        # Add tool results to memory
        self.memory.append({
            "role": "user",
            "content": tool_results
        })

    def _execute_tool(self, name: str, params: Dict) -> Any:
        """Execute a tool (override in subclasses)."""
        # Call actual tool implementation
        pass
```

**Usage:**
```python
# Define tools
tools = [
    {
        "name": "calculate_component",
        "description": "Calculate component values",
        "input_schema": {...}
    }
]

# Create agent
agent = SimpleAgent(
    name="Calculator Agent",
    goal="Calculate electronic component values accurately",
    tools=tools
)

# Run task
result = agent.run(
    task="Calculate buck converter components for 12V→5V @ 3A"
)
```

---

## Exercise 7.2: Multi-Agent System

### Agent Roles

Different agents for different responsibilities:

**1. Designer Agent**
- Role: Create initial designs
- Tools: Component calculation, topology selection
- Output: Circuit design with values

**2. Verification Agent**
- Role: Verify design correctness
- Tools: Simulation, analysis
- Output: Verification report with issues

**3. Optimizer Agent**
- Role: Improve design
- Tools: Cost analysis, efficiency calculation
- Output: Optimized design

### Multi-Agent Architecture

**Python:**
```python
class MultiAgentSystem:
    """Orchestrates multiple specialized agents."""

    def __init__(self):
        self.agents = {}
        self.message_bus = []  # Agent communication

    def add_agent(self, agent):
        """Register an agent."""
        self.agents[agent.name] = agent

    def run_workflow(self, task: str):
        """Execute multi-agent workflow."""
        print(f"\n{'='*60}")
        print(f"MULTI-AGENT SYSTEM")
        print(f"{'='*60}")
        print(f"Task: {task}\n")

        # Step 1: Design
        design = self.agents["Designer"].run(task)
        self.broadcast("design_complete", design)

        # Step 2: Verify
        verification = self.agents["Verifier"].run(
            f"Verify this design: {design}"
        )
        self.broadcast("verification_complete", verification)

        # Step 3: Optimize (if needed)
        if "issues" in verification.lower():
            print("\n⚠️  Issues found, running optimizer...")
            optimized = self.agents["Optimizer"].run(
                f"Fix these issues: {verification}\nOriginal: {design}"
            )
            return optimized
        else:
            return design

    def broadcast(self, event: str, data: Any):
        """Send message to all agents."""
        self.message_bus.append({
            "event": event,
            "data": data,
            "timestamp": datetime.now()
        })
```

**See:** `examples/multi-agent/power_design_system.py` for complete implementation.

---

## Exercise 7.3: Agent Communication Protocols

### Message Passing

Agents communicate via structured messages:

```python
class AgentMessage:
    """Structured message between agents."""

    def __init__(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: Any
    ):
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.content = content
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
```

### Communication Patterns

**1. Request-Response**
```python
# Agent A requests information
request = AgentMessage(
    sender="Agent_A",
    recipient="Agent_B",
    message_type="request",
    content={"query": "What is the voltage?"}
)

# Agent B responds
response = AgentMessage(
    sender="Agent_B",
    recipient="Agent_A",
    message_type="response",
    content={"voltage": 5.0}
)
```

**2. Broadcast**
```python
# Agent announces to all
broadcast = AgentMessage(
    sender="Agent_A",
    recipient="*",  # All agents
    message_type="announcement",
    content={"status": "Design complete"}
)
```

**3. Publish-Subscribe**
```python
# Agents subscribe to topics
system.subscribe("design_updates", agent_b)
system.subscribe("design_updates", agent_c)

# Agent A publishes
system.publish("design_updates", design_data)
```

---

## Exercise 7.4: Agent Orchestration Patterns

### Sequential Orchestration

Agents run one after another:

```python
class SequentialOrchestrator:
    """Run agents in sequence."""

    def __init__(self, agents: List[Agent]):
        self.agents = agents

    def execute(self, initial_task: str):
        result = initial_task

        for agent in self.agents:
            print(f"\n→ Running {agent.name}...")
            result = agent.run(result)

        return result
```

**Use when:** Each step depends on previous step

### Parallel Orchestration

Agents run simultaneously:

```python
import asyncio

class ParallelOrchestrator:
    """Run agents in parallel."""

    async def execute(self, task: str):
        # Run all agents concurrently
        tasks = [
            asyncio.create_task(agent.run_async(task))
            for agent in self.agents
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        return results
```

**Use when:** Independent tasks can run concurrently

### Hierarchical Orchestration

Manager agent coordinates worker agents:

```python
class HierarchicalOrchestrator:
    """Manager delegates to workers."""

    def __init__(self, manager: Agent, workers: List[Agent]):
        self.manager = manager
        self.workers = workers

    def execute(self, task: str):
        # Manager creates plan
        plan = self.manager.plan(task)

        # Delegate subtasks
        results = {}
        for subtask in plan["subtasks"]:
            worker = self._select_worker(subtask)
            results[subtask["id"]] = worker.run(subtask["description"])

        # Manager synthesizes results
        final = self.manager.synthesize(results)
        return final
```

**Use when:** Complex tasks need decomposition and coordination

---

## Exercise 7.5: Power Electronics Multi-Agent Design System

### System Architecture

```
User: "Design 12V to 5V buck converter, 3A, 100kHz"
                    ↓
         ┌──────────────────────┐
         │  Orchestrator Agent  │
         └──────────────────────┘
                    ↓
      ┌─────────────┼─────────────┐
      ↓             ↓             ↓
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Designer │  │ Analyzer │  │ Verifier │
│  Agent   │  │  Agent   │  │  Agent   │
└──────────┘  └──────────┘  └──────────┘
      ↓             ↓             ↓
  Components    Simulation    Validation
      ↓             ↓             ↓
      └─────────────┼─────────────┘
                    ↓
         ┌──────────────────────┐
         │  Optimizer Agent     │
         └──────────────────────┘
                    ↓
         Final Design + BOM + Report
```

### Agent Responsibilities

**Designer Agent:**
```python
class DesignerAgent(Agent):
    """Designs circuit topology and calculates components."""

    def __init__(self):
        super().__init__(
            name="Designer",
            goal="Create functional circuit designs",
            tools=[
                calculate_buck_components,
                select_mosfet,
                calculate_thermal
            ]
        )

    def design_buck_converter(self, specs: Dict) -> Dict:
        """Design buck converter from specifications."""
        # Calculate duty cycle
        # Select components
        # Create BOM
        # Return design
```

**Analyzer Agent:**
```python
class AnalyzerAgent(Agent):
    """Simulates and analyzes circuit performance."""

    def __init__(self):
        super().__init__(
            name="Analyzer",
            goal="Verify circuit performance through simulation",
            tools=[
                simulate_circuit,
                calculate_efficiency,
                analyze_ripple
            ]
        )

    def analyze_design(self, design: Dict) -> Dict:
        """Analyze circuit design."""
        # Run SPICE simulation
        # Calculate efficiency
        # Measure ripple
        # Return analysis results
```

**Verifier Agent:**
```python
class VerifierAgent(Agent):
    """Validates design against requirements."""

    def __init__(self):
        super().__init__(
            name="Verifier",
            goal="Ensure design meets all specifications",
            tools=[
                check_component_ratings,
                verify_thermal,
                validate_specs
            ]
        )

    def verify_design(self, design: Dict, specs: Dict) -> Dict:
        """Verify design meets specifications."""
        # Check voltage/current ratings
        # Verify thermal management
        # Validate against specs
        # Return verification report
```

**Optimizer Agent:**
```python
class OptimizerAgent(Agent):
    """Optimizes design for cost, efficiency, or size."""

    def __init__(self):
        super().__init__(
            name="Optimizer",
            goal="Optimize design based on criteria",
            tools=[
                find_alternative_components,
                calculate_cost,
                optimize_efficiency
            ]
        )

    def optimize(self, design: Dict, criteria: str) -> Dict:
        """Optimize design based on criteria."""
        # Find cheaper components
        # Improve efficiency
        # Reduce size
        # Return optimized design
```

**See:** `examples/power-design/multi_agent_designer.py` for complete implementation.

---

## Agent Memory and Learning

### Short-Term Memory

Conversation history for current task:

```python
class Agent:
    def __init__(self):
        self.memory = []  # Short-term memory

    def remember(self, role: str, content: str):
        """Add to short-term memory."""
        self.memory.append({
            "role": role,
            "content": content
        })
```

### Long-Term Memory

Persistent storage across tasks:

```python
import json

class Agent:
    def __init__(self, memory_file: str):
        self.long_term_memory = self._load_memory(memory_file)

    def _load_memory(self, file: str) -> Dict:
        """Load long-term memory from disk."""
        if os.path.exists(file):
            with open(file, 'r') as f:
                return json.load(f)
        return {}

    def learn(self, key: str, value: Any):
        """Store in long-term memory."""
        self.long_term_memory[key] = value
        self._save_memory()

    def recall(self, key: str) -> Any:
        """Retrieve from long-term memory."""
        return self.long_term_memory.get(key)
```

### Retrieval-Augmented Memory

Use RAG for relevant memory retrieval:

```python
class RAGMemoryAgent(Agent):
    """Agent with RAG-based memory."""

    def __init__(self):
        super().__init__()
        self.vector_db = chromadb.Client()
        self.memories = self.vector_db.create_collection("memories")

    def remember_experience(self, experience: str, outcome: str):
        """Store experience with embedding."""
        self.memories.add(
            documents=[f"Experience: {experience}\nOutcome: {outcome}"],
            ids=[str(uuid.uuid4())]
        )

    def recall_similar(self, situation: str, n: int = 3):
        """Recall similar past experiences."""
        results = self.memories.query(
            query_texts=[situation],
            n_results=n
        )
        return results['documents']
```

---

## Error Handling and Recovery

### Retry Logic

```python
class RobustAgent(Agent):
    """Agent with automatic retry."""

    def run(self, task: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                return super().run(task)
            except Exception as e:
                print(f"⚠️  Attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    print("   Retrying...")
                else:
                    print("   Max retries reached")
                    raise
```

### Fallback Strategies

```python
class FallbackAgent(Agent):
    """Agent with fallback options."""

    def run(self, task: str):
        try:
            # Try primary method
            return self._primary_strategy(task)
        except Exception as e:
            print(f"⚠️  Primary failed: {e}")
            print("   Using fallback strategy...")
            return self._fallback_strategy(task)

    def _fallback_strategy(self, task: str):
        """Simpler, more reliable approach."""
        # Use cached results
        # Use simpler model
        # Use predefined templates
```

### Agent Health Monitoring

```python
class MonitoredAgent(Agent):
    """Agent with health monitoring."""

    def __init__(self):
        super().__init__()
        self.health = {
            "status": "healthy",
            "success_rate": 1.0,
            "total_tasks": 0,
            "failed_tasks": 0
        }

    def run(self, task: str):
        self.health["total_tasks"] += 1

        try:
            result = super().run(task)
            self._update_health(success=True)
            return result
        except Exception as e:
            self.health["failed_tasks"] += 1
            self._update_health(success=False)
            raise

    def _update_health(self, success: bool):
        """Update health metrics."""
        self.health["success_rate"] = (
            (self.health["total_tasks"] - self.health["failed_tasks"]) /
            self.health["total_tasks"]
        )

        if self.health["success_rate"] < 0.5:
            self.health["status"] = "degraded"
        elif self.health["success_rate"] < 0.8:
            self.health["status"] = "warning"
        else:
            self.health["status"] = "healthy"
```

---

## Performance Optimization

### Caching Agent Results

```python
from functools import lru_cache

class CachedAgent(Agent):
    """Agent with result caching."""

    @lru_cache(maxsize=100)
    def run(self, task: str):
        """Cached execution."""
        return super().run(task)
```

### Parallel Agent Execution

```python
import asyncio

class ParallelAgentSystem:
    """Run multiple agents in parallel."""

    async def run_parallel(self, tasks: List[str]):
        """Execute tasks in parallel."""
        agent_tasks = [
            asyncio.create_task(agent.run_async(task))
            for agent, task in zip(self.agents, tasks)
        ]

        results = await asyncio.gather(*agent_tasks)
        return results
```

### Cost Optimization

```python
class CostOptimizedAgent(Agent):
    """Agent that optimizes API costs."""

    def __init__(self):
        super().__init__()
        self.use_haiku_for_simple_tasks = True
        self.cache_system_prompts = True

    def run(self, task: str):
        # Use cheaper model for simple tasks
        if self._is_simple(task) and self.use_haiku_for_simple_tasks:
            model = "claude-3-5-haiku-20241022"
        else:
            model = "claude-3-5-sonnet-20241022"

        # Use prompt caching
        # ...
```

---

## Real-World Applications

### 1. Automated Circuit Design

```python
# User provides specs
specs = {
    "input_voltage": 12,
    "output_voltage": 5,
    "output_current": 3,
    "efficiency_target": 0.90
}

# Multi-agent system designs
system = PowerDesignSystem()
result = system.design_converter(specs)

# Output: Complete design with:
# - Component values and part numbers
# - Simulation results
# - Verification report
# - BOM with pricing
# - PCB layout suggestions
```

### 2. Collaborative Code Review

```python
# Multiple agents review different aspects
reviewers = {
    "security": SecurityAgent(),
    "performance": PerformanceAgent(),
    "style": StyleAgent()
}

for agent in reviewers.values():
    review = agent.review_code(code)
    print(f"{agent.name}: {review}")
```

### 3. Research Assistant

```python
# Agents collaborate on research
research_team = MultiAgentSystem()
research_team.add_agent(SearchAgent())      # Find papers
research_team.add_agent(SummaryAgent())     # Summarize findings
research_team.add_agent(AnalysisAgent())    # Analyze data
research_team.add_agent(WriterAgent())      # Write report

report = research_team.research("Buck converter efficiency trends")
```

---

## Best Practices

### 1. Clear Agent Responsibilities

```python
# ✅ Good: Specific role
class ComponentSelector(Agent):
    """Selects optimal components for circuits."""

# ❌ Bad: Too broad
class GeneralDesigner(Agent):
    """Does everything related to design."""
```

### 2. Explicit Communication

```python
# ✅ Good: Structured messages
message = {
    "type": "design_complete",
    "data": design,
    "metadata": {"version": 1, "timestamp": now}
}

# ❌ Bad: Implicit communication
global_variable = design
```

### 3. Stateless When Possible

```python
# ✅ Good: Stateless operation
def analyze(design: Dict) -> Dict:
    return analysis_result

# ⚠️  Use carefully: Stateful operation
self.previous_designs.append(design)
```

### 4. Monitoring and Logging

```python
# Always log agent actions
logger.info(f"Agent {self.name} starting task: {task}")
logger.info(f"Agent {self.name} completed in {duration}s")
logger.error(f"Agent {self.name} failed: {error}")
```

---

## Self-Assessment

Before completing this module, ensure you can:

- [ ] Explain autonomous agent architecture
- [ ] Create single-purpose agents with tools
- [ ] Build multi-agent systems with communication
- [ ] Implement agent orchestration patterns
- [ ] Handle agent errors and recovery
- [ ] Optimize agent performance and cost
- [ ] Design specialized agent systems
- [ ] Monitor agent health and metrics

---

## Additional Resources

- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- [MetaGPT](https://github.com/geekan/MetaGPT)
- [Anthropic Tool Use Guide](https://docs.anthropic.com/claude/docs/tool-use)

---

## Conclusion

Congratulations! You've completed the comprehensive LLM API tutorial covering:

1. **Basic API Usage** - Claude and OpenAI fundamentals
2. **Token Optimization** - Cost management and efficiency
3. **Advanced Features** - Vision, tools, function calling
4. **RAG** - Knowledge retrieval and datasheet lookup
5. **MCP** - Standardized tool integration
6. **CLI Integration** - Command-line tools for all providers
7. **Agents** - Autonomous systems and multi-agent workflows

You now have the skills to build sophisticated AI applications for power electronics and beyond!

---

**Questions or issues?** Open a GitHub issue or check the examples.
