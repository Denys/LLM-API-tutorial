# Module 3: Advanced Features - Vision, Tools & Function Calling

**Duration:** 2-3 hours
**Difficulty:** Intermediate to Advanced
**Prerequisites:** Modules 1 and 2 completed

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Work with images using Claude and GPT-4 Vision
- ✅ Implement function/tool calling with both APIs
- ✅ Build interactive AI applications that use external tools
- ✅ Create multi-tool orchestration systems
- ✅ Handle structured outputs from LLMs
- ✅ Build a practical Power Electronics Assistant

## Overview

This module introduces advanced features that make LLMs more powerful and versatile. You'll learn multimodal AI (text + images), function calling to integrate with external systems, and how to build practical applications.

### What You'll Build

Throughout this module, you'll build a **Power Electronics Assistant** that can:
- Analyze circuit diagrams (vision)
- Calculate component values (function calling)
- Look up datasheets (tool integration)
- Provide design recommendations

---

## Comparing Claude and OpenAI

Both Claude and OpenAI offer advanced features. Here's when to use each:

| Feature | Claude (Anthropic) | OpenAI (GPT-4) | Use Case |
|---------|-------------------|----------------|----------|
| **Vision API** | ✅ Excellent for documents, diagrams | ✅ Great for photos, general images | Circuit analysis: Both work well |
| **Function Calling** | ✅ Native tool use | ✅ Function calling | Power calc: Both excellent |
| **Structured Output** | ✅ Via prompting | ✅ JSON mode | Data extraction: OpenAI slightly easier |
| **Context Window** | ✅ 200K tokens | ⚠️ 128K tokens | Long documents: Claude |
| **Cost** | ✅ More affordable | ⚠️ Higher cost | Budget apps: Claude |
| **Reasoning** | ✅ Strong analytical | ✅ Strong creative | Technical work: Claude |

### Setup for Both APIs

```bash
# Install SDKs
pip install anthropic openai

# Add to .env
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
```

---

## Part 1: Vision API

### Understanding Multimodal AI

Vision APIs allow LLMs to "see" and analyze images. Use cases:
- 📊 Circuit diagram analysis
- 📄 Document OCR and understanding
- 🖼️ Image description and classification
- 📈 Chart and graph interpretation
- 🔍 Visual inspection and quality control

### Example 1: Analyzing Circuit Diagrams

**Claude Vision:**

```python
import anthropic
import base64
from pathlib import Path

client = anthropic.Anthropic()

def analyze_circuit_claude(image_path: str, question: str = "Describe this circuit"):
    """Analyze circuit diagram with Claude."""

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Determine media type
    suffix = Path(image_path).suffix.lower()
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    media_type = media_types.get(suffix, "image/jpeg")

    # Create message with image
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }
        ]
    )

    return message.content[0].text

# Usage
analysis = analyze_circuit_claude(
    "circuit_diagram.png",
    "Identify all components and explain what this circuit does"
)
print(analysis)
```

**OpenAI Vision (GPT-4):**

```python
from openai import OpenAI
import base64

client = OpenAI()

def analyze_circuit_openai(image_path: str, question: str = "Describe this circuit"):
    """Analyze circuit diagram with GPT-4 Vision."""

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Create message with image
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content

# Usage
analysis = analyze_circuit_openai(
    "circuit_diagram.png",
    "Identify all components and explain what this circuit does"
)
print(analysis)
```

### Vision Best Practices

✅ **DO:**
- Use high-quality, clear images
- Provide specific questions
- For technical diagrams, use Claude (better at text/diagrams)
- Compress images to save costs (maintain readability)

❌ **DON'T:**
- Send blurry or low-resolution images
- Ask vague questions like "what is this?"
- Use vision for text-only content (use OCR or plain text)
- Send unnecessarily large images

---

## Part 2: Function Calling & Tool Use

### Understanding Function Calling

Function calling allows LLMs to interact with external systems:
- 🔢 Call calculators for precise math
- 🌐 Fetch real-time data (weather, stock prices)
- 💾 Query databases
- 📡 Call external APIs
- 🛠️ Execute custom business logic

### Power Electronics Calculator Example

Let's build a tool that calculates component values for power electronics circuits.

**Define Tools (Claude):**

