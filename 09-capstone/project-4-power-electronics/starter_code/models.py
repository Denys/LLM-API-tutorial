"""
Data models for Power Electronics Design Assistant.

Define all the data structures used throughout the system.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from enum import Enum
from dataclasses import dataclass


class Topology(str, Enum):
    """Supported converter topologies."""
    BUCK = "buck"
    BOOST = "boost"
    BUCK_BOOST = "buck_boost"
    FLYBACK = "flyback"
    LLC = "llc_resonant"


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

    @validator('input_voltage_max')
    def validate_input_range(cls, v, values):
        if 'input_voltage_min' in values and v <= values['input_voltage_min']:
            raise ValueError("input_voltage_max must be > input_voltage_min")
        return v

    @validator('output_voltage')
    def validate_output_voltage(cls, v, values):
        if 'input_voltage_min' in values:
            # For buck, output must be less than input
            # For boost, output must be greater than input
            # This is a simplified check
            pass
        return v


class InductorSpec(BaseModel):
    """Inductor specifications."""
    inductance: float = Field(..., gt=0, description="Inductance (H)")
    current_avg: float = Field(..., gt=0, description="Average current rating (A)")
    current_peak: float = Field(..., gt=0, description="Peak current rating (A)")
    current_sat: float = Field(..., gt=0, description="Saturation current (A)")
    dcr_max: float = Field(..., gt=0, description="Maximum DC resistance (Ω)")
    frequency: float = Field(..., gt=0, description="Operating frequency (Hz)")
    package: Optional[str] = None


class CapacitorSpec(BaseModel):
    """Capacitor specifications."""
    capacitance: float = Field(..., gt=0, description="Capacitance (F)")
    voltage_rating: float = Field(..., gt=0, description="Voltage rating (V)")
    esr_max: float = Field(..., gt=0, description="Maximum ESR (Ω)")
    ripple_current: float = Field(..., gt=0, description="Ripple current rating (A)")
    type: str = Field(default="ceramic", description="Capacitor type")
    package: Optional[str] = None


class MOSFETSpec(BaseModel):
    """MOSFET specifications."""
    v_ds_min: float = Field(..., gt=0, description="Minimum V_DS rating (V)")
    i_d_min: float = Field(..., gt=0, description="Minimum I_D rating (A)")
    rds_on_max: float = Field(..., gt=0, description="Maximum R_DS(on) (Ω)")
    q_g_max: float = Field(..., gt=0, description="Maximum Q_g (C)")
    package: Optional[str] = None


class Component(BaseModel):
    """Generic component from database."""
    part_number: str
    manufacturer: str
    description: str
    parameters: Dict[str, float]
    price: float
    stock: int
    datasheet_url: Optional[str] = None


class BOMItem(BaseModel):
    """Bill of Materials item."""
    reference: str
    component: Component
    quantity: int
    unit_price: float
    total_price: float


class ThermalAnalysis(BaseModel):
    """Thermal analysis results."""
    total_losses: float = Field(..., description="Total power loss (W)")
    mosfet_losses: float = Field(..., description="MOSFET losses (W)")
    inductor_losses: float = Field(..., description="Inductor losses (W)")
    junction_temp: float = Field(..., description="Junction temperature (°C)")
    margin: float = Field(..., description="Thermal margin (°C)")
    recommendation: str


class DesignReview(BaseModel):
    """Design review from an agent."""
    agent_name: str
    status: str  # "pass", "warning", "fail"
    findings: List[str]
    recommendations: List[str]
    score: float = Field(..., ge=0, le=100)


class DesignResult(BaseModel):
    """Complete design result."""
    design_id: str
    topology: Topology
    specifications: DesignSpecs
    calculated_values: Dict[str, float]

    # Components
    inductor: Optional[InductorSpec] = None
    output_capacitor: Optional[CapacitorSpec] = None
    input_capacitor: Optional[CapacitorSpec] = None
    mosfet_hs: Optional[MOSFETSpec] = None  # High-side
    mosfet_ls: Optional[MOSFETSpec] = None  # Low-side

    # Selected components
    selected_components: List[Component] = []
    bom: List[BOMItem] = []
    total_cost: float = 0.0

    # Analysis
    thermal_analysis: Optional[ThermalAnalysis] = None
    design_reviews: List[DesignReview] = []

    # Performance
    calculated_efficiency: float
    calculated_ripple: float

    # Documentation
    documentation: Optional[str] = None
    schematic_netlist: Optional[str] = None


# Agent-specific models

class AgentTaskType(str, Enum):
    """Types of agent tasks."""
    DESIGN = "design"
    REVIEW = "review"
    OPTIMIZE = "optimize"
    VALIDATE = "validate"


class AgentTask(BaseModel):
    """Task for an agent."""
    task_id: str
    task_type: AgentTaskType
    input_data: Dict
    priority: int = 0
    timeout: int = 300


class AgentResult(BaseModel):
    """Result from an agent."""
    task_id: str
    agent_name: str
    success: bool
    result: Dict
    warnings: List[str] = []
    errors: List[str] = []
    execution_time: float = 0.0


# Database/Cache models

class ComponentSearchQuery(BaseModel):
    """Component search query."""
    component_type: str
    parameters: Dict[str, float]
    filters: Dict[str, any] = {}
    max_results: int = 50
    sort_by: str = "price"  # "price", "performance", "availability"


class CachedComponent(BaseModel):
    """Cached component data."""
    query_hash: str
    components: List[Component]
    timestamp: str
    ttl: int = 86400  # 24 hours
