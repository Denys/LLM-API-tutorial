#!/usr/bin/env python3
"""
Agent with Memory Example

Demonstrates an autonomous agent with persistent memory capabilities:
- Short-term memory: Recent conversation context
- Long-term memory: Important facts stored persistently
- Memory retrieval: Search and recall relevant information
- Learning: Update knowledge base from interactions

This shows how agents can maintain context across sessions and learn from experience.
"""

import os
import sys
import json
import pickle
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


class MemorySystem:
    """Memory management system for agents."""

    def __init__(self, memory_file: Optional[Path] = None):
        """
        Initialize memory system.

        Args:
            memory_file: Path to persistent memory storage file
        """
        self.short_term_memory: List[Dict] = []  # Recent interactions
        self.long_term_memory: List[Dict] = []   # Important facts/learnings
        self.memory_file = memory_file or Path(__file__).parent / "memory" / "agent_memory.pkl"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing long-term memory if available
        self._load_memory()

    def _load_memory(self):
        """Load long-term memory from disk."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "rb") as f:
                    self.long_term_memory = pickle.load(f)
                print(f"📚 Loaded {len(self.long_term_memory)} memories from {self.memory_file}")
            except Exception as e:
                print(f"⚠️ Could not load memory: {e}")
                self.long_term_memory = []

    def _save_memory(self):
        """Save long-term memory to disk."""
        try:
            with open(self.memory_file, "wb") as f:
                pickle.dump(self.long_term_memory, f)
            print(f"💾 Saved {len(self.long_term_memory)} memories to {self.memory_file}")
        except Exception as e:
            print(f"⚠️ Could not save memory: {e}")

    def add_to_short_term(self, memory: Dict):
        """Add item to short-term memory (conversation context)."""
        self.short_term_memory.append({
            **memory,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only recent items (last 20)
        if len(self.short_term_memory) > 20:
            self.short_term_memory = self.short_term_memory[-20:]

    def add_to_long_term(self, memory: Dict):
        """Add important fact to long-term memory."""
        memory_entry = {
            **memory,
            "timestamp": datetime.now().isoformat(),
            "access_count": 0
        }
        self.long_term_memory.append(memory_entry)
        self._save_memory()

    def search_long_term(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search long-term memory for relevant information.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of relevant memories
        """
        # Simple keyword-based search (in production, use embeddings)
        query_lower = query.lower()
        scored_memories = []

        for memory in self.long_term_memory:
            # Score based on keyword matches
            content = str(memory).lower()
            score = sum(1 for word in query_lower.split() if word in content)

            if score > 0:
                scored_memories.append((score, memory))

        # Sort by score and return top_k
        scored_memories.sort(reverse=True, key=lambda x: x[0])
        results = [mem for score, mem in scored_memories[:top_k]]

        # Update access counts
        for mem in results:
            mem["access_count"] = mem.get("access_count", 0) + 1

        if results:
            self._save_memory()

        return results

    def get_context_summary(self) -> str:
        """Get summary of current context for agent."""
        summary = []

        # Recent short-term memories
        if self.short_term_memory:
            summary.append("Recent Context:")
            for mem in self.short_term_memory[-5:]:
                summary.append(f"  - {mem.get('summary', str(mem)[:100])}")

        # Long-term memory stats
        summary.append(f"\nKnowledge Base: {len(self.long_term_memory)} stored facts")

        return "\n".join(summary)


# Agent tools including memory operations
MEMORY_AGENT_TOOLS = [
    {
        "name": "store_fact",
        "description": "Store an important fact or learning in long-term memory for future recall.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category of the fact (component, calculation, design_rule, etc.)"
                },
                "fact": {
                    "type": "string",
                    "description": "The fact or learning to store"
                },
                "context": {
                    "type": "string",
                    "description": "Context or application of this fact"
                }
            },
            "required": ["category", "fact"]
        }
    },
    {
        "name": "recall_memory",
        "description": "Search long-term memory for relevant information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in memory"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate",
        "description": "Perform mathematical calculations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "finish",
        "description": "Complete the task and provide final result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Final result or summary"
                }
            },
            "required": ["result"]
        }
    }
]


