#!/usr/bin/env python3
"""
Basic RAG (Retrieval-Augmented Generation) Implementation

This example demonstrates the fundamentals of RAG:
1. Creating vector embeddings
2. Storing in vector database (ChromaDB)
3. Semantic search
4. Integration with LLM

Usage:
    pip install chromadb openai anthropic
    python basic_rag.py
"""

import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class SimpleRAG:
    """Simple RAG implementation using ChromaDB and OpenAI embeddings."""

    def __init__(self, collection_name: str = "power_electronics"):
        """Initialize RAG system with vector database."""

        # Initialize ChromaDB (in-memory for demo)
        self.chroma_client = chromadb.Client(Settings(
            anonymized_telemetry=False
        ))

        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Power electronics knowledge base"}
        )

        self.doc_count = 0

    def add_document(self, text: str, metadata: Dict = None):
        """
        Add document to vector database.

        Args:
            text: Document text
            metadata: Optional metadata (component type, manufacturer, etc.)
        """
        # Create embedding using OpenAI
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )

        embedding = response.data[0].embedding

        # Add to ChromaDB
        doc_id = f"doc_{self.doc_count}"
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )

        self.doc_count += 1
        print(f"✅ Added document {doc_id}")

    def add_documents_batch(self, texts: List[str], metadatas: List[Dict] = None):
        """Add multiple documents at once (more efficient)."""

        # Create embeddings in batch
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )

        embeddings = [data.embedding for data in response.data]

        # Generate IDs
        ids = [f"doc_{self.doc_count + i}" for i in range(len(texts))]

        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{} for _ in texts],
            ids=ids
        )

        self.doc_count += len(texts)
        print(f"✅ Added {len(texts)} documents in batch")

    def search(self, query: str, n_results: int = 3) -> Dict:
        """
        Search for relevant documents.

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            Dictionary with documents, distances, and metadata
        """
        # Create query embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )

        query_embedding = response.data[0].embedding

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return results

    def query_with_llm(self, query: str, provider: str = "claude", n_results: int = 3) -> str:
        """
        Query with LLM using retrieved context.

        Args:
            query: User query
            provider: "claude" or "openai"
            n_results: Number of documents to retrieve

        Returns:
            LLM response
        """
        # Retrieve relevant documents
        results = self.search(query, n_results=n_results)

        # Build context from results
        context = "\n\n".join([
            f"[Document {i+1}]\n{doc}"
            for i, doc in enumerate(results['documents'][0])
        ])

        # Query LLM with context
        if provider == "claude":
            message = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": f"""Based on the following technical documents:

{context}

Question: {query}

Please provide a detailed answer based on the documents above."""
                }]
            )
            return message.content[0].text

        else:  # OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=1024,
                messages=[
                    {"role": "system", "content": "You are a technical expert. Answer questions based on provided documentation."},
                    {"role": "user", "content": f"Documents:\n{context}\n\nQuestion: {query}"}
                ]
            )
            return response.choices[0].message.content


def demo_basic_rag():
    """Demonstrate basic RAG functionality."""
    print("\n" + "=" * 80)
    print("🔍 BASIC RAG DEMONSTRATION")
    print("=" * 80)

    # Initialize RAG system
    rag = SimpleRAG()

    # Add some power electronics knowledge
    print("\n📚 Adding documents to knowledge base...")

    documents = [
        {
            "text": """IRF540N N-Channel MOSFET Specifications:
- Voltage Rating (Vds): 100V
- Continuous Drain Current (Id): 33A at 25°C
- Drain-Source On-Resistance (Rds_on): 44mΩ typical at Vgs=10V
- Gate Threshold Voltage (Vgs_th): 2-4V
- Maximum Power Dissipation: 130W
- Package: TO-220AB
- Applications: Motor control, switching power supplies, PWM applications
- Manufacturer: Infineon (formerly International Rectifier)""",
            "metadata": {
                "part_number": "IRF540N",
                "type": "MOSFET",
                "manufacturer": "Infineon"
            }
        },
        {
            "text": """LM7805 Voltage Regulator Specifications:
