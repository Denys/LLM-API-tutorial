# Week 2: Advanced API - Structured Output & Context

**Focus:** Moving beyond free-form text to machine-readable JSON output for engineering workflows.

**Prerequisites:** Basic Claude API usage, Python fundamentals
**Time:** 2-3 hours hands-on

---

## Table of Contents

1. [Why Structured Output?](#1-why-structured-output)
2. [JSON Mode](#2-json-mode)
3. [Schema Enforcement](#3-schema-enforcement)
4. [System Instructions](#4-system-instructions)
5. [PDF Processing](#5-pdf-processing)
6. [Hands-On Project: Datasheet Parameter Extractor](#6-hands-on-project-datasheet-parameter-extractor)
7. [Exercises](#7-exercises)

---

## 1. Why Structured Output?

### The Problem with Free-Form Text

```python
# Free-form response - hard to parse programmatically
response = """
The BSC010N04LS has a maximum drain-source voltage of 40V and can handle
up to 100A of continuous drain current. The on-resistance is typically
1.0 milliohms at Vgs=10V, and the total gate charge is 15nC.
"""

# How do you extract Vds_max = 40? Regex? String parsing? Fragile!
```

### The Solution: Structured JSON

```python
# Structured response - directly usable in code
response = {
    "part_number": "BSC010N04LS",
    "parameters": {
        "Vds_max": {"value": 40, "unit": "V"},
        "Id_max": {"value": 100, "unit": "A"},
        "Rds_on_typ": {"value": 1.0, "unit": "mΩ", "conditions": "Vgs=10V"},
        "Qg_typ": {"value": 15, "unit": "nC"}
    }
}

# Direct access
vds = response["parameters"]["Vds_max"]["value"]  # 40
```

### Engineering Use Cases

| Use Case | Why Structured Output? |
|----------|------------------------|
| BOM Generation | Export to Excel/ERP systems |
| Design Automation | Feed parameters into calculators |
| Database Population | Store in SQL/NoSQL databases |
| Report Generation | Consistent formatting |
| Tool Integration | Interface with SPICE, MATLAB |
| Comparison Tables | Standardized component comparison |

---

## 2. JSON Mode

### Basic JSON Output

Claude doesn't have a dedicated "JSON mode" flag like some APIs, but you can reliably get JSON output by:
1. Explicitly requesting JSON in the prompt
2. Providing a schema/example
3. Using system instructions

```python
import anthropic
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_json_response(prompt: str) -> dict:
    """Get JSON response from Claude."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"{prompt}\n\nRespond with valid JSON only. No markdown, no explanation."
        }]
    )

    # Parse JSON from response
    text = response.content[0].text

    # Handle potential markdown code blocks
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    return json.loads(text.strip())


# Example: Extract MOSFET parameters
result = get_json_response("""
Extract parameters for BSC010N04LS MOSFET:
- Vds_max: 40V
- Id_max: 100A
- Rds_on: 1.0 mΩ @ Vgs=10V
- Qg: 15 nC

Return as JSON with structure:
{
    "part_number": "string",
    "Vds_max_V": number,
    "Id_max_A": number,
    "Rds_on_mOhm": number,
    "Qg_nC": number
}
""")

print(json.dumps(result, indent=2))
```

### Robust JSON Extraction

```python
import re
from typing import Optional

def extract_json(text: str) -> Optional[dict]:
    """Extract JSON from response, handling various formats."""

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code block
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object/array pattern
    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    return None


def get_json_response_robust(prompt: str, max_retries: int = 2) -> dict:
    """Get JSON response with retry on parse failure."""

    for attempt in range(max_retries + 1):
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"{prompt}\n\nRespond with valid JSON only."
            }]
        )

        result = extract_json(response.content[0].text)

        if result is not None:
            return result

        if attempt < max_retries:
            print(f"JSON parse failed, retrying ({attempt + 1}/{max_retries})...")

    raise ValueError(f"Failed to get valid JSON after {max_retries + 1} attempts")
```

---

## 3. Schema Enforcement

### Why Schema Enforcement?

Without a schema, Claude might return:
- Missing fields
- Wrong data types (string instead of number)
- Inconsistent field names
- Extra unnecessary fields

### Using Pydantic for Schema Validation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from enum import Enum

# Define your schema
class ParameterValue(BaseModel):
    """Single parameter with value, unit, and conditions."""
    value: float
    unit: str
    conditions: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None

    @validator('value')
    def value_must_be_positive(cls, v, values):
        # Most electrical parameters are positive
        if v < 0 and 'temperature' not in str(values.get('unit', '')).lower():
            raise ValueError('Value must be positive for electrical parameters')
        return v


class MOSFETParameters(BaseModel):
    """MOSFET electrical parameters schema."""
    part_number: str
    manufacturer: str
    package: str

    # Absolute maximum ratings
    Vds_max: ParameterValue
    Vgs_max: ParameterValue
    Id_max: ParameterValue
    Pd_max: ParameterValue

    # Electrical characteristics
    Rds_on: ParameterValue
    Vgs_th: ParameterValue

    # Dynamic characteristics
    Qg: ParameterValue
    Qgd: Optional[ParameterValue] = None
    Qgs: Optional[ParameterValue] = None
    Qrr: Optional[ParameterValue] = None

    # Thermal
    Rth_jc: Optional[ParameterValue] = None
    Rth_ja: Optional[ParameterValue] = None


class PackageType(str, Enum):
    TDSON_8 = "TDSON-8"
    SO_8 = "SO-8"
    DPAK = "DPAK"
    D2PAK = "D2PAK"
    QFN = "QFN"
    TO_220 = "TO-220"


def get_validated_parameters(prompt: str) -> MOSFETParameters:
    """Get MOSFET parameters with schema validation."""

    # Include schema in prompt
    schema_example = {
        "part_number": "BSC010N04LS",
        "manufacturer": "Infineon",
        "package": "TDSON-8",
        "Vds_max": {"value": 40, "unit": "V"},
        "Vgs_max": {"value": 20, "unit": "V"},
        "Id_max": {"value": 100, "unit": "A", "conditions": "Tc=25°C"},
        "Pd_max": {"value": 88, "unit": "W", "conditions": "Tc=25°C"},
        "Rds_on": {"value": 1.0, "unit": "mΩ", "conditions": "Vgs=10V, Id=50A"},
        "Vgs_th": {"value": 2.5, "unit": "V", "min": 1.5, "max": 3.5},
        "Qg": {"value": 15, "unit": "nC", "conditions": "Vds=20V, Vgs=10V"},
        "Qgd": {"value": 3.5, "unit": "nC"},
        "Rth_jc": {"value": 1.0, "unit": "K/W"}
    }

    full_prompt = f"""{prompt}

Return JSON matching this exact schema:
{json.dumps(schema_example, indent=2)}

Important:
- All numeric values must be numbers, not strings
- Include units for every parameter
- Include measurement conditions where relevant
- Use null for unavailable parameters
"""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        messages=[{"role": "user", "content": full_prompt}]
    )

    # Extract and validate
    data = extract_json(response.content[0].text)

    if data is None:
        raise ValueError("Failed to extract JSON from response")

    # Pydantic validation
    return MOSFETParameters(**data)


# Usage
try:
    params = get_validated_parameters(
        "Extract parameters for BSC010N04LS from Infineon datasheet"
    )
    print(f"Part: {params.part_number}")
    print(f"Vds_max: {params.Vds_max.value} {params.Vds_max.unit}")
    print(f"Rds_on: {params.Rds_on.value} {params.Rds_on.unit}")
except Exception as e:
    print(f"Validation error: {e}")
```

### Nested Schemas for Complex Data

```python
from pydantic import BaseModel
from typing import List, Optional

class TestCondition(BaseModel):
    """Test condition for a parameter."""
    Vgs: Optional[float] = None  # Gate voltage
    Id: Optional[float] = None   # Drain current
    Vds: Optional[float] = None  # Drain voltage
    Tc: Optional[float] = None   # Case temperature
    Tj: Optional[float] = None   # Junction temperature


class ParameterSpec(BaseModel):
    """Complete parameter specification."""
    symbol: str
    description: str
    min: Optional[float] = None
    typ: Optional[float] = None
    max: Optional[float] = None
    unit: str
    conditions: Optional[TestCondition] = None


class DatasheetExtract(BaseModel):
    """Complete datasheet extraction."""
    part_number: str
    manufacturer: str
    description: str
    package: str

    absolute_maximum_ratings: List[ParameterSpec]
    electrical_characteristics: List[ParameterSpec]
    thermal_characteristics: List[ParameterSpec]

    features: List[str]
    applications: List[str]

    # Metadata
    datasheet_revision: Optional[str] = None
    extraction_confidence: float = Field(ge=0, le=1)


# Generate schema description for Claude
def get_schema_description(model: type) -> str:
    """Generate human-readable schema description."""
    schema = model.model_json_schema()
    return json.dumps(schema, indent=2)
```

---

## 4. System Instructions

### Setting the AI Persona

System instructions define Claude's behavior, expertise level, and response style. Critical for consistent engineering outputs.

```python
def create_engineering_assistant():
    """Create Claude client with engineering system prompt."""

    system_prompt = """You are a Senior Power Electronics Engineer with 15+ years of experience in:
- Switch-mode power supply design
- MOSFET/GaN device selection and characterization
- Thermal management and reliability analysis
- EMI/EMC compliance

Response Guidelines:
1. Be precise and quantitative - always include units
2. Reference actual component parameters from datasheets
3. Consider worst-case conditions (temperature, tolerances)
4. Flag safety concerns proactively
5. Use standard engineering notation (e.g., 1.5mΩ, not 0.0015Ω)

When extracting datasheet parameters:
- Distinguish between min/typ/max values
- Include test conditions (Vgs, Id, Tc, etc.)
- Note any derating factors
- Flag parameters that seem inconsistent or unusual

Output Format:
- For structured data: Return valid JSON only
- For analysis: Use clear sections with headers
- For calculations: Show intermediate steps"""

    return system_prompt


def query_with_system(user_prompt: str, system_prompt: str) -> str:
    """Query Claude with custom system instructions."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )

    return response.content[0].text


# Usage
system = create_engineering_assistant()

result = query_with_system(
    "Compare BSC010N04LS vs IPD90N04S4L-02 for 48V to 12V buck converter at 20A",
    system
)
print(result)
```

### Task-Specific System Instructions

```python
# For parameter extraction
EXTRACTION_SYSTEM = """You are a datasheet parameter extraction system.

Your task is to extract electrical parameters from component datasheets with high precision.

Rules:
1. Extract ONLY information explicitly stated in the datasheet
2. If a parameter is not found, use null - never guess
3. Always include the exact test conditions
4. Preserve the original units from the datasheet
5. Note any footnotes or special conditions
6. Flag any values that appear to be typos or errors

Output: Valid JSON only. No explanations or markdown."""


# For design calculations
CALCULATION_SYSTEM = """You are a power electronics design calculator.

For every calculation:
1. State the formula being used
2. List all input values with units
3. Show substitution step
4. Calculate intermediate results
5. State final answer with appropriate significant figures
6. Verify result is physically reasonable

Use SI units internally, convert to engineering units for output.
Flag any assumptions made."""


# For component selection
SELECTION_SYSTEM = """You are a component selection advisor for power electronics.

When recommending components:
1. Consider: performance, cost, availability, package options
2. Provide 2-3 alternatives with trade-off analysis
3. Include specific part numbers from major manufacturers
4. Note any critical parameters that limit selection
5. Consider second-source options
6. Flag end-of-life or NRND (not recommended for new designs) parts

Always explain WHY a component is recommended for the specific application."""
```

### Multi-Turn Conversations with Context

```python
class EngineeringSession:
    """Maintain conversation context for engineering analysis."""

    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages = []
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def ask(self, question: str) -> str:
        """Ask a question, maintaining conversation history."""

        self.messages.append({
            "role": "user",
            "content": question
        })

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=self.messages
        )

        assistant_message = response.content[0].text

        self.messages.append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    def reset(self):
        """Clear conversation history."""
        self.messages = []


# Usage - multi-turn design session
session = EngineeringSession(create_engineering_assistant())

# First question
response1 = session.ask(
    "I need to design a 48V to 12V/20A buck converter. What switching frequency would you recommend?"
)
print("Q1:", response1)

# Follow-up uses context
response2 = session.ask(
    "Based on that frequency, what inductance should I use for 30% ripple?"
)
print("Q2:", response2)

# Another follow-up
response3 = session.ask(
    "Now recommend a MOSFET for the high-side switch"
)
print("Q3:", response3)
```

---

## 5. PDF Processing

### Claude's PDF Capabilities

Claude can directly process PDF documents, including:
- Text extraction
- Table parsing
- Figure/chart understanding
- Multi-page analysis

### Sending PDFs to Claude

```python
import anthropic
import base64
from pathlib import Path

def encode_pdf(pdf_path: str) -> str:
    """Encode PDF file to base64."""
    with open(pdf_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def analyze_pdf(pdf_path: str, prompt: str) -> str:
    """Send PDF to Claude for analysis."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    pdf_data = encode_pdf(pdf_path)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
    )

    return response.content[0].text


# Example: Extract parameters from datasheet PDF
pdf_path = "datasheets/BSC010N04LS.pdf"

result = analyze_pdf(
    pdf_path,
    """Extract all electrical parameters from this MOSFET datasheet.

Return as JSON with structure:
{
    "part_number": "string",
    "manufacturer": "string",
    "absolute_maximum_ratings": {
        "Vds": {"value": number, "unit": "V"},
        "Vgs": {"value": number, "unit": "V"},
        "Id": {"value": number, "unit": "A", "conditions": "string"},
        "Pd": {"value": number, "unit": "W", "conditions": "string"}
    },
    "electrical_characteristics": {
        "Rds_on": {"min": number, "typ": number, "max": number, "unit": "mΩ", "conditions": "string"},
        "Vgs_th": {"min": number, "typ": number, "max": number, "unit": "V"},
        "Qg": {"typ": number, "unit": "nC", "conditions": "string"},
        "Qgd": {"typ": number, "unit": "nC"},
        "Qgs": {"typ": number, "unit": "nC"},
        "Ciss": {"typ": number, "unit": "pF"},
        "Coss": {"typ": number, "unit": "pF"},
        "Crss": {"typ": number, "unit": "pF"}
    },
    "thermal": {
        "Rth_jc": {"value": number, "unit": "K/W"},
        "Rth_ja": {"value": number, "unit": "K/W"}
    }
}

Include test conditions for each parameter."""
)

print(result)
```

### Processing Multiple Pages

```python
def extract_from_multipage_pdf(
    pdf_path: str,
    extraction_prompt: str,
    pages_to_analyze: str = "all"
) -> dict:
    """Extract structured data from multi-page PDF.

    Args:
        pdf_path: Path to PDF file
        extraction_prompt: What to extract
        pages_to_analyze: "all", "first", "1-5", etc.

    Returns:
        Extracted data as dictionary
    """

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    pdf_data = encode_pdf(pdf_path)

    system_prompt = """You are a technical document parser specialized in electronic component datasheets.

When extracting data:
1. Focus on tables with electrical specifications
2. Note the test conditions column carefully
3. Distinguish between guaranteed min/max vs typical values
4. Include relevant footnotes
5. Return valid JSON only"""

    full_prompt = f"""Analyze this datasheet and extract the requested information.

Pages to analyze: {pages_to_analyze}

{extraction_prompt}

Return valid JSON only. No markdown formatting."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": full_prompt
                }
            ]
        }]
    )

    return extract_json(response.content[0].text)
```

### Handling Large Datasheets

```python
import anthropic
from typing import List, Dict

def extract_from_large_datasheet(
    pdf_path: str,
    sections_to_extract: List[str]
) -> Dict:
    """Extract specific sections from large datasheets.

    For datasheets > 50 pages, extract specific sections rather than entire document.

    Args:
        pdf_path: Path to PDF
        sections_to_extract: List of section names
            e.g., ["Absolute Maximum Ratings", "Electrical Characteristics", "Thermal Data"]

    Returns:
        Dictionary with extracted sections
    """

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    pdf_data = encode_pdf(pdf_path)

    sections_list = "\n".join(f"- {s}" for s in sections_to_extract)

    prompt = f"""From this datasheet, extract ONLY the following sections:
{sections_list}

For each section, extract all parameters as structured JSON.

Return format:
{{
    "part_number": "string",
    "sections": {{
        "section_name": [
            {{
                "parameter": "string",
                "symbol": "string",
                "min": number or null,
                "typ": number or null,
                "max": number or null,
                "unit": "string",
                "conditions": "string"
            }}
        ]
    }}
}}

Focus on accuracy. If a value is not clearly stated, use null."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8192,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }]
    )

    return extract_json(response.content[0].text)


# Usage
result = extract_from_large_datasheet(
    "datasheets/LM5146.pdf",
    [
        "Absolute Maximum Ratings",
        "Recommended Operating Conditions",
        "Electrical Characteristics",
        "Timing Requirements"
    ]
)
```

---

## 6. Hands-On Project: Datasheet Parameter Extractor

### Project Overview

Build a complete tool that:
1. Takes a MOSFET datasheet PDF
2. Extracts key parameters into structured JSON
3. Validates the extraction
4. Exports to multiple formats (JSON, CSV, Excel)

### Project Structure

```
datasheet_extractor/
├── src/
│   ├── __init__.py
│   ├── extractor.py      # Main extraction logic
│   ├── schemas.py        # Pydantic schemas
│   ├── exporters.py      # Export to JSON/CSV/Excel
│   └── validators.py     # Parameter validation
├── tests/
│   └── test_extractor.py
├── datasheets/           # Input PDFs
├── output/               # Extracted data
├── main.py
├── requirements.txt
└── .env
```

### Schema Definitions

```python
# src/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from enum import Enum

class PackageType(str, Enum):
    TDSON_8 = "TDSON-8"
    SO_8 = "SO-8"
    DPAK = "DPAK"
    D2PAK = "D2PAK"
    QFN_5x6 = "QFN-5x6"
    TO_220 = "TO-220"
    TO_247 = "TO-247"
    LFPAK = "LFPAK"


class ParameterValue(BaseModel):
    """Single parameter value with metadata."""
    value: Optional[float] = None
    min: Optional[float] = None
    typ: Optional[float] = None
    max: Optional[float] = None
    unit: str
    conditions: Optional[str] = None
    notes: Optional[str] = None

    @validator('unit')
    def standardize_unit(cls, v):
        """Standardize unit notation."""
        replacements = {
            'mohm': 'mΩ',
            'mOhm': 'mΩ',
            'milliohm': 'mΩ',
            'nc': 'nC',
            'pf': 'pF',
            'uf': 'µF',
            'degc': '°C',
            'deg c': '°C'
        }
        return replacements.get(v.lower(), v)


class AbsoluteMaximumRatings(BaseModel):
    """Absolute maximum ratings - do not exceed."""
    Vds: ParameterValue = Field(description="Drain-source voltage")
    Vgs: ParameterValue = Field(description="Gate-source voltage")
    Id_25C: ParameterValue = Field(description="Continuous drain current @ Tc=25°C")
    Id_100C: Optional[ParameterValue] = Field(description="Continuous drain current @ Tc=100°C")
    Idm: Optional[ParameterValue] = Field(description="Pulsed drain current")
    Pd: ParameterValue = Field(description="Power dissipation")
    Tj: ParameterValue = Field(description="Operating junction temperature")
    Tstg: Optional[ParameterValue] = Field(description="Storage temperature")


class ElectricalCharacteristics(BaseModel):
    """Static and dynamic electrical characteristics."""
    # Static
    Vgs_th: ParameterValue = Field(description="Gate threshold voltage")
    Rds_on: ParameterValue = Field(description="Drain-source on-resistance")
    Idss: Optional[ParameterValue] = Field(description="Drain-source leakage current")
    Igss: Optional[ParameterValue] = Field(description="Gate-source leakage current")

    # Dynamic
    Qg: ParameterValue = Field(description="Total gate charge")
    Qgd: Optional[ParameterValue] = Field(description="Gate-drain charge")
    Qgs: Optional[ParameterValue] = Field(description="Gate-source charge")
    Qoss: Optional[ParameterValue] = Field(description="Output charge")
    Qrr: Optional[ParameterValue] = Field(description="Reverse recovery charge")

    # Capacitances
    Ciss: Optional[ParameterValue] = Field(description="Input capacitance")
    Coss: Optional[ParameterValue] = Field(description="Output capacitance")
    Crss: Optional[ParameterValue] = Field(description="Reverse transfer capacitance")

    # Timing
    td_on: Optional[ParameterValue] = Field(description="Turn-on delay time")
    tr: Optional[ParameterValue] = Field(description="Rise time")
    td_off: Optional[ParameterValue] = Field(description="Turn-off delay time")
    tf: Optional[ParameterValue] = Field(description="Fall time")


class ThermalCharacteristics(BaseModel):
    """Thermal resistance values."""
    Rth_jc: ParameterValue = Field(description="Junction-to-case thermal resistance")
    Rth_ja: Optional[ParameterValue] = Field(description="Junction-to-ambient thermal resistance")


class MOSFETDatasheet(BaseModel):
    """Complete MOSFET datasheet extraction."""
    # Identification
    part_number: str
    manufacturer: str
    description: str
    package: str

    # Parameters
    absolute_maximum_ratings: AbsoluteMaximumRatings
    electrical_characteristics: ElectricalCharacteristics
    thermal_characteristics: ThermalCharacteristics

    # Additional info
    features: List[str] = []
    applications: List[str] = []

    # Metadata
    datasheet_version: Optional[str] = None
    extraction_date: Optional[str] = None
    confidence_score: float = Field(ge=0, le=1, default=0.9)


# Simplified schema for quick extraction
class QuickMOSFETParams(BaseModel):
    """Essential MOSFET parameters for quick extraction."""
    part_number: str
    manufacturer: str
    Vds_max_V: float
    Id_max_A: float
    Rds_on_mOhm: float
    Rds_on_conditions: str
    Qg_nC: float
    Qgd_nC: Optional[float] = None
    Rth_jc_KW: float
    package: str
```

### Main Extractor

```python
# src/extractor.py
import anthropic
import json
import base64
from pathlib import Path
from typing import Optional, Union
from datetime import datetime
import os
from dotenv import load_dotenv

from .schemas import MOSFETDatasheet, QuickMOSFETParams, ParameterValue

load_dotenv()


class DatasheetExtractor:
    """Extract structured parameters from MOSFET datasheets."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

        self.system_prompt = """You are an expert power electronics engineer specializing in MOSFET characterization and datasheet analysis.

Your task is to extract electrical parameters from MOSFET datasheets with high precision.

Extraction Rules:
1. Extract ONLY values explicitly stated in the datasheet
2. If a parameter is not found, use null
3. Always include complete test conditions (Vgs, Id, Tc, etc.)
4. Preserve original units from datasheet
5. For min/typ/max, extract all available values
6. Note any important footnotes or derating information
7. If values seem incorrect or inconsistent, flag them in notes

Output: Valid JSON only. No explanations or markdown formatting."""

    def _encode_pdf(self, pdf_path: Union[str, Path]) -> str:
        """Encode PDF to base64."""
        with open(pdf_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from response text."""
        import re

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object
        match = re.search(r'(\{[\s\S]*\})', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return None

    def extract_quick(self, pdf_path: Union[str, Path]) -> QuickMOSFETParams:
        """Quick extraction of essential parameters.

        Args:
            pdf_path: Path to MOSFET datasheet PDF

        Returns:
            QuickMOSFETParams with essential values
        """
        pdf_data = self._encode_pdf(pdf_path)

        prompt = """Extract these essential MOSFET parameters:

{
    "part_number": "string",
    "manufacturer": "string",
    "Vds_max_V": number,
    "Id_max_A": number (at Tc=25°C),
    "Rds_on_mOhm": number (typical value),
    "Rds_on_conditions": "string (e.g., Vgs=10V, Id=50A)",
    "Qg_nC": number (typical),
    "Qgd_nC": number or null,
    "Rth_jc_KW": number,
    "package": "string"
}

Return valid JSON only."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=self.system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        data = self._extract_json(response.content[0].text)

        if data is None:
            raise ValueError("Failed to extract JSON from response")

        return QuickMOSFETParams(**data)

    def extract_full(self, pdf_path: Union[str, Path]) -> MOSFETDatasheet:
        """Full extraction of all datasheet parameters.

        Args:
            pdf_path: Path to MOSFET datasheet PDF

        Returns:
            MOSFETDatasheet with complete parameter set
        """
        pdf_data = self._encode_pdf(pdf_path)

        # Create schema example
        schema_example = {
            "part_number": "BSC010N04LS",
            "manufacturer": "Infineon",
            "description": "OptiMOS 40V N-channel MOSFET",
            "package": "TDSON-8",
            "absolute_maximum_ratings": {
                "Vds": {"value": 40, "unit": "V"},
                "Vgs": {"value": 20, "unit": "V"},
                "Id_25C": {"value": 100, "unit": "A", "conditions": "Tc=25°C"},
                "Id_100C": {"value": 70, "unit": "A", "conditions": "Tc=100°C"},
                "Idm": {"value": 400, "unit": "A", "conditions": "tp=100µs"},
                "Pd": {"value": 88, "unit": "W", "conditions": "Tc=25°C"},
                "Tj": {"min": -55, "max": 175, "unit": "°C"},
                "Tstg": {"min": -55, "max": 175, "unit": "°C"}
            },
            "electrical_characteristics": {
                "Vgs_th": {"min": 1.5, "typ": 2.5, "max": 3.5, "unit": "V", "conditions": "Vds=Vgs, Id=100µA"},
                "Rds_on": {"typ": 1.0, "max": 1.4, "unit": "mΩ", "conditions": "Vgs=10V, Id=50A"},
                "Idss": {"max": 1, "unit": "µA", "conditions": "Vds=40V, Vgs=0V"},
                "Igss": {"max": 100, "unit": "nA", "conditions": "Vgs=20V"},
                "Qg": {"typ": 15, "unit": "nC", "conditions": "Vds=20V, Vgs=10V, Id=50A"},
                "Qgd": {"typ": 3.5, "unit": "nC"},
                "Qgs": {"typ": 5.5, "unit": "nC"},
                "Qoss": {"typ": 25, "unit": "nC", "conditions": "Vds=20V"},
                "Qrr": {"typ": 35, "unit": "nC", "conditions": "If=50A, di/dt=100A/µs"},
                "Ciss": {"typ": 2500, "unit": "pF", "conditions": "Vds=20V, Vgs=0V, f=1MHz"},
                "Coss": {"typ": 500, "unit": "pF"},
                "Crss": {"typ": 50, "unit": "pF"},
                "td_on": {"typ": 8, "unit": "ns"},
                "tr": {"typ": 4, "unit": "ns"},
                "td_off": {"typ": 20, "unit": "ns"},
                "tf": {"typ": 5, "unit": "ns"}
            },
            "thermal_characteristics": {
                "Rth_jc": {"value": 1.0, "unit": "K/W"},
                "Rth_ja": {"value": 62, "unit": "K/W"}
            },
            "features": [
                "OptiMOS technology",
                "N-channel enhancement mode",
                "100% avalanche tested"
            ],
            "applications": [
                "DC-DC converters",
                "Motor drives",
                "Battery management"
            ],
            "datasheet_version": "Rev 2.5",
            "extraction_date": "2024-01-15",
            "confidence_score": 0.95
        }

        prompt = f"""Extract ALL parameters from this MOSFET datasheet.

Use this exact JSON structure:
{json.dumps(schema_example, indent=2)}

Important:
- Extract all min/typ/max values where available
- Include complete test conditions
- Use null for unavailable parameters
- Note extraction confidence (0-1)

Return valid JSON only."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=self.system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }]
        )

        data = self._extract_json(response.content[0].text)

        if data is None:
            raise ValueError("Failed to extract JSON from response")

        # Add extraction date if not present
        if "extraction_date" not in data or data["extraction_date"] is None:
            data["extraction_date"] = datetime.now().isoformat()

        return MOSFETDatasheet(**data)

    def compare_parts(
        self,
        pdf_paths: list,
        parameters: list = None
    ) -> dict:
        """Compare multiple MOSFETs from datasheets.

        Args:
            pdf_paths: List of PDF paths
            parameters: Parameters to compare (default: key switching params)

        Returns:
            Comparison dictionary
        """
        if parameters is None:
            parameters = ["Vds_max", "Id_max", "Rds_on", "Qg", "Qgd", "Rth_jc"]

        results = {}
        for path in pdf_paths:
            params = self.extract_quick(path)
            results[params.part_number] = params.model_dump()

        return results
```

### Export Functions

```python
# src/exporters.py
import json
import csv
from pathlib import Path
from typing import Union
import pandas as pd

from .schemas import MOSFETDatasheet, QuickMOSFETParams


def export_to_json(
    data: Union[MOSFETDatasheet, QuickMOSFETParams],
    output_path: Union[str, Path],
    indent: int = 2
) -> None:
    """Export extracted data to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data.model_dump(), f, indent=indent)
    print(f"Exported to {output_path}")


def export_to_csv(
    data: Union[MOSFETDatasheet, QuickMOSFETParams],
    output_path: Union[str, Path]
) -> None:
    """Export extracted data to CSV file."""

    if isinstance(data, QuickMOSFETParams):
        # Simple flat export
        df = pd.DataFrame([data.model_dump()])
    else:
        # Flatten nested structure for full export
        flat_data = {
            "part_number": data.part_number,
            "manufacturer": data.manufacturer,
            "package": data.package,
        }

        # Add absolute maximum ratings
        for key, value in data.absolute_maximum_ratings.model_dump().items():
            if value and isinstance(value, dict):
                if value.get('value') is not None:
                    flat_data[f"{key}"] = value['value']
                elif value.get('max') is not None:
                    flat_data[f"{key}_max"] = value['max']
                if value.get('unit'):
                    flat_data[f"{key}_unit"] = value['unit']

        # Add electrical characteristics
        for key, value in data.electrical_characteristics.model_dump().items():
            if value and isinstance(value, dict):
                if value.get('typ') is not None:
                    flat_data[f"{key}_typ"] = value['typ']
                if value.get('max') is not None:
                    flat_data[f"{key}_max"] = value['max']
                if value.get('unit'):
                    flat_data[f"{key}_unit"] = value['unit']

        df = pd.DataFrame([flat_data])

    df.to_csv(output_path, index=False)
    print(f"Exported to {output_path}")


def export_to_excel(
    data: MOSFETDatasheet,
    output_path: Union[str, Path]
) -> None:
    """Export extracted data to Excel with multiple sheets."""

    with pd.ExcelWriter(output_path) as writer:
        # Summary sheet
        summary = pd.DataFrame([{
            "Part Number": data.part_number,
            "Manufacturer": data.manufacturer,
            "Description": data.description,
            "Package": data.package,
            "Extraction Date": data.extraction_date
        }])
        summary.to_excel(writer, sheet_name="Summary", index=False)

        # Absolute maximum ratings
        max_ratings = []
        for key, value in data.absolute_maximum_ratings.model_dump().items():
            if value:
                max_ratings.append({
                    "Parameter": key,
                    "Min": value.get('min'),
                    "Typ": value.get('typ'),
                    "Max": value.get('max'),
                    "Value": value.get('value'),
                    "Unit": value.get('unit'),
                    "Conditions": value.get('conditions')
                })
        pd.DataFrame(max_ratings).to_excel(
            writer, sheet_name="Maximum Ratings", index=False
        )

        # Electrical characteristics
        elec_chars = []
        for key, value in data.electrical_characteristics.model_dump().items():
            if value:
                elec_chars.append({
                    "Parameter": key,
                    "Min": value.get('min'),
                    "Typ": value.get('typ'),
                    "Max": value.get('max'),
                    "Unit": value.get('unit'),
                    "Conditions": value.get('conditions')
                })
        pd.DataFrame(elec_chars).to_excel(
            writer, sheet_name="Electrical Characteristics", index=False
        )

        # Thermal
        thermal = []
        for key, value in data.thermal_characteristics.model_dump().items():
            if value:
                thermal.append({
                    "Parameter": key,
                    "Value": value.get('value'),
                    "Unit": value.get('unit')
                })
        pd.DataFrame(thermal).to_excel(
            writer, sheet_name="Thermal", index=False
        )

    print(f"Exported to {output_path}")


def create_comparison_table(
    parts_data: list[QuickMOSFETParams]
) -> pd.DataFrame:
    """Create comparison table for multiple MOSFETs."""

    data = []
    for part in parts_data:
        data.append({
            "Part Number": part.part_number,
            "Manufacturer": part.manufacturer,
            "Vds (V)": part.Vds_max_V,
            "Id (A)": part.Id_max_A,
            "Rds_on (mΩ)": part.Rds_on_mOhm,
            "Qg (nC)": part.Qg_nC,
            "Qgd (nC)": part.Qgd_nC,
            "Rth_jc (K/W)": part.Rth_jc_KW,
            "Package": part.package,
            "FOM (Rds*Qg)": part.Rds_on_mOhm * part.Qg_nC
        })

    df = pd.DataFrame(data)
    # Sort by figure of merit
    df = df.sort_values("FOM (Rds*Qg)")

    return df
```

### Main Application

```python
# main.py
import argparse
from pathlib import Path
import json

from src.extractor import DatasheetExtractor
from src.exporters import export_to_json, export_to_csv, export_to_excel, create_comparison_table


def main():
    parser = argparse.ArgumentParser(
        description="Extract MOSFET parameters from datasheets"
    )
    parser.add_argument(
        "pdf",
        help="Path to PDF datasheet (or multiple for comparison)"
    )
    parser.add_argument(
        "--mode",
        choices=["quick", "full"],
        default="quick",
        help="Extraction mode (default: quick)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path"
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "excel"],
        default="json",
        help="Output format (default: json)"
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        return 1

    # Create extractor
    extractor = DatasheetExtractor()

    # Extract parameters
    print(f"Extracting from: {pdf_path}")
    print(f"Mode: {args.mode}")

    try:
        if args.mode == "quick":
            data = extractor.extract_quick(pdf_path)
        else:
            data = extractor.extract_full(pdf_path)

        # Display results
        print("\n" + "=" * 50)
        print("Extraction Results")
        print("=" * 50)

        if args.mode == "quick":
            print(f"Part: {data.part_number}")
            print(f"Manufacturer: {data.manufacturer}")
            print(f"Package: {data.package}")
            print(f"Vds_max: {data.Vds_max_V} V")
            print(f"Id_max: {data.Id_max_A} A")
            print(f"Rds_on: {data.Rds_on_mOhm} mΩ ({data.Rds_on_conditions})")
            print(f"Qg: {data.Qg_nC} nC")
            if data.Qgd_nC:
                print(f"Qgd: {data.Qgd_nC} nC")
            print(f"Rth_jc: {data.Rth_jc_KW} K/W")
            print(f"\nFigure of Merit (Rds*Qg): {data.Rds_on_mOhm * data.Qg_nC:.1f} mΩ·nC")
        else:
            print(json.dumps(data.model_dump(), indent=2))

        # Export if output specified
        if args.output:
            output_path = Path(args.output)

            if args.format == "json":
                export_to_json(data, output_path)
            elif args.format == "csv":
                export_to_csv(data, output_path)
            elif args.format == "excel":
                if args.mode == "quick":
                    print("Excel export requires full mode")
                    return 1
                export_to_excel(data, output_path)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
```

### Requirements

```text
# requirements.txt
anthropic>=0.18.0
pydantic>=2.0.0
pandas>=2.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
pytest>=7.0.0
```

### Usage Examples

```bash
# Quick extraction
python main.py datasheets/BSC010N04LS.pdf

# Full extraction with JSON export
python main.py datasheets/BSC010N04LS.pdf --mode full -o output/BSC010N04LS.json

# Export to CSV
python main.py datasheets/BSC010N04LS.pdf -o output/params.csv --format csv

# Full extraction to Excel
python main.py datasheets/BSC010N04LS.pdf --mode full -o output/BSC010N04LS.xlsx --format excel
```

### Unit Tests

```python
# tests/test_extractor.py
import pytest
from src.schemas import QuickMOSFETParams, ParameterValue, MOSFETDatasheet
from src.exporters import create_comparison_table

def test_quick_params_validation():
    """Test QuickMOSFETParams schema validation."""
    params = QuickMOSFETParams(
        part_number="BSC010N04LS",
        manufacturer="Infineon",
        Vds_max_V=40,
        Id_max_A=100,
        Rds_on_mOhm=1.0,
        Rds_on_conditions="Vgs=10V, Id=50A",
        Qg_nC=15,
        Qgd_nC=3.5,
        Rth_jc_KW=1.0,
        package="TDSON-8"
    )

    assert params.Vds_max_V == 40
    assert params.Rds_on_mOhm == 1.0


def test_parameter_value_unit_standardization():
    """Test unit standardization."""
    param = ParameterValue(value=1.0, unit="mohm")
    assert param.unit == "mΩ"

    param = ParameterValue(value=15, unit="nc")
    assert param.unit == "nC"


def test_comparison_table():
    """Test comparison table generation."""
    parts = [
        QuickMOSFETParams(
            part_number="PART_A",
            manufacturer="Mfg1",
            Vds_max_V=40,
            Id_max_A=100,
            Rds_on_mOhm=1.0,
            Rds_on_conditions="Vgs=10V",
            Qg_nC=15,
            Rth_jc_KW=1.0,
            package="PKG"
        ),
        QuickMOSFETParams(
            part_number="PART_B",
            manufacturer="Mfg2",
            Vds_max_V=40,
            Id_max_A=80,
            Rds_on_mOhm=1.5,
            Rds_on_conditions="Vgs=10V",
            Qg_nC=12,
            Rth_jc_KW=1.2,
            package="PKG"
        )
    ]

    df = create_comparison_table(parts)

    assert len(df) == 2
    assert "FOM (Rds*Qg)" in df.columns
    # PART_A has better FOM: 1.0 * 15 = 15 < 1.5 * 12 = 18
    assert df.iloc[0]["Part Number"] == "PART_A"


def test_fom_calculation():
    """Test figure of merit calculation."""
    params = QuickMOSFETParams(
        part_number="TEST",
        manufacturer="Test",
        Vds_max_V=40,
        Id_max_A=100,
        Rds_on_mOhm=1.0,
        Rds_on_conditions="Vgs=10V",
        Qg_nC=15,
        Rth_jc_KW=1.0,
        package="PKG"
    )

    fom = params.Rds_on_mOhm * params.Qg_nC
    assert fom == 15.0


# Run with: pytest tests/ -v
```

---

## 7. Exercises

### Exercise 1: Basic JSON Extraction (20 min)
1. Create a function that extracts inductor parameters from text description
2. Schema: part_number, inductance_uH, dcr_mOhm, isat_A, irms_A
3. Test with: "XAL7070-152MEB: 15µH, DCR 3.8mΩ, Isat 28A, Irms 22A"

### Exercise 2: System Instructions (20 min)
1. Create system prompt for a "Conservative Design Engineer"
2. Personality: Always uses worst-case values, adds safety margins
3. Test by asking for MOSFET junction temperature calculation

### Exercise 3: Schema Validation (30 min)
1. Extend ParameterValue to include:
   - `temperature_coefficient`: Optional percentage per °C
   - `tolerance`: Optional percentage
2. Add validators to ensure physical consistency
3. Test with Rds_on temperature coefficient

### Exercise 4: PDF Comparison (45 min)
1. Download 3 similar MOSFET datasheets (40V, 100A class)
2. Extract parameters from all three using the extractor
3. Create comparison table with FOM (Rds_on × Qg)
4. Export to Excel with formatting

### Exercise 5: Multi-Turn Extraction (30 min)
1. Modify DatasheetExtractor to use conversation context
2. First message: Extract absolute maximum ratings
3. Second message: "Now extract the switching characteristics"
4. Third message: "Calculate FOM and recommend applications"

### Exercise 6: Batch Processing (45 min)
1. Create async version of DatasheetExtractor
2. Process 5 datasheets in parallel
3. Add progress tracking
4. Generate combined comparison report

---

## Pro Tips

1. **Always include schema examples** - Claude follows examples more reliably than descriptions
2. **Validate before using** - Pydantic catches issues immediately
3. **Use null explicitly** - Better than having Claude guess values
4. **Include test conditions** - Parameters without conditions are incomplete
5. **Request confidence scores** - Helps identify uncertain extractions
6. **Standardize units** - Convert everything to consistent notation
7. **Log API calls** - Track token usage and costs
8. **Cache results** - Don't re-extract unchanged datasheets
9. **Version control extractions** - Track changes over datasheet revisions
10. **Cross-validate** - Compare extracted values against known references

---

## Next Steps

After mastering structured output:
1. **Module 3:** Function calling for dynamic parameter lookup
2. **Module 4:** RAG for datasheet Q&A system
3. **Module 7:** Build autonomous component selection agent

---

**Ready to build your datasheet extractor? Download a MOSFET PDF and start extracting!**
