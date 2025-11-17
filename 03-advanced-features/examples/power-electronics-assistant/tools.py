#!/usr/bin/env python3
"""
Power Electronics Calculation Tools

This module provides calculation tools for power electronics design:
- Resistor power calculations
- Capacitor value selection
- Inductor design
- MOSFET selection
- Thermal analysis
- Efficiency calculations
"""

import math
from typing import Dict, Any, Optional

class PowerElectronicsTools:
    """Collection of power electronics calculation tools."""

    @staticmethod
    def calculate_resistor_power(
        voltage: Optional[float] = None,
        current: Optional[float] = None,
        resistance: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate power dissipation in a resistor.

        Args:
            voltage: Voltage across resistor (V)
            current: Current through resistor (A)
            resistance: Resistance value (Ω)

        Returns:
            Dict with power, calculation method, and recommendations
        """
        try:
            if voltage is not None and current is not None:
                power = voltage * current
                calc_method = "P = V × I"
                if resistance is None and current > 0:
                    resistance = voltage / current
            elif current is not None and resistance is not None:
                power = current ** 2 * resistance
                calc_method = "P = I² × R"
                if voltage is None:
                    voltage = current * resistance
            elif voltage is not None and resistance is not None:
                power = voltage ** 2 / resistance
                calc_method = "P = V² / R"
                if current is None:
                    current = voltage / resistance
            else:
                return {"error": "Need at least two of: voltage, current, resistance"}

            # Recommend standard power ratings
            standard_ratings = [0.125, 0.25, 0.5, 1, 2, 5, 10, 25, 50, 100]
            recommended_rating = min([r for r in standard_ratings if r >= power * 2], default=100)

            return {
                "power_watts": round(power, 4),
                "voltage_volts": round(voltage, 2) if voltage else None,
                "current_amps": round(current, 4) if current else None,
                "resistance_ohms": round(resistance, 2) if resistance else None,
                "calculation_method": calc_method,
                "recommended_rating_watts": recommended_rating,
                "safety_factor": 2.0,
                "note": f"Use at least {recommended_rating}W resistor for {power:.3f}W dissipation"
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def calculate_capacitor_value(
        load_current: float,
        ripple_voltage: float,
        frequency: float,
        duty_cycle: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate capacitance for power supply filter.

        Args:
            load_current: Load current (A)
            ripple_voltage: Acceptable ripple voltage (V)
            frequency: Switching frequency (Hz)
            duty_cycle: PWM duty cycle (0-1)

        Returns:
            Dict with calculated and recommended capacitance
        """
        try:
            # C = I × (1-D) / (f × ΔV) for buck converter
            # For general case: C = I / (f × ΔV)
            capacitance = load_current * (1 - duty_cycle) / (frequency * ripple_voltage)
            capacitance_uf = capacitance * 1e6  # Convert to microfarads

            # Recommend standard E12 values
            e12_values = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]
            decades = [1, 10, 100, 1000, 10000]

            standard_values = [v * d for d in decades for v in e12_values]
            recommended = min([v for v in standard_values if v >= capacitance_uf], default=10000)

            # Calculate ESR requirements
            max_esr = ripple_voltage / (load_current * 0.2)  # Assuming 20% ripple from ESR

            return {
                "calculated_capacitance_uf": round(capacitance_uf, 2),
                "recommended_value_uf": recommended,
                "formula": "C = I × (1-D) / (f × ΔV)",
                "max_esr_ohms": round(max_esr, 4),
                "voltage_rating_note": "Use capacitor rated for at least 1.5x max voltage",
                "ripple_current_note": f"Ensure ripple current rating > {round(load_current * 0.3, 2)}A",
                "parallel_suggestion": f"Or use {int(recommended/100)} × 100µF in parallel for better ripple current"
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def calculate_inductor_value(
        input_voltage: float,
        output_voltage: float,
        load_current: float,
        frequency: float,
        ripple_ratio: float = 0.3
    ) -> Dict[str, Any]:
        """
        Calculate inductance for buck/boost converter.

        Args:
            input_voltage: Input voltage (V)
            output_voltage: Output voltage (V)
            load_current: Load current (A)
            frequency: Switching frequency (Hz)
            ripple_ratio: Inductor current ripple ratio (0-1)

        Returns:
            Dict with inductance value and recommendations
        """
        try:
            # Determine topology
            if output_voltage < input_voltage:
                topology = "buck"
                duty_cycle = output_voltage / input_voltage
                # L = (Vin - Vout) × D / (f × ΔIL)
                delta_il = load_current * ripple_ratio
                inductance = (input_voltage - output_voltage) * duty_cycle / (frequency * delta_il)
            else:
                topology = "boost"
                duty_cycle = 1 - (input_voltage / output_voltage)
                # L = Vin × D / (f × ΔIL)
                delta_il = load_current * ripple_ratio
                inductance = input_voltage * duty_cycle / (frequency * delta_il)

            inductance_uh = inductance * 1e6  # Convert to microhenries

            # Recommend standard values
            standard_values = [10, 15, 22, 33, 47, 68, 100, 150, 220, 330, 470, 680, 1000]
            recommended = min([v for v in standard_values if v >= inductance_uh], default=1000)

            # Calculate peak current
            peak_current = load_current + (delta_il / 2)

            return {
                "topology": topology,
                "calculated_inductance_uh": round(inductance_uh, 2),
                "recommended_value_uh": recommended,
                "duty_cycle": round(duty_cycle, 3),
                "ripple_current_amps": round(delta_il, 3),
                "peak_current_amps": round(peak_current, 2),
                "saturation_current_rating": f"Use inductor rated for at least {round(peak_current * 1.2, 2)}A",
                "core_note": "Consider shielded inductor to reduce EMI"
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def select_mosfet(
        voltage_rating: float,
        current_rating: float,
        application: str = "switching",
        frequency: float = 100000
    ) -> Dict[str, Any]:
        """
        Recommend MOSFET based on requirements.

        Args:
            voltage_rating: Required drain-source voltage (V)
            current_rating: Required continuous drain current (A)
            application: Application type (switching/linear/high_frequency)
            frequency: Switching frequency if applicable (Hz)

        Returns:
            Dict with MOSFET recommendations
        """
        try:
            # Apply derating
            required_vds = voltage_rating * 1.25  # 25% derating
            required_id = current_rating * 1.43   # 70% of rated for continuous

            # Simple recommendation database
            recommendations = {
                "low": {  # < 100V
                    "switching": ["IRFZ44N (55V, 49A)", "IPP045N10N5 (100V, 120A, low RdsOn)"],
                    "high_frequency": ["IRFS3006 (60V, 195A, ultra-low RdsOn)", "BSC028N08NS5"]
                },
                "medium": {  # 100-300V
                    "switching": ["IRFP260N (200V, 50A)", "IPB60R190C6 (600V, CoolMOS)"],
                    "high_frequency": ["IPP60R099C6 (600V, CoolMOS)"]
                },
                "high": {  # > 300V
                    "switching": ["IRFP460 (500V, 20A)", "SPW47N60C3 (650V, 47A)"],
                    "high_frequency": ["C3M0075120K (SiC, 1200V, 36A)"]
                }
            }

            # Categorize voltage
            if required_vds < 100:
                v_cat = "low"
            elif required_vds < 300:
                v_cat = "medium"
            else:
                v_cat = "high"

            app_key = "high_frequency" if frequency > 100000 else "switching"
            suggested = recommendations[v_cat].get(app_key, ["Consult manufacturer catalog"])

            # Calculate gate drive requirements
            if frequency > 0:
                # Qg typical values (nC) for different categories
                typical_qg = {"low": 50, "medium": 100, "high": 200}[v_cat]
                gate_drive_current = typical_qg * 1e-9 * frequency
            else:
                gate_drive_current = None

            return {
                "voltage_category": v_cat,
                "required_vds_volts": round(required_vds, 1),
                "required_id_amps": round(required_id, 1),
                "recommended_parts": suggested,
                "application": application,
                "switching_frequency_hz": frequency if frequency > 0 else "N/A",
                "gate_drive_current_amps": round(gate_drive_current * 1000, 2) if gate_drive_current else "N/A",
                "additional_requirements": {
                    "gate_resistor": "10-47Ω typical for most applications",
                    "gate_driver": "Use dedicated driver IC for >1A gate current",
                    "heatsink": "Required for >10W dissipation",
                    "snubber": "Consider RC snubber for inductive loads"
                }
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def calculate_thermal(
        power_dissipation: float,
        ambient_temp: float = 25,
        junction_temp_max: float = 150,
        rth_jc: float = 1.0,
        rth_cs: float = 0.5
    ) -> Dict[str, Any]:
        """
        Calculate heatsink requirements and junction temperature.

        Args:
            power_dissipation: Power dissipation (W)
            ambient_temp: Ambient temperature (°C)
            junction_temp_max: Maximum junction temperature (°C)
            rth_jc: Junction-to-case thermal resistance (°C/W)
            rth_cs: Case-to-sink thermal resistance (°C/W)

        Returns:
            Dict with thermal analysis results
        """
        try:
            # Calculate required sink-to-ambient thermal resistance
            # Tj = Ta + P × (Rth_jc + Rth_cs + Rth_sa)
            # Rth_sa = (Tj_max - Ta) / P - Rth_jc - Rth_cs

            rth_sa_required = (junction_temp_max - ambient_temp) / power_dissipation - rth_jc - rth_cs

            # Calculate junction temp with typical small heatsink (10°C/W)
            rth_sa_typical = 10
            tj_typical = ambient_temp + power_dissipation * (rth_jc + rth_cs + rth_sa_typical)

            # Natural vs forced cooling
            if rth_sa_required < 2:
                cooling_type = "Forced air cooling required"
            elif rth_sa_required < 10:
                cooling_type = "Large heatsink with fan recommended"
            else:
                cooling_type = "Natural convection acceptable"

            return {
                "power_dissipation_watts": power_dissipation,
                "ambient_temp_celsius": ambient_temp,
                "max_junction_temp_celsius": junction_temp_max,
                "rth_jc": rth_jc,
                "rth_cs": rth_cs,
                "required_rth_sa": round(rth_sa_required, 2),
                "junction_temp_with_typical_heatsink": round(tj_typical, 1),
                "cooling_recommendation": cooling_type,
                "thermal_margin_celsius": round(junction_temp_max - tj_typical, 1),
                "note": "Always verify with thermal camera or thermocouple in actual application"
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def calculate_efficiency(
        input_voltage: float,
        output_voltage: float,
        output_current: float,
        switching_loss: float = 0,
        conduction_loss: float = 0,
        gate_drive_loss: float = 0
    ) -> Dict[str, Any]:
        """
        Calculate converter efficiency.

        Args:
            input_voltage: Input voltage (V)
            output_voltage: Output voltage (V)
            output_current: Output current (A)
            switching_loss: Switching losses (W)
            conduction_loss: Conduction losses (W)
            gate_drive_loss: Gate drive losses (W)

        Returns:
            Dict with efficiency analysis
        """
        try:
            output_power = output_voltage * output_current
            total_loss = switching_loss + conduction_loss + gate_drive_loss
            input_power = output_power + total_loss

            if input_power > 0:
                efficiency = (output_power / input_power) * 100
            else:
                return {"error": "Invalid power values"}

            input_current = input_power / input_voltage if input_voltage > 0 else 0

            return {
                "output_power_watts": round(output_power, 2),
                "input_power_watts": round(input_power, 2),
                "total_loss_watts": round(total_loss, 2),
                "efficiency_percent": round(efficiency, 2),
                "input_current_amps": round(input_current, 3),
                "loss_breakdown": {
                    "switching_loss_watts": switching_loss,
                    "conduction_loss_watts": conduction_loss,
                    "gate_drive_loss_watts": gate_drive_loss
                },
                "power_factor": "Assumed unity for DC-DC converter",
                "note": f"At {efficiency:.1f}% efficiency, dissipating {total_loss:.2f}W as heat"
            }
        except Exception as e:
            return {"error": str(e)}


# Tool definitions for Claude/OpenAI
POWER_TOOLS_CLAUDE = [
    {
        "name": "calculate_resistor_power",
        "description": "Calculate power dissipation in a resistor and recommend power rating. Provide at least two of: voltage, current, resistance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "voltage": {"type": "number", "description": "Voltage across resistor in volts"},
                "current": {"type": "number", "description": "Current through resistor in amperes"},
                "resistance": {"type": "number", "description": "Resistance in ohms"}
            }
        }
    },
    {
        "name": "calculate_capacitor_value",
        "description": "Calculate required capacitance for power supply output filter to achieve specified ripple voltage",
        "input_schema": {
            "type": "object",
            "properties": {
                "load_current": {"type": "number", "description": "Load current in amperes"},
                "ripple_voltage": {"type": "number", "description": "Maximum acceptable ripple voltage in volts"},
                "frequency": {"type": "number", "description": "Switching frequency in Hz"},
                "duty_cycle": {"type": "number", "description": "PWM duty cycle (0-1), default 0.5"}
            },
            "required": ["load_current", "ripple_voltage", "frequency"]
        }
    },
    {
        "name": "calculate_inductor_value",
        "description": "Calculate inductance for buck or boost converter based on voltages and load",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_voltage": {"type": "number", "description": "Input voltage in volts"},
                "output_voltage": {"type": "number", "description": "Output voltage in volts"},
                "load_current": {"type": "number", "description": "Load current in amperes"},
                "frequency": {"type": "number", "description": "Switching frequency in Hz"},
                "ripple_ratio": {"type": "number", "description": "Inductor current ripple ratio (0-1), default 0.3"}
            },
            "required": ["input_voltage", "output_voltage", "load_current", "frequency"]
        }
    },
    {
        "name": "select_mosfet",
        "description": "Recommend MOSFET part numbers based on voltage, current, and application requirements",
        "input_schema": {
            "type": "object",
            "properties": {
                "voltage_rating": {"type": "number", "description": "Required voltage rating in volts"},
                "current_rating": {"type": "number", "description": "Required current rating in amperes"},
                "application": {
                    "type": "string",
                    "enum": ["switching", "linear", "high_frequency"],
                    "description": "Application type"
                },
                "frequency": {"type": "number", "description": "Switching frequency in Hz (for switching applications)"}
            },
            "required": ["voltage_rating", "current_rating"]
        }
    },
    {
        "name": "calculate_thermal",
        "description": "Calculate heatsink requirements and junction temperature for power devices",
        "input_schema": {
            "type": "object",
            "properties": {
                "power_dissipation": {"type": "number", "description": "Power dissipation in watts"},
                "ambient_temp": {"type": "number", "description": "Ambient temperature in °C, default 25"},
                "junction_temp_max": {"type": "number", "description": "Max junction temp in °C, default 150"},
                "rth_jc": {"type": "number", "description": "Junction-to-case thermal resistance in °C/W"},
                "rth_cs": {"type": "number", "description": "Case-to-sink thermal resistance in °C/W"}
            },
            "required": ["power_dissipation"]
        }
    },
    {
        "name": "calculate_efficiency",
        "description": "Calculate power converter efficiency based on losses",
        "input_schema": {
            "type": "object",
            "properties": {
                "input_voltage": {"type": "number", "description": "Input voltage in volts"},
                "output_voltage": {"type": "number", "description": "Output voltage in volts"},
                "output_current": {"type": "number", "description": "Output current in amperes"},
                "switching_loss": {"type": "number", "description": "Switching losses in watts"},
                "conduction_loss": {"type": "number", "description": "Conduction losses in watts"},
                "gate_drive_loss": {"type": "number", "description": "Gate drive losses in watts"}
            },
            "required": ["input_voltage", "output_voltage", "output_current"]
        }
    }
]

# Map tool names to functions
TOOL_FUNCTIONS = {
    "calculate_resistor_power": PowerElectronicsTools.calculate_resistor_power,
    "calculate_capacitor_value": PowerElectronicsTools.calculate_capacitor_value,
    "calculate_inductor_value": PowerElectronicsTools.calculate_inductor_value,
    "select_mosfet": PowerElectronicsTools.select_mosfet,
    "calculate_thermal": PowerElectronicsTools.calculate_thermal,
    "calculate_efficiency": PowerElectronicsTools.calculate_efficiency
}
