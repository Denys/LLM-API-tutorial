#!/usr/bin/env python3
"""
Agent Orchestration Framework

Implements different orchestration patterns for coordinating multiple agents:
1. Sequential: Agents execute one after another in a pipeline
2. Parallel: Multiple agents execute simultaneously
3. Hierarchical: Supervisor agent coordinates worker agents
4. Conditional: Agent selection based on conditions

This framework provides the infrastructure for complex multi-agent workflows.
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import concurrent.futures

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


class OrchestrationPattern(Enum):
    """Types of orchestration patterns."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    CONDITIONAL = "conditional"


@dataclass
class Task:
    """Task to be executed by an agent."""
    id: str
    description: str
    agent_name: str
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    status: str = "pending"  # pending, running, complete, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    pattern: OrchestrationPattern
    tasks: List[Task]
    final_result: Any
    execution_time: float
    success: bool


class Agent:
    """Agent that can be orchestrated."""

    def __init__(self, name: str, role: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize agent.

        Args:
            name: Agent name
            role: Agent role/specialty
            model: Claude model
        """
        self.name = name
        self.role = role
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def execute(self, task: Task) -> str:
        """
        Execute a task.

        Args:
            task: Task to execute

        Returns:
            Task result
        """
        print(f"\n  🔹 {self.name} executing: {task.description[:60]}...")

        # Build prompt with context
        prompt_parts = [f"Task: {task.description}"]

        if task.context:
            prompt_parts.append("\nContext:")
            for key, value in task.context.items():
                prompt_parts.append(f"  {key}: {value}")

        prompt_parts.append(f"\nYou are {self.name}, specialized in {self.role}.")
        prompt_parts.append("Provide your expert analysis concisely.")

        prompt = "\n".join(prompt_parts)

        try:
            task.status = "running"
            task.start_time = datetime.now().isoformat()

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text
            task.result = result
            task.status = "complete"
            task.end_time = datetime.now().isoformat()

            print(f"     ✓ Complete: {result[:80]}...")
            return result

        except Exception as e:
            task.status = "failed"
            task.end_time = datetime.now().isoformat()
            error_msg = f"Error: {e}"
            task.result = error_msg
            print(f"     ✗ Failed: {error_msg}")
            return error_msg


class Orchestrator:
    """Orchestrates multiple agents using different patterns."""

    def __init__(self):
        """Initialize orchestrator."""
        self.agents: Dict[str, Agent] = {}
        self.workflows: List[WorkflowResult] = []

    def register_agent(self, agent: Agent):
        """Register an agent with the orchestrator."""
        self.agents[agent.name] = agent
        print(f"  ✓ Registered agent: {agent.name} ({agent.role})")

    def sequential(self, tasks: List[Task], workflow_id: str = "seq") -> WorkflowResult:
        """
        Execute tasks sequentially in order.

        Args:
            tasks: List of tasks
            workflow_id: Workflow identifier

        Returns:
            Workflow result
        """
        print(f"\n{'='*70}")
        print(f"🔄 Sequential Workflow: {workflow_id}")
        print(f"{'='*70}")

        start_time = datetime.now()
        results = []

        for i, task in enumerate(tasks, 1):
            print(f"\nStep {i}/{len(tasks)}")

            # Get previous results as context
            if results:
                task.context["previous_results"] = results

            agent = self.agents.get(task.agent_name)
            if not agent:
                print(f"  ✗ Agent {task.agent_name} not found")
                task.status = "failed"
                continue

            result = agent.execute(task)
            results.append(result)

        execution_time = (datetime.now() - start_time).total_seconds()
        success = all(t.status == "complete" for t in tasks)

        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            pattern=OrchestrationPattern.SEQUENTIAL,
            tasks=tasks,
            final_result=results[-1] if results else None,
            execution_time=execution_time,
            success=success
        )

        self.workflows.append(workflow_result)
        print(f"\n✅ Sequential workflow complete ({execution_time:.2f}s)")
        return workflow_result

    def parallel(self, tasks: List[Task], workflow_id: str = "par") -> WorkflowResult:
        """
        Execute tasks in parallel.

        Args:
            tasks: List of tasks
            workflow_id: Workflow identifier

        Returns:
            Workflow result
        """
        print(f"\n{'='*70}")
        print(f"⚡ Parallel Workflow: {workflow_id}")
        print(f"{'='*70}")
        print(f"Executing {len(tasks)} tasks in parallel...\n")

        start_time = datetime.now()

        # Execute all tasks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
            futures = {}

            for task in tasks:
                agent = self.agents.get(task.agent_name)
                if agent:
                    future = executor.submit(agent.execute, task)
                    futures[future] = task

            # Wait for all to complete
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)

        execution_time = (datetime.now() - start_time).total_seconds()
        success = all(t.status == "complete" for t in tasks)

        # Combine results
        combined_result = "\n\n".join([f"{t.agent_name}: {t.result}" for t in tasks])

        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            pattern=OrchestrationPattern.PARALLEL,
            tasks=tasks,
            final_result=combined_result,
            execution_time=execution_time,
            success=success
        )

        self.workflows.append(workflow_result)
        print(f"\n✅ Parallel workflow complete ({execution_time:.2f}s)")
        return workflow_result

    def hierarchical(self, supervisor_task: Task, worker_tasks: List[Task],
                     workflow_id: str = "hier") -> WorkflowResult:
        """
        Execute with supervisor-worker hierarchy.

        Args:
            supervisor_task: Supervisor's task
            worker_tasks: Worker tasks
            workflow_id: Workflow identifier

        Returns:
            Workflow result
        """
        print(f"\n{'='*70}")
        print(f"👔 Hierarchical Workflow: {workflow_id}")
        print(f"{'='*70}")

        start_time = datetime.now()

        # Step 1: Supervisor plans
        print(f"\n📋 Supervisor Planning Phase")
        supervisor = self.agents.get(supervisor_task.agent_name)
        if not supervisor:
            raise ValueError(f"Supervisor agent {supervisor_task.agent_name} not found")

        supervisor_result = supervisor.execute(supervisor_task)

        # Step 2: Workers execute in parallel
        print(f"\n👷 Worker Execution Phase ({len(worker_tasks)} workers)")

        for task in worker_tasks:
            task.context["supervisor_guidance"] = supervisor_result

        worker_result = self.parallel(worker_tasks, workflow_id=f"{workflow_id}_workers")

        # Step 3: Supervisor synthesizes
        print(f"\n📊 Supervisor Synthesis Phase")
        synthesis_task = Task(
            id=f"{workflow_id}_synthesis",
            description="Synthesize worker results into final deliverable",
            agent_name=supervisor_task.agent_name,
            context={
                "worker_results": [t.result for t in worker_tasks],
                "initial_plan": supervisor_result
            }
        )

        final_result = supervisor.execute(synthesis_task)

        execution_time = (datetime.now() - start_time).total_seconds()
        all_tasks = [supervisor_task] + worker_tasks + [synthesis_task]
        success = all(t.status == "complete" for t in all_tasks)

        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            pattern=OrchestrationPattern.HIERARCHICAL,
            tasks=all_tasks,
            final_result=final_result,
            execution_time=execution_time,
            success=success
        )

        self.workflows.append(workflow_result)
        print(f"\n✅ Hierarchical workflow complete ({execution_time:.2f}s)")
        return workflow_result

    def conditional(self, tasks: List[Task], condition_func: Callable[[Task], bool],
                    workflow_id: str = "cond") -> WorkflowResult:
        """
        Execute tasks based on conditions.

        Args:
            tasks: List of potential tasks
            condition_func: Function that determines if a task should execute
            workflow_id: Workflow identifier

        Returns:
            Workflow result
        """
        print(f"\n{'='*70}")
        print(f"🔀 Conditional Workflow: {workflow_id}")
        print(f"{'='*70}")

        start_time = datetime.now()
        executed_tasks = []

        for task in tasks:
            if condition_func(task):
                print(f"\n✓ Condition met for: {task.description[:60]}")
                agent = self.agents.get(task.agent_name)
                if agent:
                    agent.execute(task)
                    executed_tasks.append(task)
            else:
                print(f"\n✗ Condition not met for: {task.description[:60]}")
                task.status = "skipped"

        execution_time = (datetime.now() - start_time).total_seconds()
        success = all(t.status == "complete" for t in executed_tasks)

        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            pattern=OrchestrationPattern.CONDITIONAL,
            tasks=tasks,
            final_result=[t.result for t in executed_tasks],
            execution_time=execution_time,
            success=success
        )

        self.workflows.append(workflow_result)
        print(f"\n✅ Conditional workflow complete ({execution_time:.2f}s)")
        return workflow_result


def demo_sequential():
    """Demonstrate sequential orchestration."""
    print("\n" + "="*70)
    print("DEMO 1: Sequential Orchestration")
    print("="*70)

    orchestrator = Orchestrator()

    # Register agents
    designer = Agent("Designer", "Circuit design and topology selection")
    analyzer = Agent("Analyzer", "Performance analysis and calculations")
    optimizer = Agent("Optimizer", "Design optimization and improvements")

    orchestrator.register_agent(designer)
    orchestrator.register_agent(analyzer)
    orchestrator.register_agent(optimizer)

    # Create sequential workflow
    tasks = [
        Task(
            id="design",
            description="Design a buck converter: 12V input, 5V 2A output",
            agent_name="Designer"
        ),
        Task(
            id="analyze",
            description="Analyze the design for efficiency, ripple, and thermal performance",
            agent_name="Analyzer"
        ),
        Task(
            id="optimize",
            description="Optimize the design for cost and performance",
            agent_name="Optimizer"
        )
    ]

    orchestrator.sequential(tasks, "buck_design")


def demo_parallel():
    """Demonstrate parallel orchestration."""
    print("\n\n" + "="*70)
    print("DEMO 2: Parallel Orchestration")
    print("="*70)

    orchestrator = Orchestrator()

    # Register specialized agents
    agents = [
        Agent("PowerAnalyst", "Power and efficiency analysis"),
        Agent("ThermalAnalyst", "Thermal analysis"),
        Agent("EMCAnalyst", "EMI/EMC analysis"),
        Agent("CostAnalyst", "Cost analysis and BOM optimization")
    ]

    for agent in agents:
        orchestrator.register_agent(agent)

    # Parallel analysis tasks
    design_spec = "24V to 5V, 5A buck converter with 100kHz switching"

    tasks = [
        Task("power", f"Analyze power efficiency for: {design_spec}", "PowerAnalyst"),
        Task("thermal", f"Analyze thermal requirements for: {design_spec}", "ThermalAnalyst"),
        Task("emc", f"Analyze EMI/EMC considerations for: {design_spec}", "EMCAnalyst"),
        Task("cost", f"Analyze BOM cost for: {design_spec}", "CostAnalyst")
    ]

    orchestrator.parallel(tasks, "parallel_analysis")


def demo_hierarchical():
    """Demonstrate hierarchical orchestration."""
    print("\n\n" + "="*70)
    print("DEMO 3: Hierarchical Orchestration")
    print("="*70)

    orchestrator = Orchestrator()

    # Register supervisor and workers
    orchestrator.register_agent(Agent("ProjectManager", "Project coordination and synthesis"))
    orchestrator.register_agent(Agent("HWEngineer", "Hardware design"))
    orchestrator.register_agent(Agent("FWEngineer", "Firmware development"))
    orchestrator.register_agent(Agent("TestEngineer", "Testing and validation"))

    # Supervisor task
    supervisor_task = Task(
        id="plan",
        description="Plan development of a smart power supply with I2C control",
        agent_name="ProjectManager"
    )

    # Worker tasks
    worker_tasks = [
        Task("hw", "Design hardware for smart power supply", "HWEngineer"),
        Task("fw", "Design firmware architecture for smart power supply", "FWEngineer"),
        Task("test", "Design test strategy for smart power supply", "TestEngineer")
    ]

    orchestrator.hierarchical(supervisor_task, worker_tasks, "smart_psu")


def main():
    """Run orchestration demonstrations."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        sys.exit(1)

    print("\n" + "="*70)
    print("Agent Orchestration Framework Demo")
    print("="*70)

    demo_sequential()

    input("\nPress Enter for parallel demo...")
    demo_parallel()

    input("\nPress Enter for hierarchical demo...")
    demo_hierarchical()

    print("\n" + "="*70)
    print("All orchestration demos complete!")
    print("="*70)


if __name__ == "__main__":
    main()
