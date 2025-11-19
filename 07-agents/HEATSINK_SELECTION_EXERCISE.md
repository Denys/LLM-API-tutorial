# Heatsink Calculation and Selection Exercise

Comprehensive exercise for building an intelligent heatsink selection system using Claude and Gemini AI ecosystems.

---

## Exercise Overview

**Objective:** Build an AI-powered system that calculates semiconductor losses, determines thermal requirements, and selects appropriate heatsinks from a database or web search.

**Duration:** 120 minutes

**Skills Practiced:**
- Tool creation and management
- Power loss calculations (SiC MOSFETs and diodes)
- Thermal resistance calculations
- Database operations with fallback to web search
- Multi-step reasoning with AI assistants

---

## Algorithm Flow

```
┌─────────────────────────┐
│ 1. Check/Create Tools   │
│    - MOSFET calculator  │
│    - Diode calculator   │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ 2. Calculate Losses     │
│    - P_mosfet (W)       │
│    - P_diode (W)        │
│    - P_total (W)        │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ 3. Calculate θSA        │
│    θSA = (Tj_max - Ta)  │
│          / P_total      │
│          - θJC - θCS    │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ 4. Define Requirements  │
│    - Surface area       │
│    - Interface quality  │
│    - Material type      │
└───────────┬─────────────┘
            │
            v
┌─────────────────────────┐
│ 5. Search Database      │
│    θSA_heatsink ≤ θSA   │
└───────────┬─────────────┘
            │
      ┌─────┴─────┐
      │  Found?   │
      └─────┬─────┘
       No   │   Yes
      ┌─────┴─────┐
      v           v
┌───────────┐ ┌───────────┐
│ 6. Search │ │  Return   │
│    Web    │ │  Result   │
└─────┬─────┘ └───────────┘
      │
      v
┌───────────────┐
│ Add to DB     │
└───────────────┘
```

---

## Part 1: Claude AI Ecosystem Solution

### Complete Implementation

