#!/usr/bin/env python3
"""
Component Specification Database with RAG

This module provides a structured database for electronic components
with semantic search capabilities.

Features:
- Component spec storage and retrieval
- Vector embeddings for semantic search
- Filtering by component type, voltage, current, etc.
- Integration-ready for LLM assistants

Usage:
    python component_database.py
"""

import os
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@dataclass
class ComponentSpec:
    """Structured component specification."""
    part_number: str
    manufacturer: str
    component_type: str  # MOSFET, Regulator, Diode, etc.
    voltage_rating: Optional[str] = None
    current_rating: Optional[str] = None
    package: Optional[str] = None
    features: Optional[List[str]] = None
    applications: Optional[List[str]] = None
    datasheet_url: Optional[str] = None
    notes: Optional[str] = None

    def to_searchable_text(self) -> str:
        """Convert to searchable text for embeddings."""
        text = f"""Part Number: {self.part_number}
Manufacturer: {self.manufacturer}
Type: {self.component_type}"""

        if self.voltage_rating:
            text += f"\nVoltage Rating: {self.voltage_rating}"
        if self.current_rating:
            text += f"\nCurrent Rating: {self.current_rating}"
        if self.package:
            text += f"\nPackage: {self.package}"
        if self.features:
            text += f"\nFeatures: {', '.join(self.features)}"
        if self.applications:
            text += f"\nApplications: {', '.join(self.applications)}"
        if self.notes:
            text += f"\nNotes: {self.notes}"

        return text


class ComponentDatabase:
    """Vector database for component specifications."""

    def __init__(self, db_path: str = "./component_db", collection_name: str = "components"):
        """
        Initialize component database.

        Args:
            db_path: Path to persist database
            collection_name: Name of the collection
        """
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(path=db_path)

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Electronic component specifications"}
        )

    def add_component(self, spec: ComponentSpec):
        """
        Add component to database.

        Args:
            spec: ComponentSpec object
        """
        # Create embedding
        text = spec.to_searchable_text()

        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        embedding = response.data[0].embedding

        # Store in database
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[asdict(spec)],
            ids=[spec.part_number]
        )

        print(f"✅ Added {spec.part_number} to database")

    def add_components_batch(self, specs: List[ComponentSpec]):
        """Add multiple components efficiently."""

        texts = [spec.to_searchable_text() for spec in specs]

        # Create embeddings in batch
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        embeddings = [data.embedding for data in response.data]

        # Store in database
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=[asdict(spec) for spec in specs],
            ids=[spec.part_number for spec in specs]
        )

        print(f"✅ Added {len(specs)} components to database")

    def search(self, query: str, n_results: int = 5, filter_type: Optional[str] = None) -> Dict:
        """
        Search for components matching query.

        Args:
            query: Search query (natural language)
            n_results: Number of results to return
            filter_type: Optional component type filter (e.g., "MOSFET")

        Returns:
            Search results with documents and metadata
        """
        # Create query embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )

        query_embedding = response.data[0].embedding

        # Build filter if provided
        where_clause = {"component_type": filter_type} if filter_type else None

        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )

        return results

    def get_component(self, part_number: str) -> Optional[Dict]:
        """Get specific component by part number."""
        try:
            result = self.collection.get(ids=[part_number])
            if result['ids']:
                return {
                    "document": result['documents'][0],
                    "metadata": result['metadatas'][0]
                }
        except Exception:
            return None

    def list_components(self, component_type: Optional[str] = None) -> List[str]:
        """List all components, optionally filtered by type."""
        where_clause = {"component_type": component_type} if component_type else None

        results = self.collection.get(where=where_clause)
        return results['ids']

    def export_to_json(self, filename: str):
        """Export database to JSON file."""
        results = self.collection.get()

        components = []
        for metadata in results['metadatas']:
            components.append(metadata)

        with open(filename, 'w') as f:
            json.dump(components, f, indent=2)

        print(f"💾 Exported {len(components)} components to {filename}")

    def import_from_json(self, filename: str):
        """Import components from JSON file."""
        with open(filename, 'r') as f:
            components_data = json.load(f)

        specs = []
        for comp_data in components_data:
            spec = ComponentSpec(**comp_data)
            specs.append(spec)

        self.add_components_batch(specs)
        print(f"📂 Imported {len(specs)} components from {filename}")