```python
# Power electronics calculation tools
POWER_TOOLS = [
    {
        "name": "calculate_resistor_power",
        "description": "Calculate power dissipation in a resistor given voltage and current, or resistance and current",
        "input_schema": {
            "type": "object",
            "properties": {
                "voltage": {
                    "type": "number",
                    "description": "Voltage across resistor in volts (optional if current and resistance provided)"
                },
                "current": {
                    "type": "number",
                    "description": "Current through resistor in amperes"
                },
                "resistance": {
                    "type": "number",
                    "description": "Resistance in ohms (optional if voltage provided)"
                }
            },
            "required": ["current"]
        }
    },
    {
        "name": "calculate_capacitor_value",
        "description": "Calculate required capacitance for a given ripple voltage in a power supply",
        "input_schema": {
            "type": "object",
            "properties": {
                "load_current": {
                    "type": "number",
                    "description": "Load current in amperes"
                },
                "ripple_voltage": {
                    "type": "number",
                    "description": "Acceptable ripple voltage in volts"
                },
                "frequency": {
                    "type": "number",
                    "description": "Switching frequency in Hz"
                }
            },
            "required": ["load_current", "ripple_voltage", "frequency"]
        }
    },
    {
        "name": "select_mosfet",
        "description": "Recommend MOSFET based on voltage, current, and application requirements",
        "input_schema": {
            "type": "object",
            "properties": {
                "voltage_rating": {
                    "type": "number",
                    "description": "Required voltage rating in volts"
                },
                "current_rating": {
                    "type": "number",
                    "description": "Required current rating in amperes"
                },
                "application": {
                    "type": "string",
                    "enum": ["switching", "linear", "high_frequency"],
                    "description": "Application type"
                }
            },
            "required": ["voltage_rating", "current_rating", "application"]
        }
    }
]

# Implement the actual functions
def calculate_resistor_power(voltage=None, current=None, resistance=None):
    """Calculate power dissipation in resistor."""
    if voltage is not None and current is not None:
        power = voltage * current
        calc_method = "P = V × I"
    elif current is not None and resistance is not None:
        power = current ** 2 * resistance
        calc_method = "P = I² × R"
    elif voltage is not None and resistance is not None:
        power = voltage ** 2 / resistance
        calc_method = "P = V² / R"
    else:
        return {"error": "Insufficient parameters"}

    return {
        "power_watts": round(power, 3),
        "calculation": calc_method,
        "recommended_rating": round(power * 2, 1),  # 2x derating
        "note": "Use at least 2x rated power for safety margin"
    }

def calculate_capacitor_value(load_current, ripple_voltage, frequency):
    """Calculate capacitance for power supply."""
    # C = I / (f × ΔV)
    capacitance = load_current / (frequency * ripple_voltage)
    capacitance_uf = capacitance * 1e6  # Convert to microfarads

    # Recommend standard values
    standard_values = [10, 22, 47, 100, 220, 470, 1000, 2200, 4700]
    recommended = min([v for v in standard_values if v >= capacitance_uf], default=10000)

    return {
        "calculated_capacitance_uf": round(capacitance_uf, 2),
        "recommended_value_uf": recommended,
        "formula": "C = I / (f × ΔV)",
        "note": f"Use at least {recommended}µF capacitor rated for your voltage"
    }

def select_mosfet(voltage_rating, current_rating, application):
    """Recommend MOSFET based on requirements."""
    # Simple recommendation logic (in real app, query database)
    recommendations = {
        "switching": {
            "low_voltage": "IRFZ44N (55V, 49A, low RdsOn)",
            "medium_voltage": "IRFP260N (200V, 50A, good for PWM)",
            "high_voltage": "IRFP460 (500V, 20A, robust)"
        },
        "linear": {
            "low_voltage": "IRF540N (100V, 33A, stable)",
            "medium_voltage": "IRFP250N (200V, 30A, low noise)"
        },
        "high_frequency": {
            "low_voltage": "IRFS3006 (60V, 195A, ultra-low RdsOn)",
            "medium_voltage": "IPP60R099C6 (600V, CoolMOS)"
        }
    }

    # Determine voltage category
    if voltage_rating < 100:
        v_cat = "low_voltage"
    elif voltage_rating < 300:
        v_cat = "medium_voltage"
    else:
        v_cat = "high_voltage"

    app_recs = recommendations.get(application, recommendations["switching"])
    recommended = app_recs.get(v_cat, "Consult datasheet for specific requirements")

    return {
        "recommended_mosfet": recommended,
        "voltage_category": v_cat,
        "application_type": application,
        "additional_specs": {
            "voltage_derating": "Use 80% of rated voltage",
            "current_derating": "Use 70% of rated current for continuous operation",
            "heatsink": "Required for >10W dissipation"
        }
    }

# Map function names to implementations
TOOL_FUNCTIONS = {
    "calculate_resistor_power": calculate_resistor_power,
    "calculate_capacitor_value": calculate_capacitor_value,
    "select_mosfet": select_mosfet
}
```

