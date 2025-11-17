#!/usr/bin/env python3
"""
Basic Autonomous Agent Example

Demonstrates a simple autonomous agent that can:
- Perceive: Receive tasks and observe results
- Reason: Use Claude to plan and make decisions
- Act: Execute tools to accomplish goals
- Observe: Track progress and adjust

This agent uses Claude's tool use capabilities to autonomously
complete tasks through multiple iterations.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


# Define tools the agent can use
AGENT_TOOLS = [
    {
        "name": "calculate",
        "description": "Perform mathematical calculations. Supports basic arithmetic, power, square root, and common functions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '(5 + 3) * 2', 'sqrt(16)', '2**8')"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "search_components",
        "description": "Search for electronic components with specifications. Returns component recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "component_type": {
                    "type": "string",
                    "description": "Type of component (mosfet, resistor, capacitor, inductor, diode, etc.)"
                },
                "specifications": {
                    "type": "string",
                    "description": "Required specifications (e.g., '100V 10A N-channel', '10uF 50V ceramic')"
                }
            },
            "required": ["component_type", "specifications"]
        }
    },
    {
        "name": "save_to_file",
        "description": "Save text content to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the file to save"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "finish",
        "description": "Indicate that the task is complete and provide final results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Final result or summary of completed task"
                }
            },
            "required": ["result"]
        }
    }
]


class BasicAgent:
    """Simple autonomous agent using Claude."""

    def __init__(self, name: str = "Agent", model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the agent.

        Args:
            name: Agent name for identification
            model: Claude model to use
        """
        self.name = name
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.conversation_history: List[Dict] = []
        self.iteration_count = 0

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result as string
        """
        print(f"  🔧 Executing tool: {tool_name}")
        print(f"     Input: {json.dumps(tool_input, indent=6)}")

        try:
            if tool_name == "calculate":
                # Safe evaluation of mathematical expressions
                import math
                allowed_names = {
                    "sqrt": math.sqrt,
                    "pow": pow,
                    "abs": abs,
                    "round": round,
                    "pi": math.pi,
                    "e": math.e,
                    "sin": math.sin,
                    "cos": math.cos,
                    "tan": math.tan,
                    "log": math.log,
                    "log10": math.log10,
                }
                result = eval(tool_input["expression"], {"__builtins__": {}}, allowed_names)
                return f"Result: {result}"

            elif tool_name == "search_components":
                # Simulate component search (in real application, this would query a database or API)
                component_type = tool_input["component_type"].lower()
                specs = tool_input["specifications"]

                # Mock component database
                components = {
                    "mosfet": [
                        "IRF540N (100V, 33A, 44mΩ) - $1.50",
                        "IRFZ44N (55V, 49A, 17.5mΩ) - $1.20",
                        "IPP200N25N3 (250V, 24A, 85mΩ) - $2.80"
                    ],
                    "resistor": [
                        "Standard 1/4W carbon film - $0.05",
                        "1W metal film - $0.15",
                        "5W wirewound - $0.50"
                    ],
                    "capacitor": [
                        "Ceramic X7R 10uF 50V - $0.20",
                        "Electrolytic 100uF 50V - $0.15",
                        "Film 1uF 100V - $0.30"
                    ]
                }

                results = components.get(component_type, ["No components found"])
                return f"Found components for {component_type} ({specs}):\n" + "\n".join(f"  - {c}" for c in results)

            elif tool_name == "save_to_file":
                filename = tool_input["filename"]
                content = tool_input["content"]

                # Save to outputs directory
                output_dir = Path(__file__).parent / "outputs"
                output_dir.mkdir(exist_ok=True)
                filepath = output_dir / filename

                with open(filepath, "w") as f:
                    f.write(content)

                return f"Saved to {filepath}"

            elif tool_name == "finish":
                return tool_input["result"]

            else:
                return f"Error: Unknown tool '{tool_name}'"

        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def run(self, task: str, max_iterations: int = 10) -> str:
        """
        Run the agent to accomplish a task autonomously.

        Args:
            task: Task description for the agent
            max_iterations: Maximum number of reasoning iterations

        Returns:
            Final result from the agent
        """
        print(f"\n{'='*70}")
        print(f"🤖 {self.name} Starting Task")
        print(f"{'='*70}")
        print(f"Task: {task}\n")

        # Initialize conversation with the task
        self.conversation_history = [
            {
                "role": "user",
                "content": f"""You are an autonomous agent helping with this task:

{task}

You have access to tools to help accomplish this task. Think step-by-step:
1. Break down the task into steps
2. Use available tools as needed
3. When complete, use the 'finish' tool with your final result

Be thorough and precise. Show your reasoning."""
            }
        ]

        self.iteration_count = 0

        while self.iteration_count < max_iterations:
            self.iteration_count += 1
            print(f"\n--- Iteration {self.iteration_count} ---")

            try:
                # Get response from Claude
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    tools=AGENT_TOOLS,
                    messages=self.conversation_history
                )

                # Display reasoning
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"\n💭 Reasoning:\n{block.text}")

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Agent finished without using tools
                    final_text = next((block.text for block in response.content if hasattr(block, "text")), "Task completed")
                    print(f"\n✅ Task Complete (no tools needed)\n")
                    return final_text

                elif response.stop_reason == "tool_use":
                    # Agent wants to use tools
                    tool_results = []

                    for block in response.content:
                        if block.type == "tool_use":
                            # Execute the tool
                            result = self._execute_tool(block.name, block.input)
                            print(f"     Result: {result}\n")

                            # Check if this was the finish tool
                            if block.name == "finish":
                                print(f"\n{'='*70}")
                                print(f"✅ {self.name} Task Complete!")
                                print(f"{'='*70}")
                                print(f"Iterations: {self.iteration_count}")
                                print(f"Result:\n{result}\n")
                                return result

                            # Prepare tool result for next iteration
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })

                    # Add assistant response and tool results to conversation
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                else:
                    # Unexpected stop reason
                    print(f"\n⚠️ Unexpected stop reason: {response.stop_reason}")
                    break

            except Exception as e:
                print(f"\n❌ Error: {e}")
                return f"Error: {e}"

        # Max iterations reached
        print(f"\n⚠️ Maximum iterations ({max_iterations}) reached")
        return "Task incomplete - maximum iterations reached"


def main():
    """Run example tasks with the basic agent."""

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found in environment")
        print("   Please set your API key in .env file")
        sys.exit(1)

    # Create agent
    agent = BasicAgent(name="PowerAgent")

    # Example 1: Simple calculation
    print("\n" + "="*70)
    print("EXAMPLE 1: Mathematical Calculation")
    print("="*70)
    result1 = agent.run(
        "Calculate the power dissipation in a resistor with 5V across it and 100mA current. "
        "Then determine what standard power rating to use (with 2x safety factor)."
    )

    # Example 2: Component search
    print("\n\n" + "="*70)
    print("EXAMPLE 2: Component Search")
    print("="*70)
    result2 = agent.run(
        "Find suitable MOSFETs for a 24V motor driver that needs to handle 10A continuous current. "
        "Search for N-channel MOSFETs and recommend the best option."
    )

    # Example 3: Design calculation with file save
    print("\n\n" + "="*70)
    print("EXAMPLE 3: Design Calculation with File Save")
    print("="*70)
    result3 = agent.run(
        "Design an LED current limiting resistor for a 12V supply with a red LED "
        "(forward voltage 2.1V, desired current 20mA). Calculate the resistor value, "
        "power rating, and save the design to a file called 'led_resistor_design.txt'."
    )

    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == "__main__":
    main()
