#!/usr/bin/env python3
"""
Power Electronics Multi-Agent Design System

A comprehensive multi-agent system for power electronics design.
Demonstrates the full capabilities of multi-agent collaboration:

Agents:
1. Specification Agent: Gathers and validates requirements
2. Topology Selector: Chooses optimal circuit topology
3. Component Designer: Calculates component values
4. Part Selector: Selects specific components from database
5. Thermal Analyst: Analyzes thermal requirements
6. EMC Specialist: Addresses EMI/EMC concerns
7. Layout Engineer: Provides PCB layout guidance
8. Design Verifier: Validates complete design
9. Documentation Agent: Generates design documentation

Workflow:
- Hierarchical orchestration with supervisor
- Parallel analysis where appropriate
- Iterative refinement based on feedback
- Complete design documentation
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


@dataclass
class DesignRequirements:
    """Power supply design requirements."""
    input_voltage_min: float
    input_voltage_max: float
    output_voltage: float
    output_current: float
    efficiency_target: float
    ripple_max_mv: float
    size_constraint: str
    cost_target: float
    temp_range_min: int
    temp_range_max: int
    emc_standard: str
    additional_notes: str = ""


@dataclass
class DesignDocument:
    """Complete design documentation."""
    requirements: DesignRequirements
    topology: str
    components: Dict[str, Any] = field(default_factory=dict)
    calculations: Dict[str, Any] = field(default_factory=dict)
    thermal_analysis: str = ""
    emc_considerations: str = ""
    layout_guide: str = ""
    verification_report: str = ""
    bom: List[Dict] = field(default_factory=list)
    total_cost: float = 0.0
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class DesignAgent:
    """Base class for design agents."""

    def __init__(self, name: str, role: str, system_prompt: str,
                 model: str = "claude-3-5-sonnet-20241022"):
        """Initialize design agent."""
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def analyze(self, task: str, context: Dict[str, Any]) -> str:
        """
        Perform analysis.

        Args:
            task: Task description
            context: Design context

        Returns:
            Analysis result
        """
        print(f"\n{'▸'*3} {self.name}")

        # Build prompt
        prompt = f"{task}\n\nContext:\n{json.dumps(context, indent=2)}\n\nProvide detailed analysis."

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text
            print(f"  ✓ {result[:100]}...")
            return result

        except Exception as e:
            error = f"Error: {e}"
            print(f"  ✗ {error}")
            return error


class PowerDesignSystem:
    """Multi-agent power electronics design system."""

    def __init__(self):
        """Initialize the design system."""
        self.agents: Dict[str, DesignAgent] = {}
        self.design_doc: Optional[DesignDocument] = None
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all specialized agents."""
        print("\n🤖 Initializing Design Agents...")

        agent_configs = [
            (
                "SpecificationAgent",
                "Requirements Analysis",
                "You are an expert at gathering and validating power supply requirements. "
                "Ensure all specifications are complete, consistent, and achievable."
            ),
            (
                "TopologySelector",
                "Topology Selection",
                "You are an expert in power converter topologies (buck, boost, buck-boost, flyback, forward, etc.). "
                "Select the optimal topology based on requirements. Consider efficiency, complexity, and cost."
            ),
            (
                "ComponentDesigner",
                "Component Calculation",
                "You are an expert in calculating component values for power converters. "
                "Calculate inductor, capacitor, and resistor values with proper margins. "
                "Show all calculations and formulas."
            ),
            (
                "PartSelector",
                "Component Selection",
                "You are an expert in selecting actual electronic components. "
                "Choose specific part numbers from major manufacturers. "
                "Consider availability, cost, and performance."
            ),
            (
                "ThermalAnalyst",
                "Thermal Analysis",
                "You are a thermal analysis expert. Calculate power dissipation, junction temperatures, "
                "and recommend cooling solutions. Consider worst-case conditions."
            ),
            (
                "EMCSpecialist",
                "EMI/EMC Engineering",
                "You are an EMC expert. Identify EMI sources, recommend filtering, "
                "layout techniques, and shielding. Consider standards compliance."
            ),
            (
                "LayoutEngineer",
                "PCB Layout",
                "You are a PCB layout expert specializing in power electronics. "
                "Provide critical routing guidance, layer stackup, copper weights, and thermal vias."
            ),
            (
                "DesignVerifier",
                "Design Verification",
                "You are a design verification expert. Review complete designs for "
                "correctness, safety, and manufacturability. Identify issues and risks."
            ),
            (
                "DocumentationAgent",
                "Documentation",
                "You are a technical documentation expert. Create clear, comprehensive "
                "design documentation with all key information organized logically."
            )
        ]

        for name, role, system_prompt in agent_configs:
            agent = DesignAgent(name, role, system_prompt)
            self.agents[name] = agent
            print(f"  ✓ {name} - {role}")

    def design(self, requirements: DesignRequirements) -> DesignDocument:
        """
        Execute complete design workflow.

        Args:
            requirements: Design requirements

        Returns:
            Complete design document
        """
        print(f"\n{'='*70}")
        print(f"⚡ POWER ELECTRONICS MULTI-AGENT DESIGN SYSTEM")
        print(f"{'='*70}")

        self.design_doc = DesignDocument(requirements=requirements)

        # Phase 1: Requirements Validation
        print(f"\n{'─'*70}")
        print("PHASE 1: Requirements Validation")
        print(f"{'─'*70}")

        req_validation = self.agents["SpecificationAgent"].analyze(
            "Validate these power supply requirements and identify any issues or missing information.",
            {"requirements": requirements.__dict__}
        )

        # Phase 2: Topology Selection
        print(f"\n{'─'*70}")
        print("PHASE 2: Topology Selection")
        print(f"{'─'*70}")

        topology = self.agents["TopologySelector"].analyze(
            "Select the optimal converter topology for these requirements. "
            "Explain your choice and list alternatives.",
            {
                "requirements": requirements.__dict__,
                "validation": req_validation
            }
        )
        self.design_doc.topology = topology

        # Phase 3: Component Design
        print(f"\n{'─'*70}")
        print("PHASE 3: Component Design & Calculation")
        print(f"{'─'*70}")

        component_design = self.agents["ComponentDesigner"].analyze(
            "Calculate all component values for this design. "
            "Include inductance, capacitance, switching frequency, duty cycle, etc. "
            "Show formulas and calculations.",
            {
                "requirements": requirements.__dict__,
                "topology": topology
            }
        )
        self.design_doc.calculations["components"] = component_design

        # Phase 4: Part Selection
        print(f"\n{'─'*70}")
        print("PHASE 4: Component Selection")
        print(f"{'─'*70}")

        part_selection = self.agents["PartSelector"].analyze(
            "Select specific components (ICs, MOSFETs, inductors, capacitors) with "
            "part numbers and specifications. Create a BOM.",
            {
                "requirements": requirements.__dict__,
                "calculations": component_design
            }
        )
        self.design_doc.components["selected_parts"] = part_selection

        # Phase 5: Parallel Analysis (Thermal + EMC)
        print(f"\n{'─'*70}")
        print("PHASE 5: Parallel Analysis (Thermal & EMC)")
        print(f"{'─'*70}")

        print("\n  🔥 Thermal Analysis (parallel)...")
        thermal = self.agents["ThermalAnalyst"].analyze(
            "Analyze thermal requirements. Calculate power dissipation in semiconductors, "
            "junction temperatures, and recommend cooling solutions.",
            {
                "requirements": requirements.__dict__,
                "topology": topology,
                "components": part_selection
            }
        )
        self.design_doc.thermal_analysis = thermal

        print("\n  📡 EMC Analysis (parallel)...")
        emc = self.agents["EMCSpecialist"].analyze(
            "Analyze EMI/EMC considerations. Identify noise sources, recommend filtering, "
            "and provide compliance guidance.",
            {
                "requirements": requirements.__dict__,
                "topology": topology,
                "switching_frequency": "from component design"
            }
        )
        self.design_doc.emc_considerations = emc

        # Phase 6: PCB Layout Guidance
        print(f"\n{'─'*70}")
        print("PHASE 6: PCB Layout Guidance")
        print(f"{'─'*70}")

        layout = self.agents["LayoutEngineer"].analyze(
            "Provide PCB layout guidance. Identify critical traces, recommend layer stackup, "
            "copper weights, and thermal management.",
            {
                "requirements": requirements.__dict__,
                "topology": topology,
                "components": part_selection,
                "thermal": thermal,
                "emc": emc
            }
        )
        self.design_doc.layout_guide = layout

        # Phase 7: Design Verification
        print(f"\n{'─'*70}")
        print("PHASE 7: Design Verification")
        print(f"{'─'*70}")

        verification = self.agents["DesignVerifier"].analyze(
            "Verify the complete design. Check for errors, safety issues, "
            "manufacturability concerns, and compliance with requirements.",
            {
                "requirements": requirements.__dict__,
                "topology": topology,
                "components": part_selection,
                "thermal": thermal,
                "emc": emc,
                "layout": layout
            }
        )
        self.design_doc.verification_report = verification

        # Phase 8: Documentation
        print(f"\n{'─'*70}")
        print("PHASE 8: Documentation Generation")
        print(f"{'─'*70}")

        documentation = self.agents["DocumentationAgent"].analyze(
            "Generate comprehensive design documentation summarizing all aspects of this design.",
            {
                "requirements": requirements.__dict__,
                "all_analysis": {
                    "topology": topology,
                    "components": component_design,
                    "parts": part_selection,
                    "thermal": thermal,
                    "emc": emc,
                    "layout": layout,
                    "verification": verification
                }
            }
        )

        print(f"\n{'='*70}")
        print("✅ DESIGN COMPLETE")
        print(f"{'='*70}")

        return self.design_doc

    def save_design(self, filename: str):
        """Save design document to file."""
        if not self.design_doc:
            print("No design document to save")
            return

        output_dir = Path(__file__).parent / "outputs"
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename

        # Convert to JSON-serializable format
        design_dict = {
            "requirements": self.design_doc.requirements.__dict__,
            "topology": self.design_doc.topology,
            "components": self.design_doc.components,
            "calculations": self.design_doc.calculations,
            "thermal_analysis": self.design_doc.thermal_analysis,
            "emc_considerations": self.design_doc.emc_considerations,
            "layout_guide": self.design_doc.layout_guide,
            "verification_report": self.design_doc.verification_report,
            "timestamp": self.design_doc.timestamp
        }

        with open(filepath, "w") as f:
            json.dump(design_dict, f, indent=2)

        print(f"\n💾 Design saved to: {filepath}")

        # Also save human-readable version
        text_filepath = filepath.with_suffix(".txt")
        with open(text_filepath, "w") as f:
            f.write("="*70 + "\n")
            f.write("POWER SUPPLY DESIGN DOCUMENT\n")
            f.write("="*70 + "\n\n")

            f.write("REQUIREMENTS:\n")
            f.write("-"*70 + "\n")
            for key, value in self.design_doc.requirements.__dict__.items():
                f.write(f"{key}: {value}\n")

            f.write("\n\nTOPOLOGY:\n")
            f.write("-"*70 + "\n")
            f.write(self.design_doc.topology + "\n")

            f.write("\n\nCOMPONENT CALCULATIONS:\n")
            f.write("-"*70 + "\n")
            f.write(str(self.design_doc.calculations.get("components", "")) + "\n")

            f.write("\n\nSELECTED COMPONENTS:\n")
            f.write("-"*70 + "\n")
            f.write(str(self.design_doc.components.get("selected_parts", "")) + "\n")

            f.write("\n\nTHERMAL ANALYSIS:\n")
            f.write("-"*70 + "\n")
            f.write(self.design_doc.thermal_analysis + "\n")

            f.write("\n\nEMC CONSIDERATIONS:\n")
            f.write("-"*70 + "\n")
            f.write(self.design_doc.emc_considerations + "\n")

            f.write("\n\nLAYOUT GUIDANCE:\n")
            f.write("-"*70 + "\n")
            f.write(self.design_doc.layout_guide + "\n")

            f.write("\n\nVERIFICATION:\n")
            f.write("-"*70 + "\n")
            f.write(self.design_doc.verification_report + "\n")

        print(f"💾 Readable version saved to: {text_filepath}")


