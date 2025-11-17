#!/usr/bin/env python3
"""
Power Electronics CLI Assistant

Specialized CLI for power electronics engineering tasks.
Combines AI assistance with calculation tools.

Commands:
    power calc <type> [params...]    - Run calculations
    power design <circuit> [specs]   - Design circuits with AI
    power analyze <file>              - Analyze circuit files
    power component <query>           - Component lookup
    power simulate <circuit>          - Simulate circuits

Examples:
    power calc resistor voltage=5 current=0.1
    power design buck vin=12 vout=5 iout=3
    power component "MOSFET for 24V 10A"
    power analyze schematic.png
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv

# Try to import from previous modules
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

load_dotenv()


# Inline calculation tools (simplified version)
class PowerElectronicsTools:
    """Power electronics calculation tools."""

    @staticmethod
    def calculate_resistor_power(voltage: float = None, current: float = None,
                                 resistance: float = None) -> Dict:
        """Calculate resistor power dissipation."""
        # P = V×I, P = I²×R, P = V²/R
        if voltage and current:
            power = voltage * current
            resistance = voltage / current if current else 0
        elif voltage and resistance:
            power = (voltage ** 2) / resistance if resistance else 0
            current = voltage / resistance if resistance else 0
        elif current and resistance:
            power = (current ** 2) * resistance
            voltage = current * resistance
        else:
            return {"error": "Need at least 2 parameters"}

        # Recommend rating
        standard_ratings = [0.125, 0.25, 0.5, 1, 2, 5, 10]
        recommended = power * 2  # 2x safety factor
        rating = next((r for r in standard_ratings if r >= recommended), 10)

        return {
            "power_watts": round(power, 3),
            "voltage_volts": round(voltage, 2) if voltage else None,
            "current_amps": round(current, 3) if current else None,
            "resistance_ohms": round(resistance, 2) if resistance else None,
            "recommended_rating": rating,
            "summary": f"Power: {power:.3f}W → Use {rating}W resistor"
        }

    @staticmethod
    def calculate_led_resistor(supply_voltage: float, led_forward_voltage: float,
                               led_current_ma: float = 20) -> Dict:
        """Calculate LED current limiting resistor."""
        current_amps = led_current_ma / 1000
        voltage_drop = supply_voltage - led_forward_voltage

        if voltage_drop <= 0:
            return {"error": "Supply voltage must be > LED forward voltage"}

        resistance = voltage_drop / current_amps

        # Find E12 standard value
        e12_series = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]
        multiplier = 10 ** max(0, int(len(str(int(resistance))) - 1))
        normalized = resistance / multiplier
        standard = min(e12_series, key=lambda x: abs(x - normalized))
        standard_resistance = standard * multiplier

        power = voltage_drop * current_amps
        rating = 0.25 if power < 0.125 else 0.5

        return {
            "calculated_resistance_ohms": round(resistance, 1),
            "standard_resistance_ohms": standard_resistance,
            "power_watts": round(power, 3),
            "recommended_rating": rating,
            "summary": f"Use {standard_resistance}Ω, {rating}W resistor"
        }

    @staticmethod
    def design_buck_converter(vin: float, vout: float, iout: float,
                              freq_khz: float = 100) -> Dict:
        """Design buck converter."""
        import math

        freq = freq_khz * 1000
        duty_cycle = vout / vin

        # Component calculations
        ripple_current = 0.3 * iout
        inductance_uh = ((vin - vout) * duty_cycle / (ripple_current * freq)) * 1e6

        voltage_ripple = 0.01 * vout
        capacitance_uf = (ripple_current / (8 * freq * voltage_ripple)) * 1e6

        # Standard values
        std_inductors = [22, 33, 47, 68, 100, 150, 220]
        inductor = min(std_inductors, key=lambda x: abs(x - inductance_uh))

        std_caps = [22, 33, 47, 68, 100, 150, 220]
        capacitor = min(std_caps, key=lambda x: abs(x - capacitance_uf))

        return {
            "duty_cycle_percent": round(duty_cycle * 100, 1),
            "inductor_uh": inductor,
            "capacitor_uf": capacitor,
            "switching_frequency_khz": freq_khz,
            "summary": f"Buck converter: L={inductor}µH, C={capacitor}µF, D={duty_cycle*100:.1f}%"
        }


class PowerCLI:
    """Power Electronics CLI."""

    def __init__(self, ai_provider: str = "claude"):
        """Initialize CLI."""
        self.ai_provider = ai_provider
        self.tools = PowerElectronicsTools()

        # Initialize AI client
        if ai_provider == "claude" and CLAUDE_AVAILABLE:
            self.ai_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            self.ai_client = None

    def calculate(self, calc_type: str, params: Dict[str, float]):
        """Run calculation."""
        print(f"\n⚡ Running {calc_type} calculation...")

        if calc_type == "resistor":
            result = self.tools.calculate_resistor_power(**params)
        elif calc_type == "led":
            result = self.tools.calculate_led_resistor(**params)
        elif calc_type == "buck":
            result = self.tools.design_buck_converter(**params)
        else:
            result = {"error": f"Unknown calculation: {calc_type}"}

        self.print_result(result)

    def design(self, circuit_type: str, specs: str):
        """Design circuit with AI assistance."""
        if not self.ai_client:
            print("❌ AI client not available")
            return

        print(f"\n🤖 Designing {circuit_type} circuit with AI...\n")

        prompt = f"""Design a {circuit_type} circuit with these specifications:
{specs}