- Output Voltage: 5V (fixed)
- Output Current: 1.5A maximum
- Input Voltage Range: 7-35V
- Dropout Voltage: 2V typical
- Line Regulation: 100mV typical
- Load Regulation: 100mV typical
- Package: TO-220
- Features: Thermal overload protection, short circuit protection
- Applications: Fixed voltage power supplies, battery chargers, automotive""",
            "metadata": {
                "part_number": "LM7805",
                "type": "Voltage Regulator",
                "manufacturer": "Texas Instruments"
            }
        },
        {
            "text": """Buck Converter Design Guidelines:
A buck converter (step-down) converts higher input voltage to lower output voltage.
Key design parameters:
- Duty Cycle: D = Vout / Vin
- Inductor Value: L = (Vin - Vout) × D / (ΔI × f)
  where ΔI is ripple current (typically 20-40% of Iout)
- Output Capacitor: C = Iout × (1-D) / (f × ΔVout)
  where ΔVout is output voltage ripple
- Switching Frequency: Typically 50kHz-500kHz
- Component Selection: MOSFET (low Rds_on), Schottky diode (low Vf), low ESR capacitor
- Efficiency: Typically 85-95% depending on design""",
            "metadata": {
                "topic": "Buck Converter",
                "type": "Design Guide"
            }
        },
        {
            "text": """LED Current Limiting Resistor Calculation:
To power an LED safely, a current-limiting resistor is required.

Formula: R = (Vsupply - Vf) / If

Where:
- R = Resistor value (Ω)
- Vsupply = Supply voltage (V)
- Vf = LED forward voltage (V) - typical values:
  * Red: 1.8-2.2V
  * Green: 2.0-3.0V
  * Blue/White: 3.0-3.6V
- If = LED forward current (A) - typically 20mA (0.020A)

Power Rating: P = I² × R
Choose resistor with rating 2x calculated power for safety margin.

Example: 5V supply, Red LED (Vf=2V, If=20mA)
R = (5V - 2V) / 0.020A = 150Ω
P = (0.020)² × 150 = 0.06W → Use 1/4W (0.25W) resistor""",
            "metadata": {
                "topic": "LED Circuits",
                "type": "Calculation Guide"
            }
        },
        {
            "text": """MOSFET Gate Drive Requirements:
Proper gate drive is critical for MOSFET performance.

Gate Charge (Qg): Total charge required to switch MOSFET
- Higher Qg = slower switching = more losses
- IRF540N Qg ≈ 72nC

Gate-Source Voltage (Vgs):
- Below Vgs_th: MOSFET off
- At Vgs_th (2-4V): Partially on (linear region)
- Above Vgs_th (10-15V): Fully on (low Rds_on)
- Maximum Vgs: ±20V (exceeding damages gate oxide)

Gate Drive Current:
Ig = Qg × f (switching frequency)
Example: IRF540N at 100kHz
Ig = 72nC × 100kHz = 7.2mA average

