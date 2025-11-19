# AI Agents for Power Electronics Design

**Focus:** Building autonomous agents that reason, plan, and execute complex converter design tasks.

---

## Examples

### Example 1: Autonomous Component Selection Agent

An agent that autonomously selects all components for a converter design based on specifications.

```python
# src/agents/component_selector_agent.py
import anthropic
from typing import Dict, List, Any
import json
import os
from dotenv import load_dotenv

load_dotenv()


class ComponentSelectorAgent:
    """Autonomous agent for complete converter component selection.

    Uses ReAct pattern: Reason → Act → Observe → Repeat
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-sonnet-4-5-20250929"

        # Define available tools
        self.tools = [
            {
                "name": "search_mosfets",
                "description": "Search MOSFET database by specifications",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "vds_min": {"type": "number", "description": "Minimum Vds rating (V)"},
                        "id_min": {"type": "number", "description": "Minimum Id rating (A)"},
                        "rds_max": {"type": "number", "description": "Maximum Rds_on (mΩ)"},
                        "package": {"type": "string", "description": "Package type filter"}
                    },
                    "required": ["vds_min", "id_min"]
                }
            },
            {
                "name": "search_inductors",
                "description": "Search inductor database by specifications",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "inductance_min": {"type": "number", "description": "Min inductance (µH)"},
                        "inductance_max": {"type": "number", "description": "Max inductance (µH)"},
                        "isat_min": {"type": "number", "description": "Min saturation current (A)"},
                        "dcr_max": {"type": "number", "description": "Max DCR (mΩ)"}
                    },
                    "required": ["inductance_min", "isat_min"]
                }
            },
            {
                "name": "search_capacitors",
                "description": "Search capacitor database",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "capacitance_min": {"type": "number", "description": "Min capacitance (µF)"},
                        "voltage_min": {"type": "number", "description": "Min voltage rating (V)"},
                        "esr_max": {"type": "number", "description": "Max ESR (mΩ)"},
                        "type": {"type": "string", "enum": ["MLCC", "electrolytic", "polymer"]}
                    },
                    "required": ["capacitance_min", "voltage_min"]
                }
            },
            {
                "name": "calculate_losses",
                "description": "Calculate component losses at operating point",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "component_type": {"type": "string", "enum": ["mosfet", "inductor", "capacitor"]},
                        "part_number": {"type": "string"},
                        "operating_conditions": {"type": "object"}
                    },
                    "required": ["component_type", "part_number", "operating_conditions"]
                }
            },
            {
                "name": "check_thermal",
                "description": "Check thermal stress and calculate junction temperature",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "power_loss": {"type": "number", "description": "Power dissipation (W)"},
                        "rth_ja": {"type": "number", "description": "Thermal resistance (K/W)"},
                        "t_ambient": {"type": "number", "description": "Ambient temperature (°C)"}
                    },
                    "required": ["power_loss", "rth_ja", "t_ambient"]
                }
            },
            {
                "name": "finalize_selection",
                "description": "Finalize and save component selection",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "bom": {"type": "array", "items": {"type": "object"}},
                        "efficiency": {"type": "number"},
                        "notes": {"type": "string"}
                    },
                    "required": ["bom", "efficiency"]
                }
            }
        ]

        self.system_prompt = """You are an expert power electronics design agent.

Your task is to autonomously select all components for a DC-DC converter.

Process:
1. Analyze specifications and calculate requirements
2. Search for suitable MOSFETs (both HS and LS)
3. Search for suitable inductors
4. Search for input and output capacitors
5. Calculate losses for each component
6. Verify thermal performance
7. Finalize BOM with efficiency estimate

Decision criteria:
- Voltage margins: >20% for MOSFETs, >30% for capacitors
- Current margins: >30% for inductors, >50% for MOSFETs
- Optimize for efficiency (minimize Rds_on × Qg FOM)
- Consider cost when multiple options meet specs

Always explain your reasoning before each action."""

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return result."""

        # Simulated tool implementations
        if tool_name == "search_mosfets":
            return json.dumps({
                "results": [
                    {
                        "part": "BSC010N04LS",
                        "vds": 40, "id": 100,
                        "rds_on": 1.0, "qg": 15, "qgd": 3.5,
                        "rth_jc": 1.0, "package": "TDSON-8",
                        "price": 1.25, "fom": 15
                    },
                    {
                        "part": "IPD90N04S4L-02",
                        "vds": 40, "id": 120,
                        "rds_on": 0.9, "qg": 12, "qgd": 2.8,
                        "rth_jc": 0.9, "package": "TDSON-8",
                        "price": 1.65, "fom": 10.8
                    }
                ]
            })

        elif tool_name == "search_inductors":
            return json.dumps({
                "results": [
                    {
                        "part": "SER2915H-103",
                        "inductance": 10, "dcr": 2.5,
                        "isat": 30, "irms": 25,
                        "package": "13x13mm", "price": 2.80
                    },
                    {
                        "part": "XAL7070-103",
                        "inductance": 10, "dcr": 2.8,
                        "isat": 28, "irms": 23,
                        "package": "7x7mm", "price": 2.20
                    }
                ]
            })

        elif tool_name == "search_capacitors":
            return json.dumps({
                "results": [
                    {
                        "part": "GRM32ER71E226KE15",
                        "capacitance": 22, "voltage": 25,
                        "esr": 3, "ripple_current": 5,
                        "type": "MLCC", "price": 0.45
                    }
                ]
            })

        elif tool_name == "calculate_losses":
            # Simplified loss calculation
            return json.dumps({
                "conduction_loss": 0.4,
                "switching_loss": 0.3,
                "total_loss": 0.7
            })

        elif tool_name == "check_thermal":
            p = tool_input["power_loss"]
            rth = tool_input["rth_ja"]
            ta = tool_input["t_ambient"]
            tj = ta + p * rth
            return json.dumps({
                "t_junction": tj,
                "margin_to_max": 150 - tj,
                "status": "PASS" if tj < 125 else "FAIL"
            })

        elif tool_name == "finalize_selection":
            return json.dumps({
                "status": "complete",
                "bom_saved": True,
                "total_cost": sum(item.get("price", 0) * item.get("qty", 1)
                                  for item in tool_input["bom"])
            })

        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def run(self, specs: Dict) -> Dict:
        """Run the agent to select components.

        Args:
            specs: Converter specifications
                - v_in_min, v_in_max: Input voltage range
                - v_out: Output voltage
                - i_out: Output current
                - f_sw: Switching frequency
                - efficiency_target: Target efficiency
                - t_ambient: Ambient temperature

        Returns:
            Complete BOM with analysis
        """

        # Initial prompt with specifications
        user_message = f"""Select all components for this synchronous buck converter:

**Specifications:**
- Input voltage: {specs['v_in_min']}-{specs['v_in_max']}V
- Output voltage: {specs['v_out']}V
- Output current: {specs['i_out']}A
- Switching frequency: {specs['f_sw']/1e3:.0f}kHz
- Efficiency target: {specs.get('efficiency_target', 0.95):.1%}
- Ambient temperature: {specs.get('t_ambient', 85)}°C

Select:
1. High-side MOSFET
2. Low-side MOSFET
3. Output inductor
4. Output capacitors
5. Input capacitors

Optimize for efficiency while meeting all stress margins."""

        messages = [{"role": "user", "content": user_message}]

        # Agent loop
        max_iterations = 15
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Get model response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                tools=self.tools,
                messages=messages
            )

            # Check if done
            if response.stop_reason == "end_turn":
                # Extract final response
                final_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_text += block.text

                return {
                    "status": "complete",
                    "iterations": iteration,
                    "result": final_text
                }

            # Process tool calls
            if response.stop_reason == "tool_use":
                # Add assistant message
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Execute tools and collect results
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"  [{iteration}] Calling: {block.name}")

                        result = self.execute_tool(block.name, block.input)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })

                # Add tool results
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

        return {
            "status": "max_iterations",
            "iterations": iteration
        }


# Usage
def main():
    agent = ComponentSelectorAgent()

    specs = {
        "v_in_min": 36,
        "v_in_max": 60,
        "v_out": 12,
        "i_out": 20,
        "f_sw": 200e3,
        "efficiency_target": 0.95,
        "t_ambient": 85
    }

    print("Starting component selection agent...")
    print(f"Specs: {specs['v_in_min']}-{specs['v_in_max']}V → {specs['v_out']}V @ {specs['i_out']}A")
    print("-" * 50)

    result = agent.run(specs)

    print("\n" + "=" * 50)
    print(f"Agent completed in {result['iterations']} iterations")
    print("=" * 50)
    print(result.get("result", "No result"))


if __name__ == "__main__":
    main()
```

