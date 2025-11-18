# Project 4: Advanced Power Electronics Design Assistant

Build a comprehensive AI-powered design assistant for power electronics engineers.

## 🎯 Project Overview

Create a production-ready system that helps power electronics engineers design, validate, and optimize switch-mode power supplies and power converters. This project integrates calculations, component selection, thermal analysis, and multi-agent design review.

**Difficulty:** 🟡 Intermediate-Advanced

**Time:** 4-6 hours

**Modules Used:** 1, 2, 3, 4, 7, 8

## 📋 Requirements

### Core Features (Must Have)

1. **Multi-Topology Support**
   - Buck converter
   - Boost converter
   - Buck-Boost converter
   - Flyback converter
   - LLC resonant converter

2. **Component Design**
   - Inductor calculation with core selection
   - Capacitor selection (input, output, bootstrap)
   - MOSFET selection with thermal analysis
   - Controller IC recommendation
   - Snubber circuit design

3. **Real-Time Component Selection**
   - Integration with Digi-Key/Mouser APIs
   - Real-time pricing and availability
   - Alternative component suggestions
   - Second source recommendations

4. **Thermal Analysis**
   - Power dissipation calculations
   - Junction temperature estimation
   - Heatsink requirements
   - Thermal derating

5. **Multi-Agent Design Review**
   - Design validation agent
   - Thermal review agent
   - EMC compliance agent
   - Cost optimization agent
   - Documentation agent

6. **Output Generation**
   - Complete BOM with pricing
   - Design calculations document
   - Thermal analysis report
   - LTspice schematic (SPICE netlist)
   - Design review summary

### Advanced Features (Nice to Have)

7. **PCB Layout Validation**
   - Critical trace analysis
   - Ground plane recommendations
   - Component placement guidelines
   - Thermal relief suggestions

8. **Simulation Integration**
   - Generate LTspice netlists
   - Run automated simulations
   - Parse simulation results
   - Optimize based on simulation

9. **Standards Compliance**
   - Safety standards check (IEC, UL)
   - EMC compliance (CE, FCC)
   - Efficiency standards (80 PLUS, Energy Star)

10. **Interactive Design Wizard**
    - Step-by-step design process
    - Real-time validation
    - Design trade-off visualization
    - Cost vs. performance optimization

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Web Interface                        │
│              (FastAPI + WebSocket)                      │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴──────────┬──────────────┐
         │                      │              │
┌────────▼────────┐  ┌─────────▼──────┐  ┌───▼────────┐
│  Design Agent   │  │ Component DB   │  │  RAG KB    │
│  (Orchestrator) │  │  (Digi-Key)    │  │ (Datasheets)│
└────────┬────────┘  └────────────────┘  └────────────┘
         │
    ┌────┴─────┬──────────┬──────────┬──────────┐
    │          │          │          │          │
┌───▼────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼─────┐ ┌──▼──────┐
│Topology│ │Thermal │ │  EMC   │ │  Cost  │ │   Doc   │
│Selector│ │Analyzer│ │Reviewer│ │Optimizer│ │Generator│
└────────┘ └────────┘ └────────┘ └────────┘ └─────────┘
```

### Data Flow

```
User Input (Specs)
     │
     ▼
Design Agent (Orchestrator)
     │
     ├─► Topology Selection
     │        │
     │        ▼
     ├─► Component Calculation
     │        │
     │        ▼
     ├─► Component Selection API
     │        │
     │        ▼
     ├─► Multi-Agent Review
     │        │
     │        ├─► Thermal Analysis
     │        ├─► EMC Check
     │        ├─► Cost Review
     │        └─► Validation
     │                 │
     ▼                 ▼
  BOM + Docs    Review Reports
