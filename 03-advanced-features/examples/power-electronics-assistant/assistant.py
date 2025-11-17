#!/usr/bin/env python3
"""
Power Electronics Assistant - Claude AI with Tool Use

This assistant helps with power electronics calculations:
- Resistor power calculations
- Capacitor value calculations
- MOSFET selection
- Thermal analysis
- LED current limiting
- Buck/Boost converter design

Features:
- Claude API integration with tool use
- Automatic tool calling
- Conversation history
- Cost tracking
- Support for both Claude and OpenAI

Usage:
    python assistant.py
    python assistant.py --provider openai
"""

import os
import json
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

from tools import (
    PowerElectronicsTools,
    POWER_TOOLS_CLAUDE,
    POWER_TOOLS_OPENAI
)

load_dotenv()


class PowerElectronicsAssistant:
    """AI assistant for power electronics with tool use."""

    def __init__(self, provider: str = "claude", model: Optional[str] = None):
        """
        Initialize the assistant.

        Args:
            provider: "claude" or "openai"
            model: Model name (optional, uses defaults if not specified)
        """
        self.provider = provider.lower()

        if self.provider == "claude":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = model or "claude-3-5-sonnet-20241022"
            self.tools = POWER_TOOLS_CLAUDE
        elif self.provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = model or "gpt-4-turbo-preview"
            self.tools = POWER_TOOLS_OPENAI
        else:
            raise ValueError(f"Unknown provider: {provider}")

        self.conversation_history = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.tool_use_count = 0

        # System prompt
        self.system_prompt = """You are an expert power electronics engineer assistant.
You help users with circuit design calculations, component selection, and troubleshooting.

When users ask questions about power electronics, use the available tools to perform calculations.
Always explain your reasoning and provide practical recommendations.

Available tools:
1. calculate_resistor_power - Calculate power dissipation in resistors
2. calculate_capacitor_value - Calculate capacitor values for circuits
3. select_mosfet - Recommend MOSFET components
4. calculate_thermal_resistance - Thermal analysis for components
5. calculate_led_resistor - LED current limiting resistor calculations
6. design_buck_converter - Buck converter design calculations

Provide clear, practical advice with safety considerations."""

    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        Send a message to the assistant and get a response.

        Args:
            user_message: User's question or request

        Returns:
            Dictionary with response and metadata
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        if self.provider == "claude":
            return self._chat_claude()
        else:
            return self._chat_openai()

    def _chat_claude(self) -> Dict[str, Any]:
        """Handle chat with Claude API."""
        # Initial API call
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt,
            tools=self.tools,
            messages=self.conversation_history
        )

        # Track usage
        self.total_input_tokens += response.usage.input_tokens
        self.total_output_tokens += response.usage.output_tokens

        # Process response
        assistant_messages = []
        tool_results = []

        # Check if Claude wants to use tools
        while response.stop_reason == "tool_use":
            # Extract tool uses
            for content_block in response.content:
                if content_block.type == "text":
                    assistant_messages.append(content_block.text)
                elif content_block.type == "tool_use":
                    # Execute tool
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_use_id = content_block.id

                    self.tool_use_count += 1

                    print(f"\n🔧 Using tool: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input, indent=2)}")

                    # Call the actual tool function
                    result = self._execute_tool(tool_name, tool_input)

                    print(f"   Result: {json.dumps(result, indent=2)}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result)
                    })

            # Add assistant's response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            # Add tool results to history
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # Continue conversation with tool results
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                tools=self.tools,
                messages=self.conversation_history
            )

            # Track usage
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

            # Reset for next iteration
            assistant_messages = []
            tool_results = []

        # Extract final text response
        final_response = ""
        for content_block in response.content:
            if content_block.type == "text":
                final_response += content_block.text

        # Add final response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        return {
            "response": final_response,
            "stop_reason": response.stop_reason,
            "tool_uses": self.tool_use_count
        }

    def _chat_openai(self) -> Dict[str, Any]:
        """Handle chat with OpenAI API."""
        # Convert conversation history to OpenAI format
        messages = [{"role": "system", "content": self.system_prompt}]

        for msg in self.conversation_history:
            if msg["role"] in ["user", "assistant"]:
                # Simple text messages
                if isinstance(msg["content"], str):
                    messages.append({"role": msg["role"], "content": msg["content"]})
                # Handle tool calls and results (simplified for now)
                elif isinstance(msg["content"], list):
                    # Skip complex multi-part messages for OpenAI compatibility
                    pass

        # Initial API call
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2048,
            messages=messages,
            functions=self.tools
        )

        # Track usage
        self.total_input_tokens += response.usage.prompt_tokens
        self.total_output_tokens += response.usage.completion_tokens

        assistant_message = response.choices[0].message

        # Check if function calling is requested
        while assistant_message.function_call:
            function_name = assistant_message.function_call.name
            function_args = json.loads(assistant_message.function_call.arguments)

            self.tool_use_count += 1

            print(f"\n🔧 Using function: {function_name}")
            print(f"   Args: {json.dumps(function_args, indent=2)}")

            # Execute function
            result = self._execute_tool(function_name, function_args)
            print(f"   Result: {json.dumps(result, indent=2)}")

            # Add function call to messages
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": function_name,
                    "arguments": json.dumps(function_args)
                }
            })

            # Add function result
            messages.append({
                "role": "function",
                "name": function_name,
                "content": json.dumps(result)
            })

            # Continue conversation
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=messages,
                functions=self.tools
            )

            # Track usage
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

            assistant_message = response.choices[0].message

        # Get final response
        final_response = assistant_message.content or ""

        # Update conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })

        return {
            "response": final_response,
            "stop_reason": response.choices[0].finish_reason,
            "tool_uses": self.tool_use_count
        }

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a tool function."""
        # Map tool names to actual functions
        tool_functions = {
            "calculate_resistor_power": PowerElectronicsTools.calculate_resistor_power,
            "calculate_capacitor_value": PowerElectronicsTools.calculate_capacitor_value,
            "select_mosfet": PowerElectronicsTools.select_mosfet,
            "calculate_thermal_resistance": PowerElectronicsTools.calculate_thermal_resistance,
            "calculate_led_resistor": PowerElectronicsTools.calculate_led_resistor,
            "design_buck_converter": PowerElectronicsTools.design_buck_converter,
        }

        if tool_name not in tool_functions:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            result = tool_functions[tool_name](**tool_input)
            return result
        except Exception as e:
            return {"error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get conversation statistics."""
        total_tokens = self.total_input_tokens + self.total_output_tokens

        # Calculate cost based on provider
        if self.provider == "claude":
            # Sonnet pricing
            input_cost = (self.total_input_tokens / 1_000_000) * 3.00
            output_cost = (self.total_output_tokens / 1_000_000) * 15.00
        else:  # OpenAI
            # GPT-4-turbo pricing
            input_cost = (self.total_input_tokens / 1_000_000) * 10.00
            output_cost = (self.total_output_tokens / 1_000_000) * 30.00

        total_cost = input_cost + output_cost

        return {
            "provider": self.provider,
            "model": self.model,
            "messages": len([m for m in self.conversation_history if m["role"] == "user"]),
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": total_tokens,
            "tool_uses": self.tool_use_count,
            "estimated_cost": total_cost
        }

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        print("🗑️  Conversation history cleared!")

    def save_conversation(self, filename: str):
        """Save conversation to JSON file."""
        data = {
            "provider": self.provider,
            "model": self.model,
            "conversation": self.conversation_history,
            "stats": self.get_stats()
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"💾 Conversation saved to {filename}")

    def load_conversation(self, filename: str):
        """Load conversation from JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)

        self.conversation_history = data["conversation"]
        print(f"📂 Conversation loaded from {filename}")


def demo():
    """Demo the assistant with example queries."""
    print("\n🔌 Power Electronics Assistant Demo")
    print("=" * 80)

    # Create assistant
    assistant = PowerElectronicsAssistant(provider="claude")

    # Example 1: LED resistor calculation
    print("\n" + "=" * 80)
    print("Example 1: LED Current Limiting Resistor")
    print("=" * 80)

    response = assistant.chat(
        "I have a red LED that needs 20mA at 2V forward voltage, "
        "and I'm using a 5V supply. What resistor do I need?"
    )

    print(f"\n🤖 Assistant: {response['response']}")

    # Example 2: MOSFET selection
    print("\n" + "=" * 80)
    print("Example 2: MOSFET Selection")
    print("=" * 80)

    response = assistant.chat(
        "I need a MOSFET for a 24V, 5A motor driver circuit. "
        "What would you recommend?"
    )

    print(f"\n🤖 Assistant: {response['response']}")

    # Example 3: Buck converter
    print("\n" + "=" * 80)
    print("Example 3: Buck Converter Design")
    print("=" * 80)

    response = assistant.chat(
        "Design a buck converter to step down 12V to 5V at 2A output current. "
        "Target 100kHz switching frequency."
    )

    print(f"\n🤖 Assistant: {response['response']}")

    # Show stats
    stats = assistant.get_stats()
    print("\n" + "=" * 80)
    print("📊 Conversation Statistics")
    print("=" * 80)
    print(f"Provider:      {stats['provider']}")
    print(f"Model:         {stats['model']}")
    print(f"Messages:      {stats['messages']}")
    print(f"Input tokens:  {stats['input_tokens']}")
    print(f"Output tokens: {stats['output_tokens']}")
    print(f"Total tokens:  {stats['total_tokens']}")
    print(f"Tool uses:     {stats['tool_uses']}")
    print(f"Cost:          ${stats['estimated_cost']:.6f}")
    print("=" * 80)


if __name__ == "__main__":
    import sys

    if "--demo" in sys.argv:
        demo()
    else:
        print("Run with --demo flag to see examples:")
        print("  python assistant.py --demo")
        print("\nOr use cli.py for interactive mode:")
        print("  python cli.py")