---

### Example 2: Multi-Agent Design Review System

Multiple specialized agents collaborate to review a converter design.

```python
# src/agents/design_review_agents.py
import anthropic
from typing import Dict, List
import json
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


class SpecialistAgent:
    """Base class for specialist review agents."""

    def __init__(self, name: str, expertise: str, system_prompt: str):
        self.name = name
        self.expertise = expertise
        self.system_prompt = system_prompt
        self.client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def review(self, design: Dict) -> Dict:
        """Review design from specialist perspective."""

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{
                "role": "user",
                "content": f"Review this converter design:\n\n{json.dumps(design, indent=2)}"
            }]
        )

        return {
            "agent": self.name,
            "expertise": self.expertise,
            "review": response.content[0].text
        }


class ThermalAgent(SpecialistAgent):
    """Agent specialized in thermal analysis."""

    def __init__(self):
        super().__init__(
            name="Thermal Specialist",
            expertise="Thermal management and reliability",
            system_prompt="""You are a thermal management specialist for power electronics.

Review designs for:
1. Junction temperature calculations (Tj = Ta + P × Rth)
2. Thermal margins (want Tj < 125°C for reliability)
3. Derating at temperature (Rds_on increases ~0.4%/°C)
4. Thermal runaway risk
5. Cooling requirements (heatsink, airflow)
6. Hot spot identification
7. MTBF impact of thermal stress

Provide specific temperature calculations and recommendations.
Flag any thermal risks with severity: LOW / MEDIUM / HIGH / CRITICAL"""
        )


class EMCAgent(SpecialistAgent):
    """Agent specialized in EMI/EMC analysis."""

    def __init__(self):
        super().__init__(
            name="EMC Specialist",
            expertise="EMI/EMC and noise",
            system_prompt="""You are an EMC specialist for switch-mode power supplies.

Review designs for:
1. Switching noise sources (dV/dt, di/dt)
2. High-frequency loop areas (minimize!)
3. Input filter requirements
4. Common-mode noise paths
5. Snubber requirements
6. Gate drive noise immunity
7. Layout recommendations for EMI

Estimate noise levels and recommend mitigation.
Flag issues with severity: LOW / MEDIUM / HIGH / CRITICAL"""
        )


class ReliabilityAgent(SpecialistAgent):
    """Agent specialized in reliability analysis."""

    def __init__(self):
        super().__init__(
            name="Reliability Specialist",
            expertise="Component stress and lifetime",
            system_prompt="""You are a reliability engineer for power electronics.

Review designs for:
1. Component stress ratios (voltage, current, power)
2. Derating compliance (want <80% of ratings)
3. Electrolytic capacitor lifetime (temperature, ripple)
4. MOSFET SOA compliance
5. Inductor saturation margin
6. Solder joint reliability (thermal cycling)
7. MTBF estimation

Calculate stress ratios and lifetime estimates.
Flag issues with severity: LOW / MEDIUM / HIGH / CRITICAL"""
        )


class EfficiencyAgent(SpecialistAgent):
    """Agent specialized in efficiency optimization."""

    def __init__(self):
        super().__init__(
            name="Efficiency Specialist",
            expertise="Loss analysis and optimization",
            system_prompt="""You are an efficiency optimization specialist.

Review designs for:
1. Conduction loss breakdown (MOSFETs, inductor, caps)
2. Switching loss analysis (hard/soft switching)
3. Gate drive losses
4. Dead time optimization
5. Light load efficiency (PFM, burst mode)
6. Loss distribution (identify dominant losses)
7. Optimization recommendations

Calculate all losses and identify improvement opportunities.
Provide specific suggestions with expected efficiency gains."""
        )


class DesignReviewOrchestrator:
    """Orchestrates multi-agent design review."""

    def __init__(self):
        self.agents = [
            ThermalAgent(),
            EMCAgent(),
            ReliabilityAgent(),
            EfficiencyAgent()
        ]
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def run_parallel_review(self, design: Dict) -> List[Dict]:
        """Run all specialist reviews in parallel."""

        tasks = [agent.review(design) for agent in self.agents]
        reviews = await asyncio.gather(*tasks)

        return reviews

    def synthesize_reviews(self, reviews: List[Dict], design: Dict) -> str:
        """Synthesize specialist reviews into final report."""

        reviews_text = "\n\n".join([
            f"### {r['agent']} ({r['expertise']})\n{r['review']}"
            for r in reviews
        ])

        synthesis_prompt = f"""You are the lead design reviewer synthesizing specialist reviews.

**Original Design:**
{json.dumps(design, indent=2)}

**Specialist Reviews:**
{reviews_text}

Synthesize into a final design review report:

1. **Executive Summary** - Overall assessment (APPROVED / CONDITIONAL / REJECTED)

2. **Critical Issues** - Must fix before production
   - List all CRITICAL and HIGH severity issues
   - Specific remediation for each

3. **Recommendations** - Should fix for optimal performance
   - List MEDIUM severity issues
   - Improvement suggestions

4. **Design Strengths** - What's done well

5. **Action Items** - Prioritized list with owners

Be specific and actionable. Include calculations where relevant."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )

        return response.content[0].text

    async def review(self, design: Dict) -> str:
        """Complete design review with all specialists."""

        print("Starting multi-agent design review...")
        print(f"Agents: {[a.name for a in self.agents]}")
        print("-" * 50)

        # Run parallel reviews
        print("Running specialist reviews in parallel...")
        reviews = await self.run_parallel_review(design)

        for review in reviews:
            print(f"  ✓ {review['agent']} complete")

        # Synthesize
        print("Synthesizing final report...")
        final_report = self.synthesize_reviews(reviews, design)

        return final_report


# Usage
async def main():
    orchestrator = DesignReviewOrchestrator()

    # Design to review
    design = {
        "topology": "synchronous_buck",
        "specs": {
            "v_in": "36-60V",
            "v_out": "12V",
            "i_out": "20A",
            "f_sw": "200kHz"
        },
        "components": {
            "hs_mosfet": {
                "part": "BSC010N04LS",
                "vds_max": 40,
                "rds_on": 1.0,
                "qg": 15
            },
            "ls_mosfet": {
                "part": "BSC010N04LS",
                "vds_max": 40,
                "rds_on": 1.0,
                "qg": 15
            },
            "inductor": {
                "part": "SER2915H-103",
                "inductance_uh": 10,
                "dcr_mohm": 2.5,
                "isat_a": 30
            },
            "output_cap": {
                "part": "GRM32ER71E226KE15",
                "capacitance_uf": 22,
                "voltage_v": 25,
                "qty": 4
            }
        },
        "calculated": {
            "duty_cycle": 0.25,
            "inductor_ripple_a": 4.5,
            "efficiency": 0.96,
            "hs_loss_w": 0.7,
            "ls_loss_w": 0.9,
            "inductor_loss_w": 1.0
        }
    }

    report = await orchestrator.review(design)

    print("\n" + "=" * 60)
    print("DESIGN REVIEW REPORT")
    print("=" * 60)
    print(report)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Exercises

### Exercise 1: Design Optimization Agent (60 min)

**Objective:** Build an agent that iteratively optimizes a converter design for a target metric.

**Requirements:**

1. Create `OptimizationAgent` that:
   - Takes initial design and optimization target (efficiency, cost, size)
   - Iteratively adjusts parameters
   - Evaluates each iteration
   - Converges on optimal solution

2. Optimization strategies:
   - Switching frequency sweep (100kHz - 500kHz)
   - MOSFET selection (trade Rds_on vs Qg)
   - Inductor selection (trade DCR vs size)
   - Dead time optimization

3. Agent should:
   - Track all iterations with metrics
   - Explain trade-offs at each step
   - Stop when improvement < threshold
   - Return Pareto-optimal solutions for multi-objective

**Starter Code:**

```python
class OptimizationAgent:
    """Agent that optimizes converter design iteratively."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.history = []  # Track iterations

        self.tools = [
            # Calculate efficiency at operating point
            {"name": "evaluate_design", ...},
            # Modify design parameter
            {"name": "modify_parameter", ...},
            # Check if converged
            {"name": "check_convergence", ...},
            # Get Pareto frontier
            {"name": "get_pareto_front", ...}
        ]

    def optimize(
        self,
        initial_design: Dict,
        target: str,  # "efficiency", "cost", "size"
        constraints: Dict,
        max_iterations: int = 20
    ) -> Dict:
        """Run optimization loop."""

        # TODO: Implement agent loop
        # 1. Evaluate current design
        # 2. Decide which parameter to adjust
        # 3. Apply modification
        # 4. Evaluate new design
        # 5. Accept/reject based on improvement
        # 6. Check convergence
        # 7. Repeat or return best
        pass
```

**Test Scenarios:**
1. Optimize for efficiency (target: 97%)
2. Optimize for cost (target: <$5 BOM)
3. Multi-objective: efficiency AND cost

**Deliverables:**
- Complete `OptimizationAgent` implementation
- Optimization trace showing iterations
- Final Pareto frontier for multi-objective case
- Analysis of convergence behavior

---

### Exercise 2: Troubleshooting Agent (75 min)

**Objective:** Build an agent that diagnoses converter problems from symptoms.

**Requirements:**

1. Create `TroubleshootingAgent` that:
   - Takes symptom description as input
   - Asks clarifying questions if needed
   - Forms hypotheses ranked by probability
   - Suggests diagnostic tests
   - Narrows down root cause

2. Knowledge base of common issues:
   - Oscillation (subharmonic, control loop, EMI)
   - Thermal (runaway, hot spots, derating)
   - Efficiency (high losses, unexpected heating)
   - Output issues (ripple, noise, regulation)
   - Startup problems (hiccup, inrush, sequencing)

3. Diagnostic tools available:
   - `measure_waveform` - Oscilloscope measurement
   - `measure_temperature` - Thermal measurement
   - `measure_spectrum` - FFT/spectrum analyzer
   - `inject_perturbation` - Bode plot / step response

4. Agent should:
   - Start with most likely hypotheses
   - Choose tests that maximize information gain
   - Update probabilities based on results
   - Provide root cause with confidence level

**Starter Code:**

```python
class TroubleshootingAgent:
    """Agent that diagnoses converter problems."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        self.hypotheses = {}  # hypothesis -> probability

        self.tools = [
            {
                "name": "measure_waveform",
                "description": "Capture oscilloscope waveform",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "signal": {"type": "string", "enum": [
                            "vout", "v_switch", "i_inductor", "vgs_hs", "vgs_ls"
                        ]},
                        "timebase": {"type": "string"},
                        "trigger": {"type": "string"}
                    }
                }
            },
            {
                "name": "measure_temperature",
                "description": "Measure component temperature",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "component": {"type": "string"},
                        "method": {"type": "string", "enum": ["thermocouple", "ir_camera"]}
                    }
                }
            },
            {
                "name": "measure_spectrum",
                "description": "FFT or spectrum analyzer measurement",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "signal": {"type": "string"},
                        "freq_range": {"type": "string"}
                    }
                }
            },
            {
                "name": "ask_clarification",
                "description": "Ask user for more information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"}
                    }
                }
            }
        ]

        self.system_prompt = """You are an expert power electronics troubleshooter.

Given symptoms, systematically diagnose the root cause:

1. Form initial hypotheses with probabilities
2. Select diagnostic test with highest information gain
3. Update probabilities based on results
4. Repeat until confident (>80%) or tests exhausted

Common issues to consider:
- Control loop instability (insufficient phase margin)
- Subharmonic oscillation (slope compensation needed)
- EMI coupling (layout, grounding)
- Thermal runaway (positive feedback)
- Component overstress (voltage spikes, current limits)
- Output noise (switching ripple, common-mode)

Always explain your reasoning and probability updates."""

    def diagnose(self, symptoms: str) -> Dict:
        """Diagnose problem from symptoms."""
        # TODO: Implement diagnostic loop
        pass