**Using Tools with Claude:**

```python
def use_power_tools_claude(user_query: str):
    """Use power electronics tools with Claude."""

    # Initial request
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        tools=POWER_TOOLS,
        messages=[{"role": "user", "content": user_query}]
    )

    # Check if Claude wants to use tools
    if message.stop_reason == "tool_use":
        # Extract tool uses
        tool_uses = [block for block in message.content if block.type == "tool_use"]

        # Execute each tool
        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use.name
            tool_input = tool_use.input

            print(f"🔧 Calling: {tool_name}")
            print(f"   Input: {tool_input}")

            # Execute the function
            result = TOOL_FUNCTIONS[tool_name](**tool_input)

            print(f"   Result: {result}\n")

            # Add to results
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": str(result)
            })

        # Send results back to Claude
        final_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=POWER_TOOLS,
            messages=[
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": message.content},
                {"role": "user", "content": tool_results}
            ]
        )

        return final_response.content[0].text
    else:
        # No tools needed
        return message.content[0].text

# Test it
response = use_power_tools_claude(
    "I need a resistor for 12V with 0.5A current. What power rating should I use?"
)
print(response)
```

**Using Function Calling with OpenAI:**

```python
from openai import OpenAI

client_openai = OpenAI()

# Convert tools to OpenAI format
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_resistor_power",
            "description": "Calculate power dissipation in a resistor",
            "parameters": {
                "type": "object",
                "properties": {
                    "voltage": {"type": "number", "description": "Voltage in volts"},
                    "current": {"type": "number", "description": "Current in amperes"},
                    "resistance": {"type": "number", "description": "Resistance in ohms"}
                },
                "required": ["current"]
            }
        }
    }
    # ... add other tools
]

def use_power_tools_openai(user_query: str):
    """Use power electronics tools with OpenAI."""

    # Initial request
    response = client_openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": user_query}],
        tools=OPENAI_TOOLS,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # Check for tool calls
    if message.tool_calls:
        # Execute tools
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            print(f"🔧 Calling: {function_name}")
            print(f"   Args: {function_args}")

            # Execute function
            result = TOOL_FUNCTIONS[function_name](**function_args)

            print(f"   Result: {result}\n")

        # Continue conversation with results
        # (Full implementation in examples/)

    return message.content

# Test it
response = use_power_tools_openai(
    "I need a resistor for 12V with 0.5A current. What power rating should I use?"
)
print(response)
```

---

## Part 3: Building the Power Electronics Assistant

Let's build a complete assistant that combines vision and tools!

### Project Structure

```
power-electronics-assistant/
├── assistant.py          # Main assistant class
├── tools.py             # Calculation tools
├── vision.py            # Circuit analysis
├── knowledge_base.py    # Component database
└── cli.py              # Command-line interface
```

### Core Features

1. **Circuit Analysis** (Vision)
   - Analyze circuit diagrams
   - Identify components
   - Explain circuit operation

2. **Component Calculations** (Tools)
   - Power dissipation
   - Capacitor sizing
   - Inductor selection
   - MOSFET recommendations

3. **Design Assistance** (RAG - Module 4)
   - Look up datasheets
   - Find application notes
   - Provide design guidelines

4. **Interactive Chat** (Streaming)
   - Real-time responses
   - Multi-turn conversations
   - Context awareness

### Example Usage