Provide:
1. Circuit topology
2. Component values with calculations
3. Design considerations
4. Recommended parts
"""

        try:
            response = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            print(response.content[0].text)

        except Exception as e:
            print(f"❌ Error: {e}")

    def component_search(self, query: str):
        """Search for components."""
        if not self.ai_client:
            print("❌ AI client not available")
            return

        print(f"\n🔍 Searching components...\n")

        prompt = f"""Find and recommend components for: {query}

Provide:
1. Part numbers and manufacturers
2. Key specifications
3. Typical applications
4. Approximate pricing
"""

        try:
            response = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            print(response.content[0].text)

        except Exception as e:
            print(f"❌ Error: {e}")

    def print_result(self, result: Dict[str, Any]):
        """Print calculation result."""
        print("\n" + "=" * 60)
        print("📊 Result")
        print("=" * 60)

        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            for key, value in result.items():
                if key != "summary":
                    print(f"  {key.replace('_', ' ').title()}: {value}")

            if "summary" in result:
                print("\n💡 " + result["summary"])

        print("=" * 60 + "\n")


def parse_params(param_strings: list) -> Dict[str, float]:
    """Parse parameter strings like 'voltage=5 current=0.1'."""
    params = {}
    for param in param_strings:
        if '=' in param:
            key, value = param.split('=', 1)
            try:
                params[key] = float(value)
            except ValueError:
                params[key] = value
    return params


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Power Electronics CLI Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  calc <type> [params]     Calculate values
  design <circuit> [spec]  Design with AI
  component <query>        Component search

Examples:
  power calc resistor voltage=5 current=0.1
  power calc led supply_voltage=9 led_forward_voltage=3.2
  power calc buck vin=12 vout=5 iout=3
  power design "buck converter" "12V to 5V, 3A, 100kHz"
  power component "MOSFET for 24V 10A motor driver"
        """
    )

    parser.add_argument("command", choices=["calc", "design", "component"])
    parser.add_argument("type_or_query", help="Calculation type or query")
    parser.add_argument("params", nargs="*", help="Parameters")
    parser.add_argument("--ai", default="claude", choices=["claude", "openai"],
                        help="AI provider for design commands")

    args = parser.parse_args()

    # Create CLI instance
    cli = PowerCLI(ai_provider=args.ai)

    try:
        if args.command == "calc":
            params = parse_params(args.params)
            cli.calculate(args.type_or_query, params)

        elif args.command == "design":
            specs = " ".join(args.params)
            cli.design(args.type_or_query, specs)

        elif args.command == "component":
            query = args.type_or_query + " " + " ".join(args.params)
            cli.component_search(query)

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
