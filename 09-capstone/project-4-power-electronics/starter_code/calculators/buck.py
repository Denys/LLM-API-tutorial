"""
Buck Converter Calculator

Implement calculations for buck (step-down) converter design.

Reference:
- Texas Instruments: "Basic Calculation of a Buck Converter's Power Stage"
- Analog Devices: "Step-Down (Buck) Regulator Design"
"""

import math
from typing import Tuple
from ..models import DesignSpecs, InductorSpec, CapacitorSpec, MOSFETSpec


def calculate_duty_cycle(v_in: float, v_out: float) -> float:
    """
    Calculate duty cycle for buck converter.

    D = V_out / V_in

    Args:
        v_in: Input voltage (V)
        v_out: Output voltage (V)

    Returns:
        Duty cycle (0-1)
    """
    if v_out >= v_in:
        raise ValueError(f"Buck converter requires V_out < V_in (got {v_out}V >= {v_in}V)")

    duty = v_out / v_in

    if duty < 0.1 or duty > 0.9:
        # Warn about extreme duty cycles
        print(f"Warning: Duty cycle {duty:.1%} is outside typical range (10-90%)")

    return duty


def calculate_inductor(
    specs: DesignSpecs,
    duty_cycle: float,
    fsw: float,
    ripple_ratio: float = 0.3
) -> InductorSpec:
    """
    Calculate inductor value and ratings for buck converter.

    L = V_out × (1 - D) / (ΔI_L × f_sw)

    where ΔI_L = ripple_ratio × I_out

    Args:
        specs: Design specifications
        duty_cycle: Duty cycle at minimum input voltage
        fsw: Switching frequency (Hz)
        ripple_ratio: Inductor ripple current as fraction of I_out (typically 0.2-0.4)

    Returns:
        Inductor specification
    """
    # Calculate ripple current
    delta_i_l = ripple_ratio * specs.output_current

    # Calculate inductance
    # L = V_out × (1 - D) / (ΔI_L × f_sw)
    inductance = specs.output_voltage * (1 - duty_cycle) / (delta_i_l * fsw)

    # Round to standard E12 series value with margin
    inductance = round_to_e_series(inductance * 1.1, series="E12")

    # Current ratings
    i_avg = specs.output_current
    i_peak = i_avg + delta_i_l / 2
    i_sat = i_peak * 1.3  # 30% margin for saturation

    # DCR budget (allow 1% efficiency loss)
    # P_loss = I_out² × R_dcr
    # For 1% loss: R_dcr = 0.01 × V_out / I_out
    dcr_max = 0.01 * specs.output_voltage / specs.output_current

    return InductorSpec(
        inductance=inductance,
        current_avg=i_avg,
        current_peak=i_peak,
        current_sat=i_sat,
        dcr_max=dcr_max,
        frequency=fsw
    )


def calculate_output_capacitor(
    specs: DesignSpecs,
    delta_i_l: float,
    fsw: float
) -> CapacitorSpec:
    """
    Calculate output capacitor for buck converter.

    Two constraints:
    1. ESR ripple: V_ripple = ΔI_L × ESR
    2. Capacitance ripple: V_ripple = ΔI_L / (8 × f_sw × C)

    Args:
        specs: Design specifications
        delta_i_l: Inductor ripple current (A)
        fsw: Switching frequency (Hz)

    Returns:
        Output capacitor specification
    """
    # ESR constraint
    esr_max = specs.ripple_voltage_max / delta_i_l

    # Capacitance constraint
    # V_ripple = ΔI_L / (8 × f_sw × C)
    # C = ΔI_L / (8 × f_sw × V_ripple)
    c_min = delta_i_l / (8 * fsw * specs.ripple_voltage_max)

    # Add margin and round up
    capacitance = round_to_e_series(c_min * 1.5, series="E12")

    # Voltage rating (2× safety margin)
    voltage_rating = specs.output_voltage * 2

    # Ripple current (RMS)
    # For buck: I_ripple_rms ≈ ΔI_L / √12
    ripple_current = delta_i_l / math.sqrt(12)

    return CapacitorSpec(
        capacitance=capacitance,
        voltage_rating=voltage_rating,
        esr_max=esr_max,
        ripple_current=ripple_current,
        type="ceramic"  # Prefer ceramic for low ESR
    )


