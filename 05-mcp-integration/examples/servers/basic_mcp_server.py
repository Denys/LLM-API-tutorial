#!/usr/bin/env python3
"""
Basic MCP Server - Power Electronics Tools

This is a simple MCP server that provides power electronics calculation tools.
It demonstrates the fundamentals of creating an MCP server.

Tools provided:
- calculate_resistor_power: Power dissipation calculation
- calculate_led_resistor: LED current limiting resistor
- calculate_voltage_divider: Resistive voltage divider

Usage:
    python basic_mcp_server.py

Note: This example uses a simplified MCP-like interface for educational purposes.
For production, use the official MCP SDK when available.
"""

import json
import sys
from typing import Dict, Any, List
import asyncio


class SimpleMCPServer:
    """Simplified MCP server implementation for educational purposes."""

    def __init__(self, name: str):
        self.name = name
        self.tools = {}

    def tool(self, name: str = None, description: str = None):
        """Decorator to register a tool."""
        def decorator(func):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

            # Extract parameter info from function signature
            import inspect
            sig = inspect.signature(func)

            parameters = {}
            for param_name, param in sig.parameters.items():
                param_type = "string"
                if param.annotation == float:
                    param_type = "number"
                elif param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"

                parameters[param_name] = {
                    "type": param_type,
                    "description": f"Parameter {param_name}"
                }

            self.tools[tool_name] = {
                "name": tool_name,
                "description": tool_desc.strip(),
                "parameters": parameters,
                "function": func
            }

            return func
        return decorator

    def list_tools(self) -> List[Dict]:
        """List all available tools."""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": tool["parameters"],
                    "required": list(tool["parameters"].keys())
                }
            }
            for tool in self.tools.values()
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Call a tool by name with arguments."""
        if name not in self.tools:
            return json.dumps({"error": f"Tool {name} not found"})

        try:
            result = self.tools[name]["function"](**arguments)
            return result
        except Exception as e:
            return json.dumps({"error": str(e)})

    def run(self):
        """Run the MCP server (stdio-based communication)."""
        print(f"🚀 MCP Server '{self.name}' started", file=sys.stderr)
        print(f"📦 Available tools: {len(self.tools)}", file=sys.stderr)

        for tool_name in self.tools:
            print(f"  - {tool_name}", file=sys.stderr)

        # For this example, we'll demonstrate the tools
        print("\n" + "=" * 60, file=sys.stderr)
        print("DEMO MODE - Tool Examples:", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)


# Create server instance
server = SimpleMCPServer("power-electronics-tools")


@server.tool(description="Calculate power dissipation in a resistor")
def calculate_resistor_power(
    voltage: float = None,
    current: float = None,
    resistance: float = None
) -> str:
    """
    Calculate power dissipation in a resistor.

    Provide any two of: voltage, current, resistance
    """
    # Calculate missing value
    if voltage is not None and current is not None:
        # P = V × I
        power = voltage * current
        if resistance is None:
            resistance = voltage / current if current != 0 else 0

    elif voltage is not None and resistance is not None:
        # P = V² / R
        power = (voltage ** 2) / resistance if resistance != 0 else 0
        current = voltage / resistance if resistance != 0 else 0

    elif current is not None and resistance is not None:
        # P = I² × R
        power = (current ** 2) * resistance
        voltage = current * resistance

    else:
        return json.dumps({
            "error": "Must provide at least two of: voltage, current, resistance"
        })

    # Recommend power rating (2x safety factor)
    recommended = power * 2

    # Find standard power rating
    standard_ratings = [0.125, 0.25, 0.5, 1, 2, 5, 10, 25, 50, 100]
    rating = next((r for r in standard_ratings if r >= recommended), 100)

    result = {
        "power_dissipation_watts": round(power, 3),
        "voltage_volts": round(voltage, 2) if voltage else None,
        "current_amps": round(current, 3) if current else None,
        "resistance_ohms": round(resistance, 2) if resistance else None,
        "recommended_rating_watts": rating,
        "safety_factor": 2.0,
        "formatted_result": f"""Power Calculation Result:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voltage:         {voltage:.2f}V
Current:         {current:.3f}A
Resistance:      {resistance:.2f}Ω
Power:           {power:.3f}W
Recommended:     {rating}W resistor (2× safety factor)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    }

    return json.dumps(result, indent=2)


