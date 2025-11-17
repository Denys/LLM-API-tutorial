#!/usr/bin/env python3
"""
Multi-Agent Communication Demo

Demonstrates different communication patterns between agents:
1. Request-Response: Direct agent-to-agent communication
2. Broadcast: One agent sends message to multiple agents
3. Publish-Subscribe: Agents subscribe to topics and receive relevant messages

Shows how agents can collaborate by exchanging information.
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from enum import Enum

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


class MessageType(Enum):
    """Types of inter-agent messages."""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    PUBLISH = "publish"


class Message:
    """Inter-agent message."""

    def __init__(self, sender: str, recipient: Optional[str], content: str,
                 message_type: MessageType = MessageType.REQUEST,
                 topic: Optional[str] = None):
        """
        Create a message.

        Args:
            sender: Name of sending agent
            recipient: Name of receiving agent (None for broadcast)
            content: Message content
            message_type: Type of message
            topic: Topic for pub-sub (optional)
        """
        self.sender = sender
        self.recipient = recipient
        self.content = content
        self.message_type = message_type
        self.topic = topic
        self.timestamp = datetime.now().isoformat()
        self.id = f"{sender}_{datetime.now().timestamp()}"

    def to_dict(self) -> Dict:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "type": self.message_type.value,
            "topic": self.topic,
            "timestamp": self.timestamp
        }

    def __str__(self) -> str:
        """String representation."""
        recipient_str = self.recipient or "ALL"
        topic_str = f" [{self.topic}]" if self.topic else ""
        return f"{self.sender} → {recipient_str}{topic_str}: {self.content[:50]}..."


class MessageBus:
    """Central message bus for agent communication."""

    def __init__(self):
        """Initialize message bus."""
        self.messages: List[Message] = []
        self.subscribers: Dict[str, List[str]] = {}  # topic -> [agent_names]
        self.message_log: List[Dict] = []

    def send(self, message: Message):
        """
        Send a message through the bus.

        Args:
            message: Message to send
        """
        self.messages.append(message)
        self.message_log.append(message.to_dict())
        print(f"  📨 {message}")

    def receive(self, agent_name: str) -> List[Message]:
        """
        Get messages for an agent.

        Args:
            agent_name: Name of receiving agent

        Returns:
            List of messages for this agent
        """
        messages = []
        for msg in self.messages:
            # Direct messages
            if msg.recipient == agent_name:
                messages.append(msg)
            # Broadcast messages (excluding sender)
            elif msg.recipient is None and msg.sender != agent_name:
                messages.append(msg)
            # Published messages on subscribed topics
            elif msg.message_type == MessageType.PUBLISH and msg.topic:
                if agent_name in self.subscribers.get(msg.topic, []):
                    messages.append(msg)

        # Remove delivered messages
        for msg in messages:
            if msg in self.messages:
                self.messages.remove(msg)

        return messages

    def subscribe(self, agent_name: str, topic: str):
        """
        Subscribe agent to a topic.

        Args:
            agent_name: Name of agent
            topic: Topic to subscribe to
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        if agent_name not in self.subscribers[topic]:
            self.subscribers[topic].append(agent_name)
        print(f"  🔔 {agent_name} subscribed to '{topic}'")

    def get_log(self) -> List[Dict]:
        """Get message log."""
        return self.message_log