def calculate_input_capacitor(
    specs: DesignSpecs,
    duty_cycle: float,
    fsw: float
) -> CapacitorSpec:
    """
    Calculate input capacitor for buck converter.

    Input capacitor must handle ripple current.

    Args:
        specs: Design specifications
        duty_cycle: Duty cycle
        fsw: Switching frequency (Hz)

    Returns:
        Input capacitor specification
    """
    # Input ripple current (RMS)
    # I_in_ripple = I_out × √(D × (1-D))
    ripple_current = specs.output_current * math.sqrt(duty_cycle * (1 - duty_cycle))

    # Capacitance for voltage ripple
    # Assume 5% input ripple voltage
    v_ripple = specs.input_voltage_max * 0.05

    # C = I_ripple / (f_sw × V_ripple)
    capacitance = ripple_current / (fsw * v_ripple)

    # Round up
    capacitance = round_to_e_series(capacitance * 1.2, series="E12")

    # Voltage rating (1.5× safety margin for input)
    voltage_rating = specs.input_voltage_max * 1.5

    # ESR requirement
    esr_max = v_ripple / ripple_current

    return CapacitorSpec(
        capacitance=capacitance,
        voltage_rating=voltage_rating,
        esr_max=esr_max,
        ripple_current=ripple_current,
        type="ceramic"
    )


def calculate_mosfet_requirements(
    specs: DesignSpecs,
    duty_cycle: float
) -> Tuple[MOSFETSpec, MOSFETSpec]:
    """
    Calculate MOSFET requirements for synchronous buck.

    Returns high-side and low-side MOSFET specs.

    Args:
        specs: Design specifications
        duty_cycle: Duty cycle at nominal input

    Returns:
        Tuple of (high_side_mosfet, low_side_mosfet)
    """
    # Voltage rating (1.5× safety margin)
    v_ds_min = specs.input_voltage_max * 1.5

    # Current rating (1.25× safety margin)
    i_d_min = specs.output_current * 1.25

    # High-side MOSFET
    # Conduction loss budget: 1% efficiency
    # P_cond = I_out² × R_DS(on) × D
    # R_DS(on) < 0.01 × V_out / (I_out × D)
    rds_on_hs_max = 0.01 * specs.output_voltage / (specs.output_current * duty_cycle)

    # Q_g affects switching losses - lower is better
    # Budget ~0.5% efficiency for switching
    # Approximate: Q_g < some_value (component-dependent)
    q_g_hs_max = 50e-9  # 50nC as starting point

    high_side = MOSFETSpec(
        v_ds_min=v_ds_min,
        i_d_min=i_d_min,
        rds_on_max=rds_on_hs_max,
        q_g_max=q_g_hs_max
    )

    # Low-side MOSFET
    # Conducts for (1-D), so different conduction loss budget
    rds_on_ls_max = 0.01 * specs.output_voltage / (specs.output_current * (1 - duty_cycle))

    # Can use same Q_g requirement
    q_g_ls_max = 50e-9

    low_side = MOSFETSpec(
        v_ds_min=v_ds_min,
        i_d_min=i_d_min,
        rds_on_max=rds_on_ls_max,
        q_g_max=q_g_ls_max
    )

    return high_side, low_side


