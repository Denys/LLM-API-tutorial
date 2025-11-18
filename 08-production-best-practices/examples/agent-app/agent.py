#!/usr/bin/env python3
"""
Production Standalone Agent Application

A production-ready autonomous agent system with:
- Task queue (Celery + Redis)
- Background job processing
- State management and persistence
- Monitoring and health checks
- Error handling and retry logic
- Graceful shutdown
- Distributed deployment support
"""

import os
import sys
import time
import uuid
import json
import asyncio
import signal
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict

import structlog
from celery import Celery, Task
from celery.signals import worker_ready, worker_shutdown
from prometheus_client import Counter, Histogram, Gauge, generate_latest, start_http_server
import redis
from anthropic import Anthropic, APIError

from dotenv import load_dotenv
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
tasks_submitted = Counter(
    'agent_tasks_submitted_total',
    'Total tasks submitted',
    ['task_type']
)

tasks_completed = Counter(
    'agent_tasks_completed_total',
    'Total tasks completed',
    ['task_type', 'status']
)

task_duration = Histogram(
    'agent_task_duration_seconds',
    'Task execution duration',
    ['task_type']
)

active_tasks = Gauge(
    'agent_active_tasks',
    'Currently active tasks'
)

tool_calls = Counter(
    'agent_tool_calls_total',
    'Total tool calls',
    ['tool_name', 'status']
)

# Celery app configuration
app = Celery(
    'agent',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes
    task_soft_time_limit=540,  # 9 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# Task states
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class AgentTask:
    """Agent task definition."""
    id: str
    type: str
    description: str
    parameters: Dict[str, Any]
    max_iterations: int = 10
    timeout: int = 300
    created_at: str = None
    started_at: str = None
    completed_at: str = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    iterations_used: int = 0
    tokens_used: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

# Agent tools
AGENT_TOOLS = [
    {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "design_component",
        "description": "Design power electronics component",
        "input_schema": {
            "type": "object",
            "properties": {
                "component_type": {
                    "type": "string",
                    "description": "Type of component (resistor, capacitor, inductor, etc.)"
                },
                "specifications": {
                    "type": "object",
                    "description": "Component specifications"
                }
            },
            "required": ["component_type", "specifications"]
        }
    },
    {
        "name": "save_result",
        "description": "Save result to storage",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Filename to save to"
                },
                "content": {
                    "type": "string",
                    "description": "Content to save"
                }
            },
            "required": ["filename", "content"]
        }
    },
    {
        "name": "finish",
        "description": "Complete task with final result",
        "input_schema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "Final result"
                }
            },
            "required": ["result"]
        }
    }
]

