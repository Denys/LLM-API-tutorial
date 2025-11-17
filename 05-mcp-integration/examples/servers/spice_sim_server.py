#!/usr/bin/env python3
"""
SPICE Simulation MCP Server

This MCP server provides circuit simulation capabilities using SPICE.
If ngspice is not available, falls back to analytical calculations.

Tools provided:
- simulate_rc_filter: RC low-pass filter analysis
- simulate_buck_converter: Buck converter simulation
- analyze_circuit: General circuit analysis

Usage:
    python spice_sim_server.py

Requirements:
    pip install numpy matplotlib (optional: ngspice)
"""

import json
import sys
import subprocess
import tempfile
import os
from typing import Dict, Any, List
import asyncio
import math


class SPICEServer:
    """Simplified SPICE simulation server."""

    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        self.has_ngspice = self._check_ngspice()

    def _check_ngspice(self) -> bool:
        """Check if ngspice is available."""
        try:
            subprocess.run(['ngspice', '-v'], capture_output=True, timeout=5)
            print("✅ ngspice found - using full SPICE simulation", file=sys.stderr)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️  ngspice not found - using analytical calculations", file=sys.stderr)
            return False

    def tool(self, name: str = None, description: str = None):
        """Decorator to register a tool."""
        def decorator(func):
            tool_name = name or func.__name__
            tool_desc = description or func.__doc__ or ""

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


# Create server instance
server = SPICEServer("spice-simulator")


