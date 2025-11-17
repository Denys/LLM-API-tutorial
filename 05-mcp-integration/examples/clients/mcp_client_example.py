#!/usr/bin/env python3
"""
MCP Client Example - Using MCP Servers with Claude

This example demonstrates how to:
1. Connect to MCP servers
2. Discover available tools
3. Use tools with Claude API
4. Handle tool results

Usage:
    python mcp_client_example.py
"""

import os
import sys
import json
import subprocess
from typing import List, Dict
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class SimpleMCPClient:
    """
    Simplified MCP client for demonstration.

    In production, use the official MCP SDK which handles stdio communication.
    This example focuses on the conceptual workflow.
    """

    def __init__(self):
        self.servers = {}
        self.tools = []

    def connect_server(self, name: str, server_path: str):
        """
        Connect to an MCP server (simplified).

        In production, this would establish stdio communication.
        """
        self.servers[name] = {
            "path": server_path,
            "process": None  # Would be subprocess in production
        }

        # In production: fetch tools from server via MCP protocol
        # For this demo, we'll use pre-defined tool schemas

        if "basic_mcp_server" in server_path:
            self._add_basic_tools()
        elif "spice_sim_server" in server_path:
            self._add_spice_tools()

        print(f"✅ Connected to server: {name}")

    def _add_basic_tools(self):
        """Add tools from basic MCP server."""
        self.tools.extend([
            {
                "name": "calculate_resistor_power",
                "description": "Calculate power dissipation in a resistor. Provide any two of: voltage, current, resistance",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "voltage": {"type": "number", "description": "Voltage across resistor (V)"},
                        "current": {"type": "number", "description": "Current through resistor (A)"},
                        "resistance": {"type": "number", "description": "Resistance value (Ω)"}
                    }
                }
            },
            {
                "name": "calculate_led_resistor",
                "description": "Calculate LED current limiting resistor value",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "supply_voltage": {"type": "number", "description": "Supply voltage (V)"},
                        "led_forward_voltage": {"type": "number", "description": "LED forward voltage (V)"},
                        "led_current_ma": {"type": "number", "description": "Desired LED current (mA)"}
                    },
                    "required": ["supply_voltage", "led_forward_voltage"]
                }
            },
            {
                "name": "calculate_voltage_divider",
                "description": "Calculate resistive voltage divider values",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "input_voltage": {"type": "number", "description": "Input voltage (V)"},
                        "output_voltage": {"type": "number", "description": "Desired output voltage (V)"},
                        "current_ma": {"type": "number", "description": "Divider current (mA)"}
                    },
                    "required": ["input_voltage", "output_voltage"]
                }
            }
        ])

    def _add_spice_tools(self):
        """Add tools from SPICE simulation server."""
        self.tools.extend([
            {
                "name": "simulate_rc_filter",
                "description": "Simulate RC low-pass filter frequency response",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "resistance": {"type": "number", "description": "Resistor value (Ω)"},
                        "capacitance_uf": {"type": "number", "description": "Capacitance (µF)"},
                        "input_voltage": {"type": "number", "description": "Input voltage (V)"}
                    },
                    "required": ["resistance", "capacitance_uf"]
                }
            },
            {
                "name": "simulate_buck_converter",
                "description": "Design and analyze synchronous buck converter",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "vin": {"type": "number", "description": "Input voltage (V)"},
                        "vout": {"type": "number", "description": "Output voltage (V)"},
                        "iout": {"type": "number", "description": "Output current (A)"},
                        "freq_khz": {"type": "number", "description": "Switching frequency (kHz)"}
                    },
                    "required": ["vin", "vout", "iout"]
                }
            }
        ])

    def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """
        Call MCP tool (simplified implementation).

        In production, this would communicate with the server via stdio.
        """
        # Find server path from tool name
        server_path = None
        if tool_name in ["calculate_resistor_power", "calculate_led_resistor", "calculate_voltage_divider"]:
            server_path = str(Path(__file__).parent.parent / "servers" / "basic_mcp_server.py")
        elif tool_name in ["simulate_rc_filter", "simulate_buck_converter"]:
            server_path = str(Path(__file__).parent.parent / "servers" / "spice_sim_server.py")

        if not server_path:
            return json.dumps({"error": f"Tool {tool_name} not found"})

        # Simulate tool call by running the server's function
        # In production: send JSON-RPC request via stdio
        print(f"  🔧 Calling tool: {tool_name}", file=sys.stderr)
        print(f"     Arguments: {arguments}", file=sys.stderr)

        # For demo: import and call directly
        # Production would use subprocess communication
        result = self._simulate_tool_call(server_path, tool_name, arguments)

        return result

    def _simulate_tool_call(self, server_path: str, tool_name: str, arguments: Dict) -> str:
        """Simulate calling a tool (for demo purposes)."""
        # In production, this would be JSON-RPC over stdio
        # For now, we'll return mock results

        if tool_name == "calculate_resistor_power":
            v = arguments.get("voltage", 5.0)
            i = arguments.get("current", 0.1)
            p = v * i
            return json.dumps({
                "power_dissipation_watts": p,
                "formatted_result": f"Power: {p}W at {v}V, {i}A"
            })

        elif tool_name == "simulate_buck_converter":
            vin = arguments["vin"]
            vout = arguments["vout"]
            iout = arguments["iout"]
            duty = vout / vin
            return json.dumps({
                "duty_cycle_percent": duty * 100,
                "formatted_result": f"Buck converter: {vin}V→{vout}V @ {iout}A, duty={duty*100:.1f}%"
            })

        return json.dumps({"result": "Tool executed"})

    def chat_with_claude(self, user_message: str) -> str:
        """Use Claude with MCP tools."""

        print(f"\n💬 User: {user_message}\n")

        messages = [{"role": "user", "content": user_message}]

        # Call Claude with tools
        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=self.tools,
            messages=messages
        )

        # Handle tool use
        iteration = 0
        max_iterations = 5

        while response.stop_reason == "tool_use" and iteration < max_iterations:
            iteration += 1

            print(f"🔄 Tool use iteration {iteration}:", file=sys.stderr)

            # Collect tool results
            tool_results = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input

                    # Call the MCP tool
                    result = self.call_tool(tool_name, tool_input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": result
                    })

            # Continue conversation with tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            response = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                tools=self.tools,
                messages=messages
            )

        # Extract final response
        final_text = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                final_text += content_block.text

        return final_text