class CommunicatingAgent:
    """Agent that can communicate with other agents."""

    def __init__(self, name: str, role: str, message_bus: MessageBus,
                 model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize communicating agent.

        Args:
            name: Agent name
            role: Agent's role/specialty
            message_bus: Shared message bus
            model: Claude model to use
        """
        self.name = name
        self.role = role
        self.message_bus = message_bus
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.conversation_history: List[Dict] = []

    def process_task(self, task: str) -> str:
        """
        Process a task, potentially communicating with other agents.

        Args:
            task: Task description

        Returns:
            Result
        """
        print(f"\n🤖 {self.name} ({self.role}) processing: {task[:60]}...")

        # Get any pending messages
        messages = self.message_bus.receive(self.name)
        context = ""
        if messages:
            context = "\n\nIncoming messages:\n"
            for msg in messages:
                context += f"- From {msg.sender}: {msg.content}\n"

        # Create prompt
        prompt = f"""You are {self.name}, a specialized agent with role: {self.role}

Task: {task}
{context}

Based on your role, provide your analysis or answer.
Be concise and focused on your specialty."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text
            print(f"  💭 {self.name}: {result[:100]}...")
            return result

        except Exception as e:
            return f"Error: {e}"

    def send_message(self, content: str, recipient: Optional[str] = None,
                     message_type: MessageType = MessageType.REQUEST,
                     topic: Optional[str] = None):
        """
        Send a message to another agent or broadcast.

        Args:
            content: Message content
            recipient: Recipient agent name (None for broadcast)
            message_type: Type of message
            topic: Topic for pub-sub
        """
        message = Message(
            sender=self.name,
            recipient=recipient,
            content=content,
            message_type=message_type,
            topic=topic
        )
        self.message_bus.send(message)

    def subscribe(self, topic: str):
        """Subscribe to a topic."""
        self.message_bus.subscribe(self.name, topic)


def demo_request_response():
    """Demonstrate request-response communication pattern."""
    print("\n" + "="*70)
    print("DEMO 1: Request-Response Communication")
    print("="*70)
    print("Pattern: Agent A asks Agent B a specific question\n")

    bus = MessageBus()

    # Create specialized agents
    circuit_agent = CommunicatingAgent("CircuitDesigner", "Circuit topology and component selection", bus)
    thermal_agent = CommunicatingAgent("ThermalAnalyst", "Thermal analysis and heat dissipation", bus)

    # Circuit agent needs thermal advice
    print("\n1️⃣ CircuitDesigner sends request to ThermalAnalyst...")
    circuit_agent.send_message(
        content="I'm designing a 100W buck converter. What MOSFET thermal considerations should I account for?",
        recipient="ThermalAnalyst",
        message_type=MessageType.REQUEST
    )

    # Thermal agent processes the request
    print("\n2️⃣ ThermalAnalyst processes request...")
    thermal_response = thermal_agent.process_task(
        "Respond to the request about MOSFET thermal considerations for a 100W buck converter"
    )

    # Thermal agent sends response
    print("\n3️⃣ ThermalAnalyst sends response...")
    thermal_agent.send_message(
        content=thermal_response,
        recipient="CircuitDesigner",
        message_type=MessageType.RESPONSE
    )

    # Circuit agent receives and processes response
    print("\n4️⃣ CircuitDesigner receives response...")
    circuit_agent.process_task(
        "Incorporate the thermal analysis feedback into your buck converter design"
    )

    print("\n✅ Request-Response completed\n")


def demo_broadcast():
    """Demonstrate broadcast communication pattern."""
    print("\n" + "="*70)
    print("DEMO 2: Broadcast Communication")
    print("="*70)
    print("Pattern: One agent broadcasts to all agents\n")

    bus = MessageBus()

    # Create multiple agents
    coordinator = CommunicatingAgent("Coordinator", "Project coordination and requirements", bus)
    designer = CommunicatingAgent("Designer", "Circuit design", bus)
    reviewer = CommunicatingAgent("Reviewer", "Design review and verification", bus)
    optimizer = CommunicatingAgent("Optimizer", "Performance optimization", bus)

    # Coordinator broadcasts requirements
    print("\n1️⃣ Coordinator broadcasts project requirements...")
    coordinator.send_message(
        content="New project: Design a 24V to 5V, 5A buck converter. Efficiency target >90%. Size constraint: 50x50mm PCB.",
        recipient=None,  # Broadcast to all
        message_type=MessageType.BROADCAST
    )

    # All agents receive and process
    print("\n2️⃣ All agents process the broadcast...")
    for agent in [designer, reviewer, optimizer]:
        agent.process_task("Acknowledge the project requirements and state your initial considerations")

    print("\n✅ Broadcast completed\n")


def demo_pub_sub():
    """Demonstrate publish-subscribe communication pattern."""
    print("\n" + "="*70)
    print("DEMO 3: Publish-Subscribe Communication")
    print("="*70)
    print("Pattern: Agents subscribe to topics and receive relevant updates\n")

    bus = MessageBus()

    # Create agents with different interests
    power_agent = CommunicatingAgent("PowerEngineer", "Power electronics design", bus)
    signal_agent = CommunicatingAgent("SignalEngineer", "Signal integrity and analog design", bus)
    pcb_agent = CommunicatingAgent("PCBDesigner", "PCB layout and routing", bus)
    test_agent = CommunicatingAgent("TestEngineer", "Testing and validation", bus)

    # Agents subscribe to topics of interest
    print("\n1️⃣ Agents subscribe to relevant topics...")
    power_agent.subscribe("power")
    power_agent.subscribe("testing")

    signal_agent.subscribe("signal_integrity")
    signal_agent.subscribe("testing")

    pcb_agent.subscribe("power")
    pcb_agent.subscribe("signal_integrity")
    pcb_agent.subscribe("layout")

    test_agent.subscribe("testing")

    # Publish messages on different topics
    print("\n2️⃣ Publishing updates on different topics...")

    # Power topic
    power_agent.send_message(
        content="Switching frequency set to 100kHz. This affects inductor selection and EMI.",
        message_type=MessageType.PUBLISH,
        topic="power"
    )

    # Signal integrity topic
    signal_agent.send_message(
        content="Critical nets identified: FB (feedback), SW (switching node). Keep away from sensitive signals.",
        message_type=MessageType.PUBLISH,
        topic="signal_integrity"
    )

    # Testing topic
    test_agent.send_message(
        content="Test plan ready. Need load testing from 0-5A and thermal imaging at full load.",
        message_type=MessageType.PUBLISH,
        topic="testing"
    )

    # Agents process messages on their subscribed topics
    print("\n3️⃣ Agents process messages on subscribed topics...")

    print("\n  PCBDesigner (subscribed to: power, signal_integrity, layout):")
    pcb_agent.process_task("Review messages and state layout considerations")

    print("\n  PowerEngineer (subscribed to: power, testing):")
    power_agent.process_task("Review messages and provide feedback")

    print("\n  SignalEngineer (subscribed to: signal_integrity, testing):")
    signal_agent.process_task("Review messages and state signal integrity plan")

    print("\n✅ Publish-Subscribe completed\n")


def main():
    """Run all communication pattern demos."""

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        sys.exit(1)

    print("\n" + "="*70)
    print("Multi-Agent Communication Patterns Demo")
    print("="*70)

    # Demo 1: Request-Response
    demo_request_response()

    input("\nPress Enter to continue to Broadcast demo...")

    # Demo 2: Broadcast
    demo_broadcast()

    input("\nPress Enter to continue to Pub-Sub demo...")

    # Demo 3: Publish-Subscribe
    demo_pub_sub()

    print("\n" + "="*70)
    print("All communication pattern demos completed!")
    print("="*70)
    print("\nKey Patterns Demonstrated:")
    print("  1. Request-Response: Direct agent-to-agent queries")
    print("  2. Broadcast: One-to-many announcements")
    print("  3. Pub-Sub: Topic-based selective communication")
    print("\nThese patterns enable flexible multi-agent collaboration.")


if __name__ == "__main__":
    main()