def populate_sample_database():
    """Populate database with sample components."""
    print("\n" + "=" * 80)
    print("📚 POPULATING SAMPLE DATABASE")
    print("=" * 80)

    db = ComponentDatabase()

    # Sample MOSFETs
    mosfets = [
        ComponentSpec(
            part_number="IRF540N",
            manufacturer="Infineon",
            component_type="MOSFET",
            voltage_rating="100V",
            current_rating="33A",
            package="TO-220",
            features=["Low Rds(on): 44mΩ", "High current capability", "Fast switching"],
            applications=["Motor control", "Switching power supplies", "PWM applications"],
            datasheet_url="https://www.infineon.com/dgdl/irf540n.pdf",
            notes="Rds(on)=44mΩ at Vgs=10V, Qg=72nC"
        ),
        ComponentSpec(
            part_number="IRFZ44N",
            manufacturer="Infineon",
            component_type="MOSFET",
            voltage_rating="55V",
            current_rating="49A",
            package="TO-220",
            features=["Very low Rds(on): 17.5mΩ", "High current", "Logic-level compatible"],
            applications=["High current switching", "Motor drivers", "Battery management"],
            notes="Rds(on)=17.5mΩ at Vgs=10V, excellent for high current low voltage"
        ),
        ComponentSpec(
            part_number="IRF3205",
            manufacturer="Infineon",
            component_type="MOSFET",
            voltage_rating="55V",
            current_rating="110A",
            package="TO-220",
            features=["Ultra-low Rds(on): 8mΩ", "Massive current capability"],
            applications=["High-power motor control", "Battery switching", "High current DC-DC"],
            notes="One of the most popular power MOSFETs for high current applications"
        ),
    ]

    # Sample Voltage Regulators
    regulators = [
        ComponentSpec(
            part_number="LM7805",
            manufacturer="Texas Instruments",
            component_type="Voltage Regulator",
            voltage_rating="35V input max",
            current_rating="1.5A",
            package="TO-220",
            features=["Fixed 5V output", "Thermal protection", "Short circuit protection"],
            applications=["Power supplies", "Battery chargers", "Automotive"],
            notes="Classic linear regulator, 2V dropout"
        ),
        ComponentSpec(
            part_number="LM317",
            manufacturer="Texas Instruments",
            component_type="Voltage Regulator",
            voltage_rating="40V input max",
            current_rating="1.5A",
            package="TO-220",
            features=["Adjustable output 1.25V-37V", "Current limiting", "Thermal protection"],
            applications=["Adjustable power supplies", "Battery chargers", "Lab supplies"],
            notes="Adjust output with two resistors: Vout = 1.25V × (1 + R2/R1)"
        ),
        ComponentSpec(
            part_number="LM2596",
            manufacturer="Texas Instruments",
            component_type="Buck Converter IC",
            voltage_rating="45V input max",
            current_rating="3A",
            package="TO-220-5",
            features=["High efficiency switching", "Adjustable/Fixed outputs", "Built-in protection"],
            applications=["DC-DC step-down", "Battery powered systems", "Automotive"],
            notes="Switching regulator, much more efficient than linear, 52kHz-150kHz"
        ),
    ]

    # Sample Diodes
    diodes = [
        ComponentSpec(
            part_number="1N4007",
            manufacturer="Various",
            component_type="Diode",
            voltage_rating="1000V",
            current_rating="1A",
            package="DO-41",
            features=["General purpose rectifier", "High voltage rating"],
            applications=["Rectifiers", "Flyback diodes", "General protection"],
            notes="Vf=1V typical, slow recovery (not for high frequency)"
        ),
        ComponentSpec(
            part_number="MBR20100CT",
            manufacturer="Various",
            component_type="Schottky Diode",
            voltage_rating="100V",
            current_rating="20A (10A per diode)",
            package="TO-220",
            features=["Low forward voltage", "Fast recovery", "Center-tap configuration"],
            applications=["Buck converters", "Flyback rectifiers", "High efficiency power"],
            notes="Vf=0.5V typical, excellent for switching applications"
        ),
    ]

    # Add all components
    all_components = mosfets + regulators + diodes
    db.add_components_batch(all_components)

    return db