```python
# heatsink_selection_claude.py
"""
Heatsink calculation and selection using Claude API with tool use.
Implements the full algorithm for SiC semiconductor thermal management.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import math

import anthropic
from pydantic import BaseModel, Field

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class MOSFETParams:
    """SiC MOSFET parameters for loss calculation."""
    part_number: str
    v_ds: float          # Drain-source voltage (V)
    i_d: float           # Drain current (A)
    r_ds_on: float       # On-resistance at Tj (Ω)
    t_on: float          # Turn-on time (s)
    t_off: float         # Turn-off time (s)
    q_rr: float          # Reverse recovery charge (C)
    f_sw: float          # Switching frequency (Hz)
    duty_cycle: float    # Duty cycle (0-1)
    r_th_jc: float       # Junction-to-case thermal resistance (°C/W)

@dataclass
class DiodeParams:
    """SiC Schottky diode parameters for loss calculation."""
    part_number: str
    v_f: float           # Forward voltage at If (V)
    i_f: float           # Forward current (A)
    q_c: float           # Junction capacitance charge (C)
    f_sw: float          # Switching frequency (Hz)
    duty_cycle: float    # Conduction duty cycle (0-1)
    r_th_jc: float       # Junction-to-case thermal resistance (°C/W)

@dataclass
class ThermalRequirements:
    """Thermal design requirements."""
    p_total: float       # Total power dissipation (W)
    t_j_max: float       # Maximum junction temperature (°C)
    t_ambient: float     # Ambient temperature (°C)
    r_th_jc: float       # Junction-to-case (°C/W)
    r_th_cs: float       # Case-to-sink (°C/W)
    r_th_sa_required: float  # Required sink-to-ambient (°C/W)

class HeatsinkSpec(BaseModel):
    """Heatsink specification."""
    part_number: str
    manufacturer: str
    r_th_sa: float = Field(..., description="Thermal resistance °C/W")
    dimensions_mm: Dict[str, float]  # L, W, H
    material: str
    fin_count: int
    mounting: str
    price_usd: Optional[float] = None
    datasheet_url: Optional[str] = None

# ============================================================================
# Heatsink Database
# ============================================================================

HEATSINK_DATABASE: List[Dict[str, Any]] = [
    {
        "part_number": "ATS-55350D-C1-R0",
        "manufacturer": "Advanced Thermal Solutions",
        "r_th_sa": 3.2,
        "dimensions_mm": {"L": 35, "W": 35, "H": 10},
        "material": "aluminum",
        "fin_count": 11,
        "mounting": "push-pin",
        "price_usd": 2.50
    },
    {
        "part_number": "ATS-55400G-C1-R0",
        "manufacturer": "Advanced Thermal Solutions",
        "r_th_sa": 2.1,
        "dimensions_mm": {"L": 40, "W": 40, "H": 15},
        "material": "aluminum",
        "fin_count": 14,
        "mounting": "push-pin",
        "price_usd": 3.80
    },
    {
        "part_number": "HSF-TO220-38E",
        "manufacturer": "Ohmite",
        "r_th_sa": 4.5,
        "dimensions_mm": {"L": 38, "W": 19, "H": 12},
        "material": "aluminum",
        "fin_count": 6,
        "mounting": "clip",
        "price_usd": 1.20
    },
    {
        "part_number": "WA-T220-101E",
        "manufacturer": "Ohmite",
        "r_th_sa": 6.8,
        "dimensions_mm": {"L": 25, "W": 23, "H": 9},
        "material": "aluminum",
        "fin_count": 5,
        "mounting": "screw",
        "price_usd": 0.85
    },
    {
        "part_number": "SK104-50.8STC",
        "manufacturer": "Fischer Elektronik",
        "r_th_sa": 1.8,
        "dimensions_mm": {"L": 50.8, "W": 41.6, "H": 25},
        "material": "aluminum",
        "fin_count": 18,
        "mounting": "screw",
        "price_usd": 5.60
    },
    {
        "part_number": "SK129-50.8STS",
        "manufacturer": "Fischer Elektronik",
        "r_th_sa": 1.2,
        "dimensions_mm": {"L": 50.8, "W": 50, "H": 40},
        "material": "aluminum",
        "fin_count": 23,
        "mounting": "screw",
        "price_usd": 8.90
    },
    {
        "part_number": "BDN09-3CB/A01",
        "manufacturer": "CUI Devices",
        "r_th_sa": 5.5,
        "dimensions_mm": {"L": 9.5, "W": 19, "H": 9.5},
        "material": "aluminum",
        "fin_count": 4,
        "mounting": "adhesive",
        "price_usd": 0.65
    },
    {
        "part_number": "374424B00035G",
        "manufacturer": "Aavid",
        "r_th_sa": 2.8,
        "dimensions_mm": {"L": 44, "W": 44, "H": 12.7},
        "material": "aluminum",
        "fin_count": 9,
        "mounting": "screw",
        "price_usd": 4.20
    }
]

# ============================================================================
# Tool Definitions for Claude
# ============================================================================

TOOLS = [
    {
        "name": "calculate_sic_mosfet_losses",
        "description": """Calculate power losses for a SiC MOSFET.
        Returns conduction losses, switching losses, and total losses.
        Uses: P_cond = I²·Rds(on)·D, P_sw = 0.5·V·I·(ton+toff)·fsw + Qrr·V·fsw""",
        "input_schema": {
            "type": "object",
            "properties": {
                "v_ds": {"type": "number", "description": "Drain-source voltage (V)"},
                "i_d": {"type": "number", "description": "Drain current (A)"},
                "r_ds_on": {"type": "number", "description": "On-resistance at operating Tj (Ω)"},
                "t_on": {"type": "number", "description": "Turn-on time (s)"},
                "t_off": {"type": "number", "description": "Turn-off time (s)"},
                "q_rr": {"type": "number", "description": "Body diode reverse recovery charge (C)"},
                "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
                "duty_cycle": {"type": "number", "description": "Duty cycle (0-1)"}
            },
            "required": ["v_ds", "i_d", "r_ds_on", "t_on", "t_off", "f_sw", "duty_cycle"]
        }
    },
    {
        "name": "calculate_sic_diode_losses",
        "description": """Calculate power losses for a SiC Schottky diode.
        Returns conduction losses, switching losses, and total losses.
        Uses: P_cond = Vf·If·D, P_sw = Qc·V·fsw""",
        "input_schema": {
            "type": "object",
            "properties": {
                "v_f": {"type": "number", "description": "Forward voltage drop (V)"},
                "i_f": {"type": "number", "description": "Forward current (A)"},
                "v_reverse": {"type": "number", "description": "Reverse blocking voltage (V)"},
                "q_c": {"type": "number", "description": "Junction capacitance charge (C)"},
                "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
                "duty_cycle": {"type": "number", "description": "Conduction duty cycle (0-1)"}
            },
            "required": ["v_f", "i_f", "v_reverse", "f_sw", "duty_cycle"]
        }
    },
    {
        "name": "calculate_thermal_resistance",
        "description": """Calculate required heatsink thermal resistance (θSA).
        Uses: θSA = (Tj_max - Ta) / P_total - θJC - θCS""",
        "input_schema": {
            "type": "object",
            "properties": {
                "p_total": {"type": "number", "description": "Total power dissipation (W)"},
                "t_j_max": {"type": "number", "description": "Maximum junction temperature (°C)"},
                "t_ambient": {"type": "number", "description": "Ambient temperature (°C)"},
                "r_th_jc": {"type": "number", "description": "Junction-to-case thermal resistance (°C/W)"},
                "r_th_cs": {"type": "number", "description": "Case-to-sink thermal resistance (°C/W)"}
            },
            "required": ["p_total", "t_j_max", "t_ambient", "r_th_jc", "r_th_cs"]
        }
    },
    {
        "name": "search_heatsink_database",
        "description": """Search local heatsink database for suitable options.
        Filters by thermal resistance requirement and optional constraints.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "r_th_sa_max": {"type": "number", "description": "Maximum thermal resistance (°C/W)"},
                "material": {"type": "string", "description": "Preferred material (aluminum, copper)"},
                "max_height_mm": {"type": "number", "description": "Maximum heatsink height (mm)"},
                "mounting_type": {"type": "string", "description": "Mounting type (screw, clip, push-pin, adhesive)"}
            },
            "required": ["r_th_sa_max"]
        }
    },
    {
        "name": "search_web_heatsinks",
        "description": """Search web for heatsinks when database has no suitable options.
        Returns heatsink specifications from online sources.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "r_th_sa_max": {"type": "number", "description": "Maximum thermal resistance (°C/W)"},
                "power_rating": {"type": "number", "description": "Power dissipation requirement (W)"},
                "package_type": {"type": "string", "description": "Semiconductor package (TO-220, TO-247, etc.)"}
            },
            "required": ["r_th_sa_max", "power_rating"]
        }
    },
    {
        "name": "add_heatsink_to_database",
        "description": """Add a new heatsink to the local database after web search.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "part_number": {"type": "string"},
                "manufacturer": {"type": "string"},
                "r_th_sa": {"type": "number"},
                "dimensions_mm": {"type": "object"},
                "material": {"type": "string"},
                "fin_count": {"type": "integer"},
                "mounting": {"type": "string"},
                "price_usd": {"type": "number"},
                "datasheet_url": {"type": "string"}
            },
            "required": ["part_number", "manufacturer", "r_th_sa", "material", "mounting"]
        }
    },
    {
        "name": "generate_thermal_report",
        "description": """Generate a complete thermal analysis report with selected heatsink.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "mosfet_losses": {"type": "object"},
                "diode_losses": {"type": "object"},
                "thermal_requirements": {"type": "object"},
                "selected_heatsink": {"type": "object"},
                "safety_margin": {"type": "number", "description": "Thermal margin in °C"}
            },
            "required": ["thermal_requirements", "selected_heatsink"]
        }
    }
]

# ============================================================================
# Tool Implementations
# ============================================================================

def calculate_sic_mosfet_losses(
    v_ds: float,
    i_d: float,
    r_ds_on: float,
    t_on: float,
    t_off: float,
    q_rr: float = 0,
    f_sw: float = 100e3,
    duty_cycle: float = 0.5
) -> Dict[str, float]:
    """
    Calculate SiC MOSFET power losses.

    Conduction losses: P_cond = I_d² × R_ds(on) × D
    Switching losses: P_sw = 0.5 × V_ds × I_d × (t_on + t_off) × f_sw
    Reverse recovery: P_rr = Q_rr × V_ds × f_sw
    """
    # Conduction losses
    p_conduction = (i_d ** 2) * r_ds_on * duty_cycle

    # Switching losses (turn-on + turn-off)
    p_switching = 0.5 * v_ds * i_d * (t_on + t_off) * f_sw

    # Reverse recovery losses (body diode)
    p_reverse_recovery = q_rr * v_ds * f_sw if q_rr else 0

    # Total losses
    p_total = p_conduction + p_switching + p_reverse_recovery

    return {
        "p_conduction_w": round(p_conduction, 3),
        "p_switching_w": round(p_switching, 3),
        "p_reverse_recovery_w": round(p_reverse_recovery, 3),
        "p_total_w": round(p_total, 3),
        "loss_breakdown": {
            "conduction_pct": round(p_conduction / p_total * 100, 1) if p_total > 0 else 0,
            "switching_pct": round(p_switching / p_total * 100, 1) if p_total > 0 else 0,
            "recovery_pct": round(p_reverse_recovery / p_total * 100, 1) if p_total > 0 else 0
        }
    }

def calculate_sic_diode_losses(
    v_f: float,
    i_f: float,
    v_reverse: float,
    q_c: float = 0,
    f_sw: float = 100e3,
    duty_cycle: float = 0.5
) -> Dict[str, float]:
    """
    Calculate SiC Schottky diode power losses.

    Conduction losses: P_cond = V_f × I_f × D
    Switching losses: P_sw = Q_c × V_reverse × f_sw
    (SiC Schottky has no reverse recovery, only junction capacitance)
    """
    # Conduction losses
    p_conduction = v_f * i_f * duty_cycle

    # Switching losses (capacitive)
    p_switching = q_c * v_reverse * f_sw if q_c else 0

    # Total losses
    p_total = p_conduction + p_switching

    return {
        "p_conduction_w": round(p_conduction, 3),
        "p_switching_w": round(p_switching, 3),
        "p_total_w": round(p_total, 3),
        "loss_breakdown": {
            "conduction_pct": round(p_conduction / p_total * 100, 1) if p_total > 0 else 0,
            "switching_pct": round(p_switching / p_total * 100, 1) if p_total > 0 else 0
        }
    }

def calculate_thermal_resistance(
    p_total: float,
    t_j_max: float,
    t_ambient: float,
    r_th_jc: float,
    r_th_cs: float
) -> Dict[str, float]:
    """
    Calculate required heatsink thermal resistance.

    θ_SA = (T_j_max - T_ambient) / P_total - θ_JC - θ_CS
    """
    # Total thermal budget
    delta_t = t_j_max - t_ambient

    # Total thermal resistance budget
    r_th_ja_max = delta_t / p_total

    # Required heatsink thermal resistance
    r_th_sa_required = r_th_ja_max - r_th_jc - r_th_cs

    # Calculate actual junction temperature with this heatsink
    # T_j = T_ambient + P × (θ_JC + θ_CS + θ_SA)

    return {
        "r_th_ja_max": round(r_th_ja_max, 3),
        "r_th_sa_required": round(r_th_sa_required, 3),
        "thermal_budget_c": round(delta_t, 1),
        "breakdown": {
            "r_th_jc": r_th_jc,
            "r_th_cs": r_th_cs,
            "r_th_sa_max": round(r_th_sa_required, 3)
        }
    }

def search_heatsink_database(
    r_th_sa_max: float,
    material: Optional[str] = None,
    max_height_mm: Optional[float] = None,
    mounting_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search local heatsink database for suitable options.
    """
    matches = []

    for hs in HEATSINK_DATABASE:
        # Check thermal resistance
        if hs["r_th_sa"] > r_th_sa_max:
            continue

        # Check optional filters
        if material and hs["material"].lower() != material.lower():
            continue

        if max_height_mm and hs["dimensions_mm"]["H"] > max_height_mm:
            continue

        if mounting_type and hs["mounting"].lower() != mounting_type.lower():
            continue

        # Calculate thermal margin
        margin = r_th_sa_max - hs["r_th_sa"]

        matches.append({
            **hs,
            "thermal_margin": round(margin, 2),
            "margin_pct": round(margin / r_th_sa_max * 100, 1)
        })

    # Sort by thermal resistance (best performance first)
    matches.sort(key=lambda x: x["r_th_sa"])

    return {
        "found": len(matches) > 0,
        "count": len(matches),
        "heatsinks": matches,
        "best_match": matches[0] if matches else None,
        "search_criteria": {
            "r_th_sa_max": r_th_sa_max,
            "material": material,
            "max_height_mm": max_height_mm,
            "mounting_type": mounting_type
        }
    }

def search_web_heatsinks(
    r_th_sa_max: float,
    power_rating: float,
    package_type: str = "TO-247"
) -> Dict[str, Any]:
    """
    Simulate web search for heatsinks.
    In production, this would call DigiKey/Mouser APIs or scrape datasheets.
    """
    # Simulated web search results
    web_results = [
        {
            "part_number": "SK481-50.8STC",
            "manufacturer": "Fischer Elektronik",
            "r_th_sa": 0.85,
            "dimensions_mm": {"L": 50.8, "W": 60, "H": 50},
            "material": "aluminum",
            "fin_count": 28,
            "mounting": "screw",
            "price_usd": 12.50,
            "datasheet_url": "https://www.fischerelektronik.de/sk481.pdf",
            "source": "DigiKey"
        },
        {
            "part_number": "LAM-5-150",
            "manufacturer": "Wakefield-Vette",
            "r_th_sa": 0.65,
            "dimensions_mm": {"L": 150, "W": 127, "H": 40},
            "material": "aluminum",
            "fin_count": 35,
            "mounting": "screw",
            "price_usd": 28.90,
            "datasheet_url": "https://www.wakefield-vette.com/lam5.pdf",
            "source": "Mouser"
        }
    ]

    # Filter by thermal resistance
    matches = [hs for hs in web_results if hs["r_th_sa"] <= r_th_sa_max]

    return {
        "found": len(matches) > 0,
        "count": len(matches),
        "heatsinks": matches,
        "best_match": matches[0] if matches else None,
        "search_query": f"heatsink {r_th_sa_max}C/W {power_rating}W {package_type}"
    }

def add_heatsink_to_database(heatsink: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new heatsink to the local database.
    """
    # Validate required fields
    required = ["part_number", "manufacturer", "r_th_sa", "material", "mounting"]
    for field in required:
        if field not in heatsink:
            return {"success": False, "error": f"Missing required field: {field}"}

    # Check for duplicates
    for existing in HEATSINK_DATABASE:
        if existing["part_number"] == heatsink["part_number"]:
            return {"success": False, "error": "Part number already exists in database"}

    # Add to database
    HEATSINK_DATABASE.append(heatsink)

    return {
        "success": True,
        "message": f"Added {heatsink['part_number']} to database",
        "database_size": len(HEATSINK_DATABASE)
    }

def generate_thermal_report(
    mosfet_losses: Optional[Dict] = None,
    diode_losses: Optional[Dict] = None,
    thermal_requirements: Dict[str, Any] = None,
    selected_heatsink: Dict[str, Any] = None,
    safety_margin: float = 0
) -> Dict[str, Any]:
    """
    Generate comprehensive thermal analysis report.
    """
    # Calculate actual junction temperature
    p_total = thermal_requirements.get("p_total", 0)
    t_ambient = thermal_requirements.get("t_ambient", 25)
    r_th_jc = thermal_requirements.get("r_th_jc", 0)
    r_th_cs = thermal_requirements.get("r_th_cs", 0)
    r_th_sa = selected_heatsink.get("r_th_sa", 0)

    r_th_ja = r_th_jc + r_th_cs + r_th_sa
    t_junction = t_ambient + p_total * r_th_ja

    return {
        "summary": {
            "total_power_w": p_total,
            "junction_temp_c": round(t_junction, 1),
            "thermal_margin_c": round(safety_margin, 1),
            "status": "PASS" if safety_margin > 0 else "FAIL"
        },
        "losses": {
            "mosfet": mosfet_losses,
            "diode": diode_losses
        },
        "thermal_path": {
            "r_th_jc": r_th_jc,
            "r_th_cs": r_th_cs,
            "r_th_sa": r_th_sa,
            "r_th_ja_total": round(r_th_ja, 3)
        },
        "heatsink": {
            "part_number": selected_heatsink.get("part_number"),
            "manufacturer": selected_heatsink.get("manufacturer"),
            "r_th_sa": r_th_sa,
            "dimensions_mm": selected_heatsink.get("dimensions_mm"),
            "price_usd": selected_heatsink.get("price_usd")
        },
        "recommendations": []
    }

# ============================================================================
# Tool Execution
# ============================================================================

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Execute a tool and return JSON result."""

    if tool_name == "calculate_sic_mosfet_losses":
        result = calculate_sic_mosfet_losses(**tool_input)
    elif tool_name == "calculate_sic_diode_losses":
        result = calculate_sic_diode_losses(**tool_input)
    elif tool_name == "calculate_thermal_resistance":
        result = calculate_thermal_resistance(**tool_input)
    elif tool_name == "search_heatsink_database":
        result = search_heatsink_database(**tool_input)
    elif tool_name == "search_web_heatsinks":
        result = search_web_heatsinks(**tool_input)
    elif tool_name == "add_heatsink_to_database":
        result = add_heatsink_to_database(tool_input)
    elif tool_name == "generate_thermal_report":
        result = generate_thermal_report(**tool_input)
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    return json.dumps(result, indent=2)

# ============================================================================
# Main Agent Class
# ============================================================================

class HeatsinkSelectionAgent:
    """
    Agent that calculates semiconductor losses and selects appropriate heatsinks.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-20250514"
        self.tools = TOOLS

    def run(self, design_specs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the heatsink selection process.

        Args:
            design_specs: Dictionary containing:
                - mosfet: MOSFET parameters (optional)
                - diode: Diode parameters (optional)
                - thermal: Thermal requirements
                - constraints: Design constraints

        Returns:
            Complete thermal analysis with selected heatsink
        """
        system_prompt = """You are a power electronics thermal engineer. Your task is to:

1. Calculate semiconductor power losses using the provided tools
2. Determine required heatsink thermal resistance
3. Search the database for suitable heatsinks
4. If no suitable heatsink found in database, search the web
5. Add any web-found heatsinks to the database
6. Generate a complete thermal analysis report

Follow this exact process:
1. First calculate MOSFET losses if MOSFET parameters provided
2. Then calculate diode losses if diode parameters provided
3. Calculate required θSA based on total losses
4. Search database with appropriate filters
5. If database search fails, search web
6. If web search succeeds, add best match to database
7. Generate final thermal report

Always provide specific part numbers and ensure adequate thermal margin (>10°C recommended)."""

        user_prompt = f"""Design specifications:

{json.dumps(design_specs, indent=2)}

Please complete the thermal analysis and heatsink selection following the algorithm.
Calculate all losses, determine thermal requirements, and select an appropriate heatsink.
If the database doesn't have a suitable option, search the web and add the result to the database."""

        messages = [{"role": "user", "content": user_prompt}]

        # Agent loop
        max_iterations = 15
        iteration = 0

        while iteration < max_iterations:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Check if done
            if response.stop_reason == "end_turn":
                # Extract final text response
                for block in response.content:
                    if hasattr(block, 'text'):
                        return {"status": "complete", "result": block.text}
                break

            # Process tool calls
            if response.stop_reason == "tool_use":
                # Add assistant response to messages
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute tools
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"Executing tool: {block.name}")
                        result = execute_tool(block.name, block.input)
                        print(f"Result: {result[:200]}...")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Add tool results to messages
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            iteration += 1

        return {"status": "max_iterations", "iterations": iteration}

# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Run heatsink selection for a buck converter."""

    # Design specifications for a 48V to 12V, 15A buck converter
    design_specs = {
        "application": "48V to 12V Buck Converter, 15A output",
        "mosfet": {
            "part_number": "C3M0065090D",
            "v_ds": 48,
            "i_d": 15,
            "r_ds_on": 0.065,  # 65mΩ at 25°C, use ~80mΩ at 100°C
            "t_on": 15e-9,     # 15ns
            "t_off": 20e-9,    # 20ns
            "q_rr": 50e-9,     # 50nC
            "f_sw": 200e3,     # 200kHz
            "duty_cycle": 0.25,  # 12V/48V
            "r_th_jc": 0.65    # °C/W
        },
        "diode": {
            "part_number": "C4D10120D",
            "v_f": 1.5,
            "i_f": 15,
            "v_reverse": 48,
            "q_c": 30e-9,      # 30nC
            "f_sw": 200e3,
            "duty_cycle": 0.75,  # 1 - D
            "r_th_jc": 0.85    # °C/W
        },
        "thermal": {
            "t_j_max": 150,    # SiC max junction temp
            "t_ambient": 50,   # Worst case ambient
            "r_th_cs": 0.3     # Case-to-sink with thermal pad
        },
        "constraints": {
            "max_height_mm": 30,
            "mounting": "screw",
            "budget_usd": 15
        }
    }

    agent = HeatsinkSelectionAgent()
    result = agent.run(design_specs)

    print("\n" + "="*60)
    print("HEATSINK SELECTION RESULT")
    print("="*60)
    print(result.get("result", result))

if __name__ == "__main__":
    main()
```

