# MCP Applications for Power Converter Design Tools

**Focus:** Building Model Context Protocol servers that expose power electronics design tools to Claude.

---

## Table of Contents

1. [Overview: MCP for Design Tools](#1-overview-mcp-for-design-tools)
2. [Converter Calculator Server](#2-converter-calculator-server)
3. [Component Database Server](#3-component-database-server)
4. [Simulation Interface Server](#4-simulation-interface-server)
5. [Design Validation Server](#5-design-validation-server)
6. [Complete Example: Power Electronics Toolkit](#6-complete-example-power-electronics-toolkit)

---

## 1. Overview: MCP for Design Tools

### Why MCP for Power Electronics?

MCP allows Claude to:
- **Execute calculations** - Loss analysis, efficiency, thermal
- **Query databases** - Component specs, vendor inventory
- **Run simulations** - SPICE, control loop analysis
- **Validate designs** - Check against rules and limits
- **Generate outputs** - BOMs, reports, schematics

### MCP Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Claude Code   │ ◀─▶ │   MCP Server     │ ◀─▶ │  Design Tools   │
│   or Claude API │     │  (Your Tools)    │     │  - Calculators  │
└─────────────────┘     └──────────────────┘     │  - Databases    │
                                                 │  - Simulators   │
                                                 └─────────────────┘
```

### MCP Server Template

```python
# src/mcp/base_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

class PowerElectronicsMCPServer:
    """Base class for power electronics MCP servers."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.server = Server(name)
        self.version = version

        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    async def list_tools(self):
        """Return list of available tools."""
        raise NotImplementedError

    async def call_tool(self, name: str, arguments: dict):
        """Execute a tool call."""
        raise NotImplementedError

    def run(self):
        """Start the server."""
        import asyncio
        from mcp.server.stdio import stdio_server

        async def main():
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, write_stream,
                    self.server.create_initialization_options()
                )

        asyncio.run(main())
```

---

## 2. Converter Calculator Server

### Buck Converter Calculations

```python
# src/mcp/calculator_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import math
import json

app = Server("power-calculator")


# Tool definitions
CALCULATOR_TOOLS = [
    Tool(
        name="buck_duty_cycle",
        description="Calculate buck converter duty cycle with loss compensation",
        inputSchema={
            "type": "object",
            "properties": {
                "v_in": {"type": "number", "description": "Input voltage (V)"},
                "v_out": {"type": "number", "description": "Output voltage (V)"},
                "v_diode": {"type": "number", "description": "Diode/FET drop (V)", "default": 0},
                "i_load": {"type": "number", "description": "Load current (A)", "default": 0},
                "r_inductor": {"type": "number", "description": "Inductor DCR (Ω)", "default": 0}
            },
            "required": ["v_in", "v_out"]
        }
    ),
    Tool(
        name="buck_inductor",
        description="Calculate buck converter inductor value for target ripple",
        inputSchema={
            "type": "object",
            "properties": {
                "v_in": {"type": "number", "description": "Input voltage (V)"},
                "v_out": {"type": "number", "description": "Output voltage (V)"},
                "i_out": {"type": "number", "description": "Output current (A)"},
                "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
                "ripple_ratio": {"type": "number", "description": "Ripple as fraction of Iout", "default": 0.3}
            },
            "required": ["v_in", "v_out", "i_out", "f_sw"]
        }
    ),
    Tool(
        name="buck_output_capacitor",
        description="Calculate output capacitance for target voltage ripple",
        inputSchema={
            "type": "object",
            "properties": {
                "i_ripple": {"type": "number", "description": "Inductor ripple current (A pp)"},
                "v_ripple": {"type": "number", "description": "Target voltage ripple (V pp)"},
                "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
                "esr": {"type": "number", "description": "Capacitor ESR (Ω)", "default": 0}
            },
            "required": ["i_ripple", "v_ripple", "f_sw"]
        }
    ),
    Tool(
        name="mosfet_losses",
        description="Calculate MOSFET conduction and switching losses",
        inputSchema={
            "type": "object",
            "properties": {
                "v_in": {"type": "number", "description": "Input voltage (V)"},
                "i_out": {"type": "number", "description": "Output current (A)"},
                "duty": {"type": "number", "description": "Duty cycle (0-1)"},
                "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
                "rds_on": {"type": "number", "description": "On-resistance (Ω)"},
                "qg": {"type": "number", "description": "Total gate charge (C)"},
                "qgd": {"type": "number", "description": "Gate-drain charge (C)"},
                "vg_drive": {"type": "number", "description": "Gate drive voltage (V)", "default": 10},
                "position": {"type": "string", "enum": ["high_side", "low_side"], "default": "high_side"}
            },
            "required": ["v_in", "i_out", "duty", "f_sw", "rds_on", "qg", "qgd"]
        }
    ),
    Tool(
        name="thermal_resistance",
        description="Calculate junction temperature from losses and thermal resistance",
        inputSchema={
            "type": "object",
            "properties": {
                "power_loss": {"type": "number", "description": "Power dissipation (W)"},
                "t_ambient": {"type": "number", "description": "Ambient temperature (°C)"},
                "rth_jc": {"type": "number", "description": "Junction-to-case thermal resistance (K/W)"},
                "rth_cs": {"type": "number", "description": "Case-to-sink thermal resistance (K/W)", "default": 0},
                "rth_sa": {"type": "number", "description": "Sink-to-ambient thermal resistance (K/W)", "default": 0}
            },
            "required": ["power_loss", "t_ambient", "rth_jc"]
        }
    ),
    Tool(
        name="efficiency",
        description="Calculate converter efficiency from losses",
        inputSchema={
            "type": "object",
            "properties": {
                "p_out": {"type": "number", "description": "Output power (W)"},
                "losses": {"type": "object", "description": "Loss breakdown dict with component losses in W"}
            },
            "required": ["p_out", "losses"]
        }
    ),
    Tool(
        name="lc_filter",
        description="Calculate LC filter characteristics (resonant freq, impedance)",
        inputSchema={
            "type": "object",
            "properties": {
                "inductance": {"type": "number", "description": "Inductance (H)"},
                "capacitance": {"type": "number", "description": "Capacitance (F)"},
                "esr": {"type": "number", "description": "Capacitor ESR (Ω)", "default": 0}
            },
            "required": ["inductance", "capacitance"]
        }
    )
]


@app.list_tools()
async def list_tools():
    return CALCULATOR_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute calculator tool."""

    if name == "buck_duty_cycle":
        result = calculate_buck_duty_cycle(**arguments)

    elif name == "buck_inductor":
        result = calculate_buck_inductor(**arguments)

    elif name == "buck_output_capacitor":
        result = calculate_output_capacitor(**arguments)

    elif name == "mosfet_losses":
        result = calculate_mosfet_losses(**arguments)

    elif name == "thermal_resistance":
        result = calculate_thermal(**arguments)

    elif name == "efficiency":
        result = calculate_efficiency(**arguments)

    elif name == "lc_filter":
        result = calculate_lc_filter(**arguments)

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# Calculation implementations
def calculate_buck_duty_cycle(
    v_in: float,
    v_out: float,
    v_diode: float = 0,
    i_load: float = 0,
    r_inductor: float = 0
) -> dict:
    """Calculate duty cycle with loss compensation."""

    # Ideal
    d_ideal = v_out / v_in

    # With losses
    v_out_eff = v_out + v_diode + (i_load * r_inductor)
    d_real = v_out_eff / v_in

    return {
        "duty_cycle_ideal": round(d_ideal, 4),
        "duty_cycle_real": round(d_real, 4),
        "duty_cycle_percent": round(d_real * 100, 2),
        "v_out_effective": round(v_out_eff, 3),
        "note": "Real duty cycle accounts for diode drop and inductor DCR loss"
    }


def calculate_buck_inductor(
    v_in: float,
    v_out: float,
    i_out: float,
    f_sw: float,
    ripple_ratio: float = 0.3
) -> dict:
    """Calculate inductor value for target ripple."""

    d = v_out / v_in
    delta_i = i_out * ripple_ratio

    # L = (Vin - Vout) * D / (f_sw * delta_I)
    l_value = (v_in - v_out) * d / (f_sw * delta_i)

    # Current ratings
    i_peak = i_out + delta_i / 2
    i_rms = math.sqrt(i_out**2 + (delta_i**2) / 12)

    return {
        "inductance_H": l_value,
        "inductance_uH": round(l_value * 1e6, 2),
        "ripple_current_A": round(delta_i, 3),
        "peak_current_A": round(i_peak, 3),
        "rms_current_A": round(i_rms, 3),
        "duty_cycle": round(d, 4),
        "recommendation": f"Select inductor ≥ {l_value*1e6:.1f}µH, Isat > {i_peak*1.2:.1f}A, Irms > {i_rms*1.1:.1f}A"
    }


def calculate_output_capacitor(
    i_ripple: float,
    v_ripple: float,
    f_sw: float,
    esr: float = 0
) -> dict:
    """Calculate output capacitance for voltage ripple."""

    # Ripple from capacitance: dV = I * dt / C = I / (8 * f * C)
    # Ripple from ESR: dV_esr = I * ESR

    if esr > 0:
        # ESR-dominated case
        v_ripple_esr = i_ripple * esr
        v_ripple_cap = v_ripple - v_ripple_esr

        if v_ripple_cap <= 0:
            return {
                "error": f"ESR ripple ({v_ripple_esr:.3f}V) exceeds target ({v_ripple}V)",
                "recommendation": "Use lower ESR capacitors or parallel multiple units"
            }

        c_value = i_ripple / (8 * f_sw * v_ripple_cap)
    else:
        c_value = i_ripple / (8 * f_sw * v_ripple)

    return {
        "capacitance_F": c_value,
        "capacitance_uF": round(c_value * 1e6, 1),
        "ripple_from_C_V": round(i_ripple / (8 * f_sw * c_value), 4) if c_value > 0 else 0,
        "ripple_from_ESR_V": round(i_ripple * esr, 4) if esr > 0 else 0,
        "total_ripple_V": round(v_ripple, 4),
        "recommendation": f"Use ≥ {c_value*1e6:.0f}µF with ESR < {v_ripple/i_ripple*1000:.1f}mΩ"
    }


def calculate_mosfet_losses(
    v_in: float,
    i_out: float,
    duty: float,
    f_sw: float,
    rds_on: float,
    qg: float,
    qgd: float,
    vg_drive: float = 10,
    position: str = "high_side"
) -> dict:
    """Calculate MOSFET losses."""

    # Conduction loss
    if position == "high_side":
        p_cond = rds_on * i_out**2 * duty
    else:
        p_cond = rds_on * i_out**2 * (1 - duty)

    # Switching loss (simplified)
    # P_sw = 0.5 * V * I * (Qgd/Ig) * f_sw
    ig = 2.0  # Assume 2A gate driver
    t_sw = qgd / ig
    p_sw = 0.5 * v_in * i_out * 2 * t_sw * f_sw  # Both edges

    # Gate drive loss
    p_gate = qg * vg_drive * f_sw

    p_total = p_cond + p_sw + p_gate

    return {
        "conduction_loss_W": round(p_cond, 4),
        "switching_loss_W": round(p_sw, 4),
        "gate_drive_loss_W": round(p_gate, 4),
        "total_loss_W": round(p_total, 4),
        "position": position,
        "duty_cycle": duty
    }


def calculate_thermal(
    power_loss: float,
    t_ambient: float,
    rth_jc: float,
    rth_cs: float = 0,
    rth_sa: float = 0
) -> dict:
    """Calculate junction temperature."""

    rth_total = rth_jc + rth_cs + rth_sa

    # If no heatsink specified, estimate Rth_ja
    if rth_cs == 0 and rth_sa == 0:
        rth_total = rth_jc + 40  # Typical package Rth_ja

    t_junction = t_ambient + power_loss * rth_total

    return {
        "t_junction_C": round(t_junction, 1),
        "t_ambient_C": t_ambient,
        "rth_total_KW": round(rth_total, 2),
        "temperature_rise_C": round(power_loss * rth_total, 1),
        "power_loss_W": power_loss,
        "warning": "Tj > 125°C - reduce losses or improve cooling" if t_junction > 125 else None
    }


def calculate_efficiency(p_out: float, losses: dict) -> dict:
    """Calculate efficiency from output power and losses."""

    p_loss_total = sum(losses.values())
    p_in = p_out + p_loss_total
    efficiency = p_out / p_in if p_in > 0 else 0

    return {
        "efficiency": round(efficiency, 4),
        "efficiency_percent": round(efficiency * 100, 2),
        "p_out_W": p_out,
        "p_in_W": round(p_in, 3),
        "p_loss_total_W": round(p_loss_total, 3),
        "loss_breakdown": {k: round(v, 4) for k, v in losses.items()}
    }


def calculate_lc_filter(
    inductance: float,
    capacitance: float,
    esr: float = 0
) -> dict:
    """Calculate LC filter characteristics."""

    # Resonant frequency
    f_res = 1 / (2 * math.pi * math.sqrt(inductance * capacitance))

    # Characteristic impedance
    z0 = math.sqrt(inductance / capacitance)

    # Q factor (if ESR provided)
    if esr > 0:
        q = z0 / esr
    else:
        q = float('inf')

    # ESR zero frequency
    f_esr = 1 / (2 * math.pi * esr * capacitance) if esr > 0 else None

    return {
        "resonant_frequency_Hz": round(f_res, 1),
        "resonant_frequency_kHz": round(f_res / 1e3, 2),
        "characteristic_impedance_Ohm": round(z0, 4),
        "q_factor": round(q, 1) if q != float('inf') else "High (low damping)",
        "esr_zero_Hz": round(f_esr, 1) if f_esr else None,
        "note": f"Place crossover frequency 5-10x below f_res ({f_res/1e3:.1f}kHz)"
    }


# Run server
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
```

---

## 3. Component Database Server

### Query Component Parameters

```python
# src/mcp/component_db_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource
import json
import sqlite3
from pathlib import Path

app = Server("component-database")

# Initialize database
DB_PATH = "./components.db"


def init_database():
    """Initialize component database with sample data."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mosfets (
            part_number TEXT PRIMARY KEY,
            manufacturer TEXT,
            vds_max REAL,
            id_max REAL,
            rds_on_typ REAL,
            rds_on_max REAL,
            qg_typ REAL,
            qgd_typ REAL,
            rth_jc REAL,
            package TEXT,
            price_usd REAL,
            in_stock INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inductors (
            part_number TEXT PRIMARY KEY,
            manufacturer TEXT,
            inductance_uh REAL,
            dcr_mohm REAL,
            isat_a REAL,
            irms_a REAL,
            package TEXT,
            price_usd REAL,
            in_stock INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS capacitors (
            part_number TEXT PRIMARY KEY,
            manufacturer TEXT,
            capacitance_uf REAL,
            voltage_rating REAL,
            esr_mohm REAL,
            ripple_current REAL,
            type TEXT,
            package TEXT,
            price_usd REAL,
            in_stock INTEGER
        )
    """)

    # Sample MOSFET data
    mosfets = [
        ("BSC010N04LS", "Infineon", 40, 100, 1.0, 1.4, 15, 3.5, 1.0, "TDSON-8", 1.25, 1000),
        ("BSC016N06NS", "Infineon", 60, 80, 1.6, 2.2, 20, 4.2, 1.2, "TDSON-8", 1.45, 500),
        ("IPD90N04S4L-02", "Infineon", 40, 120, 0.9, 1.2, 12, 2.8, 0.9, "TDSON-8", 1.65, 800),
        ("CSD18540Q5B", "TI", 60, 100, 1.8, 2.4, 18, 4.0, 1.1, "SON-5x6", 1.35, 1200),
        ("NVMFS5C604NL", "ON Semi", 40, 90, 1.2, 1.6, 14, 3.2, 1.0, "SO-8 FL", 1.15, 600),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO mosfets VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, mosfets)

    # Sample inductor data
    inductors = [
        ("SER2915H-103", "Coilcraft", 10, 2.5, 30, 25, "SER2915H", 2.80, 300),
        ("XAL7070-152", "Coilcraft", 15, 3.8, 28, 22, "XAL7070", 3.20, 250),
        ("IHLP4040DZ-01", "Vishay", 4.7, 1.8, 35, 30, "IHLP4040", 2.50, 400),
        ("SRP1265A-100M", "Bourns", 10, 2.2, 28, 24, "SRP1265A", 2.10, 500),
        ("744325100", "Wurth", 10, 3.0, 25, 20, "WE-LHMI", 1.90, 600),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO inductors VALUES (?,?,?,?,?,?,?,?,?)
    """, inductors)

    conn.commit()
    conn.close()


# Tools
COMPONENT_TOOLS = [
    Tool(
        name="search_mosfets",
        description="Search MOSFETs by specifications",
        inputSchema={
            "type": "object",
            "properties": {
                "vds_min": {"type": "number", "description": "Minimum Vds rating (V)"},
                "id_min": {"type": "number", "description": "Minimum Id rating (A)"},
                "rds_max": {"type": "number", "description": "Maximum Rds_on (mΩ)"},
                "qg_max": {"type": "number", "description": "Maximum gate charge (nC)"},
                "package": {"type": "string", "description": "Package type"},
                "in_stock_only": {"type": "boolean", "default": True}
            }
        }
    ),
    Tool(
        name="search_inductors",
        description="Search inductors by specifications",
        inputSchema={
            "type": "object",
            "properties": {
                "inductance_min": {"type": "number", "description": "Minimum inductance (µH)"},
                "inductance_max": {"type": "number", "description": "Maximum inductance (µH)"},
                "isat_min": {"type": "number", "description": "Minimum saturation current (A)"},
                "dcr_max": {"type": "number", "description": "Maximum DCR (mΩ)"},
                "in_stock_only": {"type": "boolean", "default": True}
            }
        }
    ),
    Tool(
        name="get_component",
        description="Get detailed specs for a specific component",
        inputSchema={
            "type": "object",
            "properties": {
                "part_number": {"type": "string", "description": "Component part number"},
                "component_type": {"type": "string", "enum": ["mosfet", "inductor", "capacitor"]}
            },
            "required": ["part_number", "component_type"]
        }
    ),
    Tool(
        name="compare_components",
        description="Compare multiple components side by side",
        inputSchema={
            "type": "object",
            "properties": {
                "part_numbers": {"type": "array", "items": {"type": "string"}},
                "component_type": {"type": "string", "enum": ["mosfet", "inductor", "capacitor"]}
            },
            "required": ["part_numbers", "component_type"]
        }
    ),
    Tool(
        name="calculate_fom",
        description="Calculate figure of merit for MOSFETs",
        inputSchema={
            "type": "object",
            "properties": {
                "part_numbers": {"type": "array", "items": {"type": "string"}},
                "fom_type": {"type": "string", "enum": ["rds_qg", "rds_qgd"], "default": "rds_qg"}
            },
            "required": ["part_numbers"]
        }
    )
]


@app.list_tools()
async def list_tools():
    return COMPONENT_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute component database tool."""

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        if name == "search_mosfets":
            result = search_mosfets(cursor, **arguments)

        elif name == "search_inductors":
            result = search_inductors(cursor, **arguments)

        elif name == "get_component":
            result = get_component(cursor, **arguments)

        elif name == "compare_components":
            result = compare_components(cursor, **arguments)

        elif name == "calculate_fom":
            result = calculate_fom(cursor, **arguments)

        else:
            result = {"error": f"Unknown tool: {name}"}

    finally:
        conn.close()

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def search_mosfets(cursor, **kwargs) -> dict:
    """Search MOSFETs by specifications."""

    conditions = []
    params = []

    if kwargs.get("vds_min"):
        conditions.append("vds_max >= ?")
        params.append(kwargs["vds_min"])

    if kwargs.get("id_min"):
        conditions.append("id_max >= ?")
        params.append(kwargs["id_min"])

    if kwargs.get("rds_max"):
        conditions.append("rds_on_typ <= ?")
        params.append(kwargs["rds_max"])

    if kwargs.get("qg_max"):
        conditions.append("qg_typ <= ?")
        params.append(kwargs["qg_max"])

    if kwargs.get("package"):
        conditions.append("package LIKE ?")
        params.append(f"%{kwargs['package']}%")

    if kwargs.get("in_stock_only", True):
        conditions.append("in_stock > 0")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT *, (rds_on_typ * qg_typ) as fom
        FROM mosfets
        WHERE {where_clause}
        ORDER BY fom ASC
        LIMIT 10
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows]
    }


def search_inductors(cursor, **kwargs) -> dict:
    """Search inductors by specifications."""

    conditions = []
    params = []

    if kwargs.get("inductance_min"):
        conditions.append("inductance_uh >= ?")
        params.append(kwargs["inductance_min"])

    if kwargs.get("inductance_max"):
        conditions.append("inductance_uh <= ?")
        params.append(kwargs["inductance_max"])

    if kwargs.get("isat_min"):
        conditions.append("isat_a >= ?")
        params.append(kwargs["isat_min"])

    if kwargs.get("dcr_max"):
        conditions.append("dcr_mohm <= ?")
        params.append(kwargs["dcr_max"])

    if kwargs.get("in_stock_only", True):
        conditions.append("in_stock > 0")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = f"""
        SELECT *
        FROM inductors
        WHERE {where_clause}
        ORDER BY dcr_mohm ASC
        LIMIT 10
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows]
    }


def get_component(cursor, part_number: str, component_type: str) -> dict:
    """Get detailed component specifications."""

    table = f"{component_type}s"

    cursor.execute(f"SELECT * FROM {table} WHERE part_number = ?", (part_number,))
    row = cursor.fetchone()

    if row:
        return {"found": True, "component": dict(row)}
    else:
        return {"found": False, "error": f"Part {part_number} not found in {table}"}


def compare_components(cursor, part_numbers: list, component_type: str) -> dict:
    """Compare multiple components."""

    table = f"{component_type}s"
    placeholders = ",".join("?" * len(part_numbers))

    cursor.execute(f"SELECT * FROM {table} WHERE part_number IN ({placeholders})", part_numbers)
    rows = cursor.fetchall()

    return {
        "count": len(rows),
        "components": [dict(row) for row in rows]
    }


def calculate_fom(cursor, part_numbers: list, fom_type: str = "rds_qg") -> dict:
    """Calculate figure of merit for MOSFETs."""

    placeholders = ",".join("?" * len(part_numbers))

    cursor.execute(f"SELECT * FROM mosfets WHERE part_number IN ({placeholders})", part_numbers)
    rows = cursor.fetchall()

    results = []
    for row in rows:
        row_dict = dict(row)

        if fom_type == "rds_qg":
            fom = row_dict["rds_on_typ"] * row_dict["qg_typ"]
            fom_label = "Rds_on × Qg (mΩ·nC)"
        else:  # rds_qgd
            fom = row_dict["rds_on_typ"] * row_dict["qgd_typ"]
            fom_label = "Rds_on × Qgd (mΩ·nC)"

        results.append({
            "part_number": row_dict["part_number"],
            "manufacturer": row_dict["manufacturer"],
            "rds_on_typ": row_dict["rds_on_typ"],
            "qg_typ": row_dict["qg_typ"],
            "qgd_typ": row_dict["qgd_typ"],
            "fom": round(fom, 2),
            "fom_type": fom_label
        })

    # Sort by FOM
    results.sort(key=lambda x: x["fom"])

    return {
        "fom_type": fom_type,
        "results": results,
        "best": results[0]["part_number"] if results else None
    }


# Initialize and run
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    # Create database
    init_database()

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
```

---

## 4. Simulation Interface Server

### SPICE Simulation via MCP

```python
# src/mcp/spice_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import subprocess
import tempfile
import json
import re
from pathlib import Path

app = Server("spice-simulator")

# Path to ngspice or LTspice
NGSPICE_PATH = "ngspice"  # Assumes in PATH


SPICE_TOOLS = [
    Tool(
        name="simulate_buck_transient",
        description="Run transient simulation of buck converter",
        inputSchema={
            "type": "object",
            "properties": {
                "v_in": {"type": "number", "description": "Input voltage (V)"},
                "v_out": {"type": "number", "description": "Output voltage (V)"},
                "i_out": {"type": "number", "description": "Load current (A)"},
                "l_value": {"type": "number", "description": "Inductance (H)"},
                "c_value": {"type": "number", "description": "Output capacitance (F)"},
                "f_sw": {"type": "number", "description": "Switching frequency (Hz)"},
                "sim_time": {"type": "number", "description": "Simulation time (s)", "default": 100e-6}
            },
            "required": ["v_in", "v_out", "i_out", "l_value", "c_value", "f_sw"]
        }
    ),
    Tool(
        name="simulate_bode",
        description="Run AC analysis for Bode plot",
        inputSchema={
            "type": "object",
            "properties": {
                "netlist": {"type": "string", "description": "SPICE netlist"},
                "f_start": {"type": "number", "description": "Start frequency (Hz)", "default": 1},
                "f_stop": {"type": "number", "description": "Stop frequency (Hz)", "default": 1e6},
                "points_per_decade": {"type": "integer", "default": 20}
            },
            "required": ["netlist"]
        }
    ),
    Tool(
        name="analyze_waveform",
        description="Analyze simulation waveform for ripple, average, etc.",
        inputSchema={
            "type": "object",
            "properties": {
                "data": {"type": "object", "description": "Waveform data with time and values"},
                "analysis_type": {"type": "string", "enum": ["ripple", "average", "rms", "peak"]}
            },
            "required": ["data", "analysis_type"]
        }
    )
]


@app.list_tools()
async def list_tools():
    return SPICE_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute SPICE simulation tool."""

    if name == "simulate_buck_transient":
        result = simulate_buck_transient(**arguments)

    elif name == "simulate_bode":
        result = simulate_bode(**arguments)

    elif name == "analyze_waveform":
        result = analyze_waveform(**arguments)

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def simulate_buck_transient(
    v_in: float,
    v_out: float,
    i_out: float,
    l_value: float,
    c_value: float,
    f_sw: float,
    sim_time: float = 100e-6
) -> dict:
    """Run transient simulation of ideal buck converter."""

    # Calculate duty cycle
    duty = v_out / v_in
    period = 1 / f_sw

    # Generate netlist
    netlist = f"""Buck Converter Transient Simulation
* Input
Vin in 0 {v_in}

* Ideal switch (voltage-controlled switch)
S1 in sw ctrl 0 SWIDEAL
.model SWIDEAL SW(Ron=1m Roff=1Meg Vt=0.5)

* PWM control signal
Vctrl ctrl 0 PULSE(0 1 0 1n 1n {duty*period} {period})

* Freewheeling diode (ideal)
D1 0 sw DIDEALK
.model DIDEALK D(Ron=1m Roff=1Meg Vfwd=0)

* LC filter
L1 sw out {l_value}
C1 out 0 {c_value}

* Load
Rload out 0 {v_out/i_out}

* Simulation
.tran {sim_time/1000} {sim_time} 0 {period/100}

* Measurements
.measure TRAN Vout_avg AVG V(out) FROM={sim_time*0.5} TO={sim_time}
.measure TRAN Vout_ripple PP V(out) FROM={sim_time*0.8} TO={sim_time}
.measure TRAN IL_avg AVG I(L1) FROM={sim_time*0.5} TO={sim_time}
.measure TRAN IL_ripple PP I(L1) FROM={sim_time*0.8} TO={sim_time}

.end
"""

    # Run simulation
    try:
        result = run_ngspice(netlist)

        # Parse measurements
        measurements = parse_measurements(result.get("output", ""))

        return {
            "success": True,
            "measurements": measurements,
            "parameters": {
                "v_in": v_in,
                "v_out_target": v_out,
                "duty_cycle": duty,
                "f_sw": f_sw,
                "l_value": l_value,
                "c_value": c_value
            },
            "raw_output": result.get("output", "")[:500]  # Truncate
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def simulate_bode(
    netlist: str,
    f_start: float = 1,
    f_stop: float = 1e6,
    points_per_decade: int = 20
) -> dict:
    """Run AC analysis for Bode plot."""

    # Add AC analysis directive if not present
    if ".ac" not in netlist.lower():
        decades = int(round(log10(f_stop) - log10(f_start)))
        total_points = decades * points_per_decade
        ac_line = f".ac dec {points_per_decade} {f_start} {f_stop}"
        netlist = netlist.replace(".end", f"{ac_line}\n.end")

    try:
        result = run_ngspice(netlist)

        return {
            "success": True,
            "f_start": f_start,
            "f_stop": f_stop,
            "raw_output": result.get("output", "")[:1000]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def analyze_waveform(data: dict, analysis_type: str) -> dict:
    """Analyze waveform data."""

    import statistics

    values = data.get("values", [])

    if not values:
        return {"error": "No waveform data provided"}

    if analysis_type == "average":
        result = statistics.mean(values)
    elif analysis_type == "rms":
        result = (sum(v**2 for v in values) / len(values)) ** 0.5
    elif analysis_type == "peak":
        result = max(abs(v) for v in values)
    elif analysis_type == "ripple":
        result = max(values) - min(values)
    else:
        return {"error": f"Unknown analysis type: {analysis_type}"}

    return {
        "analysis_type": analysis_type,
        "result": result,
        "points": len(values)
    }


def run_ngspice(netlist: str) -> dict:
    """Run ngspice simulation."""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False) as f:
        f.write(netlist)
        netlist_path = f.name

    try:
        result = subprocess.run(
            [NGSPICE_PATH, "-b", netlist_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "output": result.stdout,
            "errors": result.stderr,
            "returncode": result.returncode
        }

    finally:
        Path(netlist_path).unlink()


def parse_measurements(output: str) -> dict:
    """Parse ngspice measurement results."""

    measurements = {}

    # Pattern for .measure results
    pattern = r"(\w+)\s*=\s*([-\d.e+]+)"

    for match in re.finditer(pattern, output, re.IGNORECASE):
        name = match.group(1).lower()
        value = float(match.group(2))
        measurements[name] = value

    return measurements


from math import log10


# Run server
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
```

---

## 5. Design Validation Server

### Check Designs Against Rules

```python
# src/mcp/validation_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import json
from typing import Dict, List
from enum import Enum

app = Server("design-validator")


class CheckResult(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


VALIDATION_TOOLS = [
    Tool(
        name="validate_mosfet_stress",
        description="Check MOSFET electrical and thermal stress against datasheet limits",
        inputSchema={
            "type": "object",
            "properties": {
                "operating": {
                    "type": "object",
                    "description": "Operating conditions",
                    "properties": {
                        "vds_applied": {"type": "number"},
                        "vgs_applied": {"type": "number"},
                        "id_continuous": {"type": "number"},
                        "id_peak": {"type": "number"},
                        "power_loss": {"type": "number"},
                        "t_ambient": {"type": "number"}
                    }
                },
                "limits": {
                    "type": "object",
                    "description": "Datasheet limits",
                    "properties": {
                        "vds_max": {"type": "number"},
                        "vgs_max": {"type": "number"},
                        "id_max": {"type": "number"},
                        "pd_max": {"type": "number"},
                        "tj_max": {"type": "number"},
                        "rth_jc": {"type": "number"},
                        "rth_ja": {"type": "number"}
                    }
                }
            },
            "required": ["operating", "limits"]
        }
    ),
    Tool(
        name="validate_inductor_stress",
        description="Check inductor current and thermal stress",
        inputSchema={
            "type": "object",
            "properties": {
                "operating": {
                    "type": "object",
                    "properties": {
                        "i_dc": {"type": "number"},
                        "i_ripple_pp": {"type": "number"},
                        "t_ambient": {"type": "number"}
                    }
                },
                "limits": {
                    "type": "object",
                    "properties": {
                        "isat": {"type": "number"},
                        "irms": {"type": "number"},
                        "dcr": {"type": "number"}
                    }
                }
            },
            "required": ["operating", "limits"]
        }
    ),
    Tool(
        name="validate_capacitor_stress",
        description="Check capacitor voltage and ripple current stress",
        inputSchema={
            "type": "object",
            "properties": {
                "operating": {
                    "type": "object",
                    "properties": {
                        "v_dc": {"type": "number"},
                        "i_ripple_rms": {"type": "number"},
                        "t_ambient": {"type": "number"}
                    }
                },
                "limits": {
                    "type": "object",
                    "properties": {
                        "v_rated": {"type": "number"},
                        "ripple_current": {"type": "number"},
                        "esr": {"type": "number"}
                    }
                }
            },
            "required": ["operating", "limits"]
        }
    ),
    Tool(
        name="full_design_check",
        description="Complete design validation for all components",
        inputSchema={
            "type": "object",
            "properties": {
                "design": {"type": "object", "description": "Complete design specification"}
            },
            "required": ["design"]
        }
    )
]


@app.list_tools()
async def list_tools():
    return VALIDATION_TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute validation tool."""

    if name == "validate_mosfet_stress":
        result = validate_mosfet(**arguments)

    elif name == "validate_inductor_stress":
        result = validate_inductor(**arguments)

    elif name == "validate_capacitor_stress":
        result = validate_capacitor(**arguments)

    elif name == "full_design_check":
        result = full_design_check(**arguments)

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


def check_margin(
    value: float,
    limit: float,
    check_type: str = "max"
) -> Dict:
    """Check value against limit and return result with margin."""

    if check_type == "max":
        margin = (limit - value) / limit * 100
        result = CheckResult.PASS if margin > 20 else (
            CheckResult.WARNING if margin > 0 else CheckResult.FAIL
        )
    else:  # min
        margin = (value - limit) / limit * 100
        result = CheckResult.PASS if margin > 20 else (
            CheckResult.WARNING if margin > 0 else CheckResult.FAIL
        )

    return {
        "result": result.value,
        "value": value,
        "limit": limit,
        "margin_percent": round(margin, 1)
    }


def validate_mosfet(operating: Dict, limits: Dict) -> Dict:
    """Validate MOSFET stress."""

    checks = {}

    # Vds check
    if "vds_applied" in operating and "vds_max" in limits:
        checks["vds"] = check_margin(
            operating["vds_applied"],
            limits["vds_max"],
            "max"
        )

    # Vgs check
    if "vgs_applied" in operating and "vgs_max" in limits:
        checks["vgs"] = check_margin(
            operating["vgs_applied"],
            limits["vgs_max"],
            "max"
        )

    # Id continuous check
    if "id_continuous" in operating and "id_max" in limits:
        checks["id_continuous"] = check_margin(
            operating["id_continuous"],
            limits["id_max"],
            "max"
        )

    # Power dissipation check
    if "power_loss" in operating and "pd_max" in limits:
        checks["power"] = check_margin(
            operating["power_loss"],
            limits["pd_max"],
            "max"
        )

    # Junction temperature calculation and check
    if all(k in operating for k in ["power_loss", "t_ambient"]) and "rth_ja" in limits:
        rth = limits.get("rth_ja", limits.get("rth_jc", 40) + 40)
        tj = operating["t_ambient"] + operating["power_loss"] * rth

        checks["junction_temp"] = {
            "result": CheckResult.PASS.value if tj < limits.get("tj_max", 150) - 25 else (
                CheckResult.WARNING.value if tj < limits.get("tj_max", 150) else CheckResult.FAIL.value
            ),
            "value": round(tj, 1),
            "limit": limits.get("tj_max", 150),
            "margin_C": round(limits.get("tj_max", 150) - tj, 1)
        }

    # Overall result
    results = [c.get("result", "PASS") for c in checks.values()]
    if "FAIL" in results:
        overall = "FAIL"
    elif "WARNING" in results:
        overall = "WARNING"
    else:
        overall = "PASS"

    return {
        "overall": overall,
        "checks": checks
    }


def validate_inductor(operating: Dict, limits: Dict) -> Dict:
    """Validate inductor stress."""

    checks = {}

    i_dc = operating.get("i_dc", 0)
    i_ripple = operating.get("i_ripple_pp", 0)

    # Peak current (for saturation)
    i_peak = i_dc + i_ripple / 2
    if "isat" in limits:
        checks["saturation"] = check_margin(
            i_peak,
            limits["isat"],
            "max"
        )

    # RMS current
    i_rms = (i_dc**2 + (i_ripple**2) / 12) ** 0.5
    if "irms" in limits:
        checks["rms_current"] = check_margin(
            i_rms,
            limits["irms"],
            "max"
        )

    # DCR power loss
    if "dcr" in limits:
        p_dcr = i_rms**2 * limits["dcr"] / 1000  # DCR in mΩ
        checks["dcr_loss"] = {
            "value_W": round(p_dcr, 3),
            "dcr_mOhm": limits["dcr"],
            "i_rms_A": round(i_rms, 2)
        }

    # Overall
    results = [c.get("result", "PASS") for c in checks.values() if "result" in c]
    overall = "FAIL" if "FAIL" in results else ("WARNING" if "WARNING" in results else "PASS")

    return {
        "overall": overall,
        "checks": checks,
        "calculated": {
            "i_peak_A": round(i_peak, 2),
            "i_rms_A": round(i_rms, 2)
        }
    }


def validate_capacitor(operating: Dict, limits: Dict) -> Dict:
    """Validate capacitor stress."""

    checks = {}

    # Voltage check
    if "v_dc" in operating and "v_rated" in limits:
        checks["voltage"] = check_margin(
            operating["v_dc"],
            limits["v_rated"],
            "max"
        )

    # Ripple current check
    if "i_ripple_rms" in operating and "ripple_current" in limits:
        checks["ripple_current"] = check_margin(
            operating["i_ripple_rms"],
            limits["ripple_current"],
            "max"
        )

    # ESR heating
    if "i_ripple_rms" in operating and "esr" in limits:
        p_esr = operating["i_ripple_rms"]**2 * limits["esr"] / 1000
        checks["esr_loss"] = {
            "value_W": round(p_esr, 4),
            "esr_mOhm": limits["esr"]
        }

    # Overall
    results = [c.get("result", "PASS") for c in checks.values() if "result" in c]
    overall = "FAIL" if "FAIL" in results else ("WARNING" if "WARNING" in results else "PASS")

    return {
        "overall": overall,
        "checks": checks
    }


def full_design_check(design: Dict) -> Dict:
    """Complete design validation."""

    results = {
        "overall": "PASS",
        "components": {}
    }

    # Check each component type if present
    if "mosfet" in design:
        results["components"]["mosfet"] = validate_mosfet(
            design["mosfet"].get("operating", {}),
            design["mosfet"].get("limits", {})
        )

    if "inductor" in design:
        results["components"]["inductor"] = validate_inductor(
            design["inductor"].get("operating", {}),
            design["inductor"].get("limits", {})
        )

    if "capacitor" in design:
        results["components"]["capacitor"] = validate_capacitor(
            design["capacitor"].get("operating", {}),
            design["capacitor"].get("limits", {})
        )

    # Overall result
    component_results = [c.get("overall", "PASS") for c in results["components"].values()]
    if "FAIL" in component_results:
        results["overall"] = "FAIL"
    elif "WARNING" in component_results:
        results["overall"] = "WARNING"

    # Summary
    results["summary"] = {
        "total_checks": sum(
            len(c.get("checks", {})) for c in results["components"].values()
        ),
        "passed": sum(
            1 for c in results["components"].values()
            for check in c.get("checks", {}).values()
            if check.get("result") == "PASS"
        ),
        "warnings": sum(
            1 for c in results["components"].values()
            for check in c.get("checks", {}).values()
            if check.get("result") == "WARNING"
        ),
        "failed": sum(
            1 for c in results["components"].values()
            for check in c.get("checks", {}).values()
            if check.get("result") == "FAIL"
        )
    }

    return results


# Run server
if __name__ == "__main__":
    import asyncio
    from mcp.server.stdio import stdio_server

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
```

---

## 6. Complete Example: Power Electronics Toolkit

### Unified MCP Server Configuration

```json
{
    "mcpServers": {
        "power-calculator": {
            "command": "python",
            "args": ["/path/to/src/mcp/calculator_server.py"],
            "env": {}
        },
        "component-database": {
            "command": "python",
            "args": ["/path/to/src/mcp/component_db_server.py"],
            "env": {
                "DB_PATH": "/path/to/components.db"
            }
        },
        "design-validator": {
            "command": "python",
            "args": ["/path/to/src/mcp/validation_server.py"],
            "env": {}
        },
        "spice-simulator": {
            "command": "python",
            "args": ["/path/to/src/mcp/spice_server.py"],
            "env": {
                "NGSPICE_PATH": "/usr/bin/ngspice"
            }
        }
    }
}
```

### Usage Examples with Claude Code

**Example 1: Design a Buck Converter**

```
User: Design a 48V to 12V/20A buck converter at 200kHz

Claude: I'll help you design this converter. Let me start with the calculations.

[Calls buck_inductor tool]
- Inductance needed: 10µH
- Ripple current: 6A (30%)
- Peak current: 23A

[Calls search_mosfets tool with vds_min=60, id_min=30, rds_max=2]
- Found BSC010N04LS, IPD90N04S4L-02, CSD18540Q5B

[Calls calculate_fom tool]
- Best FOM: IPD90N04S4L-02 (10.8 mΩ·nC)

[Calls mosfet_losses tool for selected MOSFET]
- HS conduction: 0.18W
- HS switching: 0.45W
- LS conduction: 0.54W

[Calls efficiency tool]
- Estimated efficiency: 96.5%

[Calls validate_mosfet_stress tool]
- All checks PASS with >30% margin
```

**Example 2: Verify Existing Design**

```
User: Check if BSC010N04LS is okay for 48V input, 25A continuous

Claude: Let me validate this operating point.

[Calls get_component tool]
- Vds_max: 40V
- Id_max: 100A
- Rth_jc: 1.0 K/W

[Calls validate_mosfet_stress tool]
Result: FAIL
- Vds check: FAIL (48V > 40V limit, -20% margin)

Recommendation: Need a MOSFET with Vds_max ≥ 60V for 20% margin.

[Calls search_mosfets with vds_min=60]
- Alternatives: BSC016N06NS (60V), CSD18540Q5B (60V)
```

**Example 3: Simulate and Verify**

```
User: Simulate the buck converter and verify output ripple

Claude: I'll run a transient simulation.

[Calls simulate_buck_transient tool]
Results:
- Vout_avg: 11.98V
- Vout_ripple: 45mV
- IL_avg: 20.1A
- IL_ripple: 5.8A

The output ripple is 45mV peak-to-peak, which meets the 50mV target.

[Calls buck_output_capacitor to verify calculation]
- Required capacitance: 180µF for 50mV ripple with 6A ripple current
- This matches the simulation results.
```

---

## Installation & Setup

### Requirements

```text
# requirements.txt
mcp>=1.0.0
anthropic>=0.18.0
sqlite3
numpy
```

### Claude Code Configuration

Add to `~/.config/claude-code/config.json` or project `.claude/config.json`:

```json
{
    "mcpServers": {
        "power-calculator": {
            "command": "python",
            "args": ["./src/mcp/calculator_server.py"]
        },
        "component-database": {
            "command": "python",
            "args": ["./src/mcp/component_db_server.py"]
        },
        "design-validator": {
            "command": "python",
            "args": ["./src/mcp/validation_server.py"]
        }
    }
}
```

### Testing MCP Servers

```bash
# Test calculator server
echo '{"method": "tools/list"}' | python src/mcp/calculator_server.py

# Test component database
python -c "from src.mcp.component_db_server import init_database; init_database()"
```

---

## Exercises

### Exercise 1: Boost Calculator (30 min)
1. Add boost converter tools to calculator_server
2. Implement: duty_cycle, inductor, input_capacitor
3. Test with 12V to 48V conversion

### Exercise 2: Capacitor Database (30 min)
1. Extend component_db_server with capacitors table
2. Add search by voltage, capacitance, ESR
3. Include MLCC DC bias derating info

### Exercise 3: Custom Validation Rule (30 min)
1. Add MLCC voltage derating check to validator
2. At 50% rated voltage, capacitance drops ~50%
3. Flag WARNING if effective capacitance too low

### Exercise 4: BOM Generator (45 min)
1. Create tool that generates complete BOM
2. Input: design specifications
3. Output: part numbers, quantities, prices, sources

### Exercise 5: Integration Test (60 min)
1. Create end-to-end design flow
2. Start with specs → calculations → selection → validation
3. Verify all MCP tools work together

---

## Pro Tips

1. **Return structured JSON** - Easy for Claude to parse
2. **Include units always** - Prevents unit confusion
3. **Add validation in tools** - Catch errors early
4. **Log tool calls** - Debug and optimize
5. **Cache database queries** - Improve response time
6. **Version your tools** - Track API changes
7. **Handle errors gracefully** - Return informative messages
8. **Document schemas clearly** - Claude uses descriptions
9. **Test edge cases** - Zero current, max voltage, etc.
10. **Provide recommendations** - Not just numbers

---

## Next Steps

- **Module 7:** Use MCP tools in autonomous design agents
- **RAG + MCP:** Combine datasheet lookup with calculations
- **Production:** Add authentication, monitoring, rate limits
