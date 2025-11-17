# Power Electronics Assistant

A practical LLM application combining vision AI and function calling to assist with power electronics design.

## Features

- 🔍 **Circuit Analysis** - Analyze circuit diagrams using vision AI
- 🔢 **Component Calculations** - Calculate resistor power, capacitor values, inductor sizing
- 🔧 **MOSFET Selection** - Recommend MOSFETs based on requirements
- 🌡️ **Thermal Analysis** - Calculate heatsink requirements
- ⚡ **Efficiency Calculation** - Estimate converter efficiency
- 💬 **Interactive Chat** - Multi-turn conversations with context

## Supported Providers

- **Claude** (Anthropic) - Recommended for technical analysis
- **GPT-4** (OpenAI) - Alternative with strong vision capabilities

## Installation

```bash
cd 03-advanced-features/examples/power-electronics-assistant
pip install -r requirements.txt
```

## Usage

### Basic Examples

```python
from assistant import PowerElectronicsAssistant

# Initialize with Claude
assistant = PowerElectronicsAssistant(provider="claude")

# Calculate resistor power
result = assistant.ask("I have 12V across a resistor with 0.5A current. What power rating do I need?")
print(result)

# Analyze circuit (requires image)
result = assistant.analyze_circuit(
    image_path="circuit.png",
    question="What type of converter is this?"
)
print(result)
```

### CLI Interface

```bash
python cli.py

# Available commands:
> calculate resistor 12V 0.5A
> analyze circuit.png
> recommend mosfet 48V 20A switching
> help
> quit
```

## Tool Reference

### calculate_resistor_power
Calculate power dissipation and recommend power rating.

**Parameters:**
- `voltage` (float): Voltage in volts
- `current` (float): Current in amperes
- `resistance` (float): Resistance in ohms

**Example:**
```
> calculate resistor voltage=12 current=0.5
Power: 6.0W, Recommended rating: 10W
```

### calculate_capacitor_value
Size output filter capacitor for specified ripple.

**Parameters:**
- `load_current` (float): Load current in amps
- `ripple_voltage` (float): Max ripple in volts
- `frequency` (float): Switching frequency in Hz

**Example:**
```
> calculate capacitor load_current=5 ripple_voltage=0.1 frequency=100000
Calculated: 250µF, Recommended: 330µF
```

### calculate_inductor_value
Design inductor for buck/boost converter.

**Parameters:**
- `input_voltage` (float): Input voltage
- `output_voltage` (float): Output voltage
- `load_current` (float): Load current in amps
- `frequency` (float): Switching frequency in Hz

**Example:**
```
> calculate inductor input_voltage=12 output_voltage=5 load_current=3 frequency=100000
Topology: buck, Inductance: 22µH
```

### select_mosfet
Recommend MOSFET based on requirements.

**Parameters:**
- `voltage_rating` (float): Required voltage in volts
- `current_rating` (float): Required current in amps
- `application` (str): "switching", "linear", or "high_frequency"

**Example:**
```
> recommend mosfet voltage_rating=48 current_rating=20 application=switching
Recommended: IRFP260N (200V, 50A)
```

## Examples

See `examples/` directory for:
- `basic_calculations.py` - Simple tool usage
- `circuit_analysis.py` - Vision AI examples
- `design_flow.py` - Complete design workflow
- `comparison.py` - Claude vs OpenAI comparison

## Project Structure

```
power-electronics-assistant/
├── README.md              # This file
├── assistant.py           # Main assistant class
├── tools.py              # Calculation tools
├── cli.py                # Command-line interface
├── requirements.txt      # Dependencies
└── examples/             # Example scripts
```

## Cost Considerations

**Typical costs per query:**
- Simple calculation: $0.0001 - $0.0005 (Claude Haiku)
- Circuit analysis: $0.001 - $0.003 (vision included)
- Complex design: $0.002 - $0.01 (multiple tools)

**Optimization tips:**
- Use Claude Haiku for calculations (cheapest)
- Cache system prompts for repeated queries
- Use streaming for better UX (same cost)

## Future Enhancements (Modules 4-7)

- **Module 4**: Add RAG for datasheet lookup
- **Module 5**: MCP integration with SPICE simulators
- **Module 6**: Claude Code CLI integration
- **Module 7**: Multi-agent system for complex designs

## Contributing

This is part of the LLM API Tutorial. See main README for contribution guidelines.

## License

MIT License - See main repository LICENSE file.