class MemoryAgent:
    """Autonomous agent with persistent memory capabilities."""

    def __init__(self, name: str = "MemoryAgent", model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize agent with memory.

        Args:
            name: Agent name
            model: Claude model to use
        """
        self.name = name
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.memory = MemorySystem()
        self.conversation_history: List[Dict] = []

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """Execute tool and return result."""
        print(f"  🔧 {tool_name}: {json.dumps(tool_input, indent=6)}")

        try:
            if tool_name == "store_fact":
                # Store in long-term memory
                self.memory.add_to_long_term({
                    "category": tool_input["category"],
                    "fact": tool_input["fact"],
                    "context": tool_input.get("context", "")
                })
                return f"Stored fact in {tool_input['category']} category"

            elif tool_name == "recall_memory":
                # Search memory
                results = self.memory.search_long_term(tool_input["query"])
                if results:
                    response = f"Found {len(results)} relevant memories:\n"
                    for i, mem in enumerate(results, 1):
                        response += f"\n{i}. [{mem.get('category', 'general')}] {mem.get('fact', str(mem))}"
                        if mem.get('context'):
                            response += f"\n   Context: {mem['context']}"
                        response += f"\n   (accessed {mem.get('access_count', 0)} times)"
                    return response
                else:
                    return "No relevant memories found"

            elif tool_name == "calculate":
                import math
                allowed_names = {
                    "sqrt": math.sqrt, "pow": pow, "abs": abs, "round": round,
                    "pi": math.pi, "e": math.e, "sin": math.sin, "cos": math.cos,
                    "tan": math.tan, "log": math.log, "log10": math.log10,
                }
                result = eval(tool_input["expression"], {"__builtins__": {}}, allowed_names)
                return f"Result: {result}"

            elif tool_name == "finish":
                return tool_input["result"]

            else:
                return f"Error: Unknown tool '{tool_name}'"

        except Exception as e:
            return f"Error: {str(e)}"

    def run(self, task: str, max_iterations: int = 15) -> str:
        """
        Run agent on a task with memory support.

        Args:
            task: Task description
            max_iterations: Maximum reasoning iterations

        Returns:
            Final result
        """
        print(f"\n{'='*70}")
        print(f"🧠 {self.name} Starting Task (with Memory)")
        print(f"{'='*70}")
        print(f"Task: {task}")
        print(f"\n{self.memory.get_context_summary()}\n")

        # Initialize conversation
        self.conversation_history = [
            {
                "role": "user",
                "content": f"""You are an autonomous agent with memory capabilities.

Current task: {task}

You can:
- store_fact: Save important learnings to long-term memory
- recall_memory: Search your memory for relevant information
- calculate: Perform calculations
- finish: Complete the task

Use your memory to:
1. Recall relevant past knowledge before starting
2. Store new learnings as you work
3. Build a knowledge base over time

{self.memory.get_context_summary()}

Think step-by-step and use your tools effectively."""
            }
        ]

        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    tools=MEMORY_AGENT_TOOLS,
                    messages=self.conversation_history
                )

                # Show reasoning
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"\n💭 {block.text}")
                        # Store in short-term memory
                        self.memory.add_to_short_term({
                            "type": "reasoning",
                            "summary": block.text[:200]
                        })

                if response.stop_reason == "end_turn":
                    final_text = next((b.text for b in response.content if hasattr(b, "text")), "Complete")
                    print(f"\n✅ Task Complete\n")
                    return final_text

                elif response.stop_reason == "tool_use":
                    tool_results = []

                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._execute_tool(block.name, block.input)
                            print(f"     ✓ {result}\n")

                            # Store tool use in short-term memory
                            self.memory.add_to_short_term({
                                "type": "tool_use",
                                "summary": f"{block.name}: {str(block.input)[:100]}"
                            })

                            if block.name == "finish":
                                print(f"\n{'='*70}")
                                print(f"✅ {self.name} Complete!")
                                print(f"{'='*70}")
                                print(f"Result:\n{result}\n")
                                return result

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })

                    # Continue conversation
                    self.conversation_history.append({"role": "assistant", "content": response.content})
                    self.conversation_history.append({"role": "user", "content": tool_results})

            except Exception as e:
                print(f"\n❌ Error: {e}")
                return f"Error: {e}"

        return "Maximum iterations reached"


def main():
    """Demonstrate agent with memory."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        sys.exit(1)

    agent = MemoryAgent(name="LearningAgent")

    # Task 1: Learn about buck converters
    print("\n" + "="*70)
    print("TASK 1: Learn and Store Knowledge")
    print("="*70)
    agent.run(
        "Calculate the duty cycle for a buck converter with 12V input and 5V output. "
        "The duty cycle formula is D = Vout/Vin. "
        "Store this formula and the result in your long-term memory for future use."
    )

    # Task 2: Use previously learned knowledge
    print("\n\n" + "="*70)
    print("TASK 2: Recall and Apply Knowledge")
    print("="*70)
    agent.run(
        "I need to design a buck converter with 24V input and 3.3V output. "
        "Try to recall the buck converter formula from your memory, then calculate the duty cycle."
    )

    # Task 3: Build on knowledge
    print("\n\n" + "="*70)
    print("TASK 3: Expand Knowledge Base")
    print("="*70)
    agent.run(
        "Recall what you know about buck converters. Then calculate the duty cycle for "
        "a 48V to 12V buck converter. Store this new result as well."
    )

    print("\n" + "="*70)
    print("Memory demonstration complete!")
    print("="*70)
    print("\nThe agent now has persistent knowledge about buck converters")
    print("that will be available in future sessions.")


if __name__ == "__main__":
    main()