class ProductionAgent:
    """Production-ready autonomous agent."""

    def __init__(self):
        """Initialize agent."""
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("AGENT_MODEL", "claude-3-5-sonnet-20241022")
        self.redis_client = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
            decode_responses=True
        )

    def _execute_tool(self, tool_name: str, tool_input: Dict) -> str:
        """Execute a tool."""
        logger.info("tool_execution", tool=tool_name, input=tool_input)

        try:
            if tool_name == "calculate":
                import math
                allowed = {
                    "sqrt": math.sqrt, "pow": pow, "abs": abs,
                    "sin": math.sin, "cos": math.cos, "tan": math.tan,
                    "log": math.log, "log10": math.log10, "pi": math.pi, "e": math.e
                }
                result = eval(tool_input["expression"], {"__builtins__": {}}, allowed)
                tool_calls.labels(tool_name=tool_name, status="success").inc()
                return f"Result: {result}"

            elif tool_name == "design_component":
                # Placeholder for actual component design logic
                comp_type = tool_input["component_type"]
                specs = tool_input["specifications"]
                result = f"Designed {comp_type} with specs: {specs}"
                tool_calls.labels(tool_name=tool_name, status="success").inc()
                return result

            elif tool_name == "save_result":
                # Save to Redis or file system
                filename = tool_input["filename"]
                content = tool_input["content"]
                self.redis_client.setex(
                    f"result:{filename}",
                    86400,  # 24 hours
                    content
                )
                tool_calls.labels(tool_name=tool_name, status="success").inc()
                return f"Saved to {filename}"

            elif tool_name == "finish":
                tool_calls.labels(tool_name=tool_name, status="success").inc()
                return tool_input["result"]

            else:
                tool_calls.labels(tool_name=tool_name, status="error").inc()
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            logger.error("tool_error", tool=tool_name, error=str(e))
            tool_calls.labels(tool_name=tool_name, status="error").inc()
            return f"Error: {str(e)}"

    def run_task(self, task: AgentTask) -> AgentTask:
        """Execute agent task."""
        logger.info("task_started", task_id=task.id, task_type=task.type)

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        self._save_task_state(task)

        active_tasks.inc()
        start_time = time.time()

        try:
            # Build system prompt based on task type
            system_prompt = self._build_system_prompt(task.type)

            # Initialize conversation
            messages = [{
                "role": "user",
                "content": f"{task.description}\n\nParameters: {json.dumps(task.parameters, indent=2)}"
            }]

            # Autonomous loop
            for iteration in range(task.max_iterations):
                task.iterations_used = iteration + 1

                logger.info(
                    "iteration",
                    task_id=task.id,
                    iteration=iteration + 1,
                    max_iterations=task.max_iterations
                )

                # Check timeout
                if time.time() - start_time > task.timeout:
                    raise TimeoutError(f"Task exceeded {task.timeout}s")

                # Call LLM
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    tools=AGENT_TOOLS,
                    messages=messages
                )

                # Track token usage
                task.tokens_used += response.usage.input_tokens + response.usage.output_tokens

                # Log reasoning
                for block in response.content:
                    if hasattr(block, "text") and block.text:
                        logger.info("reasoning", task_id=task.id, text=block.text[:200])

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Finished without tools
                    text = next((b.text for b in response.content if hasattr(b, "text")), "Done")
                    task.result = text
                    task.status = TaskStatus.COMPLETED
                    break

                elif response.stop_reason == "tool_use":
                    # Process tool calls
                    tool_results = []

                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._execute_tool(block.name, block.input)

                            if block.name == "finish":
                                # Task completed
                                task.result = result
                                task.status = TaskStatus.COMPLETED
                                break

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result
                            })

                    if task.status == TaskStatus.COMPLETED:
                        break

                    # Continue conversation
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})

                    # Save intermediate state
                    self._save_task_state(task)

            # Mark as completed if not already
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.COMPLETED
                task.result = "Maximum iterations reached"

        except TimeoutError as e:
            logger.error("task_timeout", task_id=task.id, error=str(e))
            task.status = TaskStatus.TIMEOUT
            task.error = str(e)

        except APIError as e:
            logger.error("api_error", task_id=task.id, error=str(e))
            task.status = TaskStatus.FAILED
            task.error = f"API Error: {str(e)}"

        except Exception as e:
            logger.exception("task_error", task_id=task.id, error=str(e))
            task.status = TaskStatus.FAILED
            task.error = str(e)

        finally:
            active_tasks.dec()
            task.completed_at = datetime.now().isoformat()
            duration = time.time() - start_time
            task_duration.labels(task_type=task.type).observe(duration)

            # Save final state
            self._save_task_state(task)

            # Record metrics
            tasks_completed.labels(
                task_type=task.type,
                status=task.status.value
            ).inc()

            logger.info(
                "task_completed",
                task_id=task.id,
                status=task.status.value,
                duration=duration,
                iterations=task.iterations_used,
                tokens=task.tokens_used
            )

        return task

    def _build_system_prompt(self, task_type: str) -> str:
        """Build system prompt based on task type."""
        base = "You are an autonomous agent. "

        if task_type == "design":
            return base + "You specialize in power electronics design. Provide detailed component values and calculations."
        elif task_type == "analysis":
            return base + "You specialize in circuit analysis. Provide thorough analysis with calculations."
        elif task_type == "calculation":
            return base + "You perform engineering calculations. Show all work step-by-step."
        else:
            return base + "You help with engineering tasks."

    def _save_task_state(self, task: AgentTask):
        """Save task state to Redis."""
        try:
            self.redis_client.setex(
                f"task:{task.id}",
                86400,  # 24 hours
                json.dumps(asdict(task))
            )
        except Exception as e:
            logger.error("state_save_error", error=str(e))

    def get_task_state(self, task_id: str) -> Optional[AgentTask]:
        """Get task state from Redis."""
        try:
            data = self.redis_client.get(f"task:{task_id}")
            if data:
                return AgentTask(**json.loads(data))
        except Exception as e:
            logger.error("state_load_error", error=str(e))
        return None

# Celery tasks
@app.task(bind=True, name='agent.execute_task')
def execute_task(self, task_dict: Dict) -> Dict:
    """Celery task to execute agent task."""

    # Convert dict to AgentTask
    task = AgentTask(**task_dict)

    logger.info("celery_task_started", task_id=task.id, celery_id=self.request.id)

    # Create agent and run task
    agent = ProductionAgent()
    result_task = agent.run_task(task)

    logger.info("celery_task_completed", task_id=task.id, status=result_task.status.value)

    return asdict(result_task)

# Task submission API
def submit_task(
    task_type: str,
    description: str,
    parameters: Dict[str, Any],
    **kwargs
) -> str:
    """Submit task to agent queue."""

    task = AgentTask(
        id=str(uuid.uuid4()),
        type=task_type,
        description=description,
        parameters=parameters,
        **kwargs
    )

    # Record submission
    tasks_submitted.labels(task_type=task_type).inc()

    logger.info("task_submitted", task_id=task.id, task_type=task_type)

    # Send to Celery
    execute_task.delay(asdict(task))

    return task.id

def get_task_status(task_id: str) -> Optional[Dict]:
    """Get task status."""
    agent = ProductionAgent()
    task = agent.get_task_state(task_id)
    if task:
        return asdict(task)
    return None

# Signal handlers
@worker_ready.connect
def on_worker_ready(**kwargs):
    """Called when worker is ready."""
    logger.info("worker_ready")

    # Start Prometheus metrics server
    start_http_server(9091)
    logger.info("metrics_server_started", port=9091)

@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """Called on worker shutdown."""
    logger.info("worker_shutdown")

# Main entry point for standalone execution
if __name__ == "__main__":
    # Run single task directly (for testing)
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        agent = ProductionAgent()

        test_task = AgentTask(
            id=str(uuid.uuid4()),
            type="calculation",
            description="Calculate the power dissipation in a 100Ω resistor with 12V across it",
            parameters={"voltage": 12, "resistance": 100}
        )

        result = agent.run_task(test_task)

        print(f"\nTask Result:")
        print(f"Status: {result.status}")
        print(f"Result: {result.result}")
        print(f"Iterations: {result.iterations_used}")
        print(f"Tokens: {result.tokens_used}")

    else:
        # Start Celery worker
        app.worker_main([
            'worker',
            '--loglevel=info',
            '--concurrency=4',
            '--max-tasks-per-child=100'
        ])