# Example test case
symptoms = """
Buck converter output has 500mV ripple instead of expected 50mV.
Ripple frequency is at switching frequency (200kHz).
Output voltage average is correct at 12V.
No audible noise.
Thermal performance normal.
"""
```

**Test Scenarios:**
1. High output ripple (capacitor ESR vs capacitance)
2. Oscillation at startup (control loop stability)
3. Random shutdowns (thermal vs overcurrent)
4. Audible noise (ceramic cap piezoelectric vs magnetostriction)

**Deliverables:**
- Complete `TroubleshootingAgent` implementation
- Diagnostic sessions for all 4 scenarios
- Probability update traces
- Correct root cause identification for each

---

## Summary

| Agent Type | Use Case | Key Features |
|------------|----------|--------------|
| **Component Selector** | Autonomous BOM creation | Tool-based, iterative selection |
| **Multi-Agent Review** | Parallel specialist analysis | Async execution, synthesis |
| **Optimization** | Parameter tuning | Iterative improvement, Pareto |
| **Troubleshooting** | Problem diagnosis | Hypothesis testing, Bayesian |

**Best Practices:**
- Clear tool definitions with examples
- Limit iterations to prevent runaway
- Log all reasoning for debugging
- Use async for parallel operations
- Validate agent outputs before use