```

## 💻 Implementation Guide

### Phase 1: Core Calculation Engine (Day 1)

**Objective:** Implement accurate calculations for each topology

**Tasks:**
1. Create calculation modules for each topology
2. Implement inductor design with core selection
3. Add capacitor sizing algorithms
4. MOSFET selection with RDS(on), Qg calculations
5. Unit tests for all calculations

**Key Files:**
- `calculators/buck.py`
- `calculators/boost.py`
- `calculators/flyback.py`
- `calculators/magnetics.py`
- `tests/test_calculators.py`

**Hints:**
- Use dataclasses for component specifications
- Validate all inputs with pydantic
- Include safety margins in calculations
- Reference IEEE and manufacturer app notes

### Phase 2: Component Database Integration (Day 2)

**Objective:** Real-time component selection with pricing

**Tasks:**
1. Set up Digi-Key API integration
2. Implement component search with filters
3. Add pricing and availability checks
4. Create alternative suggestions
5. Cache component data with Redis

**Key Files:**
- `components/digikey_client.py`
- `components/component_selector.py`
- `components/cache.py`

**Hints:**
- Use Digi-Key's OAuth2 API
- Cache aggressively to reduce API calls
- Handle rate limiting gracefully
- Provide fallback for offline mode

### Phase 3: Multi-Agent System (Day 3)

**Objective:** Specialized agents for design review

**Tasks:**
1. Implement orchestrator agent
2. Create thermal analysis agent
3. Add EMC compliance agent
4. Build cost optimization agent
5. Implement documentation generator

**Key Files:**
- `agents/orchestrator.py`
- `agents/thermal_agent.py`
- `agents/emc_agent.py`
- `agents/cost_agent.py`
- `agents/doc_agent.py`

**Hints:**
- Use Celery for parallel agent execution
- Implement agent communication protocol
- Store agent state in Redis
- Add timeout handling

### Phase 4: RAG Knowledge Base (Day 4)

**Objective:** Datasheet search and reference

**Tasks:**
1. Ingest component datasheets (PDFs)
2. Create vector embeddings
3. Implement semantic search
4. Add citation tracking
5. Build query rewriting for better retrieval

**Key Files:**
- `rag/ingest.py`
- `rag/retrieval.py`
- `rag/embeddings.py`
- `data/datasheets/` (sample PDFs)

**Hints:**
- Use PyPDF2 or pdfplumber for extraction
- Chunk with overlap for better context
- Store in ChromaDB or FAISS
- Add metadata filters

### Phase 5: API & Interface (Day 5)

**Objective:** Production-ready API and web interface

**Tasks:**
1. Build FastAPI endpoints
2. Add WebSocket for real-time updates
3. Implement request validation
4. Add rate limiting
5. Create OpenAPI documentation

**Key Files:**
- `api/main.py`
- `api/models.py`
- `api/routes/`
- `frontend/` (optional)

**Hints:**
- Use pydantic for request/response models
- Implement streaming for long operations
- Add comprehensive error handling
- Include health checks

### Phase 6: Testing & Deployment (Day 6)

**Objective:** Production-ready deployment

**Tasks:**
1. Unit tests for all modules
2. Integration tests for workflows
3. Docker containerization
4. Monitoring with Prometheus
5. Documentation and examples

**Key Files:**
- `tests/`
- `Dockerfile`
- `docker-compose.yml`
- `docs/`

## 📐 Technical Specifications

### Design Specifications Format

```python
from pydantic import BaseModel, Field

class DesignSpecs(BaseModel):
    """Power supply design specifications."""

    # Input/Output
    input_voltage_min: float = Field(..., gt=0, description="Minimum input voltage (V)")
    input_voltage_max: float = Field(..., gt=0, description="Maximum input voltage (V)")
    output_voltage: float = Field(..., gt=0, description="Output voltage (V)")
    output_current: float = Field(..., gt=0, description="Output current (A)")

    # Performance
    efficiency_target: float = Field(default=0.90, ge=0.5, le=1.0)
    ripple_voltage_max: float = Field(default=0.050, gt=0, description="Max output ripple (V)")
    transient_response: float = Field(default=0.001, gt=0, description="Load step response (s)")

    # Constraints
    switching_frequency: Optional[float] = Field(default=None, gt=0, description="Switching freq (Hz)")
    size_constraint: Optional[str] = Field(default=None, description="Size limit (e.g., '50x50mm')")
    cost_target: Optional[float] = Field(default=None, gt=0, description="Max BOM cost ($)")

    # Environment
    temp_min: int = Field(default=-20, description="Min operating temp (°C)")
    temp_max: int = Field(default=70, description="Max operating temp (°C)")

    # Standards
    safety_standard: str = Field(default="IEC 60950", description="Safety standard")
    emc_standard: str = Field(default="CE/FCC Class B", description="EMC standard")