def demo_basic_usage():
    """Demonstrate basic MCP client usage."""
    print("\n" + "=" * 70)
    print("  DEMO 1: Basic MCP Tool Usage")
    print("=" * 70)

    client = SimpleMCPClient()

    # Connect to basic server
    server_path = str(Path(__file__).parent.parent / "servers" / "basic_mcp_server.py")
    client.connect_server("power-tools", server_path)

    print(f"\n📦 Available tools: {len(client.tools)}")
    for tool in client.tools:
        print(f"  • {tool['name']}")

    # Use Claude with tools
    response = client.chat_with_claude(
        "I have a 5V power supply and need to power a red LED (forward voltage 2V) at 20mA. What resistor do I need?"
    )

    print(f"\n🤖 Claude: {response}\n")


def demo_simulation():
    """Demonstrate SPICE simulation integration."""
    print("\n" + "=" * 70)
    print("  DEMO 2: SPICE Simulation Integration")
    print("=" * 70)

    client = SimpleMCPClient()

    # Connect to SPICE server
    server_path = str(Path(__file__).parent.parent / "servers" / "spice_sim_server.py")
    client.connect_server("spice-simulator", server_path)

    print(f"\n📦 Available simulation tools: {len(client.tools)}")
    for tool in client.tools:
        print(f"  • {tool['name']}")

    # Use Claude with simulation tools
    response = client.chat_with_claude(
        "Design a buck converter to step down 12V to 5V for a 3A load. Simulate it at 100kHz."
    )

    print(f"\n🤖 Claude: {response}\n")


def demo_combined():
    """Demonstrate using multiple MCP servers together."""
    print("\n" + "=" * 70)
    print("  DEMO 3: Multiple MCP Servers Combined")
    print("=" * 70)

    client = SimpleMCPClient()

    # Connect to both servers
    basic_server = str(Path(__file__).parent.parent / "servers" / "basic_mcp_server.py")
    spice_server = str(Path(__file__).parent.parent / "servers" / "spice_sim_server.py")

    client.connect_server("power-tools", basic_server)
    client.connect_server("spice-simulator", spice_server)

    print(f"\n📦 Total available tools: {len(client.tools)}")

    # Complex query using multiple tools
    response = client.chat_with_claude("""
I need to design a complete LED driver circuit:
1. Input: 12V DC
2. Output: Blue LED (3.2V forward voltage) at 20mA
3. Also include an RC filter at the input with fc=1kHz

Calculate the resistor and simulate the filter.
    """)

    print(f"\n🤖 Claude: {response}\n")


def main():
    """Run all demonstrations."""
    print("\n" + "🔌 " + "=" * 66 + " 🔌")
    print("    MCP CLIENT EXAMPLE - Using MCP Servers with Claude")
    print("🔌 " + "=" * 66 + " 🔌")

    try:
        # Run demos
        demo_basic_usage()
        demo_simulation()
        demo_combined()

        print("\n" + "=" * 70)
        print("💡 KEY CONCEPTS")
        print("=" * 70)
        print("""
MCP Client Workflow:
1. Connect to MCP server(s)
2. Discover available tools
3. Pass tools to Claude API
4. Handle tool_use responses
5. Call MCP tools with arguments
6. Return results to Claude
7. Get final response

Benefits:
✅ Standardized protocol
✅ Multiple tool sources
✅ Easy integration
✅ Reusable servers
✅ Ecosystem growth

Production Notes:
• Use official MCP SDK for real implementations
• Servers communicate via stdio (standard input/output)
• Use JSON-RPC for requests
• Handle errors and timeouts
• Consider security and sandboxing
        """)

        print("=" * 70)
        print("✅ MCP client demonstration complete!")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Set ANTHROPIC_API_KEY in .env")
        print("  2. MCP server files in examples/servers/")
        raise


if __name__ == "__main__":
    main()