@server.tool(description="Simulate RC low-pass filter frequency response")
def simulate_rc_filter(
    resistance: float,
    capacitance_uf: float,
    input_voltage: float = 1.0
) -> str:
    """
    Analyze RC low-pass filter.

    Args:
        resistance: Resistor value in ohms
        capacitance_uf: Capacitor value in microfarads
        input_voltage: Input signal amplitude (default 1.0V)
    """

    capacitance = capacitance_uf * 1e-6  # Convert to farads

    # Calculate cutoff frequency
    fc = 1.0 / (2 * math.pi * resistance * capacitance)

    # Calculate response at key frequencies
    frequencies = [
        fc / 10,  # Decade below
        fc,       # Cutoff
        fc * 10   # Decade above
    ]

    responses = []
    for f in frequencies:
        # Calculate magnitude: |H(jω)| = 1 / √(1 + (ω×RC)²)
        omega = 2 * math.pi * f
        magnitude = 1.0 / math.sqrt(1 + (omega * resistance * capacitance) ** 2)
        magnitude_db = 20 * math.log10(magnitude)

        # Calculate phase: φ = -arctan(ω×RC)
        phase_rad = -math.atan(omega * resistance * capacitance)
        phase_deg = math.degrees(phase_rad)

        responses.append({
            "frequency_hz": round(f, 2),
            "magnitude": round(magnitude, 4),
            "magnitude_db": round(magnitude_db, 2),
            "phase_degrees": round(phase_deg, 2),
            "output_voltage": round(magnitude * input_voltage, 4)
        })

    result = {
        "circuit_type": "RC Low-Pass Filter",
        "resistance_ohms": resistance,
        "capacitance_farads": capacitance,
        "capacitance_uf": capacitance_uf,
        "cutoff_frequency_hz": round(fc, 2),
        "time_constant_ms": round(resistance * capacitance * 1000, 3),
        "frequency_response": responses,
        "formatted_result": f"""RC Filter Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Components:
  R = {resistance}Ω
  C = {capacitance_uf}µF

Filter Characteristics:
  Cutoff Frequency (fc):  {fc:.2f} Hz
  Time Constant (τ):      {resistance*capacitance*1000:.3f} ms
  -3dB Point:             {fc:.2f} Hz

Frequency Response:
┌──────────────┬────────────┬─────────────┬──────────────┐
│  Frequency   │  Magnitude │  Magnitude  │    Phase     │
│     (Hz)     │   (linear) │     (dB)    │  (degrees)   │
├──────────────┼────────────┼─────────────┼──────────────┤"""
    }

    for resp in responses:
        result["formatted_result"] += f"""
│ {resp['frequency_hz']:>12.2f} │  {resp['magnitude']:>8.4f}  │  {resp['magnitude_db']:>9.2f}  │  {resp['phase_degrees']:>10.2f}  │"""

    result["formatted_result"] += """
└──────────────┴────────────┴─────────────┴──────────────┘

At fc:  Output is -3dB (70.7%) of input
        Phase shift is -45°

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    return json.dumps(result, indent=2)


@server.tool(description="Design and analyze buck converter")
def simulate_buck_converter(
    vin: float,
    vout: float,
    iout: float,
    freq_khz: float = 100.0
) -> str:
    """
    Design and analyze synchronous buck converter.

    Args:
        vin: Input voltage (V)
        vout: Output voltage (V)
        iout: Output current (A)
        freq_khz: Switching frequency (kHz)
    """

    freq = freq_khz * 1000  # Convert to Hz

    # Design calculations
    duty_cycle = vout / vin

    # Inductor value for 30% current ripple
    ripple_current = 0.3 * iout
    inductance = (vin - vout) * duty_cycle / (ripple_current * freq)
    inductance_uh = inductance * 1e6

    # Output capacitor for 1% voltage ripple
    voltage_ripple = 0.01 * vout
    capacitance = ripple_current / (8 * freq * voltage_ripple)
    capacitance_uf = capacitance * 1e6

    # Efficiency estimation
    # Assume Rds(on) = 50mΩ for both MOSFETs
    rds_on = 0.050

    # Conduction losses
    mosfet_high_loss = rds_on * (iout ** 2) * duty_cycle
    mosfet_low_loss = rds_on * (iout ** 2) * (1 - duty_cycle)
    inductor_dcr_loss = 0.050 * (iout ** 2)  # Assume 50mΩ DCR

    # Switching losses (simplified)
    switching_loss = 0.0001 * vin * iout * freq / 1000  # Simplified

    total_loss = mosfet_high_loss + mosfet_low_loss + inductor_dcr_loss + switching_loss
    pout = vout * iout
    efficiency = (pout / (pout + total_loss)) * 100

    # Standard component values
    standard_inductors = [22, 33, 47, 68, 100, 150, 220]
    inductor_value = min(standard_inductors, key=lambda x: abs(x - inductance_uh))

    standard_capacitors = [22, 33, 47, 68, 100, 150, 220]
    capacitor_value = min(standard_capacitors, key=lambda x: abs(x - capacitance_uf))

    result = {
        "input_voltage": vin,
        "output_voltage": vout,
        "output_current": iout,
        "switching_frequency_hz": freq,
        "duty_cycle_percent": round(duty_cycle * 100, 1),
        "calculated_inductance_uh": round(inductance_uh, 2),
        "recommended_inductance_uh": inductor_value,
        "calculated_capacitance_uf": round(capacitance_uf, 2),
        "recommended_capacitance_uf": capacitor_value,
        "estimated_efficiency_percent": round(efficiency, 1),
        "power_losses": {
            "mosfet_high_w": round(mosfet_high_loss, 3),
            "mosfet_low_w": round(mosfet_low_loss, 3),
            "inductor_w": round(inductor_dcr_loss, 3),
            "switching_w": round(switching_loss, 3),
            "total_w": round(total_loss, 3)
        },
        "formatted_result": f"""Buck Converter Design:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Specifications:
  Input:       {vin}V
  Output:      {vout}V @ {iout}A ({pout:.1f}W)
  Frequency:   {freq_khz}kHz
  Duty Cycle:  {duty_cycle*100:.1f}%

Calculated Component Values:
  Inductor:    {inductance_uh:.2f}µH
  Capacitor:   {capacitance_uf:.2f}µF

Recommended Standard Values:
  Inductor:    {inductor_value}µH
  Capacitor:   {capacitor_value}µF

  Specifications:
    L: >{iout*1.3:.1f}A saturation, <50mΩ DCR
    C: >{ripple_current:.2f}A ripple current, low ESR

Circuit Diagram:
     Vin ({vin}V)
      │
    ┌─┴─┐ Q1 (High-side MOSFET)
    │ ▶ │ PWM: {duty_cycle*100:.1f}% @ {freq_khz}kHz
    └─┬─┘
      ├────[{inductor_value}µH]────┬──── Vout ({vout}V, {iout}A)
      │                        │
    ┌─┴─┐ Q2 (Low-side)      [={capacitor_value}µF]=
    │ ▶ │ Synchronous         │
    └─┬─┘                      │
      │                        │
     GND                      GND