```

### Component Selection Criteria

```python
class ComponentCriteria(BaseModel):
    """Criteria for component selection."""

    # Electrical ratings (with margins)
    voltage_rating: float  # Must be ≥ max voltage × 1.5
    current_rating: float  # Must be ≥ max current × 1.25
    power_rating: float    # Must be ≥ max power × 2.0

    # Performance
    esr_max: Optional[float] = None  # For capacitors
    rds_on_max: Optional[float] = None  # For MOSFETs
    inductance_tolerance: float = 0.20  # ±20%

    # Physical
    package_type: Optional[str] = None
    mounting: str = "SMD"  # or "Through-hole"

    # Business
    max_cost: Optional[float] = None
    min_availability: int = 100  # Minimum stock
    lead_time_max: int = 30  # Days
    preferred_manufacturers: List[str] = []
```

### Agent Communication Protocol

```python
from enum import Enum
from dataclasses import dataclass

class AgentTaskType(Enum):
    DESIGN = "design"
    REVIEW = "review"
    OPTIMIZE = "optimize"
    VALIDATE = "validate"

@dataclass
class AgentTask:
    """Task for an agent."""
    task_id: str
    task_type: AgentTaskType
    input_data: dict
    priority: int = 0
    timeout: int = 300

@dataclass
class AgentResult:
    """Result from an agent."""
    task_id: str
    agent_name: str
    success: bool
    result: dict
    warnings: List[str] = None
    errors: List[str] = None
    execution_time: float = 0.0
```

## 🧮 Example Calculations

### Buck Converter Design

```python
def design_buck_converter(specs: DesignSpecs) -> BuckDesign:
    """Design buck converter."""

    # Calculate duty cycle
    duty_cycle = specs.output_voltage / specs.input_voltage_max

    # Select switching frequency (if not specified)
    if not specs.switching_frequency:
        # Choose based on size/efficiency trade-off
        fsw = 100e3 if specs.size_constraint else 50e3
    else:
        fsw = specs.switching_frequency

    # Calculate inductor value
    # ΔI_L = 20-30% of I_out for CCM
    delta_i_l = 0.3 * specs.output_current

    L = (specs.output_voltage * (1 - duty_cycle)) / (delta_i_l * fsw)

    # Select inductor with margin
    L_selected = next_standard_value(L * 1.1)

    # Calculate output capacitor
    # Based on ripple voltage requirement
    esr_max = specs.ripple_voltage_max / delta_i_l
    C_out = delta_i_l / (8 * fsw * specs.ripple_voltage_max)

    # MOSFET selection
    V_ds_min = specs.input_voltage_max * 1.5  # 50% margin
    I_d_min = specs.output_current * 1.25  # 25% margin

    # Calculate losses
    mosfet_losses = calculate_mosfet_losses(
        duty_cycle=duty_cycle,
        rds_on=0.010,  # Estimated, will be refined
        i_rms=specs.output_current,
        fsw=fsw
    )

    return BuckDesign(
        topology="Buck",
        duty_cycle=duty_cycle,
        switching_frequency=fsw,
        inductor=InductorSpec(
            inductance=L_selected,
            current_rating=specs.output_current * 1.3,
            saturation_current=specs.output_current * 1.5,
            dcr_max=0.010  # 1% efficiency loss budget
        ),
        output_capacitor=CapacitorSpec(
            capacitance=C_out,
            voltage_rating=specs.output_voltage * 2,
            esr_max=esr_max,
            ripple_current=delta_i_l
        ),
        mosfet=MOSFETSpec(
            v_ds_min=V_ds_min,
            i_d_min=I_d_min,
            rds_on_max=0.015,
            q_g_max=50e-9
        )
    )