---

## Part 2: Google AI (Gemini) Ecosystem Solution

### Complete Implementation

```python
# heatsink_selection_gemini.py
"""
Heatsink calculation and selection using Google Gemini API with function calling.
Implements the full algorithm for SiC semiconductor thermal management.
"""

import os
import json
from typing import Dict, Any, Optional, List

import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

# ============================================================================
# Configuration
# ============================================================================

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# ============================================================================
# Heatsink Database (same as Claude version)
# ============================================================================

HEATSINK_DATABASE: List[Dict[str, Any]] = [
    {
        "part_number": "ATS-55350D-C1-R0",
        "manufacturer": "Advanced Thermal Solutions",
        "r_th_sa": 3.2,
        "dimensions_mm": {"L": 35, "W": 35, "H": 10},
        "material": "aluminum",
        "fin_count": 11,
        "mounting": "push-pin",
        "price_usd": 2.50
    },
    {
        "part_number": "ATS-55400G-C1-R0",
        "manufacturer": "Advanced Thermal Solutions",
        "r_th_sa": 2.1,
        "dimensions_mm": {"L": 40, "W": 40, "H": 15},
        "material": "aluminum",
        "fin_count": 14,
        "mounting": "push-pin",
        "price_usd": 3.80
    },
    {
        "part_number": "SK104-50.8STC",
        "manufacturer": "Fischer Elektronik",
        "r_th_sa": 1.8,
        "dimensions_mm": {"L": 50.8, "W": 41.6, "H": 25},
        "material": "aluminum",
        "fin_count": 18,
        "mounting": "screw",
        "price_usd": 5.60
    },
    {
        "part_number": "SK129-50.8STS",
        "manufacturer": "Fischer Elektronik",
        "r_th_sa": 1.2,
        "dimensions_mm": {"L": 50.8, "W": 50, "H": 40},
        "material": "aluminum",
        "fin_count": 23,
        "mounting": "screw",
        "price_usd": 8.90
    },
    {
        "part_number": "374424B00035G",
        "manufacturer": "Aavid",
        "r_th_sa": 2.8,
        "dimensions_mm": {"L": 44, "W": 44, "H": 12.7},
        "material": "aluminum",
        "fin_count": 9,
        "mounting": "screw",
        "price_usd": 4.20
    }
]

# ============================================================================
# Function Declarations for Gemini
# ============================================================================

calculate_mosfet_losses_func = FunctionDeclaration(
    name="calculate_sic_mosfet_losses",
    description="Calculate power losses for a SiC MOSFET including conduction and switching losses",
    parameters={
        "type": "object",
        "properties": {
            "v_ds": {"type": "number", "description": "Drain-source voltage (V)"},
            "i_d": {"type": "number", "description": "Drain current (A)"},
            "r_ds_on": {"type": "number", "description": "On-resistance (Ω)"},
            "t_on": {"type": "number", "description": "Turn-on time (s)"},
            "t_off": {"type": "number", "description": "Turn-off time (s)"},
            "q_rr": {"type": "number", "description": "Reverse recovery charge (C)"},
            "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
            "duty_cycle": {"type": "number", "description": "Duty cycle (0-1)"}
        },
        "required": ["v_ds", "i_d", "r_ds_on", "t_on", "t_off", "f_sw", "duty_cycle"]
    }
)

calculate_diode_losses_func = FunctionDeclaration(
    name="calculate_sic_diode_losses",
    description="Calculate power losses for a SiC Schottky diode",
    parameters={
        "type": "object",
        "properties": {
            "v_f": {"type": "number", "description": "Forward voltage (V)"},
            "i_f": {"type": "number", "description": "Forward current (A)"},
            "v_reverse": {"type": "number", "description": "Reverse voltage (V)"},
            "q_c": {"type": "number", "description": "Junction capacitance charge (C)"},
            "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
            "duty_cycle": {"type": "number", "description": "Duty cycle (0-1)"}
        },
        "required": ["v_f", "i_f", "v_reverse", "f_sw", "duty_cycle"]
    }
)

calculate_thermal_func = FunctionDeclaration(
    name="calculate_thermal_resistance",
    description="Calculate required heatsink thermal resistance θSA",
    parameters={
        "type": "object",
        "properties": {
            "p_total": {"type": "number", "description": "Total power (W)"},
            "t_j_max": {"type": "number", "description": "Max junction temp (°C)"},
            "t_ambient": {"type": "number", "description": "Ambient temp (°C)"},
            "r_th_jc": {"type": "number", "description": "θJC (°C/W)"},
            "r_th_cs": {"type": "number", "description": "θCS (°C/W)"}
        },
        "required": ["p_total", "t_j_max", "t_ambient", "r_th_jc", "r_th_cs"]
    }
)

search_database_func = FunctionDeclaration(
    name="search_heatsink_database",
    description="Search local database for heatsinks meeting thermal requirements",
    parameters={
        "type": "object",
        "properties": {
            "r_th_sa_max": {"type": "number", "description": "Max thermal resistance (°C/W)"},
            "material": {"type": "string", "description": "Preferred material"},
            "max_height_mm": {"type": "number", "description": "Max height (mm)"},
            "mounting_type": {"type": "string", "description": "Mounting type"}
        },
        "required": ["r_th_sa_max"]
    }
)

search_web_func = FunctionDeclaration(
    name="search_web_heatsinks",
    description="Search web for heatsinks when database has no matches",
    parameters={
        "type": "object",
        "properties": {
            "r_th_sa_max": {"type": "number", "description": "Max thermal resistance (°C/W)"},
            "power_rating": {"type": "number", "description": "Power requirement (W)"},
            "package_type": {"type": "string", "description": "Package type"}
        },
        "required": ["r_th_sa_max", "power_rating"]
    }
)

add_to_database_func = FunctionDeclaration(
    name="add_heatsink_to_database",
    description="Add a new heatsink from web search to local database",
    parameters={
        "type": "object",
        "properties": {
            "part_number": {"type": "string"},
            "manufacturer": {"type": "string"},
            "r_th_sa": {"type": "number"},
            "dimensions_mm": {"type": "object"},
            "material": {"type": "string"},
            "fin_count": {"type": "integer"},
            "mounting": {"type": "string"},
            "price_usd": {"type": "number"},
            "datasheet_url": {"type": "string"}
        },
        "required": ["part_number", "manufacturer", "r_th_sa", "material", "mounting"]
    }
)

generate_report_func = FunctionDeclaration(
    name="generate_thermal_report",
    description="Generate complete thermal analysis report",
    parameters={
        "type": "object",
        "properties": {
            "mosfet_losses": {"type": "object"},
            "diode_losses": {"type": "object"},
            "thermal_requirements": {"type": "object"},
            "selected_heatsink": {"type": "object"},
            "safety_margin": {"type": "number"}
        },
        "required": ["thermal_requirements", "selected_heatsink"]
    }
)

# Create tool with all functions
thermal_tools = Tool(function_declarations=[
    calculate_mosfet_losses_func,
    calculate_diode_losses_func,
    calculate_thermal_func,
    search_database_func,
    search_web_func,
    add_to_database_func,
    generate_report_func
])

# ============================================================================
# Tool Implementations (same as Claude version)
# ============================================================================

def calculate_sic_mosfet_losses(**kwargs) -> Dict[str, float]:
    v_ds = kwargs.get("v_ds")
    i_d = kwargs.get("i_d")
    r_ds_on = kwargs.get("r_ds_on")
    t_on = kwargs.get("t_on")
    t_off = kwargs.get("t_off")
    q_rr = kwargs.get("q_rr", 0)
    f_sw = kwargs.get("f_sw")
    duty_cycle = kwargs.get("duty_cycle")

    p_conduction = (i_d ** 2) * r_ds_on * duty_cycle
    p_switching = 0.5 * v_ds * i_d * (t_on + t_off) * f_sw
    p_reverse_recovery = q_rr * v_ds * f_sw if q_rr else 0
    p_total = p_conduction + p_switching + p_reverse_recovery

    return {
        "p_conduction_w": round(p_conduction, 3),
        "p_switching_w": round(p_switching, 3),
        "p_reverse_recovery_w": round(p_reverse_recovery, 3),
        "p_total_w": round(p_total, 3)
    }

def calculate_sic_diode_losses(**kwargs) -> Dict[str, float]:
    v_f = kwargs.get("v_f")
    i_f = kwargs.get("i_f")
    v_reverse = kwargs.get("v_reverse")
    q_c = kwargs.get("q_c", 0)
    f_sw = kwargs.get("f_sw")
    duty_cycle = kwargs.get("duty_cycle")

    p_conduction = v_f * i_f * duty_cycle
    p_switching = q_c * v_reverse * f_sw if q_c else 0
    p_total = p_conduction + p_switching

    return {
        "p_conduction_w": round(p_conduction, 3),
        "p_switching_w": round(p_switching, 3),
        "p_total_w": round(p_total, 3)
    }

def calculate_thermal_resistance(**kwargs) -> Dict[str, float]:
    p_total = kwargs.get("p_total")
    t_j_max = kwargs.get("t_j_max")
    t_ambient = kwargs.get("t_ambient")
    r_th_jc = kwargs.get("r_th_jc")
    r_th_cs = kwargs.get("r_th_cs")

    delta_t = t_j_max - t_ambient
    r_th_ja_max = delta_t / p_total
    r_th_sa_required = r_th_ja_max - r_th_jc - r_th_cs

    return {
        "r_th_ja_max": round(r_th_ja_max, 3),
        "r_th_sa_required": round(r_th_sa_required, 3),
        "thermal_budget_c": round(delta_t, 1)
    }

def search_heatsink_database(**kwargs) -> Dict[str, Any]:
    r_th_sa_max = kwargs.get("r_th_sa_max")
    material = kwargs.get("material")
    max_height_mm = kwargs.get("max_height_mm")
    mounting_type = kwargs.get("mounting_type")

    matches = []
    for hs in HEATSINK_DATABASE:
        if hs["r_th_sa"] > r_th_sa_max:
            continue
        if material and hs["material"].lower() != material.lower():
            continue
        if max_height_mm and hs["dimensions_mm"]["H"] > max_height_mm:
            continue
        if mounting_type and hs["mounting"].lower() != mounting_type.lower():
            continue

        margin = r_th_sa_max - hs["r_th_sa"]
        matches.append({**hs, "thermal_margin": round(margin, 2)})

    matches.sort(key=lambda x: x["r_th_sa"])

    return {
        "found": len(matches) > 0,
        "count": len(matches),
        "heatsinks": matches,
        "best_match": matches[0] if matches else None
    }

def search_web_heatsinks(**kwargs) -> Dict[str, Any]:
    r_th_sa_max = kwargs.get("r_th_sa_max")
    power_rating = kwargs.get("power_rating")
    package_type = kwargs.get("package_type", "TO-247")

    # Simulated web results
    web_results = [
        {
            "part_number": "SK481-50.8STC",
            "manufacturer": "Fischer Elektronik",
            "r_th_sa": 0.85,
            "dimensions_mm": {"L": 50.8, "W": 60, "H": 50},
            "material": "aluminum",
            "fin_count": 28,
            "mounting": "screw",
            "price_usd": 12.50,
            "datasheet_url": "https://www.fischerelektronik.de/sk481.pdf"
        }
    ]

    matches = [hs for hs in web_results if hs["r_th_sa"] <= r_th_sa_max]

    return {
        "found": len(matches) > 0,
        "heatsinks": matches,
        "best_match": matches[0] if matches else None
    }

def add_heatsink_to_database(heatsink: Dict[str, Any]) -> Dict[str, Any]:
    HEATSINK_DATABASE.append(heatsink)
    return {
        "success": True,
        "message": f"Added {heatsink.get('part_number')} to database"
    }

def generate_thermal_report(**kwargs) -> Dict[str, Any]:
    thermal_req = kwargs.get("thermal_requirements", {})
    heatsink = kwargs.get("selected_heatsink", {})
    safety_margin = kwargs.get("safety_margin", 0)

    p_total = thermal_req.get("p_total", 0)
    t_ambient = thermal_req.get("t_ambient", 25)
    r_th_jc = thermal_req.get("r_th_jc", 0)
    r_th_cs = thermal_req.get("r_th_cs", 0)
    r_th_sa = heatsink.get("r_th_sa", 0)

    t_junction = t_ambient + p_total * (r_th_jc + r_th_cs + r_th_sa)

    return {
        "total_power_w": p_total,
        "junction_temp_c": round(t_junction, 1),
        "thermal_margin_c": round(safety_margin, 1),
        "selected_heatsink": heatsink.get("part_number"),
        "status": "PASS" if safety_margin > 0 else "FAIL"
    }

# ============================================================================
# Function Dispatcher
# ============================================================================

def execute_function(function_name: str, function_args: Dict[str, Any]) -> str:
    """Execute a function and return result as JSON string."""

    functions = {
        "calculate_sic_mosfet_losses": calculate_sic_mosfet_losses,
        "calculate_sic_diode_losses": calculate_sic_diode_losses,
        "calculate_thermal_resistance": calculate_thermal_resistance,
        "search_heatsink_database": search_heatsink_database,
        "search_web_heatsinks": search_web_heatsinks,
        "add_heatsink_to_database": add_heatsink_to_database,
        "generate_thermal_report": generate_thermal_report
    }

    if function_name in functions:
        result = functions[function_name](**function_args)
        return json.dumps(result, indent=2)
    else:
        return json.dumps({"error": f"Unknown function: {function_name}"})

# ============================================================================
# Gemini Agent Class
# ============================================================================

class GeminiHeatsinkAgent:
    """
    Heatsink selection agent using Google Gemini with function calling.
    """

    def __init__(self):
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            tools=[thermal_tools],
            system_instruction="""You are a power electronics thermal engineer.

Your task is to:
1. Calculate semiconductor losses using the provided functions
2. Determine required heatsink thermal resistance
3. Search database for suitable heatsinks
4. If not found, search web and add to database
5. Generate complete thermal report

Always calculate all losses first, then thermal requirements, then search for heatsinks.
Provide specific recommendations with part numbers and thermal margins."""
        )

    def run(self, design_specs: Dict[str, Any]) -> str:
        """Run the heatsink selection process."""

        prompt = f"""Analyze these power converter specifications and select an appropriate heatsink:

{json.dumps(design_specs, indent=2)}

Follow the complete algorithm:
1. Calculate MOSFET losses
2. Calculate diode losses
3. Calculate required θSA
4. Search database for heatsinks
5. If not found, search web
6. Generate thermal report"""

        chat = self.model.start_chat(enable_automatic_function_calling=False)

        response = chat.send_message(prompt)

        # Process function calls in a loop
        max_iterations = 15
        iteration = 0

        while iteration < max_iterations:
            # Check for function calls
            function_calls = []
            for part in response.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_calls.append(part.function_call)

            if not function_calls:
                # No more function calls, return final response
                return response.text

            # Execute all function calls
            function_responses = []
            for fc in function_calls:
                print(f"Executing: {fc.name}")
                result = execute_function(fc.name, dict(fc.args))
                print(f"Result: {result[:200]}...")

                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fc.name,
                            response={"result": json.loads(result)}
                        )
                    )
                )

            # Send function results back
            response = chat.send_message(function_responses)
            iteration += 1

        return "Max iterations reached"

# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Run Gemini heatsink selection."""

    design_specs = {
        "application": "48V to 12V Buck Converter, 15A",
        "mosfet": {
            "v_ds": 48,
            "i_d": 15,
            "r_ds_on": 0.065,
            "t_on": 15e-9,
            "t_off": 20e-9,
            "q_rr": 50e-9,
            "f_sw": 200e3,
            "duty_cycle": 0.25
        },
        "diode": {
            "v_f": 1.5,
            "i_f": 15,
            "v_reverse": 48,
            "q_c": 30e-9,
            "f_sw": 200e3,
            "duty_cycle": 0.75
        },
        "thermal": {
            "t_j_max": 150,
            "t_ambient": 50,
            "r_th_jc": 0.75,  # Combined MOSFET + diode
            "r_th_cs": 0.3
        },
        "constraints": {
            "max_height_mm": 30,
            "mounting": "screw"
        }
    }

    agent = GeminiHeatsinkAgent()
    result = agent.run(design_specs)

    print("\n" + "="*60)
    print("GEMINI HEATSINK SELECTION RESULT")
    print("="*60)
    print(result)

if __name__ == "__main__":
    main()
```