@server.tool(description="Calculate LED current limiting resistor")
def calculate_led_resistor(
    supply_voltage: float,
    led_forward_voltage: float,
    led_current_ma: float = 20.0
) -> str:
    """Calculate current limiting resistor for LED circuit."""

    current_amps = led_current_ma / 1000.0

    # Calculate resistor value: R = (Vsupply - Vf) / I
    voltage_drop = supply_voltage - led_forward_voltage

    if voltage_drop <= 0:
        return json.dumps({
            "error": "Supply voltage must be greater than LED forward voltage"
        })

    resistance = voltage_drop / current_amps

    # Find nearest E12 standard value
    e12_series = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]
    multiplier = 10 ** int(len(str(int(resistance))) - 1)
    normalized = resistance / multiplier
    standard_value = min(e12_series, key=lambda x: abs(x - normalized))
    standard_resistance = standard_value * multiplier

    # Calculate actual current with standard resistor
    actual_current = voltage_drop / standard_resistance
    actual_current_ma = actual_current * 1000

    # Calculate power dissipation
    power = voltage_drop * actual_current
    recommended_rating = power * 2

    # Standard power rating
    ratings = [0.125, 0.25, 0.5, 1, 2]
    power_rating = next((r for r in ratings if r >= recommended_rating), 2)

    result = {
        "calculated_resistance_ohms": round(resistance, 2),
        "standard_resistance_ohms": standard_resistance,
        "actual_current_ma": round(actual_current_ma, 2),
        "power_dissipation_watts": round(power, 3),
        "recommended_rating_watts": power_rating,
        "formatted_result": f"""LED Resistor Calculation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Supply Voltage:  {supply_voltage}V
LED Vf:          {led_forward_voltage}V
Target Current:  {led_current_ma}mA

Calculated:      {resistance:.1f}Ω
Standard Value:  {standard_resistance}Ω (E12 series)
Actual Current:  {actual_current_ma:.1f}mA
Power:           {power:.3f}W

Recommendation:  {standard_resistance}Ω, {power_rating}W resistor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    }

    return json.dumps(result, indent=2)


@server.tool(description="Calculate resistive voltage divider")
def calculate_voltage_divider(
    input_voltage: float,
    output_voltage: float,
    current_ma: float = 1.0
) -> str:
    """Calculate resistor values for voltage divider."""

    current_amps = current_ma / 1000.0

    # Total resistance
    r_total = input_voltage / current_amps

    # Voltage divider: Vout = Vin × (R2 / (R1 + R2))
    # R2 = Vout × Rtotal / Vin
    # R1 = Rtotal - R2

    r2 = (output_voltage * r_total) / input_voltage
    r1 = r_total - r2

    # Find E12 standard values
    e12_series = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]

    def find_e12(value):
        multiplier = 10 ** max(0, int(len(str(int(value))) - 1))
        normalized = value / multiplier
        standard = min(e12_series, key=lambda x: abs(x - normalized))
        return standard * multiplier

    r1_standard = find_e12(r1)
    r2_standard = find_e12(r2)

    # Calculate actual output voltage with standard resistors
    actual_output = input_voltage * (r2_standard / (r1_standard + r2_standard))
    actual_current = input_voltage / (r1_standard + r2_standard)

    # Power dissipation
    p1 = actual_current ** 2 * r1_standard
    p2 = actual_current ** 2 * r2_standard
    p_total = p1 + p2

    result = {
        "r1_calculated_ohms": round(r1, 2),
        "r2_calculated_ohms": round(r2, 2),
        "r1_standard_ohms": r1_standard,
        "r2_standard_ohms": r2_standard,
        "actual_output_voltage": round(actual_output, 3),
        "actual_current_ma": round(actual_current * 1000, 2),
        "power_r1_watts": round(p1, 3),
        "power_r2_watts": round(p2, 3),
        "total_power_watts": round(p_total, 3),
        "formatted_result": f"""Voltage Divider Calculation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:           {input_voltage}V
Target Output:   {output_voltage}V

Calculated:
  R1 = {r1:.1f}Ω
  R2 = {r2:.1f}Ω

Standard Values (E12):
  R1 = {r1_standard}Ω
  R2 = {r2_standard}Ω

Actual Performance:
  Output:  {actual_output:.3f}V
  Current: {actual_current*1000:.2f}mA
  Power:   {p_total:.3f}W total

Circuit Diagram:
  Vin ({input_voltage}V)
    │
  ┌─┴─┐
  │R1 │ {r1_standard}Ω ({p1:.3f}W)
  └─┬─┘
    ├──── Vout ({actual_output:.3f}V)
  ┌─┴─┐
  │R2 │ {r2_standard}Ω ({p2:.3f}W)
  └─┬─┘
    │
   GND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    }

    return json.dumps(result, indent=2)


def demo_tools():
    """Demonstrate all tools."""
    print("\n📝 TOOL DEMONSTRATIONS\n", file=sys.stderr)

    # Demo 1: Resistor Power
    print("1️⃣  Calculate Resistor Power (5V, 100mA):", file=sys.stderr)
    result = asyncio.run(server.call_tool(
        "calculate_resistor_power",
        {"voltage": 5.0, "current": 0.1}
    ))
    data = json.loads(result)
    print(data.get("formatted_result", result), file=sys.stderr)
    print()

    # Demo 2: LED Resistor
    print("\n2️⃣  Calculate LED Resistor (5V supply, 2V LED, 20mA):", file=sys.stderr)
    result = asyncio.run(server.call_tool(
        "calculate_led_resistor",
        {"supply_voltage": 5.0, "led_forward_voltage": 2.0, "led_current_ma": 20.0}
    ))
    data = json.loads(result)
    print(data.get("formatted_result", result), file=sys.stderr)
    print()

    # Demo 3: Voltage Divider
    print("\n3️⃣  Calculate Voltage Divider (12V → 5V, 1mA):", file=sys.stderr)
    result = asyncio.run(server.call_tool(
        "calculate_voltage_divider",
        {"input_voltage": 12.0, "output_voltage": 5.0, "current_ma": 1.0}
    ))
    data = json.loads(result)
    print(data.get("formatted_result", result), file=sys.stderr)
    print()


def main():
    """Main entry point."""
    print("\n" + "=" * 60, file=sys.stderr)
    print("  BASIC MCP SERVER - Power Electronics Tools", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # List available tools
    tools = server.list_tools()
    print(f"\n📦 Server provides {len(tools)} tools:", file=sys.stderr)
    for tool in tools:
        print(f"\n  • {tool['name']}", file=sys.stderr)
        print(f"    {tool['description']}", file=sys.stderr)

    # Run demonstrations
    demo_tools()

    print("\n" + "=" * 60, file=sys.stderr)
    print("  ✅ MCP Server demonstration complete!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("\n💡 In production, this server would communicate via stdio", file=sys.stderr)
    print("   and be controlled by an MCP client (like Claude)", file=sys.stderr)
    print()


if __name__ == "__main__":
    main()