```

### Thermal Analysis

```python
def analyze_thermal(design: BuckDesign, specs: DesignSpecs) -> ThermalAnalysis:
    """Perform thermal analysis."""

    # Power dissipation sources
    P_mosfet_cond = design.mosfet.rds_on * (specs.output_current ** 2) * design.duty_cycle
    P_mosfet_sw = 0.5 * specs.input_voltage_max * specs.output_current * \
                   (design.mosfet.t_rise + design.mosfet.t_fall) * design.switching_frequency

    P_inductor = design.inductor.dcr * (specs.output_current ** 2)

    P_diode = 0  # Synchronous design (replace with MOSFET)

    P_total = P_mosfet_cond + P_mosfet_sw + P_inductor

    # Junction temperature calculation
    # T_j = T_a + P × (θ_jc + θ_cs + θ_sa)
    theta_jc = 1.0  # Junction-to-case (from datasheet)
    theta_cs = 0.5  # Case-to-sink (with thermal paste)
    theta_sa = 10.0  # Sink-to-ambient (depends on heatsink)

    T_junction = specs.temp_max + P_mosfet_total * (theta_jc + theta_cs + theta_sa)

    # Check against limits
    T_j_max = 150  # Typical for MOSFETs
    margin = T_j_max - T_junction

    if margin < 25:
        recommendation = "Add heatsink or reduce losses"
    else:
        recommendation = "Thermal design adequate"

    return ThermalAnalysis(
        total_losses=P_total,
        mosfet_losses=P_mosfet_cond + P_mosfet_sw,
        inductor_losses=P_inductor,
        junction_temp=T_junction,
        margin=margin,
        recommendation=recommendation
    )
```

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/test_buck_calculator.py
def test_buck_duty_cycle():
    """Test duty cycle calculation."""
    specs = DesignSpecs(
        input_voltage_min=10,
        input_voltage_max=15,
        output_voltage=5,
        output_current=2
    )

    design = design_buck_converter(specs)

    expected_duty = 5 / 15  # 0.333
    assert abs(design.duty_cycle - expected_duty) < 0.01

def test_inductor_selection():
    """Test inductor value selection."""
    # Test that inductor prevents excessive ripple
    # Test that inductor is in standard E12/E24 series
    # Test current rating has proper margin
    pass

def test_thermal_analysis():
    """Test thermal calculations."""
    # Test junction temperature calculation
    # Test that margins are appropriate
    # Test heatsink recommendations
    pass
```

### Integration Tests

```python
# tests/test_integration.py
@pytest.mark.integration
def test_full_design_flow():
    """Test complete design workflow."""
    specs = DesignSpecs(
        input_voltage_min=18,
        input_voltage_max=30,
        output_voltage=12,
        output_current=5
    )

    # Run full design
    design = PowerSupplyDesigner().design(specs)

    # Verify all components selected
    assert design.bom is not None
    assert len(design.bom) >= 5  # At least 5 components

    # Verify thermal analysis done
    assert design.thermal_analysis is not None
    assert design.thermal_analysis.junction_temp < 125

    # Verify documentation generated
    assert design.documentation is not None
    assert "BOM" in design.documentation
```

## 📊 Example Output

### Design Summary

```
================================================================================
POWER SUPPLY DESIGN SUMMARY
================================================================================

Topology: Buck Converter
Input: 18-30V DC
Output: 12V @ 5A (60W)
Efficiency Target: 92%

CALCULATED PARAMETERS:
- Duty Cycle (min): 40% @ 30V input
- Duty Cycle (max): 67% @ 18V input
- Switching Frequency: 100 kHz
- Inductor: 47µH, 8A sat, DCR < 10mΩ
- Output Cap: 100µF, ESR < 50mΩ
- MOSFET: 60V, 15A, RDS(on) < 15mΩ

COMPONENT SELECTION:
┌────────────────┬──────────────────────┬─────────┬─────────┬───────────┐
│ Component      │ Part Number          │ Mfr     │ Price   │ Stock     │
├────────────────┼──────────────────────┼─────────┼─────────┼───────────┤
│ Controller IC  │ LM5116               │ TI      │ $3.25   │ 1,250     │
│ High-side FET  │ CSD19536KCS          │ TI      │ $2.10   │ 5,000     │
│ Low-side FET   │ CSD19536KCS          │ TI      │ $2.10   │ 5,000     │
│ Inductor       │ SRP1038A-470M        │ Bourns  │ $1.85   │ 2,100     │
│ Output Cap     │ GRM32ER71H106KA12L   │ Murata  │ $0.45   │ 10,000    │
│ Input Cap      │ GRM32ER71H106KA12L   │ Murata  │ $0.45   │ 10,000    │
└────────────────┴──────────────────────┴─────────┴─────────┴───────────┘

Total BOM Cost: $12.35 (Qty 1), $6.80 (Qty 1000)

THERMAL ANALYSIS:
- Total Losses: 4.8W (92% efficiency)
- Junction Temp: 95°C @ 70°C ambient
- Thermal Margin: 55°C (Good)
- Heatsink: Not required with proper PCB design

DESIGN REVIEW:
✅ Electrical: All ratings adequate with proper margins
✅ Thermal: Junction temperatures within limits
✅ Cost: Within budget ($15 target)
⚠️  EMC: Add input filter for conducted emissions
✅ Standards: Meets IEC 60950 requirements

FILES GENERATED:
- design_summary.pdf
- bom.csv
- schematic.asc (LTspice)
- pcb_guidelines.pdf
```