def select_switching_frequency(specs: DesignSpecs) -> float:
    """
    Select appropriate switching frequency based on requirements.

    Trade-offs:
    - Higher frequency → smaller magnetics, faster response, higher switching loss
    - Lower frequency → larger magnetics, lower switching loss, slower response

    Args:
        specs: Design specifications

    Returns:
        Recommended switching frequency (Hz)
    """
    # If specified, use it
    if specs.switching_frequency:
        return specs.switching_frequency

    # Otherwise, select based on power level and constraints
    power_out = specs.output_voltage * specs.output_current

    if specs.size_constraint:
        # Size constrained → higher frequency for smaller components
        if power_out < 25:
            return 500e3  # 500kHz for <25W
        elif power_out < 100:
            return 300e3  # 300kHz for 25-100W
        else:
            return 200e3  # 200kHz for >100W
    else:
        # Optimize for efficiency → lower frequency
        if power_out < 25:
            return 200e3  # 200kHz for <25W
        elif power_out < 100:
            return 100e3  # 100kHz for 25-100W
        else:
            return 50e3   # 50kHz for >100W


def round_to_e_series(value: float, series: str = "E12") -> float:
    """
    Round value to standard E-series.

    E12 series: 10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82
    E24 series: E12 + intermediate values

    Args:
        value: Value to round
        series: "E12" or "E24"

    Returns:
        Rounded value
    """
    e12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
    e24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
           3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

    values = e12 if series == "E12" else e24

    # Get exponent
    exp = math.floor(math.log10(value))
    mantissa = value / (10 ** exp)

    # Find closest value (round up for safety)
    closest = min([v for v in values if v >= mantissa], default=values[-1])

    # If mantissa was larger than largest value, go to next decade
    if closest < mantissa:
        exp += 1
        closest = values[0]

    return closest * (10 ** exp)


def design_buck_converter(specs: DesignSpecs) -> dict:
    """
    Complete buck converter design.

    This is the main entry point that uses all the calculation functions.

    Args:
        specs: Design specifications

    Returns:
        Dictionary with complete design
    """
    # Select switching frequency
    fsw = select_switching_frequency(specs)

    # Calculate duty cycle at minimum input (worst case)
    duty_cycle = calculate_duty_cycle(specs.input_voltage_min, specs.output_voltage)

    # Calculate inductor
    inductor = calculate_inductor(specs, duty_cycle, fsw)

    # Calculate capacitors
    delta_i_l = 0.3 * specs.output_current  # Ripple current
    output_cap = calculate_output_capacitor(specs, delta_i_l, fsw)
    input_cap = calculate_input_capacitor(specs, duty_cycle, fsw)

    # Calculate MOSFET requirements
    mosfet_hs, mosfet_ls = calculate_mosfet_requirements(specs, duty_cycle)

    return {
        "topology": "buck",
        "switching_frequency": fsw,
        "duty_cycle_min": duty_cycle,
        "duty_cycle_max": calculate_duty_cycle(specs.input_voltage_max, specs.output_voltage),
        "inductor": inductor.dict(),
        "output_capacitor": output_cap.dict(),
        "input_capacitor": input_cap.dict(),
        "mosfet_high_side": mosfet_hs.dict(),
        "mosfet_low_side": mosfet_ls.dict()
    }


# Example usage
if __name__ == "__main__":
    # Test with example specifications
    specs = DesignSpecs(
        input_voltage_min=18,
        input_voltage_max=30,
        output_voltage=12,
        output_current=5,
        efficiency_target=0.92
    )

    design = design_buck_converter(specs)

    print("Buck Converter Design Results:")
    print(f"Switching Frequency: {design['switching_frequency']/1e3:.0f} kHz")
    print(f"Duty Cycle: {design['duty_cycle_min']:.1%} - {design['duty_cycle_max']:.1%}")
    print(f"\nInductor: {design['inductor']['inductance']*1e6:.1f} µH")
    print(f"  Saturation Current: {design['inductor']['current_sat']:.1f} A")
    print(f"  DCR < {design['inductor']['dcr_max']*1000:.1f} mΩ")
    print(f"\nOutput Capacitor: {design['output_capacitor']['capacitance']*1e6:.0f} µF")
    print(f"  ESR < {design['output_capacitor']['esr_max']*1000:.1f} mΩ")
