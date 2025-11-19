# Python & VS Code Essentials for Power Electronics

**Module Focus:** Foundational Python and development environment skills for API integration and engineering data analysis.

**Prerequisites:** WSL2 installed (see main README), basic programming concepts
**Time:** 3-4 hours hands-on

---

## Table of Contents

1. [VS Code Setup for Engineering Development](#1-vs-code-setup-for-engineering-development)
2. [Python Fundamentals for Engineering](#2-python-fundamentals-for-engineering)
3. [Scientific Libraries](#3-scientific-libraries)
4. [Asynchronous Programming](#4-asynchronous-programming)
5. [Hands-On Project: Buck Converter Efficiency Analyzer](#5-hands-on-project-buck-converter-efficiency-analyzer)

---

## 1. VS Code Setup for Engineering Development

### 1.1 Essential Extensions

Install these extensions for power electronics development:

```bash
# Install via command line (run in WSL terminal)
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-toolsai.jupyter
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
```

| Extension | Purpose | Why It Matters |
|-----------|---------|----------------|
| **Python** | Core Python support | Debugging, IntelliSense, environments |
| **Pylance** | Type checking, autocomplete | Catch errors before runtime (critical for API calls) |
| **Jupyter** | Interactive notebooks | Rapid prototyping, visualization |
| **Black Formatter** | Code formatting | Consistent style, readability |
| **Ruff** | Fast linting | Catch bugs, enforce best practices |

**Additional Recommended:**
```bash
code --install-extension redhat.vscode-yaml          # For config files
code --install-extension ms-azuretools.vscode-docker # For deployment
code --install-extension eamodio.gitlens             # Git visualization
```

### 1.2 Virtual Environment Setup

**Why venv:** Isolate project dependencies. Avoid "works on my machine" issues. Critical when different projects need different library versions.

```bash
# Create project directory
mkdir -p ~/projects/power-electronics-ai
cd ~/projects/power-electronics-ai

# Create virtual environment
python3 -m venv .venv

# Activate (do this every time you work on the project)
source .venv/bin/activate

# Verify activation (should show .venv path)
which python
# Output: /home/denkov/projects/power-electronics-ai/.venv/bin/python

# Install core packages
pip install --upgrade pip
pip install numpy matplotlib pandas scipy
pip install anthropic python-dotenv  # For LLM API
pip install pytest pytest-asyncio    # For testing

# Save dependencies
pip freeze > requirements.txt
```

**VS Code Integration:**

1. Open folder in VS Code: `code .`
2. Press `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose `.venv` interpreter (shows `('.venv': venv)`)

**Pro Tip:** Add to `.bashrc` for auto-activation:
```bash
# Auto-activate venv when entering project directory
cd() {
    builtin cd "$@"
    if [[ -f .venv/bin/activate ]]; then
        source .venv/bin/activate
    fi
}
```

### 1.3 VS Code Settings for Engineering Work

Create `.vscode/settings.json` in your project:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,

    "editor.formatOnSave": true,
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.rulers": [88, 120],

    "[python]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    },

    "jupyter.notebookFileRoot": "${workspaceFolder}",

    "files.associations": {
        "*.spice": "spice",
        "*.lib": "spice"
    }
}
```

### 1.4 Project Structure

```
power-electronics-ai/
├── .venv/                    # Virtual environment (don't commit)
├── .vscode/
│   └── settings.json         # VS Code settings
├── src/
│   ├── __init__.py
│   ├── converters/           # Converter models
│   │   ├── __init__.py
│   │   ├── buck.py
│   │   └── boost.py
│   ├── analysis/             # Analysis tools
│   │   ├── __init__.py
│   │   ├── efficiency.py
│   │   └── bode.py
│   └── api/                  # LLM API integration
│       ├── __init__.py
│       └── claude_client.py
├── tests/
│   ├── __init__.py
│   └── test_converters.py
├── notebooks/                # Jupyter notebooks
│   └── buck_analysis.ipynb
├── data/                     # Test data, waveforms
├── .env                      # API keys (don't commit!)
├── .gitignore
├── requirements.txt
└── README.md
```

**Essential .gitignore:**
```gitignore
.venv/
__pycache__/
*.pyc
.env
.ipynb_checkpoints/
*.egg-info/
dist/
build/
```

---

## 2. Python Fundamentals for Engineering

### 2.1 Data Types for Engineering Calculations

```python
# ============================================================
# NUMERIC TYPES - Use appropriately for precision
# ============================================================

# Integers - for discrete quantities
switching_freq_hz = 100_000  # 100 kHz (underscores for readability)
num_phases = 4

# Floats - for continuous quantities
duty_cycle = 0.375           # 37.5%
v_in = 48.0                  # 48V input
v_out = 12.0                 # 12V output
i_out = 20.0                 # 20A output

# Complex - for AC analysis, impedance
z_capacitor = complex(0.01, -1/(2 * 3.14159 * 100e3 * 100e-6))  # ESR - j*Xc
print(f"Z_cap = {z_capacitor.real:.3f} + j{z_capacitor.imag:.3f} Ω")
print(f"|Z| = {abs(z_capacitor):.3f} Ω")

# ============================================================
# STRINGS - For component names, file paths, prompts
# ============================================================

part_number = "LM5146"
manufacturer = "Texas Instruments"

# f-strings for formatted output (USE THIS)
print(f"Using {part_number} from {manufacturer}")
print(f"Duty cycle: {duty_cycle:.1%}")  # 37.5%
print(f"Frequency: {switching_freq_hz/1e3:.0f} kHz")

# Multi-line strings for prompts
system_prompt = """You are a power electronics expert assistant.
When analyzing converters, always consider:
- Conduction losses (I²R)
- Switching losses (CV²f)
- Core losses (Steinmetz equation)
- Thermal constraints"""

# ============================================================
# LISTS - Ordered, mutable sequences
# ============================================================

# Sweep parameters
load_currents = [1, 5, 10, 15, 20]  # Amps
frequencies = [50e3, 100e3, 200e3, 500e3]  # Hz

# Append results
efficiencies = []
for i_load in load_currents:
    eta = calculate_efficiency(v_in, v_out, i_load)
    efficiencies.append(eta)

# List comprehension (preferred - more Pythonic, faster)
efficiencies = [calculate_efficiency(v_in, v_out, i) for i in load_currents]

# ============================================================
# TUPLES - Immutable, for fixed data
# ============================================================

# Component specs (value, tolerance, rating)
r_sense = (0.002, 0.01, 2.0)  # 2mΩ, 1%, 2W
mosfet_params = ("BSC010N04LS", 1.0e-3, 40, 100)  # Part, Rds_on, Vds_max, Id_max

# Unpack
part, rds_on, vds_max, id_max = mosfet_params
print(f"{part}: Rds_on={rds_on*1e3:.1f}mΩ, Vds={vds_max}V, Id={id_max}A")

# ============================================================
# DICTIONARIES - Key-value pairs for structured data
# ============================================================

# Component parameters
mosfet = {
    "part_number": "BSC010N04LS",
    "manufacturer": "Infineon",
    "rds_on_mohm": 1.0,
    "qg_nc": 15,
    "qrr_nc": 10,
    "vds_max_v": 40,
    "id_max_a": 100,
    "package": "TDSON-8"
}

# Access
print(f"Gate charge: {mosfet['qg_nc']} nC")

# Nested dict for converter specs
buck_specs = {
    "input": {"v_min": 36, "v_max": 60, "v_nom": 48},
    "output": {"v_out": 12, "i_max": 20, "v_ripple_pp": 0.05},
    "switching": {"f_sw_khz": 200, "t_dead_ns": 50},
    "thermal": {"t_amb_max": 85, "r_theta_ja": 40}
}

# Access nested
v_in_range = f"{buck_specs['input']['v_min']}-{buck_specs['input']['v_max']}V"

# ============================================================
# SETS - Unique elements, fast membership testing
# ============================================================

# Available packages in stock
packages_available = {"TDSON-8", "SO-8", "DPAK", "D2PAK"}
packages_needed = {"TDSON-8", "QFN-5x6", "SO-8"}

# Set operations
in_stock = packages_needed & packages_available  # Intersection
need_to_order = packages_needed - packages_available  # Difference

print(f"In stock: {in_stock}")
print(f"Need to order: {need_to_order}")
```

### 2.2 Control Flow for Engineering Logic

```python
# ============================================================
# CONDITIONAL LOGIC - Operating mode selection
# ============================================================

def select_control_mode(v_in: float, v_out: float, i_load: float) -> str:
    """Select optimal control mode based on operating point."""

    duty_cycle = v_out / v_in

    # Mode selection based on operating conditions
    if duty_cycle < 0.1:
        # Very low duty - pulse skipping may be needed
        return "pulse_skip"
    elif duty_cycle < 0.2:
        # Low duty - watch for minimum on-time
        return "constant_on_time"
    elif i_load < 1.0:
        # Light load - efficiency priority
        return "discontinuous"
    elif duty_cycle > 0.8:
        # High duty - watch for minimum off-time
        return "constant_off_time"
    else:
        # Normal operation
        return "voltage_mode" if i_load < 10 else "current_mode"


def check_safe_operating_area(
    vds: float,
    id: float,
    t_pulse_us: float,
    soa_curves: dict
) -> tuple[bool, str]:
    """Check if operating point is within MOSFET SOA.

    Returns:
        (is_safe, reason)
    """
    # DC limit
    if vds > soa_curves["vds_max"]:
        return False, f"Vds={vds}V exceeds max {soa_curves['vds_max']}V"

    if id > soa_curves["id_max"]:
        return False, f"Id={id}A exceeds max {soa_curves['id_max']}A"

    # Pulsed SOA check (simplified)
    if t_pulse_us < 10:
        id_limit = soa_curves["id_10us"]
    elif t_pulse_us < 100:
        id_limit = soa_curves["id_100us"]
    elif t_pulse_us < 1000:
        id_limit = soa_curves["id_1ms"]
    else:
        id_limit = soa_curves["id_dc"]

    # Interpolate for voltage
    id_limit_derated = id_limit * (1 - vds / soa_curves["vds_max"])

    if id > id_limit_derated:
        return False, f"Id={id}A exceeds pulsed limit {id_limit_derated:.1f}A at {t_pulse_us}µs"

    return True, "Within SOA"


# ============================================================
# LOOPS - Parameter sweeps, iteration
# ============================================================

# For loop - known iteration count
frequencies = [100e3, 200e3, 300e3, 400e3, 500e3]
switching_losses = []

for f_sw in frequencies:
    # P_sw = 0.5 * Qg * Vg * f_sw (simplified)
    qg = 15e-9  # 15 nC
    vg = 10     # 10V gate drive
    p_sw = 0.5 * qg * vg * f_sw
    switching_losses.append(p_sw)
    print(f"f_sw = {f_sw/1e3:.0f} kHz: P_sw = {p_sw:.2f} W")

# While loop - condition-based iteration
def find_optimal_turns(
    l_target_uh: float,
    al_value: float,
    n_max: int = 100
) -> int:
    """Find turns for target inductance.

    L = AL * N²
    """
    n = 1
    while n <= n_max:
        l_actual = al_value * n**2 * 1e-9  # AL in nH/turn²
        if l_actual >= l_target_uh * 1e-6:
            return n
        n += 1

    return -1  # Could not achieve target

# Enumerate - when you need index and value
components = ["input_cap", "inductor", "output_cap", "mosfet_hs", "mosfet_ls"]
for idx, comp in enumerate(components, start=1):
    print(f"{idx}. {comp}")

# Zip - iterate multiple sequences together
voltages = [36, 48, 60]
currents = [22, 20, 18]  # Derated at higher Vin

for v, i in zip(voltages, currents):
    power = v * i
    print(f"Vin={v}V: Imax={i}A, Pmax={power}W")


# ============================================================
# EXCEPTION HANDLING - Robust calculations
# ============================================================

def calculate_inductor_ripple(
    v_in: float,
    v_out: float,
    f_sw: float,
    l_h: float
) -> float:
    """Calculate inductor current ripple.

    ΔI = (V_in - V_out) * D / (f_sw * L)
    """
    try:
        if l_h <= 0:
            raise ValueError(f"Inductance must be positive, got {l_h}")
        if f_sw <= 0:
            raise ValueError(f"Frequency must be positive, got {f_sw}")
        if v_in <= v_out:
            raise ValueError(f"Vin ({v_in}V) must exceed Vout ({v_out}V) for buck")

        d = v_out / v_in
        delta_i = (v_in - v_out) * d / (f_sw * l_h)

        return delta_i

    except ZeroDivisionError as e:
        print(f"Division error: {e}")
        raise
    except ValueError as e:
        print(f"Invalid parameter: {e}")
        raise
```

### 2.3 Functions for Reusable Calculations

```python
from typing import Optional, Tuple
import math

# ============================================================
# BASIC FUNCTION STRUCTURE
# ============================================================

def calculate_buck_duty_cycle(
    v_in: float,
    v_out: float,
    v_diode_drop: float = 0.0,
    r_inductor: float = 0.0,
    i_load: float = 0.0
) -> float:
    """Calculate buck converter duty cycle with loss compensation.

    Ideal: D = Vout / Vin
    Real: D = (Vout + Vf + I*RL) / Vin

    Args:
        v_in: Input voltage (V)
        v_out: Output voltage (V)
        v_diode_drop: Diode/body diode forward voltage (V)
        r_inductor: Inductor DCR (Ω)
        i_load: Load current (A)

    Returns:
        Duty cycle (0 to 1)

    Raises:
        ValueError: If Vin <= 0 or Vout >= Vin

    Example:
        >>> calculate_buck_duty_cycle(48, 12)
        0.25
        >>> calculate_buck_duty_cycle(48, 12, v_diode_drop=0.5, r_inductor=0.01, i_load=20)
        0.268
    """
    if v_in <= 0:
        raise ValueError(f"Input voltage must be positive: {v_in}")

    # Account for losses
    v_out_effective = v_out + v_diode_drop + (i_load * r_inductor)

    d = v_out_effective / v_in

    if d >= 1.0:
        raise ValueError(f"Duty cycle {d:.3f} >= 1.0 - increase Vin or reduce Vout")

    return d


# ============================================================
# FUNCTIONS RETURNING MULTIPLE VALUES
# ============================================================

def analyze_inductor_current(
    v_in: float,
    v_out: float,
    i_out: float,
    f_sw: float,
    l_h: float
) -> Tuple[float, float, float, float]:
    """Analyze inductor current waveform.

    Returns:
        Tuple of (i_avg, i_ripple_pp, i_peak, i_valley)
    """
    d = v_out / v_in

    # Current ripple
    delta_i = (v_in - v_out) * d / (f_sw * l_h)

    # For CCM, I_L_avg = I_out (assuming ideal)
    i_avg = i_out
    i_peak = i_avg + delta_i / 2
    i_valley = i_avg - delta_i / 2

    return i_avg, delta_i, i_peak, i_valley


# Usage with unpacking
i_avg, i_pp, i_pk, i_val = analyze_inductor_current(
    v_in=48, v_out=12, i_out=20, f_sw=200e3, l_h=10e-6
)
print(f"I_avg={i_avg:.1f}A, ΔI={i_pp:.2f}App, I_pk={i_pk:.2f}A, I_val={i_val:.2f}A")


# ============================================================
# FUNCTIONS WITH OPTIONAL PARAMETERS
# ============================================================

def calculate_mosfet_losses(
    v_in: float,
    i_out: float,
    f_sw: float,
    rds_on: float,
    qg: float,
    vg_drive: float = 10.0,
    t_rise: Optional[float] = None,
    t_fall: Optional[float] = None,
    duty_cycle: Optional[float] = None,
    v_out: Optional[float] = None
) -> dict:
    """Calculate MOSFET conduction and switching losses.

    Args:
        v_in: Input voltage (V)
        i_out: Output current (A)
        f_sw: Switching frequency (Hz)
        rds_on: On-state resistance (Ω)
        qg: Total gate charge (C)
        vg_drive: Gate drive voltage (V)
        t_rise: Rise time (s), estimated from Qg if None
        t_fall: Fall time (s), estimated from Qg if None
        duty_cycle: Duty cycle, calculated from v_out if None
        v_out: Output voltage (V), required if duty_cycle is None

    Returns:
        Dictionary with loss breakdown
    """
    # Calculate or use provided duty cycle
    if duty_cycle is None:
        if v_out is None:
            raise ValueError("Must provide either duty_cycle or v_out")
        duty_cycle = v_out / v_in

    # Estimate switching times from gate charge if not provided
    # t ≈ Qg / Ig, assume 1A gate drive current
    if t_rise is None:
        t_rise = qg / 1.0  # Simplified
    if t_fall is None:
        t_fall = qg / 1.0

    # Conduction loss (high-side MOSFET)
    p_cond_hs = rds_on * i_out**2 * duty_cycle

    # Conduction loss (low-side MOSFET)
    p_cond_ls = rds_on * i_out**2 * (1 - duty_cycle)

    # Switching loss (simplified: P = 0.5 * V * I * (tr + tf) * f)
    p_sw = 0.5 * v_in * i_out * (t_rise + t_fall) * f_sw

    # Gate drive loss
    p_gate = qg * vg_drive * f_sw * 2  # Both HS and LS

    return {
        "p_cond_hs_w": p_cond_hs,
        "p_cond_ls_w": p_cond_ls,
        "p_switching_w": p_sw,
        "p_gate_w": p_gate,
        "p_total_w": p_cond_hs + p_cond_ls + p_sw + p_gate,
        "duty_cycle": duty_cycle
    }


# Usage
losses = calculate_mosfet_losses(
    v_in=48, i_out=20, f_sw=200e3,
    rds_on=1e-3, qg=15e-9, v_out=12
)

print("MOSFET Loss Breakdown:")
for key, value in losses.items():
    if key.startswith("p_"):
        print(f"  {key}: {value:.3f} W")


# ============================================================
# LAMBDA FUNCTIONS - Quick calculations
# ============================================================

# Single-use calculations
ripple_factor = lambda delta_i, i_avg: delta_i / (2 * i_avg) * 100  # %
crossover_freq = lambda r, c: 1 / (2 * math.pi * r * c)  # Hz

# Usage
rf = ripple_factor(4.0, 20.0)
print(f"Ripple factor: {rf:.1f}%")

fc = crossover_freq(10e3, 100e-9)
print(f"Crossover frequency: {fc/1e3:.1f} kHz")
```

### 2.4 Classes for Converter Models

```python
from dataclasses import dataclass
from typing import Optional
import math

# ============================================================
# DATACLASS - Simple data containers
# ============================================================

@dataclass
class MOSFETParams:
    """MOSFET electrical parameters."""
    part_number: str
    rds_on_mohm: float      # On-resistance at 25°C
    qg_nc: float            # Total gate charge
    qgd_nc: float           # Gate-drain charge
    qrr_nc: float           # Reverse recovery charge
    vds_max_v: float        # Maximum drain-source voltage
    id_max_a: float         # Maximum continuous drain current
    rds_on_tc: float = 0.004  # Temperature coefficient (/°C)

    def rds_on_at_temp(self, temp_c: float) -> float:
        """Calculate Rds_on at operating temperature."""
        return self.rds_on_mohm * 1e-3 * (1 + self.rds_on_tc * (temp_c - 25))


@dataclass
class InductorParams:
    """Inductor parameters."""
    part_number: str
    inductance_uh: float
    dcr_mohm: float
    isat_a: float           # Saturation current (30% drop)
    irms_a: float           # RMS current rating
    core_material: str = "ferrite"


@dataclass
class CapacitorParams:
    """Capacitor parameters."""
    part_number: str
    capacitance_uf: float
    voltage_rating_v: float
    esr_mohm: float
    ripple_current_a: float
    type: str = "MLCC"      # MLCC, electrolytic, polymer


# ============================================================
# FULL CLASS - Buck converter model
# ============================================================

class BuckConverter:
    """Synchronous buck converter model for loss analysis.

    Attributes:
        v_in: Input voltage (V)
        v_out: Output voltage (V)
        i_out: Output current (A)
        f_sw: Switching frequency (Hz)
        hs_fet: High-side MOSFET parameters
        ls_fet: Low-side MOSFET parameters
        inductor: Inductor parameters
        output_cap: Output capacitor parameters
    """

    def __init__(
        self,
        v_in: float,
        v_out: float,
        i_out: float,
        f_sw: float,
        hs_fet: MOSFETParams,
        ls_fet: MOSFETParams,
        inductor: InductorParams,
        output_cap: CapacitorParams,
        t_dead_ns: float = 50.0
    ):
        self.v_in = v_in
        self.v_out = v_out
        self.i_out = i_out
        self.f_sw = f_sw
        self.hs_fet = hs_fet
        self.ls_fet = ls_fet
        self.inductor = inductor
        self.output_cap = output_cap
        self.t_dead_ns = t_dead_ns

        # Validate inputs
        if v_out >= v_in:
            raise ValueError(f"Vout ({v_out}V) must be less than Vin ({v_in}V)")

    @property
    def duty_cycle(self) -> float:
        """Ideal duty cycle."""
        return self.v_out / self.v_in

    @property
    def inductor_ripple(self) -> float:
        """Peak-to-peak inductor current ripple (A)."""
        l_h = self.inductor.inductance_uh * 1e-6
        return (self.v_in - self.v_out) * self.duty_cycle / (self.f_sw * l_h)

    @property
    def inductor_rms_current(self) -> float:
        """RMS inductor current (A)."""
        # I_rms = sqrt(I_avg² + (ΔI/sqrt(12))²)
        return math.sqrt(self.i_out**2 + (self.inductor_ripple / math.sqrt(12))**2)

    def calculate_conduction_losses(self, t_junction: float = 100) -> dict:
        """Calculate conduction losses for all components.

        Args:
            t_junction: Junction temperature (°C)

        Returns:
            Dictionary with loss breakdown
        """
        d = self.duty_cycle
        i_rms = self.inductor_rms_current

        # MOSFET conduction (temperature compensated)
        rds_hs = self.hs_fet.rds_on_at_temp(t_junction)
        rds_ls = self.ls_fet.rds_on_at_temp(t_junction)

        p_hs_cond = i_rms**2 * rds_hs * d
        p_ls_cond = i_rms**2 * rds_ls * (1 - d)

        # Inductor DCR loss
        p_inductor = i_rms**2 * self.inductor.dcr_mohm * 1e-3

        # Output capacitor ESR loss (ripple current only)
        i_cap_rms = self.inductor_ripple / math.sqrt(12)
        p_cap = i_cap_rms**2 * self.output_cap.esr_mohm * 1e-3

        return {
            "hs_mosfet_w": p_hs_cond,
            "ls_mosfet_w": p_ls_cond,
            "inductor_w": p_inductor,
            "output_cap_w": p_cap,
            "total_w": p_hs_cond + p_ls_cond + p_inductor + p_cap
        }

    def calculate_switching_losses(self) -> dict:
        """Calculate switching losses.

        Returns:
            Dictionary with loss breakdown
        """
        # High-side switching loss
        # P_sw ≈ 0.5 * Vin * Iout * (Qgd/Ig) * f_sw
        # Simplified: assume Ig = 2A
        ig = 2.0
        t_rise = self.hs_fet.qgd_nc * 1e-9 / ig
        t_fall = t_rise  # Approximate

        p_sw_hs = 0.5 * self.v_in * self.i_out * (t_rise + t_fall) * self.f_sw

        # Low-side body diode reverse recovery
        p_qrr = self.ls_fet.qrr_nc * 1e-9 * self.v_in * self.f_sw

        # Dead time body diode conduction (both transitions)
        v_body_diode = 0.7  # V
        p_dead = 2 * v_body_diode * self.i_out * self.t_dead_ns * 1e-9 * self.f_sw

        # Gate drive losses (both MOSFETs)
        vg = 10.0  # Gate drive voltage
        p_gate = (self.hs_fet.qg_nc + self.ls_fet.qg_nc) * 1e-9 * vg * self.f_sw

        return {
            "hs_switching_w": p_sw_hs,
            "reverse_recovery_w": p_qrr,
            "dead_time_w": p_dead,
            "gate_drive_w": p_gate,
            "total_w": p_sw_hs + p_qrr + p_dead + p_gate
        }

    def calculate_efficiency(self, t_junction: float = 100) -> float:
        """Calculate overall converter efficiency.

        Args:
            t_junction: Junction temperature (°C)

        Returns:
            Efficiency (0 to 1)
        """
        p_out = self.v_out * self.i_out

        cond_losses = self.calculate_conduction_losses(t_junction)
        sw_losses = self.calculate_switching_losses()

        p_loss = cond_losses["total_w"] + sw_losses["total_w"]
        p_in = p_out + p_loss

        return p_out / p_in

    def loss_breakdown(self, t_junction: float = 100) -> None:
        """Print detailed loss breakdown."""
        cond = self.calculate_conduction_losses(t_junction)
        sw = self.calculate_switching_losses()

        p_out = self.v_out * self.i_out
        p_loss = cond["total_w"] + sw["total_w"]
        eta = p_out / (p_out + p_loss)

        print(f"{'='*50}")
        print(f"Buck Converter Loss Analysis")
        print(f"{'='*50}")
        print(f"Operating Point: {self.v_in}V → {self.v_out}V @ {self.i_out}A")
        print(f"Switching Frequency: {self.f_sw/1e3:.0f} kHz")
        print(f"Duty Cycle: {self.duty_cycle:.1%}")
        print(f"Inductor Ripple: {self.inductor_ripple:.2f} App")
        print(f"{'-'*50}")
        print(f"Conduction Losses:")
        print(f"  HS MOSFET:    {cond['hs_mosfet_w']:.3f} W")
        print(f"  LS MOSFET:    {cond['ls_mosfet_w']:.3f} W")
        print(f"  Inductor:     {cond['inductor_w']:.3f} W")
        print(f"  Output Cap:   {cond['output_cap_w']:.3f} W")
        print(f"  Subtotal:     {cond['total_w']:.3f} W")
        print(f"{'-'*50}")
        print(f"Switching Losses:")
        print(f"  HS Switching: {sw['hs_switching_w']:.3f} W")
        print(f"  Qrr:          {sw['reverse_recovery_w']:.3f} W")
        print(f"  Dead Time:    {sw['dead_time_w']:.3f} W")
        print(f"  Gate Drive:   {sw['gate_drive_w']:.3f} W")
        print(f"  Subtotal:     {sw['total_w']:.3f} W")
        print(f"{'='*50}")
        print(f"Total Losses:   {p_loss:.3f} W")
        print(f"Output Power:   {p_out:.1f} W")
        print(f"Efficiency:     {eta:.2%}")
        print(f"{'='*50}")


# ============================================================
# USAGE EXAMPLE
# ============================================================

if __name__ == "__main__":
    # Define components
    hs_mosfet = MOSFETParams(
        part_number="BSC010N04LS",
        rds_on_mohm=1.0,
        qg_nc=15,
        qgd_nc=3.5,
        qrr_nc=0,  # HS doesn't conduct body diode
        vds_max_v=40,
        id_max_a=100
    )

    ls_mosfet = MOSFETParams(
        part_number="BSC010N04LS",
        rds_on_mohm=1.0,
        qg_nc=15,
        qgd_nc=3.5,
        qrr_nc=35,
        vds_max_v=40,
        id_max_a=100
    )

    inductor = InductorParams(
        part_number="SER2915H-103",
        inductance_uh=10,
        dcr_mohm=2.5,
        isat_a=30,
        irms_a=25
    )

    output_cap = CapacitorParams(
        part_number="GRM32ER71E226KE15",
        capacitance_uf=22,
        voltage_rating_v=25,
        esr_mohm=3,
        ripple_current_a=5
    )

    # Create converter
    buck = BuckConverter(
        v_in=48,
        v_out=12,
        i_out=20,
        f_sw=200e3,
        hs_fet=hs_mosfet,
        ls_fet=ls_mosfet,
        inductor=inductor,
        output_cap=output_cap
    )

    # Analyze
    buck.loss_breakdown()
```

---

## 3. Scientific Libraries

### 3.1 NumPy for Engineering Calculations

```python
import numpy as np

# ============================================================
# ARRAY CREATION FOR PARAMETER SWEEPS
# ============================================================

# Linear sweep - load current
i_load = np.linspace(1, 20, 20)  # 1A to 20A, 20 points

# Logarithmic sweep - frequency for Bode plots
f = np.logspace(1, 6, 100)  # 10 Hz to 1 MHz, 100 points

# Custom ranges
v_in_range = np.array([36, 42, 48, 54, 60])  # Discrete input voltages

# 2D arrays for multi-parameter sweeps
V_IN, I_LOAD = np.meshgrid(v_in_range, i_load)


# ============================================================
# VECTORIZED CALCULATIONS
# ============================================================

# Buck converter calculations across all operating points
v_out = 12.0
f_sw = 200e3
l_h = 10e-6

# Duty cycle (vectorized - works on entire array)
d = v_out / V_IN

# Inductor ripple
delta_i = (V_IN - v_out) * d / (f_sw * l_h)

# Conduction losses
rds_on = 1e-3  # 1 mΩ
p_cond = rds_on * I_LOAD**2 * d

# Find minimum losses for each input voltage
min_loss_idx = np.argmin(p_cond, axis=0)
print(f"Optimal load for each Vin: {i_load[min_loss_idx]}")


# ============================================================
# COMPLEX NUMBERS FOR AC ANALYSIS
# ============================================================

# Bode plot data
f = np.logspace(1, 6, 1000)  # 10 Hz to 1 MHz
omega = 2 * np.pi * f

# LC filter transfer function: H(s) = 1 / (s²LC + sRC + 1)
L = 10e-6   # 10 µH
C = 100e-6  # 100 µF
R = 0.01    # 10 mΩ ESR

s = 1j * omega
H = 1 / (s**2 * L * C + s * R * C + 1)

# Magnitude and phase
magnitude_db = 20 * np.log10(np.abs(H))
phase_deg = np.angle(H, deg=True)

# Find resonant frequency
f_res_idx = np.argmax(magnitude_db)
f_res = f[f_res_idx]
print(f"Resonant frequency: {f_res:.0f} Hz")


# ============================================================
# STATISTICAL ANALYSIS
# ============================================================

# Monte Carlo for tolerance analysis
n_samples = 10000

# Component tolerances
l_nom = 10e-6
l_samples = np.random.normal(l_nom, l_nom * 0.1, n_samples)  # 10% tolerance

c_nom = 100e-6
c_samples = np.random.normal(c_nom, c_nom * 0.2, n_samples)  # 20% tolerance

# Calculate resonant frequency distribution
f_res_samples = 1 / (2 * np.pi * np.sqrt(l_samples * c_samples))

print(f"Resonant frequency statistics:")
print(f"  Mean: {np.mean(f_res_samples):.0f} Hz")
print(f"  Std:  {np.std(f_res_samples):.0f} Hz")
print(f"  Min:  {np.min(f_res_samples):.0f} Hz")
print(f"  Max:  {np.max(f_res_samples):.0f} Hz")


# ============================================================
# LINEAR ALGEBRA FOR CONTROL SYSTEMS
# ============================================================

# State-space representation of buck converter
# dx/dt = Ax + Bu
# y = Cx + Du

# State: [i_L, v_C]
# Input: [d] (duty cycle)
# Output: [v_out]

L = 10e-6
C = 100e-6
R_load = 0.6  # 12V/20A

A = np.array([
    [0, -1/L],
    [1/C, -1/(R_load*C)]
])

B = np.array([
    [48/L],  # Vin/L
    [0]
])

C_mat = np.array([[0, 1]])  # Output is capacitor voltage
D = np.array([[0]])

# Eigenvalues (poles)
eigenvalues = np.linalg.eigvals(A)
print(f"System poles: {eigenvalues}")
print(f"Natural frequency: {np.abs(eigenvalues[0])/(2*np.pi):.0f} Hz")
print(f"Damping ratio: {-np.real(eigenvalues[0])/np.abs(eigenvalues[0]):.3f}")


# ============================================================
# FFT FOR WAVEFORM ANALYSIS
# ============================================================

# Generate PWM waveform
t = np.linspace(0, 10e-6, 10000)  # 10 µs, 10000 points
f_sw = 200e3  # 200 kHz
d = 0.25  # 25% duty cycle

# PWM signal
pwm = (t % (1/f_sw)) < (d / f_sw)
pwm = pwm.astype(float)

# FFT
n = len(t)
fft_result = np.fft.rfft(pwm)
frequencies = np.fft.rfftfreq(n, t[1] - t[0])
magnitude = np.abs(fft_result) / n

# Find harmonic content
harmonics = [1, 2, 3, 4, 5]
for h in harmonics:
    idx = np.argmin(np.abs(frequencies - h * f_sw))
    print(f"{h}x f_sw ({h*f_sw/1e3:.0f} kHz): {magnitude[idx]:.4f}")
```

### 3.2 Matplotlib for Engineering Plots

```python
import matplotlib.pyplot as plt
import numpy as np

# Set engineering-appropriate style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'legend.fontsize': 9,
    'figure.figsize': (10, 6),
    'figure.dpi': 100,
    'lines.linewidth': 1.5,
    'grid.alpha': 0.3
})


# ============================================================
# BODE PLOT
# ============================================================

def plot_bode(f, H, title="Bode Plot"):
    """Create standard Bode plot with magnitude and phase."""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # Magnitude
    magnitude_db = 20 * np.log10(np.abs(H))
    ax1.semilogx(f, magnitude_db, 'b-', linewidth=1.5)
    ax1.set_ylabel('Magnitude (dB)')
    ax1.set_title(title)
    ax1.grid(True, which='both', linestyle='-', alpha=0.3)
    ax1.axhline(y=0, color='k', linestyle='--', linewidth=0.5)

    # Phase
    phase_deg = np.angle(H, deg=True)
    # Unwrap phase for continuous plot
    phase_unwrapped = np.unwrap(np.angle(H)) * 180 / np.pi
    ax2.semilogx(f, phase_unwrapped, 'r-', linewidth=1.5)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Phase (degrees)')
    ax2.grid(True, which='both', linestyle='-', alpha=0.3)
    ax2.axhline(y=-180, color='k', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    return fig


# Example: LC filter Bode plot
f = np.logspace(1, 6, 1000)
L, C, R = 10e-6, 100e-6, 0.01
s = 2j * np.pi * f
H = 1 / (s**2 * L * C + s * R * C + 1)

fig = plot_bode(f, H, "LC Filter Transfer Function")
plt.savefig('bode_plot.png', dpi=150, bbox_inches='tight')
plt.show()


# ============================================================
# EFFICIENCY CURVE
# ============================================================

def plot_efficiency_curves(load_current, efficiency_data, v_in_values, v_out):
    """Plot efficiency curves for multiple input voltages."""

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = plt.cm.viridis(np.linspace(0, 0.8, len(v_in_values)))

    for i, (v_in, eta) in enumerate(zip(v_in_values, efficiency_data)):
        ax.plot(load_current, eta * 100, color=colors[i],
                label=f'Vin = {v_in}V', linewidth=2)

    ax.set_xlabel('Load Current (A)')
    ax.set_ylabel('Efficiency (%)')
    ax.set_title(f'Buck Converter Efficiency (Vout = {v_out}V)')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([load_current.min(), load_current.max()])
    ax.set_ylim([80, 100])

    # Add annotations
    ax.axhline(y=95, color='g', linestyle='--', alpha=0.5, label='95% Target')
    ax.axhline(y=90, color='orange', linestyle='--', alpha=0.5, label='90% Minimum')

    plt.tight_layout()
    return fig


# Example data
i_load = np.linspace(1, 20, 50)
v_in_values = [36, 48, 60]
efficiency_data = []

for v_in in v_in_values:
    # Simplified efficiency model
    d = 12 / v_in
    p_loss = 0.001 * i_load**2 * d + 0.5 + 0.1 * v_in * i_load / 1000
    p_out = 12 * i_load
    eta = p_out / (p_out + p_loss)
    efficiency_data.append(eta)

fig = plot_efficiency_curves(i_load, efficiency_data, v_in_values, 12)
plt.savefig('efficiency_curve.png', dpi=150, bbox_inches='tight')
plt.show()


# ============================================================
# TRANSIENT RESPONSE
# ============================================================

def plot_transient_response(t, signals, labels, title="Transient Response"):
    """Plot multiple signals on same time axis."""

    n_signals = len(signals)
    fig, axes = plt.subplots(n_signals, 1, figsize=(10, 2.5*n_signals), sharex=True)

    if n_signals == 1:
        axes = [axes]

    colors = ['b', 'r', 'g', 'orange', 'purple']

    for i, (signal, label) in enumerate(zip(signals, labels)):
        axes[i].plot(t * 1e6, signal, color=colors[i % len(colors)], linewidth=1.2)
        axes[i].set_ylabel(label)
        axes[i].grid(True, alpha=0.3)

    axes[-1].set_xlabel('Time (µs)')
    axes[0].set_title(title)

    plt.tight_layout()
    return fig


# Example: Buck converter waveforms
t = np.linspace(0, 50e-6, 5000)  # 50 µs
f_sw = 200e3
d = 0.25

# Generate waveforms
pwm = ((t % (1/f_sw)) < (d / f_sw)).astype(float)
v_sw = pwm * 48  # Switch node voltage

# Inductor current (triangular)
i_l_avg = 20
delta_i = 4
phase = (t % (1/f_sw)) / (1/f_sw)
i_l = i_l_avg + delta_i * np.where(phase < d,
                                    phase / d - 0.5,
                                    (1 - phase) / (1 - d) - 0.5)

# Output voltage (DC with ripple)
v_out = 12 + 0.05 * np.sin(2 * np.pi * f_sw * t)

signals = [v_sw, i_l, v_out]
labels = ['Vsw (V)', 'IL (A)', 'Vout (V)']

fig = plot_transient_response(t, signals, labels, "Buck Converter Waveforms")
plt.savefig('transient_response.png', dpi=150, bbox_inches='tight')
plt.show()


# ============================================================
# LOSS BREAKDOWN PIE/BAR CHART
# ============================================================

def plot_loss_breakdown(losses_dict, title="Loss Breakdown"):
    """Create bar chart of power losses."""

    fig, ax = plt.subplots(figsize=(10, 6))

    # Filter out total and non-loss entries
    loss_items = {k: v for k, v in losses_dict.items()
                  if 'total' not in k and v > 0}

    names = [k.replace('_', ' ').replace(' w', '').title() for k in loss_items.keys()]
    values = list(loss_items.values())

    colors = plt.cm.Set2(np.linspace(0, 1, len(names)))

    bars = ax.barh(names, values, color=colors, edgecolor='black', linewidth=0.5)

    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                f'{val:.3f} W', va='center', fontsize=9)

    ax.set_xlabel('Power Loss (W)')
    ax.set_title(title)
    ax.grid(True, axis='x', alpha=0.3)

    # Add total
    total = sum(values)
    ax.text(0.95, 0.05, f'Total: {total:.3f} W',
            transform=ax.transAxes, ha='right',
            fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    return fig


# Example
losses = {
    "hs_mosfet_w": 0.240,
    "ls_mosfet_w": 0.720,
    "inductor_w": 1.001,
    "switching_w": 0.480,
    "gate_drive_w": 0.060,
    "output_cap_w": 0.012
}

fig = plot_loss_breakdown(losses, "48V to 12V/20A Buck Converter Losses")
plt.savefig('loss_breakdown.png', dpi=150, bbox_inches='tight')
plt.show()
```

### 3.3 Pandas for Data Analysis

```python
import pandas as pd
import numpy as np

# ============================================================
# LOADING AND INSPECTING DATA
# ============================================================

# Load oscilloscope CSV data
# Typical format: Time, CH1 (voltage), CH2 (current)
df = pd.read_csv('scope_capture.csv')

# Quick inspection
print(df.head())
print(df.info())
print(df.describe())

# Rename columns for clarity
df.columns = ['time_s', 'v_sw', 'i_l']


# ============================================================
# DATA CLEANING AND PREPROCESSING
# ============================================================

# Handle missing values
df = df.dropna()

# Convert units
df['time_us'] = df['time_s'] * 1e6
df['time_ns'] = df['time_s'] * 1e9

# Calculate derived quantities
df['power_w'] = df['v_sw'] * df['i_l']
df['power_abs_w'] = df['power_w'].abs()


# ============================================================
# STATISTICAL ANALYSIS
# ============================================================

# Summary statistics
print(f"Average current: {df['i_l'].mean():.2f} A")
print(f"RMS current: {np.sqrt((df['i_l']**2).mean()):.2f} A")
print(f"Peak current: {df['i_l'].max():.2f} A")
print(f"Min current: {df['i_l'].min():.2f} A")

# Average power
print(f"Average power: {df['power_w'].mean():.2f} W")


# ============================================================
# TIME-DOMAIN ANALYSIS
# ============================================================

# Find switching edges
# Rising edge: where voltage goes from low to high
threshold = df['v_sw'].max() * 0.5
df['above_threshold'] = df['v_sw'] > threshold
df['rising_edge'] = df['above_threshold'].diff() == 1
df['falling_edge'] = df['above_threshold'].diff() == -1

# Extract switching times
rising_times = df[df['rising_edge']]['time_us'].values
falling_times = df[df['falling_edge']]['time_us'].values

if len(rising_times) >= 2:
    period = np.diff(rising_times).mean()
    frequency = 1 / (period * 1e-6)
    print(f"Measured switching frequency: {frequency/1e3:.1f} kHz")

if len(rising_times) > 0 and len(falling_times) > 0:
    # Duty cycle (assuming rising comes before falling)
    duty = (falling_times[0] - rising_times[0]) / period
    print(f"Measured duty cycle: {duty:.1%}")


# ============================================================
# GROUPING AND AGGREGATION
# ============================================================

# Load efficiency test data
efficiency_data = pd.DataFrame({
    'v_in': [36, 36, 36, 48, 48, 48, 60, 60, 60],
    'i_load': [5, 10, 20, 5, 10, 20, 5, 10, 20],
    'p_in': [65, 125, 245, 62, 122, 242, 61, 121, 241],
    'p_out': [60, 120, 240, 60, 120, 240, 60, 120, 240]
})

# Calculate efficiency
efficiency_data['efficiency'] = efficiency_data['p_out'] / efficiency_data['p_in']
efficiency_data['losses'] = efficiency_data['p_in'] - efficiency_data['p_out']

# Group by input voltage
grouped = efficiency_data.groupby('v_in').agg({
    'efficiency': ['mean', 'min', 'max'],
    'losses': ['mean', 'max']
})

print("\nEfficiency by Input Voltage:")
print(grouped)


# ============================================================
# PIVOT TABLES FOR MULTI-PARAMETER ANALYSIS
# ============================================================

# Create pivot table: efficiency vs Vin and Iload
pivot = efficiency_data.pivot_table(
    values='efficiency',
    index='i_load',
    columns='v_in',
    aggfunc='mean'
)

print("\nEfficiency Matrix:")
print(pivot.to_string(float_format='{:.1%}'.format))


# ============================================================
# THERMAL DATA ANALYSIS
# ============================================================

# Thermal chamber test data
thermal_data = pd.DataFrame({
    'temp_c': [-40, -20, 0, 25, 50, 85, 105],
    'efficiency': [0.94, 0.945, 0.95, 0.955, 0.95, 0.94, 0.93],
    'rds_on_mohm': [1.5, 1.3, 1.1, 1.0, 1.3, 1.8, 2.2],
    'vout_v': [12.05, 12.03, 12.01, 12.00, 11.99, 11.97, 11.95]
})

# Temperature coefficients
rds_on_tc = (thermal_data['rds_on_mohm'].iloc[-1] / thermal_data['rds_on_mohm'].iloc[3] - 1) / (105 - 25)
print(f"Rds_on temperature coefficient: {rds_on_tc*100:.2f} %/°C")

# Find operating temperature for target efficiency
target_eta = 0.95
temp_at_target = thermal_data[thermal_data['efficiency'] >= target_eta]['temp_c'].max()
print(f"Max temperature for η ≥ {target_eta:.0%}: {temp_at_target}°C")


# ============================================================
# EXPORTING RESULTS
# ============================================================

# Save processed data
efficiency_data.to_csv('efficiency_results.csv', index=False)

# Save to Excel with multiple sheets
with pd.ExcelWriter('converter_analysis.xlsx') as writer:
    efficiency_data.to_excel(writer, sheet_name='Efficiency', index=False)
    thermal_data.to_excel(writer, sheet_name='Thermal', index=False)
    pivot.to_excel(writer, sheet_name='Matrix')


# ============================================================
# API COST TRACKING EXAMPLE
# ============================================================

# Track LLM API usage
api_log = pd.DataFrame({
    'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='h'),
    'model': np.random.choice(['claude-sonnet-4-5-20250929', 'claude-haiku-20250306'], 100),
    'input_tokens': np.random.randint(100, 2000, 100),
    'output_tokens': np.random.randint(50, 1000, 100),
    'latency_ms': np.random.randint(200, 5000, 100)
})

# Pricing
pricing = {
    'claude-sonnet-4-5-20250929': {'input': 3.00, 'output': 15.00},
    'claude-haiku-20250306': {'input': 0.25, 'output': 1.25}
}

# Calculate costs
def calc_cost(row):
    p = pricing[row['model']]
    return (row['input_tokens'] * p['input'] + row['output_tokens'] * p['output']) / 1_000_000

api_log['cost_usd'] = api_log.apply(calc_cost, axis=1)

# Daily summary
api_log['date'] = api_log['timestamp'].dt.date
daily_summary = api_log.groupby('date').agg({
    'cost_usd': 'sum',
    'input_tokens': 'sum',
    'output_tokens': 'sum',
    'latency_ms': 'mean'
})

print("\nDaily API Cost Summary:")
print(daily_summary.head())
print(f"\nTotal cost: ${api_log['cost_usd'].sum():.4f}")

# Cost by model
model_summary = api_log.groupby('model').agg({
    'cost_usd': ['sum', 'count'],
    'latency_ms': 'mean'
})
print("\nCost by Model:")
print(model_summary)
```

---

## 4. Asynchronous Programming

### 4.1 Why Async for LLM APIs?

**The Problem:** Synchronous API calls block execution.

```python
# SYNCHRONOUS - Takes 30 seconds for 10 calls (3s each)
import anthropic
import time

def sync_example():
    client = anthropic.Anthropic()
    start = time.time()

    results = []
    for i in range(10):
        response = client.messages.create(
            model="claude-haiku-20250306",
            max_tokens=100,
            messages=[{"role": "user", "content": f"Count to {i}"}]
        )
        results.append(response.content[0].text)

    print(f"Sync time: {time.time() - start:.1f}s")
    return results
```

**The Solution:** Async allows concurrent execution.

```python
# ASYNCHRONOUS - Takes ~3 seconds for 10 calls
import anthropic
import asyncio
import time

async def async_example():
    client = anthropic.AsyncAnthropic()
    start = time.time()

    async def single_call(i):
        response = await client.messages.create(
            model="claude-haiku-20250306",
            max_tokens=100,
            messages=[{"role": "user", "content": f"Count to {i}"}]
        )
        return response.content[0].text

    # Run all 10 calls concurrently
    results = await asyncio.gather(*[single_call(i) for i in range(10)])

    print(f"Async time: {time.time() - start:.1f}s")
    return results

asyncio.run(async_example())
```

**Result:** 10x speedup, same API cost.

### 4.2 Core Async Concepts

```python
import asyncio

# ============================================================
# BASIC ASYNC FUNCTION
# ============================================================

async def fetch_data(item_id: int) -> dict:
    """Async function that simulates API call."""
    await asyncio.sleep(1)  # Simulates network latency
    return {"id": item_id, "data": f"Result {item_id}"}


# ============================================================
# RUNNING ASYNC CODE
# ============================================================

# From synchronous context (main script)
result = asyncio.run(fetch_data(1))

# From within async context
async def main():
    result = await fetch_data(1)
    return result


# ============================================================
# CONCURRENT EXECUTION
# ============================================================

async def concurrent_example():
    # Method 1: gather - runs all tasks, returns when ALL complete
    results = await asyncio.gather(
        fetch_data(1),
        fetch_data(2),
        fetch_data(3)
    )
    return results


async def concurrent_with_exceptions():
    # Method 2: gather with exception handling
    results = await asyncio.gather(
        fetch_data(1),
        fetch_data(2),
        fetch_data(3),
        return_exceptions=True  # Don't fail if one task fails
    )

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {result}")
        else:
            print(f"Task {i}: {result}")

    return results


# ============================================================
# TASK CREATION AND MANAGEMENT
# ============================================================

async def task_example():
    # Create task (starts immediately)
    task = asyncio.create_task(fetch_data(1))

    # Do other work while task runs
    print("Task started, doing other work...")

    # Wait for task when needed
    result = await task
    return result


async def cancel_example():
    # Create cancellable task
    task = asyncio.create_task(fetch_data(1))

    # Cancel if taking too long
    try:
        result = await asyncio.wait_for(task, timeout=0.5)
    except asyncio.TimeoutError:
        task.cancel()
        print("Task cancelled due to timeout")
        result = None

    return result


# ============================================================
# SEMAPHORES FOR RATE LIMITING
# ============================================================

async def rate_limited_example():
    """Limit concurrent requests to avoid rate limiting."""

    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

    async def limited_fetch(item_id):
        async with semaphore:
            return await fetch_data(item_id)

    # Try to run 20 tasks, but only 5 at a time
    results = await asyncio.gather(*[
        limited_fetch(i) for i in range(20)
    ])

    return results


# ============================================================
# QUEUES FOR PRODUCER-CONSUMER
# ============================================================

async def producer_consumer_example():
    """Process items as they become available."""

    queue = asyncio.Queue()

    async def producer():
        for i in range(10):
            await queue.put(i)
            await asyncio.sleep(0.1)  # Simulate items arriving

        # Signal completion
        await queue.put(None)

    async def consumer():
        results = []
        while True:
            item = await queue.get()
            if item is None:
                break

            result = await fetch_data(item)
            results.append(result)
            queue.task_done()

        return results

    # Run producer and consumer concurrently
    _, results = await asyncio.gather(
        producer(),
        consumer()
    )

    return results
```

### 4.3 Async with Claude API

```python
import anthropic
import asyncio
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# BASIC ASYNC API CALL
# ============================================================

async def ask_claude(prompt: str) -> str:
    """Single async API call."""
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = await client.messages.create(
        model="claude-haiku-20250306",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# ============================================================
# BATCH PROCESSING WITH RATE LIMITING
# ============================================================

async def batch_process_datasheets(
    part_numbers: List[str],
    query: str,
    max_concurrent: int = 5
) -> List[Dict]:
    """Process multiple datasheet queries with rate limiting."""

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_one(part_number: str) -> Dict:
        async with semaphore:
            response = await client.messages.create(
                model="claude-haiku-20250306",
                max_tokens=256,
                messages=[{
                    "role": "user",
                    "content": f"For the {part_number}: {query}"
                }]
            )

            return {
                "part_number": part_number,
                "response": response.content[0].text,
                "tokens": response.usage.input_tokens + response.usage.output_tokens
            }

    results = await asyncio.gather(*[
        process_one(pn) for pn in part_numbers
    ], return_exceptions=True)

    # Filter out exceptions
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error processing {part_numbers[i]}: {result}")
        else:
            valid_results.append(result)

    return valid_results


# Usage
async def main():
    parts = ["LM5146", "TPS54360", "LT3080", "LM7805", "LM317"]
    results = await batch_process_datasheets(
        parts,
        "What is the maximum output current?",
        max_concurrent=3
    )

    for r in results:
        print(f"{r['part_number']}: {r['response'][:100]}...")

asyncio.run(main())


# ============================================================
# STREAMING WITH ASYNC
# ============================================================

async def stream_analysis(prompt: str):
    """Stream response for better UX on long analyses."""

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async with client.messages.stream(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)

        print()  # Newline at end

        # Get final message with usage
        final = await stream.get_final_message()
        return final


# Usage
asyncio.run(stream_analysis(
    "Analyze the trade-offs between voltage mode and current mode control "
    "in a synchronous buck converter for 48V to 12V conversion at 200kHz."
))


# ============================================================
# RETRY WITH EXPONENTIAL BACKOFF
# ============================================================

async def call_with_retry(
    prompt: str,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> str:
    """Call API with automatic retry on rate limits."""

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    for attempt in range(max_retries):
        try:
            response = await client.messages.create(
                model="claude-haiku-20250306",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise

            delay = base_delay * (2 ** attempt)
            print(f"Rate limited, waiting {delay}s...")
            await asyncio.sleep(delay)

        except anthropic.APIError as e:
            print(f"API error: {e}")
            raise

    raise RuntimeError("Max retries exceeded")


# ============================================================
# PROGRESS TRACKING
# ============================================================

async def batch_with_progress(items: List[str]) -> List[str]:
    """Process batch with progress updates."""

    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    total = len(items)
    completed = 0

    async def process_one(item: str) -> str:
        nonlocal completed

        response = await client.messages.create(
            model="claude-haiku-20250306",
            max_tokens=128,
            messages=[{"role": "user", "content": item}]
        )

        completed += 1
        print(f"\rProgress: {completed}/{total} ({completed/total:.0%})", end="")

        return response.content[0].text

    # Limit concurrency
    semaphore = asyncio.Semaphore(5)

    async def limited_process(item):
        async with semaphore:
            return await process_one(item)

    results = await asyncio.gather(*[limited_process(i) for i in items])
    print()  # Newline after progress

    return results
```

### 4.4 Async Testing with pytest

```python
# test_async_api.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Pytest fixture for async tests
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test async function
@pytest.mark.asyncio
async def test_ask_claude():
    """Test basic async API call."""

    with patch('anthropic.AsyncAnthropic') as mock_client:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20

        mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)

        # Test
        result = await ask_claude("Test prompt")

        assert result == "Test response"
        mock_client.return_value.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_batch_processing():
    """Test batch processing with rate limiting."""

    with patch('anthropic.AsyncAnthropic') as mock_client:
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20

        mock_client.return_value.messages.create = AsyncMock(return_value=mock_response)

        # Test
        parts = ["PART1", "PART2", "PART3"]
        results = await batch_process_datasheets(parts, "query", max_concurrent=2)

        assert len(results) == 3
        assert all(r["part_number"] in parts for r in results)


@pytest.mark.asyncio
async def test_retry_on_rate_limit():
    """Test that retry works on rate limit."""

    with patch('anthropic.AsyncAnthropic') as mock_client:
        import anthropic

        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Success")]

        mock_client.return_value.messages.create = AsyncMock(
            side_effect=[
                anthropic.RateLimitError("Rate limited", response=MagicMock(), body=None),
                mock_response
            ]
        )

        # Test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await call_with_retry("Test", max_retries=3)

        assert result == "Success"
        assert mock_client.return_value.messages.create.call_count == 2


# Run with: pytest test_async_api.py -v
```

---

## 5. Hands-On Project: Buck Converter Efficiency Analyzer

### 5.1 Project Overview

**Objective:** Build a complete Python application that:
1. Models a synchronous buck converter
2. Calculates losses across operating range
3. Generates efficiency curves
4. Uses async for parallel parameter sweeps
5. Integrates with Claude API for analysis assistance

**Files to create:**
```
buck_efficiency_analyzer/
├── src/
│   ├── __init__.py
│   ├── converter.py      # Buck converter model
│   ├── components.py     # Component dataclasses
│   ├── plotting.py       # Visualization functions
│   └── api_client.py     # Claude API integration
├── tests/
│   └── test_converter.py
├── main.py               # Main application
├── requirements.txt
└── .env
```

### 5.2 Component Definitions

```python
# src/components.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class MOSFETParams:
    """MOSFET parameters for loss calculation."""
    part_number: str
    rds_on_mohm: float
    qg_nc: float
    qgd_nc: float
    vds_max_v: float
    id_max_a: float
    rds_on_tc: float = 0.004  # Temperature coefficient (%/°C)

    def rds_at_temp(self, temp_c: float) -> float:
        """Rds_on adjusted for temperature."""
        return self.rds_on_mohm * 1e-3 * (1 + self.rds_on_tc * (temp_c - 25))


@dataclass
class InductorParams:
    """Inductor parameters."""
    part_number: str
    inductance_uh: float
    dcr_mohm: float
    isat_a: float
    irms_a: float


@dataclass
class ConverterSpecs:
    """Converter operating specifications."""
    v_in_min: float
    v_in_max: float
    v_in_nom: float
    v_out: float
    i_out_max: float
    f_sw_khz: float

    @property
    def f_sw_hz(self) -> float:
        return self.f_sw_khz * 1e3


# Pre-defined components for quick selection
MOSFETS = {
    "BSC010N04LS": MOSFETParams(
        "BSC010N04LS", 1.0, 15, 3.5, 40, 100
    ),
    "BSC016N06NS": MOSFETParams(
        "BSC016N06NS", 1.6, 20, 4.2, 60, 80
    ),
    "IPD90N04S4L-02": MOSFETParams(
        "IPD90N04S4L-02", 0.9, 12, 2.8, 40, 120
    )
}

INDUCTORS = {
    "SER2915H-103": InductorParams(
        "SER2915H-103", 10, 2.5, 30, 25
    ),
    "XAL7070-152": InductorParams(
        "XAL7070-152", 15, 3.8, 28, 22
    ),
    "IHLP4040DZ-01": InductorParams(
        "IHLP4040DZ-01", 4.7, 1.8, 35, 30
    )
}
```

### 5.3 Converter Model

```python
# src/converter.py
import numpy as np
from typing import Tuple, Dict
from .components import MOSFETParams, InductorParams, ConverterSpecs

class BuckConverter:
    """Synchronous buck converter model for efficiency analysis."""

    def __init__(
        self,
        specs: ConverterSpecs,
        hs_mosfet: MOSFETParams,
        ls_mosfet: MOSFETParams,
        inductor: InductorParams,
        vg_drive: float = 10.0,
        t_dead_ns: float = 50.0
    ):
        self.specs = specs
        self.hs_mosfet = hs_mosfet
        self.ls_mosfet = ls_mosfet
        self.inductor = inductor
        self.vg_drive = vg_drive
        self.t_dead_ns = t_dead_ns

    def duty_cycle(self, v_in: float) -> float:
        """Calculate ideal duty cycle."""
        return self.specs.v_out / v_in

    def inductor_ripple(self, v_in: float) -> float:
        """Calculate inductor current ripple (peak-to-peak)."""
        d = self.duty_cycle(v_in)
        l_h = self.inductor.inductance_uh * 1e-6
        return (v_in - self.specs.v_out) * d / (self.specs.f_sw_hz * l_h)

    def rms_current(self, i_load: float, v_in: float) -> float:
        """Calculate RMS inductor current."""
        delta_i = self.inductor_ripple(v_in)
        return np.sqrt(i_load**2 + (delta_i**2) / 12)

    def conduction_losses(
        self,
        v_in: float,
        i_load: float,
        t_junction: float = 100
    ) -> Dict[str, float]:
        """Calculate conduction losses.

        Returns:
            Dictionary with loss breakdown (all in Watts)
        """
        d = self.duty_cycle(v_in)
        i_rms = self.rms_current(i_load, v_in)

        # MOSFET conduction losses
        rds_hs = self.hs_mosfet.rds_at_temp(t_junction)
        rds_ls = self.ls_mosfet.rds_at_temp(t_junction)

        p_hs = i_rms**2 * rds_hs * d
        p_ls = i_rms**2 * rds_ls * (1 - d)

        # Inductor DCR loss
        p_ind = i_rms**2 * self.inductor.dcr_mohm * 1e-3

        return {
            "hs_mosfet": p_hs,
            "ls_mosfet": p_ls,
            "inductor": p_ind,
            "total": p_hs + p_ls + p_ind
        }

    def switching_losses(self, v_in: float, i_load: float) -> Dict[str, float]:
        """Calculate switching losses.

        Returns:
            Dictionary with loss breakdown (all in Watts)
        """
        # Switching transitions
        # Assume 2A gate drive current
        ig = 2.0
        t_rise = self.hs_mosfet.qgd_nc * 1e-9 / ig
        t_fall = t_rise

        p_sw = 0.5 * v_in * i_load * (t_rise + t_fall) * self.specs.f_sw_hz

        # Gate drive
        qg_total = self.hs_mosfet.qg_nc + self.ls_mosfet.qg_nc
        p_gate = qg_total * 1e-9 * self.vg_drive * self.specs.f_sw_hz

        # Dead time
        v_diode = 0.7  # Body diode forward voltage
        p_dead = 2 * v_diode * i_load * self.t_dead_ns * 1e-9 * self.specs.f_sw_hz

        return {
            "switching": p_sw,
            "gate_drive": p_gate,
            "dead_time": p_dead,
            "total": p_sw + p_gate + p_dead
        }

    def efficiency(
        self,
        v_in: float,
        i_load: float,
        t_junction: float = 100
    ) -> Tuple[float, Dict]:
        """Calculate efficiency at operating point.

        Returns:
            Tuple of (efficiency, loss_breakdown)
        """
        p_out = self.specs.v_out * i_load

        cond = self.conduction_losses(v_in, i_load, t_junction)
        sw = self.switching_losses(v_in, i_load)

        p_loss = cond["total"] + sw["total"]
        p_in = p_out + p_loss

        eta = p_out / p_in if p_in > 0 else 0

        breakdown = {
            "conduction": cond,
            "switching": sw,
            "total_loss": p_loss,
            "efficiency": eta
        }

        return eta, breakdown

    def sweep_efficiency(
        self,
        v_in_values: np.ndarray,
        i_load_values: np.ndarray,
        t_junction: float = 100
    ) -> np.ndarray:
        """Sweep efficiency over operating range.

        Args:
            v_in_values: Array of input voltages
            i_load_values: Array of load currents
            t_junction: Junction temperature (°C)

        Returns:
            2D array of efficiency values [len(i_load), len(v_in)]
        """
        eta = np.zeros((len(i_load_values), len(v_in_values)))

        for i, i_load in enumerate(i_load_values):
            for j, v_in in enumerate(v_in_values):
                eta[i, j], _ = self.efficiency(v_in, i_load, t_junction)

        return eta
```

### 5.4 Plotting Functions

```python
# src/plotting.py
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional

def setup_plot_style():
    """Configure matplotlib for engineering plots."""
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'figure.figsize': (10, 6),
        'figure.dpi': 100,
        'lines.linewidth': 2,
        'grid.alpha': 0.3
    })


def plot_efficiency_curves(
    i_load: np.ndarray,
    efficiency_data: List[np.ndarray],
    v_in_labels: List[str],
    v_out: float,
    f_sw_khz: float,
    save_path: Optional[str] = None
) -> plt.Figure:
    """Plot efficiency curves for multiple input voltages.

    Args:
        i_load: Load current array
        efficiency_data: List of efficiency arrays (one per Vin)
        v_in_labels: Labels for each Vin curve
        v_out: Output voltage
        f_sw_khz: Switching frequency
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    setup_plot_style()

    fig, ax = plt.subplots()

    colors = plt.cm.viridis(np.linspace(0, 0.8, len(v_in_labels)))

    for eta, label, color in zip(efficiency_data, v_in_labels, colors):
        ax.plot(i_load, eta * 100, color=color, label=label)

    ax.set_xlabel('Load Current (A)')
    ax.set_ylabel('Efficiency (%)')
    ax.set_title(f'Buck Converter Efficiency\nVout = {v_out}V, fsw = {f_sw_khz} kHz')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([i_load.min(), i_load.max()])
    ax.set_ylim([80, 100])

    # Reference lines
    ax.axhline(y=95, color='g', linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=90, color='orange', linestyle='--', alpha=0.5, linewidth=1)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_loss_breakdown(
    losses: dict,
    title: str = "Loss Breakdown",
    save_path: Optional[str] = None
) -> plt.Figure:
    """Create horizontal bar chart of losses.

    Args:
        losses: Dictionary of loss names and values (Watts)
        title: Plot title
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    setup_plot_style()

    fig, ax = plt.subplots()

    # Format names
    names = [k.replace('_', ' ').title() for k in losses.keys()]
    values = list(losses.values())

    colors = plt.cm.Set2(np.linspace(0, 1, len(names)))

    bars = ax.barh(names, values, color=colors, edgecolor='black', linewidth=0.5)

    # Value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                f'{val:.3f} W', va='center', fontsize=9)

    ax.set_xlabel('Power Loss (W)')
    ax.set_title(title)
    ax.grid(True, axis='x', alpha=0.3)

    # Total annotation
    total = sum(values)
    ax.text(0.95, 0.05, f'Total: {total:.3f} W',
            transform=ax.transAxes, ha='right', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def plot_efficiency_surface(
    v_in: np.ndarray,
    i_load: np.ndarray,
    efficiency: np.ndarray,
    v_out: float,
    save_path: Optional[str] = None
) -> plt.Figure:
    """Create 3D surface plot of efficiency.

    Args:
        v_in: Input voltage array
        i_load: Load current array
        efficiency: 2D efficiency array
        v_out: Output voltage
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure
    """
    setup_plot_style()

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    V, I = np.meshgrid(v_in, i_load)

    surf = ax.plot_surface(V, I, efficiency * 100,
                           cmap='viridis', edgecolor='none', alpha=0.8)

    ax.set_xlabel('Input Voltage (V)')
    ax.set_ylabel('Load Current (A)')
    ax.set_zlabel('Efficiency (%)')
    ax.set_title(f'Efficiency Surface (Vout = {v_out}V)')

    fig.colorbar(surf, ax=ax, shrink=0.6, label='Efficiency (%)')

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig
```

### 5.5 Claude API Integration

```python
# src/api_client.py
import anthropic
import asyncio
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class ConverterAnalysisAssistant:
    """Claude API integration for converter analysis assistance."""

    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-5-20250929"

    async def analyze_efficiency(
        self,
        specs: dict,
        peak_efficiency: float,
        peak_load: float,
        losses: dict
    ) -> str:
        """Get analysis of efficiency results.

        Args:
            specs: Converter specifications
            peak_efficiency: Maximum efficiency achieved
            peak_load: Load current at peak efficiency
            losses: Loss breakdown at peak efficiency

        Returns:
            Analysis text from Claude
        """
        prompt = f"""Analyze this buck converter efficiency result:

**Specifications:**
- Input: {specs['v_in_min']}-{specs['v_in_max']}V
- Output: {specs['v_out']}V @ {specs['i_out_max']}A max
- Switching frequency: {specs['f_sw_khz']} kHz

**Results:**
- Peak efficiency: {peak_efficiency:.2%} at {peak_load:.1f}A
- Losses at peak:
  - HS MOSFET: {losses['hs_mosfet']:.3f}W
  - LS MOSFET: {losses['ls_mosfet']:.3f}W
  - Inductor: {losses['inductor']:.3f}W
  - Switching: {losses['switching']:.3f}W
  - Gate drive: {losses['gate_drive']:.3f}W

Provide:
1. Assessment of efficiency (good/acceptable/needs improvement)
2. Dominant loss mechanisms
3. 2-3 specific recommendations for improvement
4. Expected improvement from each recommendation

Be concise and quantitative."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def suggest_components(
        self,
        specs: dict,
        current_efficiency: float,
        target_efficiency: float
    ) -> str:
        """Get component recommendations for efficiency improvement.

        Args:
            specs: Converter specifications
            current_efficiency: Current peak efficiency
            target_efficiency: Target efficiency

        Returns:
            Component recommendations from Claude
        """
        prompt = f"""Recommend components for this buck converter to achieve efficiency target:

**Requirements:**
- Input: {specs['v_in_nom']}V nominal ({specs['v_in_min']}-{specs['v_in_max']}V)
- Output: {specs['v_out']}V @ {specs['i_out_max']}A
- Switching frequency: {specs['f_sw_khz']} kHz
- Current efficiency: {current_efficiency:.1%}
- Target efficiency: {target_efficiency:.1%}

Provide specific component recommendations:
1. HS MOSFET: Part number, key specs (Rds_on, Qg, Qgd)
2. LS MOSFET: Part number, key specs
3. Inductor: Part number, inductance, DCR, Isat
4. Why these components will achieve the target

Focus on readily available parts from major manufacturers."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def batch_analyze_sweeps(
        self,
        sweep_results: List[Dict],
        max_concurrent: int = 3
    ) -> List[str]:
        """Analyze multiple parameter sweep results concurrently.

        Args:
            sweep_results: List of sweep result dictionaries
            max_concurrent: Maximum concurrent API calls

        Returns:
            List of analysis results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_one(result: Dict) -> str:
            async with semaphore:
                return await self.analyze_efficiency(
                    result["specs"],
                    result["peak_efficiency"],
                    result["peak_load"],
                    result["losses"]
                )

        analyses = await asyncio.gather(*[
            analyze_one(r) for r in sweep_results
        ])

        return analyses
```

### 5.6 Main Application

```python
# main.py
import numpy as np
import asyncio
from src.components import (
    MOSFETParams, InductorParams, ConverterSpecs,
    MOSFETS, INDUCTORS
)
from src.converter import BuckConverter
from src.plotting import (
    plot_efficiency_curves, plot_loss_breakdown, plot_efficiency_surface
)
from src.api_client import ConverterAnalysisAssistant


def main():
    """Main application - Buck converter efficiency analysis."""

    print("=" * 60)
    print("Buck Converter Efficiency Analyzer")
    print("=" * 60)

    # Define converter specifications
    specs = ConverterSpecs(
        v_in_min=36,
        v_in_max=60,
        v_in_nom=48,
        v_out=12,
        i_out_max=20,
        f_sw_khz=200
    )

    # Select components
    hs_mosfet = MOSFETS["BSC010N04LS"]
    ls_mosfet = MOSFETS["BSC010N04LS"]
    inductor = INDUCTORS["SER2915H-103"]

    print(f"\nConverter Specs:")
    print(f"  Vin: {specs.v_in_min}-{specs.v_in_max}V")
    print(f"  Vout: {specs.v_out}V")
    print(f"  Iout: {specs.i_out_max}A max")
    print(f"  fsw: {specs.f_sw_khz} kHz")

    print(f"\nComponents:")
    print(f"  HS MOSFET: {hs_mosfet.part_number} ({hs_mosfet.rds_on_mohm}mΩ)")
    print(f"  LS MOSFET: {ls_mosfet.part_number} ({ls_mosfet.rds_on_mohm}mΩ)")
    print(f"  Inductor: {inductor.part_number} ({inductor.inductance_uh}µH, {inductor.dcr_mohm}mΩ)")

    # Create converter model
    buck = BuckConverter(specs, hs_mosfet, ls_mosfet, inductor)

    # Define sweep parameters
    v_in_values = np.array([36, 48, 60])
    i_load_values = np.linspace(1, 20, 50)

    # Calculate efficiency sweep
    print("\nCalculating efficiency sweep...")
    efficiency_matrix = buck.sweep_efficiency(v_in_values, i_load_values)

    # Extract efficiency curves for each Vin
    efficiency_curves = [efficiency_matrix[:, i] for i in range(len(v_in_values))]
    v_in_labels = [f"Vin = {v}V" for v in v_in_values]

    # Find peak efficiency
    max_idx = np.unravel_index(np.argmax(efficiency_matrix), efficiency_matrix.shape)
    peak_efficiency = efficiency_matrix[max_idx]
    peak_i_load = i_load_values[max_idx[0]]
    peak_v_in = v_in_values[max_idx[1]]

    print(f"\nPeak Efficiency: {peak_efficiency:.2%}")
    print(f"  at Vin = {peak_v_in}V, Iload = {peak_i_load:.1f}A")

    # Get loss breakdown at peak
    _, breakdown = buck.efficiency(peak_v_in, peak_i_load)

    print(f"\nLoss Breakdown at Peak:")
    print(f"  Conduction: {breakdown['conduction']['total']:.3f}W")
    print(f"    HS MOSFET: {breakdown['conduction']['hs_mosfet']:.3f}W")
    print(f"    LS MOSFET: {breakdown['conduction']['ls_mosfet']:.3f}W")
    print(f"    Inductor: {breakdown['conduction']['inductor']:.3f}W")
    print(f"  Switching: {breakdown['switching']['total']:.3f}W")
    print(f"  Total: {breakdown['total_loss']:.3f}W")

    # Generate plots
    print("\nGenerating plots...")

    # Efficiency curves
    fig1 = plot_efficiency_curves(
        i_load_values, efficiency_curves, v_in_labels,
        specs.v_out, specs.f_sw_khz,
        save_path="efficiency_curves.png"
    )

    # Loss breakdown
    loss_dict = {
        "HS MOSFET": breakdown['conduction']['hs_mosfet'],
        "LS MOSFET": breakdown['conduction']['ls_mosfet'],
        "Inductor": breakdown['conduction']['inductor'],
        "Switching": breakdown['switching']['switching'],
        "Gate Drive": breakdown['switching']['gate_drive'],
        "Dead Time": breakdown['switching']['dead_time']
    }
    fig2 = plot_loss_breakdown(
        loss_dict,
        f"Loss Breakdown at {peak_v_in}V, {peak_i_load:.0f}A",
        save_path="loss_breakdown.png"
    )

    # 3D surface (optional - slower)
    # fig3 = plot_efficiency_surface(
    #     v_in_values, i_load_values, efficiency_matrix,
    #     specs.v_out, save_path="efficiency_surface.png"
    # )

    print("Plots saved: efficiency_curves.png, loss_breakdown.png")

    # Optional: Claude API analysis
    print("\n" + "=" * 60)
    print("Claude AI Analysis")
    print("=" * 60)

    async def run_analysis():
        assistant = ConverterAnalysisAssistant()

        # Prepare loss data for API
        losses_for_api = {
            "hs_mosfet": breakdown['conduction']['hs_mosfet'],
            "ls_mosfet": breakdown['conduction']['ls_mosfet'],
            "inductor": breakdown['conduction']['inductor'],
            "switching": breakdown['switching']['switching'],
            "gate_drive": breakdown['switching']['gate_drive']
        }

        specs_dict = {
            "v_in_min": specs.v_in_min,
            "v_in_max": specs.v_in_max,
            "v_out": specs.v_out,
            "i_out_max": specs.i_out_max,
            "f_sw_khz": specs.f_sw_khz
        }

        analysis = await assistant.analyze_efficiency(
            specs_dict, peak_efficiency, peak_i_load, losses_for_api
        )

        print("\n" + analysis)

    # Run async analysis
    try:
        asyncio.run(run_analysis())
    except Exception as e:
        print(f"\nAPI analysis skipped: {e}")
        print("Set ANTHROPIC_API_KEY in .env to enable Claude analysis")

    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

### 5.7 Requirements and Setup

```text
# requirements.txt
numpy>=1.24.0
matplotlib>=3.7.0
pandas>=2.0.0
scipy>=1.10.0
anthropic>=0.18.0
python-dotenv>=1.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

```bash
# Setup
cd ~/projects/power-electronics-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env

# Run
python main.py
```

### 5.8 Unit Tests

```python
# tests/test_converter.py
import pytest
import numpy as np
from src.components import MOSFETParams, InductorParams, ConverterSpecs
from src.converter import BuckConverter

@pytest.fixture
def sample_converter():
    """Create sample converter for testing."""
    specs = ConverterSpecs(36, 60, 48, 12, 20, 200)
    hs_mosfet = MOSFETParams("TEST-HS", 1.0, 15, 3.5, 40, 100)
    ls_mosfet = MOSFETParams("TEST-LS", 1.0, 15, 3.5, 40, 100)
    inductor = InductorParams("TEST-L", 10, 2.5, 30, 25)

    return BuckConverter(specs, hs_mosfet, ls_mosfet, inductor)


def test_duty_cycle(sample_converter):
    """Test duty cycle calculation."""
    d = sample_converter.duty_cycle(48)
    assert d == pytest.approx(0.25, rel=0.01)


def test_inductor_ripple(sample_converter):
    """Test inductor ripple calculation."""
    ripple = sample_converter.inductor_ripple(48)
    # (48-12) * 0.25 / (200e3 * 10e-6) = 4.5A
    assert ripple == pytest.approx(4.5, rel=0.01)


def test_efficiency_range(sample_converter):
    """Test efficiency is in valid range."""
    eta, _ = sample_converter.efficiency(48, 10)
    assert 0.8 < eta < 1.0


def test_efficiency_increases_with_load(sample_converter):
    """Test efficiency curve shape (increases then decreases)."""
    loads = [1, 5, 10, 15, 20]
    efficiencies = [sample_converter.efficiency(48, i)[0] for i in loads]

    # Peak should be in middle range
    peak_idx = np.argmax(efficiencies)
    assert 0 < peak_idx < len(loads) - 1


def test_losses_positive(sample_converter):
    """Test all losses are positive."""
    _, breakdown = sample_converter.efficiency(48, 10)

    assert breakdown['conduction']['hs_mosfet'] > 0
    assert breakdown['conduction']['ls_mosfet'] > 0
    assert breakdown['conduction']['inductor'] > 0
    assert breakdown['switching']['switching'] > 0
    assert breakdown['switching']['gate_drive'] > 0


def test_higher_vin_lower_conduction_loss(sample_converter):
    """Test that higher Vin reduces conduction losses (lower duty)."""
    _, breakdown_low = sample_converter.efficiency(36, 10)
    _, breakdown_high = sample_converter.efficiency(60, 10)

    # Higher Vin = lower duty = lower HS conduction
    assert breakdown_high['conduction']['hs_mosfet'] < breakdown_low['conduction']['hs_mosfet']


# Run with: pytest tests/ -v
```

---

## Exercises

### Exercise 1: VS Code Setup (15 min)
1. Install all recommended extensions
2. Create project structure for `buck-analyzer`
3. Configure virtual environment
4. Create `.vscode/settings.json` with type checking enabled
5. Verify Python interpreter selection

### Exercise 2: Data Types Practice (20 min)
1. Create dataclass for capacitor parameters (capacitance, ESR, voltage rating, ripple current)
2. Create dictionary with full converter BOM (3 MOSFETs, 2 inductors, 10 capacitors)
3. Write function to calculate total BOM cost given unit prices

### Exercise 3: NumPy Calculations (30 min)
1. Calculate boost converter duty cycle for Vin range [12, 24, 36, 48]V, Vout=48V
2. Compute inductor current ripple for all combinations of Vin and L=[4.7, 10, 22]µH
3. Find minimum inductance to keep ripple < 30% of load current (10A)

### Exercise 4: Matplotlib Plotting (30 min)
1. Create efficiency curve plot with 3 different switching frequencies
2. Add second y-axis showing losses in Watts
3. Create subplot with efficiency curve and loss breakdown bar chart

### Exercise 5: Async API Integration (45 min)
1. Modify `batch_process_datasheets` to track and print progress
2. Implement rate limiting with 10 requests per minute max
3. Add retry logic with exponential backoff
4. Create function to compare 3 different MOSFETs using parallel API calls

### Exercise 6: Complete Project (60 min)
1. Add boost converter model class (similar to BuckConverter)
2. Implement `compare_topologies` function that analyzes buck vs boost for same specs
3. Add API function to get Claude's recommendation on topology selection
4. Create comparison plot showing both topologies

---

## Pro Tips

1. **Use type hints everywhere** - Catches errors before running expensive API calls
2. **Virtual environments are mandatory** - Never install packages globally
3. **f-strings > .format() > %** - Modern Python, better readability
4. **List comprehensions > loops** - Faster, more Pythonic
5. **async for API batches** - 10x speedup typical
6. **NumPy for vectorized math** - 100x faster than Python loops
7. **dataclasses for structured data** - Less boilerplate, better documentation
8. **pytest for everything** - Fast feedback, easy mocking
9. **Log API calls** - Debug issues, track costs
10. **Semaphores for rate limiting** - Prevent 429 errors

---

## Next Steps

After completing this module:
1. **Module 1:** Basic Claude API calls
2. **Module 2:** Token optimization for large datasheets
3. **Module 4:** RAG for datasheet lookup system
4. **Module 7:** Build autonomous design assistant agent

---

**Ready to build intelligent power electronics tools? Start with the Buck Converter Efficiency Analyzer!**