## 🎨 User Interface (Optional)

### CLI Interface

```bash
$ python power_designer.py design --interactive

Power Electronics Design Assistant
===================================

1. Select Topology:
   [1] Buck Converter
   [2] Boost Converter
   [3] Buck-Boost Converter
   [4] Flyback Converter
   [5] LLC Resonant

Choice: 1

2. Enter Specifications:
   Input Voltage (min): 18
   Input Voltage (max): 30
   Output Voltage: 12
   Output Current: 5
   Efficiency Target (%): 92

3. Design Options:
   Optimize for: [1] Cost [2] Size [3] Efficiency
   Choice: 3

Designing... [████████████████████████] 100%

Design Complete!
- Efficiency: 92.3%
- BOM Cost: $12.35
- Est. Size: 45x35mm

Generate files? (y/n): y

Files created:
✓ design_summary.pdf
✓ bom.csv
✓ schematic.asc
✓ pcb_guidelines.pdf
```

### Web Interface (Advanced)

Build with React + FastAPI:
- Real-time design updates via WebSocket
- Interactive schematic viewer
- Component parametric search
- Design comparison tool
- Cost vs performance charts

## 🚀 Deployment

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DIGIKEY_CLIENT_ID=${DIGIKEY_CLIENT_ID}
      - DIGIKEY_CLIENT_SECRET=${DIGIKEY_CLIENT_SECRET}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - redis
      - worker

  worker:
    build: .
    command: celery -A app.tasks worker
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## 📚 Learning Outcomes

After completing this project, you will:

✅ **Master Domain-Specific AI** - Build specialized engineering tools
✅ **Integrate Multiple APIs** - Work with Digi-Key, LLMs, databases
✅ **Implement Multi-Agent Systems** - Coordinate specialized agents
✅ **Apply RAG** - Use datasheets and technical docs effectively
✅ **Build Production Tools** - Create deployable engineering software
✅ **Validate Complex Designs** - Ensure correctness and safety
✅ **Generate Documentation** - Automate technical documentation

## 🎓 Evaluation Criteria

### Functionality (30%)
- [ ] All topologies work correctly (10%)
- [ ] Component selection is accurate (8%)
- [ ] Thermal analysis is reliable (7%)
- [ ] Multi-agent system functions (5%)

### Code Quality (25%)
- [ ] Clean, maintainable code (8%)
- [ ] Comprehensive error handling (7%)
- [ ] Type hints throughout (5%)
- [ ] Following engineering standards (5%)

### Integration (20%)
- [ ] API integrations work (7%)
- [ ] RAG provides useful context (6%)
- [ ] Agents coordinate effectively (7%)

### Production-Ready (15%)
- [ ] Deployed and running (5%)
- [ ] Monitoring in place (4%)
- [ ] Documentation complete (3%)
- [ ] Tests passing (3%)

### Documentation (10%)
- [ ] Setup instructions (3%)
- [ ] Usage examples (3%)
- [ ] Design decisions explained (2%)
- [ ] API documented (2%)

## 🔗 Resources

### APIs
- [Digi-Key API](https://developer.digikey.com/)
- [Mouser API](https://www.mouser.com/api-hub/)
- [Octopart API](https://octopart.com/api/home)

### Technical References
- IEEE Power Electronics Standards
- TI Power Design Seminars
- Infineon Application Notes
- Analog Devices Design Tools

### Software Tools
- LTspice (circuit simulation)
- KiCad (PCB design)
- FreeCAD (mechanical design)
- MATLAB/Python for analysis

## 💡 Next Steps

1. Start with Phase 1 (calculations)
2. Test thoroughly with known designs
3. Add API integrations incrementally
4. Build multi-agent system
5. Polish and deploy

**Good luck building your Power Electronics Design Assistant!** 🔌⚡