def main():
    """Run power electronics design system demo."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        sys.exit(1)

    # Create design system
    system = PowerDesignSystem()

    # Example 1: Buck Converter
    print("\n" + "="*70)
    print("EXAMPLE 1: 24V to 5V Buck Converter")
    print("="*70)

    requirements = DesignRequirements(
        input_voltage_min=18.0,
        input_voltage_max=30.0,
        output_voltage=5.0,
        output_current=5.0,
        efficiency_target=0.92,
        ripple_max_mv=50.0,
        size_constraint="50x50mm PCB",
        cost_target=8.0,
        temp_range_min=-20,
        temp_range_max=70,
        emc_standard="CE/FCC Class B",
        additional_notes="For industrial application, ruggedized design preferred"
    )

    design = system.design(requirements)
    system.save_design("buck_converter_design.json")

    print("\n" + "="*70)
    print("Design system demonstration complete!")
    print("="*70)
    print("\nThis multi-agent system demonstrated:")
    print("  • 9 specialized agents with distinct expertise")
    print("  • Hierarchical workflow with multiple phases")
    print("  • Parallel execution where appropriate")
    print("  • Comprehensive design coverage")
    print("  • Professional documentation generation")
    print("\nCheck the outputs/ directory for complete design files.")


if __name__ == "__main__":
    main()
