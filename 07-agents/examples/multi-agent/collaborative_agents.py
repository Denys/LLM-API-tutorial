#!/usr/bin/env python3
"""
Collaborative Multi-Agent System

Demonstrates multiple specialized agents working together on complex tasks.
Each agent has specific expertise and they collaborate to solve problems
that require multiple domains of knowledge.

Example: Design a complete power supply system with:
- Circuit Designer: Topology and component selection
- Thermal Analyst: Heat dissipation and cooling
- EMC Engineer: EMI/EMC considerations
- Cost Optimizer: BOM optimization and sourcing
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


@dataclass
class DesignArtifact:
    """Design artifact passed between agents."""
    component: str
    details: Dict[str, Any]
    agent: str
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            "component": self.component,
            "details": self.details,
            "agent": self.agent,
            "timestamp": self.timestamp
        }


class CollaborativeAgent:
    """Agent that contributes to collaborative design."""

    def __init__(self, name: str, specialty: str, system_prompt: str,
                 model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize collaborative agent.

        Args:
            name: Agent name
            specialty: Area of expertise
            system_prompt: Specialized system prompt
            model: Claude model
        """
        self.name = name
        self.specialty = specialty
        self.system_prompt = system_prompt
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.contributions: List[DesignArtifact] = []

    def contribute(self, task: str, context: Optional[str] = None,
                   previous_work: Optional[List[DesignArtifact]] = None) -> str:
        """
        Contribute to the collaborative design.

        Args:
            task: Specific task for this agent
            context: Overall project context
            previous_work: Work done by other agents

        Returns:
            Agent's contribution
        """
        print(f"\n{'─'*70}")
        print(f"🔧 {self.name} ({self.specialty})")
        print(f"{'─'*70}")

        # Build prompt with context
        prompt_parts = [f"Task: {task}"]

        if context:
            prompt_parts.append(f"\nProject Context:\n{context}")

        if previous_work:
            prompt_parts.append("\n Previous Team Contributions:")
            for work in previous_work:
                prompt_parts.append(f"\n{work.agent} ({work.component}):")
                prompt_parts.append(f"{json.dumps(work.details, indent=2)}")

        prompt_parts.append(f"\nProvide your expert analysis and recommendations as {self.specialty}.")
        prompt_parts.append("Be specific with values, part numbers, and calculations where relevant.")

        prompt = "\n".join(prompt_parts)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            contribution = response.content[0].text
            print(f"\n{contribution}\n")

            return contribution

        except Exception as e:
            error_msg = f"Error: {e}"
            print(f"❌ {error_msg}")
            return error_msg


class DesignTeam:
    """Coordinated team of collaborative agents."""

    def __init__(self):
        """Initialize the design team."""
        self.agents: Dict[str, CollaborativeAgent] = {}
        self.design_artifacts: List[DesignArtifact] = []
        self.conversation_log: List[Dict] = []

    def add_agent(self, agent: CollaborativeAgent):
        """Add agent to the team."""
        self.agents[agent.name] = agent
        print(f"  ✅ Added {agent.name} - {agent.specialty}")

    def collaborate(self, project: str, requirements: str) -> Dict[str, Any]:
        """
        Run collaborative design process.

        Args:
            project: Project description
            requirements: Project requirements

        Returns:
            Final design with all contributions
        """
        print(f"\n{'='*70}")
        print(f"🎯 Project: {project}")
        print(f"{'='*70}")
        print(f"\nRequirements:\n{requirements}\n")

        context = f"Project: {project}\nRequirements: {requirements}"
        results = {}

        # Each agent contributes in sequence, building on previous work
        for agent_name, agent in self.agents.items():
            task = f"Contribute to {project} based on your expertise in {agent.specialty}"

            contribution = agent.contribute(
                task=task,
                context=context,
                previous_work=self.design_artifacts
            )

            results[agent_name] = contribution

            # Store in conversation log
            self.conversation_log.append({
                "agent": agent_name,
                "specialty": agent.specialty,
                "contribution": contribution
            })

        return results

    def generate_report(self) -> str:
        """Generate final design report."""
        report = []
        report.append("="*70)
        report.append("COLLABORATIVE DESIGN REPORT")
        report.append("="*70)
        report.append("")

        for entry in self.conversation_log:
            report.append(f"\n{entry['agent']} - {entry['specialty']}")
            report.append("─" * 70)
            report.append(entry['contribution'])
            report.append("")

        return "\n".join(report)