---

## Part 3: Exercise Variations

### Variation A: High-Power Application (Challenging)

```python
# Exercise: Select heatsink for 3-phase motor drive
# Requirements: 3x MOSFETs + 3x diodes, shared heatsink

high_power_specs = {
    "application": "3-Phase Motor Drive, 400V DC bus, 20A phase current",
    "mosfets": [
        {
            "phase": "A_high",
            "v_ds": 400,
            "i_d": 20,
            "r_ds_on": 0.040,
            "t_on": 25e-9,
            "t_off": 35e-9,
            "q_rr": 100e-9,
            "f_sw": 20e3,
            "duty_cycle": 0.5
        }
        # Similar for A_low, B_high, B_low, C_high, C_low
    ],
    "thermal": {
        "t_j_max": 175,
        "t_ambient": 60,
        "r_th_jc": 0.35,  # TO-247
        "r_th_cs": 0.2    # Good thermal interface
    },
    "constraints": {
        "shared_heatsink": True,
        "forced_convection": True,
        "max_volume_cm3": 500
    }
}

# Expected total losses: ~150-200W
# Expected θSA requirement: ~0.3-0.5 °C/W
# Solution: Large extruded heatsink with fan
```

### Variation B: Space-Constrained Application

```python
# Exercise: Select heatsink for drone ESC
# Requirements: Minimal size, must fit in 30x30x15mm envelope

drone_esc_specs = {
    "application": "Drone ESC, 6S LiPo, 30A burst",
    "mosfet": {
        "v_ds": 25.2,
        "i_d": 30,
        "r_ds_on": 0.003,  # Low Rds(on) for efficiency
        "t_on": 8e-9,
        "t_off": 12e-9,
        "f_sw": 48e3,
        "duty_cycle": 0.8
    },
    "thermal": {
        "t_j_max": 150,
        "t_ambient": 40,
        "r_th_jc": 1.5,   # Small package
        "r_th_cs": 0.5
    },
    "constraints": {
        "max_dimensions_mm": {"L": 30, "W": 30, "H": 15},
        "weight_max_g": 20,
        "forced_convection": True  # Prop wash cooling
    }
}

# Challenge: Very tight space constraint
# May need custom heatsink or copper spreader
```

