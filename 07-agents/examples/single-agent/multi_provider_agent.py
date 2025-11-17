#!/usr/bin/env python3
"""
Multi-Provider Agent Example

Demonstrates an agent that can work with multiple AI providers:
- Claude (Anthropic)
- OpenAI (GPT-4, GPT-3.5)
- Allows switching between providers
- Compares responses from different providers

This shows how to build provider-agnostic agent systems.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv

# Import both providers
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️ Anthropic not available")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available")

load_dotenv()


class Provider(Enum):
    """AI provider options."""
    CLAUDE = "claude"
    OPENAI = "openai"


# Tool definitions (compatible with both Claude and OpenAI format)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_power",
            "description": "Calculate electrical power given voltage and current",
            "parameters": {
                "type": "object",
                "properties": {
                    "voltage": {
                        "type": "number",
                        "description": "Voltage in volts"
                    },
                    "current": {
                        "type": "number",
                        "description": "Current in amps"
                    }
                },
                "required": ["voltage", "current"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_resistor",
            "description": "Calculate resistor value for LED current limiting",
            "parameters": {
                "type": "object",
                "properties": {
                    "supply_voltage": {
                        "type": "number",
                        "description": "Supply voltage in volts"
                    },
                    "led_forward_voltage": {
                        "type": "number",
                        "description": "LED forward voltage in volts"
                    },
                    "led_current_ma": {
                        "type": "number",
                        "description": "Desired LED current in milliamps"
                    }
                },
                "required": ["supply_voltage", "led_forward_voltage", "led_current_ma"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Complete the task with final result",
            "parameters": {
                "type": "object",
                "properties": {
                    "result": {
                        "type": "string",
                        "description": "Final result or answer"
                    }
                },
                "required": ["result"]
            }
        }
    }
]


class MultiProviderAgent:
    """Agent that can use multiple AI providers."""

    def __init__(self, name: str = "MultiAgent", default_provider: Provider = Provider.CLAUDE):
        """
        Initialize multi-provider agent.

        Args:
            name: Agent name
            default_provider: Default AI provider to use
        """
        self.name = name
        self.default_provider = default_provider

        # Initialize clients
        self.claude_client = None
        self.openai_client = None

        if CLAUDE_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            self.claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            print("✓ Claude available")

        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            print("✓ OpenAI available")

        if not self.claude_client and not self.openai_client:
            raise ValueError("No AI providers available. Check API keys.")

    def _execute_tool(self, tool_name: str, tool_args: Dict) -> str:
        """Execute a tool function."""
        print(f"  🔧 {tool_name}({json.dumps(tool_args)})")

        try:
            if tool_name == "calculate_power":
                power = tool_args["voltage"] * tool_args["current"]
                return f"Power: {power}W"

            elif tool_name == "calculate_resistor":
                voltage_drop = tool_args["supply_voltage"] - tool_args["led_forward_voltage"]
                current_amps = tool_args["led_current_ma"] / 1000
                resistance = voltage_drop / current_amps
                power = voltage_drop * current_amps

                return f"Resistor: {resistance:.1f}Ω, Power: {power:.3f}W"

            elif tool_name == "finish":
                return tool_args["result"]

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Error: {e}"

    def _run_claude(self, task: str, max_iterations: int = 10) -> str:
        """Run task using Claude."""
        print(f"\n🔵 Using Claude")

        if not self.claude_client:
            return "Claude not available"

        # Convert tools to Claude format
        claude_tools = []
        for tool in TOOLS:
            func = tool["function"]
            claude_tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"]
            })

        messages = [{
            "role": "user",
            "content": f"Task: {task}\n\nUse available tools to complete this task, then use 'finish' with your final result."
        }]

        for iteration in range(max_iterations):
            print(f"  Iteration {iteration + 1}")

            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                tools=claude_tools,
                messages=messages
            )

            # Check for text content
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    print(f"    💭 {block.text[:100]}")

            if response.stop_reason == "end_turn":
                # No tools used, return text
                text = next((b.text for b in response.content if hasattr(b, "text")), "Done")
                return text

            elif response.stop_reason == "tool_use":
                # Process tool calls
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        result = self._execute_tool(block.name, block.input)
                        print(f"    ✓ {result}")

                        if block.name == "finish":
                            return result

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Continue conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

        return "Max iterations reached"

    def _run_openai(self, task: str, max_iterations: int = 10) -> str:
        """Run task using OpenAI."""
        print(f"\n🟢 Using OpenAI")

        if not self.openai_client:
            return "OpenAI not available"

        messages = [{
            "role": "user",
            "content": f"Task: {task}\n\nUse available tools to complete this task, then use 'finish' with your final result."
        }]

        for iteration in range(max_iterations):
            print(f"  Iteration {iteration + 1}")

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto"
            )

            message = response.choices[0].message

            # Check for text content
            if message.content:
                print(f"    💭 {message.content[:100]}")

            # Check if finished
            if not message.tool_calls:
                return message.content or "Done"

            # Process tool calls
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                result = self._execute_tool(func_name, func_args)
                print(f"    ✓ {result}")

                if func_name == "finish":
                    return result

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": result
                })

        return "Max iterations reached"

    def run(self, task: str, provider: Optional[Provider] = None) -> str:
        """
        Run task with specified provider.

        Args:
            task: Task description
            provider: Provider to use (None = default)

        Returns:
            Task result
        """
        provider = provider or self.default_provider

        print(f"\n{'='*70}")
        print(f"🤖 {self.name} - Task")
        print(f"{'='*70}")
        print(f"Task: {task}")

        if provider == Provider.CLAUDE:
            result = self._run_claude(task)
        elif provider == Provider.OPENAI:
            result = self._run_openai(task)
        else:
            return "Invalid provider"

        print(f"\n✅ Result: {result}")
        return result

    def compare_providers(self, task: str) -> Dict[str, str]:
        """
        Run same task with both providers and compare.

        Args:
            task: Task to run

        Returns:
            Results from both providers
        """
        print(f"\n{'='*70}")
        print(f"🔄 Comparing Providers")
        print(f"{'='*70}")

        results = {}

        if self.claude_client:
            results["claude"] = self.run(task, Provider.CLAUDE)

        if self.openai_client:
            results["openai"] = self.run(task, Provider.OPENAI)

        print(f"\n{'='*70}")
        print("Comparison Summary")
        print(f"{'='*70}")
        for provider, result in results.items():
            print(f"\n{provider.upper()}:")
            print(f"  {result[:200]}")

        return results


def main():
    """Demonstrate multi-provider agent."""

    print("\n" + "="*70)
    print("Multi-Provider Agent Demo")
    print("="*70)

    # Create agent
    agent = MultiProviderAgent(name="FlexiAgent")

    # Example 1: Run with Claude
    if agent.claude_client:
        print("\n\n" + "="*70)
        print("EXAMPLE 1: Using Claude")
        print("="*70)
        agent.run(
            "Calculate the power dissipation in a 47Ω resistor with 12V across it.",
            provider=Provider.CLAUDE
        )

    # Example 2: Run with OpenAI
    if agent.openai_client:
        print("\n\n" + "="*70)
        print("EXAMPLE 2: Using OpenAI")
        print("="*70)
        agent.run(
            "Calculate the current limiting resistor for a red LED (Vf=2.1V, If=20mA) "
            "powered by a 9V battery.",
            provider=Provider.OPENAI
        )

    # Example 3: Compare providers
    if agent.claude_client and agent.openai_client:
        print("\n\n" + "="*70)
        print("EXAMPLE 3: Provider Comparison")
        print("="*70)
        agent.compare_providers(
            "Calculate the resistor needed for a 5V, 100mA LED powered from 12V. "
            "Also calculate the power rating needed."
        )

    print("\n" + "="*70)
    print("Multi-provider demo complete!")
    print("="*70)


if __name__ == "__main__":
    main()