def demo_power_supply_design():
    """Demonstrate collaborative design of a power supply."""

    print("\n" + "="*70)
    print("DEMO: Collaborative Power Supply Design")
    print("="*70)

    # Create specialized agents
    team = DesignTeam()

    # 1. Circuit Designer
    circuit_agent = CollaborativeAgent(
        name="CircuitDesigner",
        specialty="Circuit Topology & Component Selection",
        system_prompt="""You are an expert circuit designer specializing in power electronics.
Your focus is on selecting the right topology, determining component values, and
choosing specific parts. Provide detailed calculations and part numbers."""
    )
    team.add_agent(circuit_agent)

    # 2. Thermal Analyst
    thermal_agent = CollaborativeAgent(
        name="ThermalAnalyst",
        specialty="Thermal Management & Heat Dissipation",
        system_prompt="""You are a thermal analysis expert. Calculate power dissipation,
junction temperatures, and recommend cooling solutions. Consider worst-case conditions
and derating. Provide thermal resistance calculations."""
    )
    team.add_agent(thermal_agent)

    # 3. EMC Engineer
    emc_agent = CollaborativeAgent(
        name="EMCEngineer",
        specialty="EMI/EMC & Noise Reduction",
        system_prompt="""You are an EMC expert specializing in switching power supplies.
Identify EMI sources, recommend filtering, shielding, and layout techniques.
Consider both conducted and radiated emissions."""
    )
    team.add_agent(emc_agent)

    # 4. Cost Optimizer
    cost_agent = CollaborativeAgent(
        name="CostOptimizer",
        specialty="BOM Optimization & Sourcing",
        system_prompt="""You are a cost optimization specialist. Review the design and
suggest cost-effective alternatives while maintaining performance. Consider
component availability, second sources, and volume pricing."""
    )
    team.add_agent(cost_agent)

    # Run collaborative design
    results = team.collaborate(
        project="24V to 5V, 5A Buck Converter",
        requirements="""
- Input: 18-30V DC
- Output: 5V, 5A (25W)
- Efficiency: >90% at full load
- Ripple: <50mV pk-pk
- Size: Fit on 50x50mm PCB
- Cost target: <$5 BOM
- Operating temp: -20°C to +70°C
- EMC: Must pass CE/FCC Class B
        """
    )

    # Generate and save report
    report = team.generate_report()

    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    report_file = output_dir / "collaborative_design_report.txt"

    with open(report_file, "w") as f:
        f.write(report)

    print(f"\n{'='*70}")
    print(f"✅ Collaborative Design Complete!")
    print(f"{'='*70}")
    print(f"\nFull report saved to: {report_file}")
    print(f"\nTeam Contributions:")
    for agent_name in results.keys():
        print(f"  ✓ {agent_name}")


def demo_simple_collaboration():
    """Demonstrate simple two-agent collaboration."""

    print("\n" + "="*70)
    print("DEMO: Simple Two-Agent Collaboration")
    print("="*70)

    team = DesignTeam()

    # Designer proposes solution
    designer = CollaborativeAgent(
        name="Designer",
        specialty="Initial Design",
        system_prompt="You are a design engineer. Propose practical solutions with specific component values."
    )
    team.add_agent(designer)

    # Reviewer checks and improves
    reviewer = CollaborativeAgent(
        name="Reviewer",
        specialty="Design Review & Verification",
        system_prompt="You are a design reviewer. Check for issues, verify calculations, and suggest improvements."
    )
    team.add_agent(reviewer)

    # Collaborative task
    team.collaborate(
        project="LED Current Limiting Resistor",
        requirements="""
- Supply voltage: 12V
- LED: Red, Vf=2.1V, If=20mA
- Calculate resistor value and power rating
        """
    )

    print(f"\n{'='*70}")
    print("Simple collaboration complete!")
    print(f"{'='*70}")


def main():
    """Run collaborative agent demonstrations."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        sys.exit(1)

    print("\n" + "="*70)
    print("Collaborative Multi-Agent System Demo")
    print("="*70)

    # Demo 1: Simple collaboration
    demo_simple_collaboration()

    input("\nPress Enter to continue to full power supply design...")

    # Demo 2: Complex collaborative design
    demo_power_supply_design()

    print("\n" + "="*70)
    print("All demos completed!")
    print("="*70)
    print("\nKey Collaboration Features Demonstrated:")
    print("  • Multiple specialized agents with distinct expertise")
    print("  • Sequential contribution building on previous work")
    print("  • Context sharing between agents")
    print("  • Comprehensive design coverage from multiple perspectives")
    print("  • Design report generation")


if __name__ == "__main__":
    main()