Gate Resistor: Limits di/dt, reduces ringing
Rg = 10-100Ω typical
Lower Rg = faster switching but more EMI""",
            "metadata": {
                "topic": "MOSFET",
                "type": "Application Guide"
            }
        }
    ]

    # Add documents in batch
    rag.add_documents_batch(
        texts=[doc["text"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents]
    )

    # Test semantic search
    print("\n" + "=" * 80)
    print("🔎 TEST 1: Semantic Search")
    print("=" * 80)

    query1 = "What MOSFET should I use for a 12V 5A motor driver?"
    print(f"\nQuery: {query1}")
    print("-" * 80)

    results = rag.search(query1, n_results=2)

    for i, (doc, distance, metadata) in enumerate(zip(
        results['documents'][0],
        results['distances'][0],
        results['metadatas'][0]
    )):
        print(f"\nResult {i+1} (similarity: {1-distance:.3f}):")
        print(f"Metadata: {metadata}")
        print(f"Content preview: {doc[:200]}...")

    # Test with LLM integration (Claude)
    print("\n" + "=" * 80)
    print("🤖 TEST 2: RAG with Claude")
    print("=" * 80)

    query2 = "How do I calculate the resistor for a blue LED with 5V supply?"
    print(f"\nQuery: {query2}")
    print("-" * 80)

    response = rag.query_with_llm(query2, provider="claude", n_results=2)
    print(f"\nClaude's Response:\n{response}")

    # Test with OpenAI
    print("\n" + "=" * 80)
    print("🤖 TEST 3: RAG with OpenAI")
    print("=" * 80)

    query3 = "Explain how to design a buck converter for 12V to 5V conversion"
    print(f"\nQuery: {query3}")
    print("-" * 80)

    response = rag.query_with_llm(query3, provider="openai", n_results=2)
    print(f"\nGPT-4's Response:\n{response}")

    # Show benefits
    print("\n" + "=" * 80)
    print("💡 RAG BENEFITS DEMONSTRATED")
    print("=" * 80)
    print("""
✅ Accurate Information: LLM uses actual datasheets/guides, not memorized data
✅ Source Attribution: Can trace answers back to specific documents
✅ Up-to-date: Add new datasheets anytime without retraining
✅ Cost Effective: Cheaper than fine-tuning custom models
✅ Flexible: Easy to update knowledge base
✅ Specific: Provides exact component specifications

Without RAG:
❌ LLM might hallucinate specifications
❌ No source references
❌ Training data cutoff limits knowledge
❌ Cannot easily add new components
    """)


def demo_comparison():
    """Compare RAG vs non-RAG responses."""
    print("\n" + "=" * 80)
    print("⚖️  RAG vs NON-RAG COMPARISON")
    print("=" * 80)

    query = "What is the Rds(on) of IRF540N at Vgs=10V?"

    # Without RAG (LLM alone)
    print("\n1️⃣  WITHOUT RAG (LLM memory only):")
    print("-" * 80)

    message = claude_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[{"role": "user", "content": query}]
    )

    print(message.content[0].text)

    # With RAG
    print("\n2️⃣  WITH RAG (Retrieved datasheet):")
    print("-" * 80)

    rag = SimpleRAG()
    rag.add_document("""IRF540N Datasheet Extract:
Drain-Source On-Resistance (Rds_on):
- At Vgs=10V, Id=17A: 44mΩ typical, 70mΩ maximum
- At Vgs=10V, Id=17A, Tj=125°C: 88mΩ typical""")

    response = rag.query_with_llm(query, provider="claude")
    print(response)

    print("\n" + "=" * 80)
    print("📊 Analysis:")
    print("=" * 80)
    print("""
WITHOUT RAG:
- May provide approximate or generic answer
- No specific source
- Might be outdated
- Could hallucinate exact values

WITH RAG:
- Provides exact datasheet value (44mΩ typical)
- Can cite source document
- Always current (if datasheet updated)
- Verifiable and accurate
    """)


def main():
    """Run all demonstrations."""
    print("\n" + "🔍 " + "=" * 76 + " 🔍")
    print("    BASIC RAG (RETRIEVAL-AUGMENTED GENERATION) DEMO")
    print("🔍 " + "=" * 76 + " 🔍")

    try:
        # Main demo
        demo_basic_rag()

        # Comparison
        demo_comparison()

        print("\n" + "=" * 80)
        print("✅ RAG demonstration complete!")
        print("=" * 80)
        print("\n💡 Next steps:")
        print("  • Try component_database.py for structured component lookup")
        print("  • See datasheet_parser.py for PDF parsing")
        print("  • Check rag_assistant.py for full integration")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. pip install chromadb openai anthropic")
        print("  2. Set OPENAI_API_KEY and ANTHROPIC_API_KEY in .env")
        raise


if __name__ == "__main__":
    main()
