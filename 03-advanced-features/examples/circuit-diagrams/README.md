# Sample Circuit Diagrams

This directory contains sample circuit diagrams for testing the vision API examples.

## Included Diagrams

### 1. LED Circuit (led_circuit.txt)
Simple LED current limiting circuit with:
- Power supply (5V)
- Current limiting resistor
- LED (red, 2V forward voltage, 20mA)

### 2. Buck Converter (buck_converter.txt)
Step-down DC-DC converter with:
- Input voltage (12V)
- Output voltage (5V)
- Switching MOSFET
- Inductor and capacitor
- Diode

### 3. MOSFET H-Bridge (h_bridge.txt)
Motor driver circuit with:
- 4 N-channel MOSFETs
- Gate drivers
- Protection diodes
- Motor connections

### 4. Voltage Divider (voltage_divider.txt)
Simple resistive voltage divider:
- Input voltage
- Two resistors in series
- Output tap point

## Using with Vision API

These diagrams can be used to test Claude's and OpenAI's vision capabilities:

1. **Analyze circuit topology** - Identify components and connections
2. **Calculate values** - Determine resistor values, capacitance, etc.
3. **Troubleshoot** - Find potential issues or improvements
4. **Design verification** - Check if circuit meets requirements

## Note on Real Images

In production, you would use:
- PNG/JPG images of schematics
- Photos of physical circuits
- PCB layouts
- Oscilloscope screenshots

The vision examples in `../claude/` and `../openai/` show how to process these images.

## Testing

See the vision examples:
- `../claude/vision_circuit_analysis.py` - Claude vision API
- `../openai/vision_circuit_analysis.py` - OpenAI vision API

Both examples demonstrate:
- Loading and encoding images
- Sending to vision-enabled models
- Getting detailed circuit analysis
- Extracting component values
