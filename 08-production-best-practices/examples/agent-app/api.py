#!/usr/bin/env python3
"""
Agent API Server

FastAPI server for submitting tasks to the agent system and monitoring status.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from prometheus_client import generate_latest
from fastapi.responses import PlainTextResponse

from agent import submit_task, get_task_status, TaskStatus
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title="Production Agent API",
    description="API for autonomous agent task management",
    version="1.0.0"
)

# Request models
class TaskSubmission(BaseModel):
    """Task submission request."""
    type: str = Field(..., description="Task type (design, analysis, calculation)")
    description: str = Field(..., min_length=10, max_length=5000)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = Field(default=10, ge=1, le=50)
    timeout: int = Field(default=300, ge=10, le=600)

class TaskStatusResponse(BaseModel):
    """Task status response."""
    id: str
    type: str
    status: str
    description: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    iterations_used: int = 0
    tokens_used: int = 0

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    worker_status: str

# Endpoints
@app.post("/tasks", response_model=Dict[str, str])
async def create_task(submission: TaskSubmission):
    """Submit a task to the agent system."""

    logger.info(
        "task_submission",
        task_type=submission.type,
        description_length=len(submission.description)
    )

    try:
        task_id = submit_task(
            task_type=submission.type,
            description=submission.description,
            parameters=submission.parameters,
            max_iterations=submission.max_iterations,
            timeout=submission.timeout
        )

        return {
            "task_id": task_id,
            "status": "submitted",
            "message": "Task submitted successfully"
        }

    except Exception as e:
        logger.error("task_submission_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task(task_id: str):
    """Get task status and results."""

    logger.info("task_status_query", task_id=task_id)

    task_data = get_task_status(task_id)

    if not task_data:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(**task_data)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        worker_status="running"  # In production, check actual worker status
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain"
    )

# Example tasks
@app.post("/tasks/design/buck-converter")
async def design_buck_converter(
    input_voltage: float = Field(..., gt=0),
    output_voltage: float = Field(..., gt=0),
    output_current: float = Field(..., gt=0),
    efficiency_target: float = Field(default=0.9, ge=0.5, le=1.0)
):
    """Design a buck converter (convenience endpoint)."""

    task_id = submit_task(
        task_type="design",
        description=f"Design a buck converter with {input_voltage}V input, {output_voltage}V output, {output_current}A current, {efficiency_target*100}% efficiency target",
        parameters={
            "input_voltage": input_voltage,
            "output_voltage": output_voltage,
            "output_current": output_current,
            "efficiency_target": efficiency_target,
            "converter_type": "buck"
        }
    )

    return {"task_id": task_id, "status": "submitted"}

@app.post("/tasks/calculate/resistor-power")
async def calculate_resistor_power(
    voltage: float = Field(..., description="Voltage across resistor (V)"),
    current: Optional[float] = None,
    resistance: Optional[float] = None
):
    """Calculate resistor power dissipation (convenience endpoint)."""

    if not current and not resistance:
        raise HTTPException(
            status_code=400,
            detail="Must provide either current or resistance"
        )

    task_id = submit_task(
        task_type="calculation",
        description=f"Calculate power dissipation in resistor with {voltage}V across it",
        parameters={
            "voltage": voltage,
            "current": current,
            "resistance": resistance
        }
    )

    return {"task_id": task_id, "status": "submitted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001"))
    )