### Variation C: Redundant Cooling (Safety-Critical)

```python
# Exercise: Medical device with redundant cooling
# Requirements: Must operate if primary cooling fails

medical_specs = {
    "application": "Medical Device Power Supply, IEC 60601 Class B",
    "semiconductors": {
        "primary_mosfet": {...},
        "sync_rect_mosfet": {...}
    },
    "thermal": {
        "t_j_max": 125,    # Derated for reliability
        "t_ambient": 35,
        "r_th_jc": 0.5,
        "r_th_cs": 0.25
    },
    "constraints": {
        "redundant_cooling": True,
        "primary": "forced_convection",
        "backup": "natural_convection",
        "mtbf_hours": 100000,
        "compliance": ["IEC 60601", "IEC 62368"]
    }
}

# Must work with both fan and natural convection
# Size heatsink for natural convection case
```

---

## Evaluation Criteria

| Criterion | Points | Description |
|-----------|--------|-------------|
| Loss Calculations | 25 | Correct MOSFET and diode loss formulas |
| Thermal Analysis | 25 | Proper θSA calculation and margin |
| Database Search | 15 | Effective filtering and ranking |
| Web Fallback | 15 | Proper fallback when database empty |
| Database Update | 10 | Successfully add web results |
| Report Quality | 10 | Complete, accurate thermal report |
| **Total** | **100** | |