```python
from power_electronics_assistant import PowerElectronicsAssistant

# Initialize assistant
assistant = PowerElectronicsAssistant(
    provider="claude",  # or "openai"
    enable_vision=True,
    enable_tools=True
)

# Analyze a circuit
result = assistant.analyze_circuit(
    image_path="buck_converter.png",
    question="What type of converter is this and what are the key components?"
)

# Calculate component values
result = assistant.calculate(
    query="I need capacitor for 5A load, 100mV ripple at 100kHz"
)

# Get design recommendations
result = assistant.recommend(
    query="Best MOSFET for 48V, 20A buck converter at 50kHz"
)

# Interactive chat
assistant.start_chat()
```

See `examples/power-electronics-assistant/` for complete implementation!

---

## Exercises

### Exercise 3.1: Vision API Practice

**Task:** Analyze different types of images
1. Circuit diagrams (power supply, amplifier)
2. PCB layouts
3. Component photos
4. Oscilloscope screenshots

**Challenge:** Build a circuit component detector

### Exercise 3.2: Custom Tools

**Task:** Create these tools for the assistant:
1. `calculate_inductor_value()` - For filter design
2. `calculate_snubber()` - Snubber circuit values
3. `thermal_analysis()` - Junction temperature calculation
4. `efficiency_calculator()` - Converter efficiency

### Exercise 3.3: Multi-Tool Orchestration

**Task:** Build a complete design flow:
1. User provides specifications
2. Assistant selects appropriate topology
3. Calculates all component values
4. Recommends specific parts
5. Validates design

### Exercise 3.4: Comparative Analysis

**Task:** Compare Claude vs OpenAI for:
- Circuit diagram analysis accuracy
- Calculation tool usage
- Response quality
- Cost effectiveness

Document your findings!

---

## Pro Tips & Best Practices

### Vision API Tips

```python
# ✅ Good: Specific, technical question
question = """
Analyze this buck converter circuit:
1. Identify the switching transistor and diode
2. What is the approximate duty cycle?
3. Calculate the output voltage if input is 12V
"""

# ❌ Bad: Vague question
question = "What is this?"
```

### Function Calling Tips

```python
# ✅ Good: Clear, specific tools
{
    "name": "calculate_duty_cycle",
    "description": "Calculate PWM duty cycle for buck converter given input and output voltages",
    # ... specific parameters
}

# ❌ Bad: Vague, multi-purpose tool
{
    "name": "do_calculation",
    "description": "Calculate stuff",
    # ... unclear parameters
}
```

### Error Handling

```python
def safe_tool_call(tool_name, **kwargs):
    """Safely execute tool with error handling."""
    try:
        result = TOOL_FUNCTIONS[tool_name](**kwargs)
        return {"success": True, "data": result}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestion": "Check input parameters and units"
        }
```

---

## Real-World Project: Power Electronics Assistant

See the complete implementation in `examples/power-electronics-assistant/`:

**Features:**
- ✅ Claude and OpenAI support
- ✅ Vision-based circuit analysis
- ✅ Multiple calculation tools
- ✅ Interactive CLI
- ✅ Design recommendations
- ✅ Cost tracking
- ✅ Conversation history

**Try it:**
```bash
cd examples/power-electronics-assistant
python cli.py

# Commands:
> analyze circuit.png
> calculate resistor 12V 0.5A
> recommend mosfet 48V 20A switching
> design buck-converter 12V 5V 3A
```

---

## Self-Assessment

Before moving to Module 4, ensure you can:

- [ ] Use vision APIs with both Claude and OpenAI
- [ ] Implement function calling / tool use
- [ ] Build custom tools for specific domains
- [ ] Handle multi-tool orchestration
- [ ] Choose between Claude and OpenAI appropriately
- [ ] Build a working assistant application

---

## Additional Resources

**Claude:**
- [Vision API Guide](https://docs.anthropic.com/en/docs/vision)
- [Tool Use Documentation](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)

**OpenAI:**
- [Vision API Guide](https://platform.openai.com/docs/guides/vision)
- [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

**Power Electronics:**
- TI Power Design Resources
- Analog Devices Design Tools
- Power Electronics Handbook

---

## Next Steps

**[Module 4: RAG Systems →](../04-rag/README.md)**

Enhance the Power Electronics Assistant with document search and datasheet lookup!

---

**Questions?** Check the examples or open a GitHub issue.