def demo_search():
    """Demonstrate search capabilities."""
    print("\n" + "=" * 80)
    print("🔍 SEARCH DEMONSTRATIONS")
    print("=" * 80)

    db = populate_sample_database()

    # Test 1: General search
    print("\n1️⃣  Natural Language Search:")
    print("-" * 80)

    query = "MOSFET for 12V 10A motor driver with low on-resistance"
    print(f"Query: {query}\n")

    results = db.search(query, n_results=3)

    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"Result {i+1} (similarity: {1-distance:.3f}):")
        print(f"  Part: {metadata['part_number']}")
        print(f"  Type: {metadata['component_type']}")
        print(f"  Voltage: {metadata['voltage_rating']}")
        print(f"  Current: {metadata['current_rating']}")
        print(f"  Package: {metadata['package']}")
        print()

    # Test 2: Filtered search
    print("\n2️⃣  Filtered Search (MOSFETs only):")
    print("-" * 80)

    query = "High current switching for 24V battery"
    print(f"Query: {query}\n")

    results = db.search(query, n_results=3, filter_type="MOSFET")

    for i, metadata in enumerate(results['metadatas'][0]):
        print(f"Result {i+1}: {metadata['part_number']} - {metadata['notes']}")

    # Test 3: Specific component lookup
    print("\n3️⃣  Direct Component Lookup:")
    print("-" * 80)

    part = "LM7805"
    print(f"Looking up: {part}\n")

    component = db.get_component(part)
    if component:
        print(component['document'])

    # Test 4: List by type
    print("\n4️⃣  List Components by Type:")
    print("-" * 80)

    mosfets = db.list_components(component_type="MOSFET")
    print(f"MOSFETs in database: {', '.join(mosfets)}")

    regulators = db.list_components(component_type="Voltage Regulator")
    print(f"Regulators in database: {', '.join(regulators)}")


def demo_export_import():
    """Demonstrate export/import functionality."""
    print("\n" + "=" * 80)
    print("💾 EXPORT/IMPORT DEMONSTRATION")
    print("=" * 80)

    db = ComponentDatabase()

    # Create sample component
    sample = ComponentSpec(
        part_number="TEST123",
        manufacturer="Test Corp",
        component_type="Test Component",
        voltage_rating="100V",
        current_rating="10A"
    )

    db.add_component(sample)

    # Export
    print("\nExporting to JSON...")
    db.export_to_json("components_export.json")

    # Import (would load into new database in practice)
    print("\nImport functionality available via import_from_json()")


def main():
    """Run all demonstrations."""
    print("\n" + "📦 " + "=" * 76 + " 📦")
    print("    COMPONENT SPECIFICATION DATABASE WITH RAG")
    print("📦 " + "=" * 76 + " 📦")

    try:
        # Demonstrate search
        demo_search()

        # Demonstrate export/import
        demo_export_import()

        print("\n" + "=" * 80)
        print("💡 KEY FEATURES")
        print("=" * 80)
        print("""
✅ Semantic Search: Find components by natural language description
✅ Structured Data: Organized component specifications
✅ Filtering: Search within specific component types
✅ Batch Operations: Efficiently add many components
✅ Persistence: Database saved to disk
✅ Export/Import: JSON format for sharing
✅ Integration Ready: Use with LLM assistants

NEXT STEPS:
- Add your own components
- Integrate with Power Electronics Assistant
- Parse datasheets automatically
- Add more metadata fields as needed
        """)

        print("=" * 80)
        print("✅ Component database demonstration complete!")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. pip install chromadb openai")
        print("  2. Set OPENAI_API_KEY in .env")
        raise


if __name__ == "__main__":
    main()
