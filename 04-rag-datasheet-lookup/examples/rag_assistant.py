#!/usr/bin/env python3
"""
RAG-Enhanced Power Electronics Assistant

This assistant combines:
- Component database lookup
- Application note retrieval
- Datasheet knowledge
- LLM reasoning

Usage:
    python rag_assistant.py
    python rag_assistant.py --provider openai
"""

import os
import sys
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parent.parent.parent))

import chromadb
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
claude_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


class RAGAssistant:
    """Power Electronics Assistant with RAG capabilities."""

    def __init__(self, provider: str = "claude"):
        """
        Initialize RAG assistant.

        Args:
            provider: "claude" or "openai"
        """
        self.provider = provider.lower()

        # Initialize ChromaDB client
        db_path = Path(__file__).parent.parent / "data" / "vector_db"
        db_path.mkdir(parents=True, exist_ok=True)

        self.chroma_client = chromadb.PersistentClient(path=str(db_path))

        # Initialize or get collections
        self.components_collection = self.chroma_client.get_or_create_collection(
            name="components",
            metadata={"description": "Component specifications"}
        )

        self.appnotes_collection = self.chroma_client.get_or_create_collection(
            name="application_notes",
            metadata={"description": "Application notes and design guides"}
        )

        # Initialize knowledge base if empty
        if self.components_collection.count() == 0:
            self._initialize_knowledge_base()

    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding for text using OpenAI."""
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def _initialize_knowledge_base(self):
        """Load datasheets and application notes into vector database."""
        print("📚 Initializing knowledge base...")

        # Load datasheets
        datasheets_dir = Path(__file__).parent.parent / "data" / "datasheets"
        if datasheets_dir.exists():
            for datasheet_file in datasheets_dir.glob("*.txt"):
                with open(datasheet_file, 'r') as f:
                    content = f.read()

                # Create chunks (simplified - split by sections)
                chunks = self._chunk_datasheet(content)

                for i, chunk in enumerate(chunks):
                    embedding = self._create_embedding(chunk["text"])

                    doc_id = f"{datasheet_file.stem}_chunk_{i}"
                    self.components_collection.add(
                        embeddings=[embedding],
                        documents=[chunk["text"]],
                        metadatas=[{
                            "source": datasheet_file.name,
                            "section": chunk.get("section", "General"),
                            "type": "datasheet"
                        }],
                        ids=[doc_id]
                    )

                print(f"  ✅ Loaded {datasheet_file.name}")

        # Load application notes
        appnotes_dir = Path(__file__).parent.parent / "data" / "application-notes"
        if appnotes_dir.exists():
            for appnote_file in appnotes_dir.glob("*.txt"):
                with open(appnote_file, 'r') as f:
                    content = f.read()

                # Create chunks
                chunks = self._chunk_text(content, chunk_size=1000)

                for i, chunk_text in enumerate(chunks):
                    embedding = self._create_embedding(chunk_text)

                    doc_id = f"{appnote_file.stem}_chunk_{i}"
                    self.appnotes_collection.add(
                        embeddings=[embedding],
                        documents=[chunk_text],
                        metadatas=[{
                            "source": appnote_file.name,
                            "type": "application_note"
                        }],
                        ids=[doc_id]
                    )

                print(f"  ✅ Loaded {appnote_file.name}")

        print(f"📊 Knowledge base initialized:")
        print(f"   • Components: {self.components_collection.count()} documents")
        print(f"   • App notes: {self.appnotes_collection.count()} documents\n")

    def _chunk_datasheet(self, text: str) -> List[Dict]:
        """Chunk datasheet by sections."""
        chunks = []

        # Simple section detection
        sections = [
            "FEATURES", "APPLICATIONS", "ABSOLUTE MAXIMUM RATINGS",
            "STATIC CHARACTERISTICS", "DYNAMIC CHARACTERISTICS",
            "THERMAL RESISTANCE", "DESIGN TIPS", "PACKAGE INFORMATION"
        ]

        lines = text.split('\n')
        current_section = "General"
        current_chunk = []

        for line in lines:
            # Check if line is a section header
            for section in sections:
                if section in line.upper():
                    # Save previous chunk
                    if current_chunk:
                        chunks.append({
                            "section": current_section,
                            "text": '\n'.join(current_chunk)
                        })
                    current_section = section
                    current_chunk = [line]
                    break
            else:
                current_chunk.append(line)

            # Create chunk if too large
            if len('\n'.join(current_chunk)) > 1000:
                chunks.append({
                    "section": current_section,
                    "text": '\n'.join(current_chunk)
                })
                current_chunk = []

        # Add final chunk
        if current_chunk:
            chunks.append({
                "section": current_section,
                "text": '\n'.join(current_chunk)
            })

        return chunks

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Chunk text with overlap."""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # Try to break at paragraph or sentence
            if end < len(text):
                last_para = chunk.rfind('\n\n')
                last_period = chunk.rfind('. ')

                if last_para > chunk_size * 0.5:
                    end = start + last_para
                elif last_period > chunk_size * 0.5:
                    end = start + last_period + 1

            chunks.append(text[start:end])
            start = end - overlap

        return chunks

    def search_knowledge(self, query: str, n_results: int = 3) -> Dict:
        """Search both component and application note databases."""

        # Create query embedding
        query_embedding = self._create_embedding(query)

        # Search components
        component_results = self.components_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Search application notes
        appnote_results = self.appnotes_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return {
            "components": component_results,
            "application_notes": appnote_results
        }

    def chat(self, user_query: str, include_rag: bool = True) -> str:
        """
        Chat with assistant, optionally using RAG.

        Args:
            user_query: User's question
            include_rag: Whether to retrieve relevant documents

        Returns:
            Assistant's response
        """

        if include_rag:
            # Retrieve relevant knowledge
            results = self.search_knowledge(user_query, n_results=2)

            # Build context
            context_parts = []

            # Add component knowledge
            if results["components"]["documents"][0]:
                context_parts.append("=== COMPONENT DATASHEETS ===\n")
                for doc, metadata in zip(
                    results["components"]["documents"][0],
                    results["components"]["metadatas"][0]
                ):
                    context_parts.append(f"[Source: {metadata['source']}]\n{doc}\n")

            # Add application note knowledge
            if results["application_notes"]["documents"][0]:
                context_parts.append("\n=== APPLICATION NOTES ===\n")
                for doc, metadata in zip(
                    results["application_notes"]["documents"][0],
                    results["application_notes"]["metadatas"][0]
                ):
                    context_parts.append(f"[Source: {metadata['source']}]\n{doc}\n")

            context = "\n".join(context_parts)

            # Build prompt with context
            full_prompt = f"""You are an expert power electronics engineer with access to a comprehensive technical library.

Retrieved Technical Documentation:
{context}

User Question: {user_query}

Please provide a detailed, accurate answer based on the technical documentation above. Include specific values, part numbers, and calculations when applicable. Cite sources when referencing specific information."""

        else:
            # No RAG - just use LLM knowledge
            full_prompt = user_query

        # Query LLM
        if self.provider == "claude":
            message = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": full_prompt}]
            )
            return message.content[0].text

        else:  # OpenAI
            response = openai_client.chat.completions.create(
                model="gpt-4-turbo",
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": "You are an expert power electronics engineer."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            return response.choices[0].message.content


def demo_comparison():
    """Demonstrate RAG vs non-RAG responses."""
    print("\n" + "=" * 80)
    print("⚖️  RAG vs NON-RAG COMPARISON")
    print("=" * 80)

    assistant = RAGAssistant(provider="claude")

    queries = [
        "What is the Rds(on) of IRF540N at Vgs=10V and Id=17A?",
        "How do I design a buck converter for 12V to 5V at 3A?",
        "What is the maximum drain current for IRF540N at 25°C?"
    ]

    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        # Without RAG
        print("\n❌ WITHOUT RAG (LLM knowledge only):")
        print("-" * 80)
        response_no_rag = assistant.chat(query, include_rag=False)
        print(response_no_rag[:300] + "..." if len(response_no_rag) > 300 else response_no_rag)

        # With RAG
        print("\n✅ WITH RAG (Retrieved documentation):")
        print("-" * 80)
        response_with_rag = assistant.chat(query, include_rag=True)
        print(response_with_rag[:400] + "..." if len(response_with_rag) > 400 else response_with_rag)

        print()


def demo_interactive():
    """Interactive demo."""
    print("\n" + "=" * 80)
    print("💬 INTERACTIVE RAG ASSISTANT")
    print("=" * 80)

    assistant = RAGAssistant(provider="claude")

    test_queries = [
        "What MOSFET do you recommend for a 12V 10A motor driver?",
        "Explain the buck converter design process step by step",
        "What is the thermal resistance of IRF540N?"
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"User: {query}")
        print(f"{'='*80}\n")

        response = assistant.chat(query, include_rag=True)
        print(f"Assistant:\n{response}\n")


def main():
    """Main demonstration."""
    import argparse

    parser = argparse.ArgumentParser(description="RAG-Enhanced Power Electronics Assistant")
    parser.add_argument("--provider", choices=["claude", "openai"], default="claude")
    parser.add_argument("--demo", choices=["comparison", "interactive", "both"], default="both")

    args = parser.parse_args()

    print("\n" + "🤖 " + "=" * 76 + " 🤖")
    print("    RAG-ENHANCED POWER ELECTRONICS ASSISTANT")
    print("🤖 " + "=" * 76 + " 🤖")
    print(f"\nProvider: {args.provider.upper()}")

    try:
        if args.demo in ["comparison", "both"]:
            demo_comparison()

        if args.demo in ["interactive", "both"]:
            demo_interactive()

        print("\n" + "=" * 80)
        print("💡 KEY BENEFITS OF RAG")
        print("=" * 80)
        print("""
✅ Accurate Specifications: Retrieves exact values from datasheets
✅ Source Attribution: Can cite specific documents
✅ Up-to-Date: Easy to add new components and app notes
✅ Comprehensive: Combines multiple knowledge sources
✅ Verifiable: Answers traceable to source documents
✅ Cost-Effective: No fine-tuning required

WITHOUT RAG:
❌ May provide approximate or outdated values
❌ Cannot cite specific sources
❌ Limited to training data
❌ Potential hallucinations

WITH RAG:
✅ Provides exact datasheet values
✅ References specific documents
✅ Always current knowledge base
✅ Verifiable and accurate
        """)

        print("=" * 80)
        print("✅ RAG Assistant demonstration complete!")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. pip install chromadb openai anthropic")
        print("  2. Set OPENAI_API_KEY and ANTHROPIC_API_KEY in .env")
        print("  3. Run from the examples directory")
        raise


if __name__ == "__main__":
    main()