---

## Solution Verification

### Expected Output for Main Example

```
MOSFET Losses:
  - Conduction: 3.66W (59.4%)
  - Switching: 2.16W (35.1%)
  - Recovery: 0.48W (7.8%)
  - Total: 6.30W

Diode Losses:
  - Conduction: 16.88W (85.3%)
  - Switching: 2.88W (14.7%)
  - Total: 19.76W

Combined Total: 26.06W

Thermal Requirements:
  - ΔT budget: 100°C (150-50)
  - θJA max: 3.84 °C/W
  - θSA required: 2.79 °C/W

Database Search:
  - Found: 3 heatsinks meeting requirements
  - Best match: ATS-55400G-C1-R0 (θSA=2.1°C/W)
  - Margin: 0.69 °C/W (24.7%)

Final Junction Temperature: 131.7°C
Thermal Margin: 18.3°C
Status: PASS
```

---

## Tips and Common Mistakes

### Do:
- Account for Rds(on) temperature coefficient (~1.5x at 100°C vs 25°C)
- Use worst-case ambient temperature
- Include all thermal resistances (TIM, mounting hardware)
- Add 10-20% safety margin on heatsink selection
- Consider thermal runaway in paralleled devices

### Don't:
- Use 25°C Rds(on) for loss calculations
- Ignore body diode losses in synchronous rectification
- Forget case-to-sink thermal interface material
- Select heatsink with zero margin
- Assume datasheet θSA values without checking test conditions

### Thermal Interface Materials (θCS typical values):
- Thermal grease: 0.1-0.3 °C/W
- Thermal pad: 0.3-0.8 °C/W
- Phase-change: 0.2-0.4 °C/W
- No interface (air gap): 1-3 °C/W