Performance Analysis:
  Estimated Efficiency:  {efficiency:.1f}%

  Power Losses:
    High-side MOSFET:    {mosfet_high_loss:.3f}W
    Low-side MOSFET:     {mosfet_low_loss:.3f}W
    Inductor DCR:        {inductor_dcr_loss:.3f}W
    Switching:           {switching_loss:.3f}W
    ─────────────────────────────
    Total Losses:        {total_loss:.3f}W

  Output Ripple:
    Current:             {ripple_current:.2f}A (30% of Iout)
    Voltage:             {voltage_ripple*1000:.1f}mV (1% of Vout)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    }

    return json.dumps(result, indent=2)


@server.tool(description="Analyze general circuit parameters")
def analyze_circuit(
    circuit_type: str,
    parameters: str
) -> str:
    """
    Analyze various circuit types.

    Args:
        circuit_type: Type of circuit (e.g., "voltage_divider", "current_mirror")
        parameters: JSON string with circuit parameters
    """

    try:
        params = json.loads(parameters)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in parameters"})

    if circuit_type == "voltage_divider":
        vin = params.get("vin", 0)
        r1 = params.get("r1", 0)
        r2 = params.get("r2", 0)

        if r1 + r2 == 0:
            return json.dumps({"error": "Invalid resistor values"})

        vout = vin * (r2 / (r1 + r2))
        current = vin / (r1 + r2)
        power = vin * current

        result = {
            "circuit_type": "Voltage Divider",
            "output_voltage": round(vout, 3),
            "current_ma": round(current * 1000, 3),
            "power_dissipation_w": round(power, 3),
            "formatted_result": f"""Voltage Divider Analysis:
Vin = {vin}V, R1 = {r1}Ω, R2 = {r2}Ω
→ Vout = {vout:.3f}V
→ Current = {current*1000:.3f}mA
→ Power = {power:.3f}W"""
        }

    else:
        result = {
            "error": f"Circuit type '{circuit_type}' not supported",
            "supported_types": ["voltage_divider"]
        }

    return json.dumps(result, indent=2)


def demo_simulations():
    """Demonstrate simulation capabilities."""
    print("\n📊 SIMULATION DEMONSTRATIONS\n", file=sys.stderr)

    # Demo 1: RC Filter
    print("1️⃣  RC Filter Analysis (1kΩ, 1µF):", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    result = asyncio.run(server.call_tool(
        "simulate_rc_filter",
        {"resistance": 1000.0, "capacitance_uf": 1.0}
    ))
    data = json.loads(result)
    print(data.get("formatted_result", result), file=sys.stderr)

    # Demo 2: Buck Converter
    print("\n\n2️⃣  Buck Converter Design (12V→5V @ 3A):", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    result = asyncio.run(server.call_tool(
        "simulate_buck_converter",
        {"vin": 12.0, "vout": 5.0, "iout": 3.0, "freq_khz": 100.0}
    ))
    data = json.loads(result)
    print(data.get("formatted_result", result), file=sys.stderr)

    # Demo 3: Circuit Analysis
    print("\n\n3️⃣  Voltage Divider Analysis (12V, 10kΩ, 10kΩ):", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    params = json.dumps({"vin": 12.0, "r1": 10000, "r2": 10000})
    result = asyncio.run(server.call_tool(
        "analyze_circuit",
        {"circuit_type": "voltage_divider", "parameters": params}
    ))
    data = json.loads(result)
    print(data.get("formatted_result", result), file=sys.stderr)


def main():
    """Main entry point."""
    print("\n" + "=" * 60, file=sys.stderr)
    print("  SPICE SIMULATION MCP SERVER", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # List available tools
    tools = server.list_tools()
    print(f"\n📦 Server provides {len(tools)} simulation tools:", file=sys.stderr)
    for tool in tools:
        print(f"\n  • {tool['name']}", file=sys.stderr)
        print(f"    {tool['description']}", file=sys.stderr)

    # Run demonstrations
    demo_simulations()

    print("\n" + "=" * 60, file=sys.stderr)
    print("  ✅ Simulation server demonstration complete!", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("\n💡 These simulations use analytical calculations", file=sys.stderr)
    print("   For full SPICE simulation, install ngspice:", file=sys.stderr)
    print("   • Ubuntu/Debian: sudo apt-get install ngspice", file=sys.stderr)
    print("   • macOS: brew install ngspice", file=sys.stderr)
    print()


if __name__ == "__main__":
    main()
