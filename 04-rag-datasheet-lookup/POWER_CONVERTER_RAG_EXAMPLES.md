# RAG Applications for Power Converter Design

**Focus:** Using Retrieval-Augmented Generation to build intelligent design assistants that query datasheets, application notes, and design guides.

---

## Table of Contents

1. [Overview: RAG for Power Electronics](#1-overview-rag-for-power-electronics)
2. [Datasheet Knowledge Base](#2-datasheet-knowledge-base)
3. [Component Selection Assistant](#3-component-selection-assistant)
4. [Design Rule Checker](#4-design-rule-checker)
5. [Application Note Q&A System](#5-application-note-qa-system)
6. [Complete Example: Buck Converter Design Assistant](#6-complete-example-buck-converter-design-assistant)

---

## 1. Overview: RAG for Power Electronics

### Why RAG for Converter Design?

| Challenge | RAG Solution |
|-----------|-------------|
| Datasheets are 50-200 pages | Retrieve only relevant sections |
| Parameters scattered across tables | Structured extraction with context |
| Multiple competing parts | Side-by-side comparison from source |
| Design rules in app notes | Query specific design guidance |
| Thermal/EMI guidelines buried | Surface critical constraints |

### RAG Architecture for Design

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Datasheets     │     │   Chunking   │     │  Embeddings │
│  App Notes      │ ──▶ │   + Index    │ ──▶ │  Database   │
│  Design Guides  │     │              │     │  (Vector)   │
└─────────────────┘     └──────────────┘     └─────────────┘
                                                    │
                                                    ▼
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Design Query   │ ──▶ │   Retrieve   │ ──▶ │   Claude    │
│  "Select MOSFET │     │   Relevant   │     │   Answer    │
│   for 48V buck" │     │   Chunks     │     │   + Source  │
└─────────────────┘     └──────────────┘     └─────────────┘
```

---

## 2. Datasheet Knowledge Base

### Document Ingestion Pipeline

```python
# src/rag/ingestion.py
import os
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import json

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
import chromadb
from chromadb.utils import embedding_functions


class DatasheetIngestionPipeline:
    """Ingest and index power electronics datasheets for RAG."""

    def __init__(
        self,
        collection_name: str = "power_electronics",
        persist_directory: str = "./chroma_db"
    ):
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Use sentence-transformers for embeddings
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "Power electronics datasheets and app notes"}
        )

        # Chunking strategy optimized for datasheets
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=[
                "\n## ",      # Major sections
                "\n### ",     # Subsections
                "\n\n",       # Paragraphs
                "\n",         # Lines
                ". ",         # Sentences
                " "           # Words
            ]
        )

    def ingest_datasheet(
        self,
        pdf_path: str,
        metadata: Dict[str, Any]
    ) -> int:
        """Ingest a single datasheet PDF.

        Args:
            pdf_path: Path to PDF file
            metadata: Document metadata (part_number, manufacturer, type, etc.)

        Returns:
            Number of chunks created
        """
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        # Create document hash for deduplication
        doc_hash = hashlib.md5(
            Path(pdf_path).read_bytes()
        ).hexdigest()

        # Check if already ingested
        existing = self.collection.get(
            where={"doc_hash": doc_hash}
        )
        if existing and len(existing['ids']) > 0:
            print(f"Document already ingested: {metadata.get('part_number', pdf_path)}")
            return 0

        # Split into chunks
        chunks = []
        for page in pages:
            page_chunks = self.text_splitter.split_text(page.page_content)
            for i, chunk in enumerate(page_chunks):
                chunks.append({
                    "text": chunk,
                    "page": page.metadata.get("page", 0),
                    "chunk_index": i
                })

        # Prepare for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_hash}_{i}"
            ids.append(chunk_id)
            documents.append(chunk["text"])

            chunk_metadata = {
                **metadata,
                "doc_hash": doc_hash,
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "source_file": str(pdf_path)
            }
            metadatas.append(chunk_metadata)

        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        print(f"Ingested {len(chunks)} chunks from {metadata.get('part_number', pdf_path)}")
        return len(chunks)

    def ingest_directory(
        self,
        directory: str,
        metadata_file: str = None
    ) -> Dict[str, int]:
        """Ingest all PDFs in a directory.

        Args:
            directory: Directory containing PDFs
            metadata_file: Optional JSON file with per-document metadata

        Returns:
            Dictionary of filename -> chunk count
        """
        # Load metadata if provided
        doc_metadata = {}
        if metadata_file and Path(metadata_file).exists():
            with open(metadata_file) as f:
                doc_metadata = json.load(f)

        results = {}
        pdf_dir = Path(directory)

        for pdf_path in pdf_dir.glob("*.pdf"):
            # Get metadata for this document
            filename = pdf_path.name
            metadata = doc_metadata.get(filename, {})

            # Default metadata from filename
            if "part_number" not in metadata:
                metadata["part_number"] = pdf_path.stem

            if "doc_type" not in metadata:
                # Guess type from filename
                name_lower = filename.lower()
                if "app" in name_lower or "an" in name_lower:
                    metadata["doc_type"] = "application_note"
                elif "design" in name_lower:
                    metadata["doc_type"] = "design_guide"
                else:
                    metadata["doc_type"] = "datasheet"

            # Ingest
            chunk_count = self.ingest_datasheet(str(pdf_path), metadata)
            results[filename] = chunk_count

        return results

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Dict = None
    ) -> List[Dict]:
        """Search the knowledge base.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of matching chunks with metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
        )

        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                "id": results['ids'][0][i],
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if results.get('distances') else None
            })

        return formatted


# Example metadata file (datasheets_metadata.json)
EXAMPLE_METADATA = {
    "BSC010N04LS.pdf": {
        "part_number": "BSC010N04LS",
        "manufacturer": "Infineon",
        "doc_type": "datasheet",
        "component_type": "MOSFET",
        "voltage_class": "40V",
        "current_rating": "100A"
    },
    "LM5146.pdf": {
        "part_number": "LM5146",
        "manufacturer": "Texas Instruments",
        "doc_type": "datasheet",
        "component_type": "controller",
        "topology": "buck",
        "input_voltage": "6-100V"
    },
    "SLVA477.pdf": {
        "part_number": "SLVA477",
        "manufacturer": "Texas Instruments",
        "doc_type": "application_note",
        "topic": "MOSFET_selection",
        "topology": "buck"
    }
}
```

### Specialized Chunking for Tables

```python
# src/rag/table_chunker.py
import re
from typing import List, Dict

class DatasheetTableChunker:
    """Specialized chunking that preserves table structure."""

    def __init__(self):
        # Patterns for common datasheet sections
        self.section_patterns = {
            "absolute_maximum": r"absolute\s+maximum\s+ratings?",
            "electrical_char": r"electrical\s+characteristics?",
            "thermal": r"thermal\s+(characteristics?|data|resistance)",
            "switching": r"switching\s+(characteristics?|times?)",
            "typical_performance": r"typical\s+performance",
        }

    def chunk_with_context(
        self,
        text: str,
        chunk_size: int = 1000
    ) -> List[Dict]:
        """Chunk text while preserving table context.

        Returns chunks with section headers prepended for context.
        """
        chunks = []
        current_section = "General"

        lines = text.split('\n')
        current_chunk = []
        current_length = 0

        for line in lines:
            # Check for section headers
            for section_name, pattern in self.section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    current_section = section_name
                    break

            # Add line to current chunk
            line_length = len(line)

            if current_length + line_length > chunk_size and current_chunk:
                # Save current chunk with section context
                chunk_text = '\n'.join(current_chunk)
                chunks.append({
                    "text": f"[Section: {current_section}]\n{chunk_text}",
                    "section": current_section,
                    "has_table": self._detect_table(chunk_text)
                })

                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length

        # Don't forget last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                "text": f"[Section: {current_section}]\n{chunk_text}",
                "section": current_section,
                "has_table": self._detect_table(chunk_text)
            })

        return chunks

    def _detect_table(self, text: str) -> bool:
        """Detect if chunk contains a table."""
        # Simple heuristics for table detection
        lines = text.split('\n')

        # Check for consistent column separators
        tab_lines = sum(1 for l in lines if '\t' in l or '  ' in l)

        # Check for numeric patterns typical in specs
        num_pattern = r'\d+\.?\d*\s*[VAmWΩnpµ]'
        spec_lines = sum(1 for l in lines if re.search(num_pattern, l))

        return tab_lines > 3 or spec_lines > 3
```

---

## 3. Component Selection Assistant

### MOSFET Selection with RAG

```python
# src/rag/mosfet_selector.py
import anthropic
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class MOSFETSelectionAssistant:
    """RAG-powered MOSFET selection for power converters."""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        self.system_prompt = """You are a power electronics design expert specializing in MOSFET selection.

When recommending MOSFETs:
1. Use ONLY information from the provided datasheet excerpts
2. Consider: Rds_on, Qg, Qgd (for switching loss), Qrr (for hard switching)
3. Calculate Figure of Merit (FOM = Rds_on × Qg) for comparison
4. Account for voltage derating (80% of Vds_max)
5. Consider thermal limits and package options
6. Flag any parameters not found in the datasheets

Always cite the specific datasheet and page number for each parameter."""

    def select_for_buck(
        self,
        v_in: float,
        v_out: float,
        i_out: float,
        f_sw: float,
        priorities: List[str] = None
    ) -> str:
        """Select MOSFETs for synchronous buck converter.

        Args:
            v_in: Input voltage (V)
            v_out: Output voltage (V)
            i_out: Output current (A)
            f_sw: Switching frequency (Hz)
            priorities: List of priorities ["efficiency", "cost", "size"]

        Returns:
            Detailed selection recommendation
        """
        if priorities is None:
            priorities = ["efficiency"]

        # Calculate requirements
        v_ds_min = v_in * 1.25  # 20% margin
        i_d_min = i_out * 1.5   # 50% margin for transients
        duty_cycle = v_out / v_in

        # Build search query
        query = f"""MOSFET for buck converter:
        - Vds > {v_ds_min:.0f}V (input {v_in}V with margin)
        - Id > {i_d_min:.0f}A (load {i_out}A with margin)
        - Low Rds_on for {i_out}A conduction
        - Low Qg for {f_sw/1e3:.0f}kHz switching
        - Rds_on, Qg, Qgd, Qrr specifications"""

        # Retrieve relevant chunks
        results = self.kb.search(
            query=query,
            n_results=10,
            filter_metadata={"component_type": "MOSFET"}
        )

        # Build context from retrieved chunks
        context = self._build_context(results)

        # Generate recommendation
        user_prompt = f"""Select MOSFETs for this synchronous buck converter:

**Specifications:**
- Input voltage: {v_in}V
- Output voltage: {v_out}V
- Output current: {i_out}A
- Switching frequency: {f_sw/1e3:.0f} kHz
- Duty cycle: {duty_cycle:.1%}

**Requirements:**
- Vds_max > {v_ds_min:.0f}V (with 20% margin)
- Id_max > {i_d_min:.0f}A (with 50% margin)

**Priorities:** {', '.join(priorities)}

**Available Datasheet Information:**
{context}

**Please provide:**
1. High-side MOSFET recommendation with key parameters
2. Low-side MOSFET recommendation with key parameters
3. FOM comparison (Rds_on × Qg)
4. Expected conduction and switching losses at full load
5. Any concerns or limitations

Cite datasheet sources for all parameters."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def compare_parts(
        self,
        part_numbers: List[str],
        application: str
    ) -> str:
        """Compare specific MOSFETs for an application.

        Args:
            part_numbers: List of part numbers to compare
            application: Application description

        Returns:
            Detailed comparison with recommendation
        """
        # Search for each part
        all_context = []
        for part in part_numbers:
            results = self.kb.search(
                query=f"{part} specifications Rds_on Qg Vds Id thermal",
                n_results=5,
                filter_metadata={"part_number": part}
            )
            all_context.extend(results)

        context = self._build_context(all_context)

        user_prompt = f"""Compare these MOSFETs for: {application}

**Parts to compare:** {', '.join(part_numbers)}

**Datasheet Information:**
{context}

**Please provide:**
1. Comparison table with key parameters:
   - Vds_max, Id_max
   - Rds_on (with conditions)
   - Qg, Qgd, Qgs
   - Rth_jc
   - Package
2. FOM (Rds_on × Qg) for each
3. Pros/cons for this application
4. Final recommendation with reasoning

Use only data from the provided datasheets."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def _build_context(self, results: List[Dict]) -> str:
        """Build context string from search results."""
        context_parts = []

        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            source = f"{metadata.get('part_number', 'Unknown')} - Page {metadata.get('page', '?')}"

            context_parts.append(f"""
--- Source {i}: {source} ---
{result['text']}
""")

        return '\n'.join(context_parts)


# Usage example
def main():
    # Initialize knowledge base
    from ingestion import DatasheetIngestionPipeline

    kb = DatasheetIngestionPipeline()

    # Ingest datasheets (do this once)
    # kb.ingest_directory("./datasheets", "datasheets_metadata.json")

    # Create assistant
    assistant = MOSFETSelectionAssistant(kb)

    # Select MOSFETs for a design
    recommendation = assistant.select_for_buck(
        v_in=48,
        v_out=12,
        i_out=20,
        f_sw=200e3,
        priorities=["efficiency", "thermal"]
    )

    print(recommendation)


if __name__ == "__main__":
    main()
```

---

## 4. Design Rule Checker

### RAG-Based Design Validation

```python
# src/rag/design_checker.py
import anthropic
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()


class DesignRuleChecker:
    """Check converter design against datasheet specs and app note guidelines."""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        self.system_prompt = """You are a power electronics design reviewer.

Your role is to check designs against datasheet specifications and application note guidelines.

For each check:
1. State the design rule or specification limit
2. Compare against the proposed design value
3. Calculate margin (%) where applicable
4. Flag as: PASS, WARNING (margin < 20%), or FAIL
5. Cite the source document and page

Be thorough but concise. Flag ALL potential issues."""

    def check_mosfet_stress(
        self,
        design: Dict,
        mosfet_part: str
    ) -> str:
        """Check MOSFET electrical and thermal stress.

        Args:
            design: Design parameters dict
            mosfet_part: MOSFET part number

        Returns:
            Design check report
        """
        # Retrieve MOSFET specs
        results = self.kb.search(
            query=f"{mosfet_part} absolute maximum ratings Vds Vgs Id Pd thermal SOA",
            n_results=8,
            filter_metadata={"part_number": mosfet_part}
        )

        context = self._build_context(results)

        user_prompt = f"""Check this MOSFET application against datasheet limits:

**MOSFET:** {mosfet_part}

**Design Operating Conditions:**
- Vds_max (applied): {design.get('vds_max', 'N/A')} V
- Vgs_drive: {design.get('vgs_drive', 'N/A')} V
- Id_continuous: {design.get('id_continuous', 'N/A')} A
- Id_peak: {design.get('id_peak', 'N/A')} A
- Switching frequency: {design.get('f_sw', 'N/A')} Hz
- Ambient temperature: {design.get('t_amb', 'N/A')} °C

**Estimated Losses:**
- Conduction loss: {design.get('p_cond', 'N/A')} W
- Switching loss: {design.get('p_sw', 'N/A')} W
- Total loss: {design.get('p_total', 'N/A')} W

**Thermal:**
- Rth_ja (system): {design.get('rth_ja', 'N/A')} K/W

**Datasheet Information:**
{context}

**Check the following and report PASS/WARNING/FAIL:**
1. Vds stress vs Vds_max (want >20% margin)
2. Vgs stress vs Vgs_max
3. Id continuous vs Id_max at operating temperature
4. Power dissipation vs Pd_max
5. Junction temperature: Tj = Ta + P × Rth_ja
6. SOA compliance for switching transients

Show calculations for each check."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def check_inductor_design(
        self,
        design: Dict,
        inductor_part: str
    ) -> str:
        """Check inductor operating conditions.

        Args:
            design: Design parameters dict
            inductor_part: Inductor part number

        Returns:
            Design check report
        """
        results = self.kb.search(
            query=f"{inductor_part} saturation current RMS current DCR inductance temperature",
            n_results=6,
            filter_metadata={"part_number": inductor_part}
        )

        context = self._build_context(results)

        user_prompt = f"""Check inductor design against datasheet limits:

**Inductor:** {inductor_part}

**Design Conditions:**
- DC current: {design.get('i_dc', 'N/A')} A
- Ripple current (pp): {design.get('i_ripple', 'N/A')} A
- RMS current: {design.get('i_rms', 'N/A')} A
- Peak current: {design.get('i_peak', 'N/A')} A
- Switching frequency: {design.get('f_sw', 'N/A')} Hz
- Ambient temperature: {design.get('t_amb', 'N/A')} °C

**Datasheet Information:**
{context}

**Check:**
1. Peak current vs Isat (want >10% margin before saturation)
2. RMS current vs Irms rating
3. Estimated copper loss: I_rms² × DCR
4. Core loss estimation (if data available)
5. Temperature rise

Calculate actual margins and flag issues."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1536,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def check_capacitor_stress(
        self,
        design: Dict,
        cap_part: str,
        position: str = "output"
    ) -> str:
        """Check capacitor voltage and ripple current stress.

        Args:
            design: Design parameters dict
            cap_part: Capacitor part number
            position: "input" or "output"

        Returns:
            Design check report
        """
        results = self.kb.search(
            query=f"{cap_part} voltage rating ripple current ESR capacitance temperature derating",
            n_results=6
        )

        context = self._build_context(results)

        user_prompt = f"""Check {position} capacitor design:

**Capacitor:** {cap_part}
**Position:** {position}

**Design Conditions:**
- DC voltage: {design.get('v_dc', 'N/A')} V
- Ripple voltage (pp): {design.get('v_ripple', 'N/A')} V
- Ripple current (RMS): {design.get('i_ripple_rms', 'N/A')} A
- Ambient temperature: {design.get('t_amb', 'N/A')} °C

**Datasheet Information:**
{context}

**Check:**
1. DC voltage vs rated voltage (want >20% margin)
2. Voltage derating at temperature
3. Ripple current vs rating at frequency
4. ESR heating: P = I_rms² × ESR
5. Expected lifetime impact

For MLCCs, also check DC bias derating if applicable."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1536,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def full_design_review(self, design: Dict) -> str:
        """Complete design review against all component datasheets.

        Args:
            design: Complete design specification dict

        Returns:
            Full design review report
        """
        # Collect all relevant documentation
        queries = [
            f"{design['hs_mosfet']} maximum ratings thermal",
            f"{design['ls_mosfet']} maximum ratings thermal",
            f"{design['inductor']} saturation current DCR",
            f"{design['output_cap']} voltage ripple current",
            f"buck converter design guideline {design.get('controller', '')}",
        ]

        all_results = []
        for query in queries:
            results = self.kb.search(query, n_results=4)
            all_results.extend(results)

        context = self._build_context(all_results)

        user_prompt = f"""Complete design review for synchronous buck converter:

**Specifications:**
- Input: {design['v_in_min']}-{design['v_in_max']}V
- Output: {design['v_out']}V @ {design['i_out']}A
- Switching frequency: {design['f_sw']/1e3:.0f} kHz

**Components:**
- Controller: {design.get('controller', 'N/A')}
- High-side MOSFET: {design['hs_mosfet']}
- Low-side MOSFET: {design['ls_mosfet']}
- Inductor: {design['inductor']} ({design['l_value']}µH)
- Output capacitor: {design['output_cap']} × {design['output_cap_qty']}

**Operating Conditions:**
- Duty cycle range: {design['d_min']:.1%} to {design['d_max']:.1%}
- Inductor ripple: {design['i_ripple']}A pp
- Output ripple: {design['v_ripple']}mV pp
- Ambient temperature: {design['t_amb']}°C max

**Calculated Losses:**
- HS MOSFET: {design['p_hs']}W
- LS MOSFET: {design['p_ls']}W
- Inductor: {design['p_ind']}W
- Total: {design['p_total']}W
- Efficiency: {design['efficiency']:.1%}

**Reference Documentation:**
{context}

**Provide complete design review:**
1. Component stress summary (PASS/WARNING/FAIL for each)
2. Thermal analysis
3. Critical design rule compliance
4. Potential issues or risks
5. Recommendations for improvement

Be thorough and cite sources for all limits."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def _build_context(self, results: List[Dict]) -> str:
        """Build context string from search results."""
        seen_texts = set()
        context_parts = []

        for i, result in enumerate(results, 1):
            # Deduplicate
            text_hash = hash(result['text'][:100])
            if text_hash in seen_texts:
                continue
            seen_texts.add(text_hash)

            metadata = result['metadata']
            source = f"{metadata.get('part_number', 'Unknown')} - Page {metadata.get('page', '?')}"

            context_parts.append(f"""
--- Source {i}: {source} ---
{result['text']}
""")

        return '\n'.join(context_parts)


# Example usage
def example_design_check():
    from ingestion import DatasheetIngestionPipeline

    kb = DatasheetIngestionPipeline()
    checker = DesignRuleChecker(kb)

    # Check MOSFET stress
    mosfet_design = {
        "vds_max": 48,           # Max applied Vds
        "vgs_drive": 10,         # Gate drive voltage
        "id_continuous": 20,     # Continuous current
        "id_peak": 30,           # Peak current
        "f_sw": 200e3,           # Switching frequency
        "t_amb": 85,             # Ambient temperature
        "p_cond": 0.4,           # Conduction loss
        "p_sw": 0.6,             # Switching loss
        "p_total": 1.0,          # Total loss
        "rth_ja": 40,            # System thermal resistance
    }

    report = checker.check_mosfet_stress(mosfet_design, "BSC010N04LS")
    print(report)


if __name__ == "__main__":
    example_design_check()
```

---

## 5. Application Note Q&A System

### Query Design Guidelines from App Notes

```python
# src/rag/appnote_qa.py
import anthropic
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class AppNoteQASystem:
    """Q&A system for power electronics application notes and design guides."""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        self.system_prompt = """You are a power electronics application engineer.

Answer questions using ONLY information from the provided application notes and design guides.

Guidelines:
1. Cite specific app note numbers and page references
2. Include relevant equations and design procedures
3. Provide typical values and ranges from the documents
4. Note any assumptions or conditions
5. If information is not in the provided context, say so clearly

Format calculations clearly and explain the reasoning."""

    def ask(
        self,
        question: str,
        topic_filter: Optional[str] = None,
        manufacturer_filter: Optional[str] = None
    ) -> str:
        """Ask a question about power converter design.

        Args:
            question: Design question
            topic_filter: Optional topic filter (e.g., "MOSFET_selection")
            manufacturer_filter: Optional manufacturer filter

        Returns:
            Answer with citations
        """
        # Build metadata filter
        where_filter = {"doc_type": "application_note"}
        if topic_filter:
            where_filter["topic"] = topic_filter
        if manufacturer_filter:
            where_filter["manufacturer"] = manufacturer_filter

        # Search for relevant content
        results = self.kb.search(
            query=question,
            n_results=8,
            filter_metadata=where_filter if len(where_filter) > 1 else None
        )

        # Also search design guides
        guide_results = self.kb.search(
            query=question,
            n_results=4,
            filter_metadata={"doc_type": "design_guide"}
        )

        all_results = results + guide_results
        context = self._build_context(all_results)

        user_prompt = f"""Question: {question}

**Reference Documentation:**
{context}

Please answer the question using only the information provided above.
Include specific citations (document name, page number) for all facts and recommendations."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def get_design_procedure(
        self,
        topology: str,
        specs: Dict
    ) -> str:
        """Get step-by-step design procedure from app notes.

        Args:
            topology: Converter topology (buck, boost, flyback, etc.)
            specs: Design specifications dict

        Returns:
            Design procedure with calculations
        """
        # Search for design procedures
        query = f"{topology} converter design procedure step by step calculation"

        results = self.kb.search(
            query=query,
            n_results=10,
            filter_metadata={"topology": topology}
        )

        context = self._build_context(results)

        specs_text = '\n'.join(f"- {k}: {v}" for k, v in specs.items())

        user_prompt = f"""Provide design procedure for {topology} converter:

**Specifications:**
{specs_text}

**Reference Documentation:**
{context}

**Please provide:**
1. Step-by-step design procedure from the app notes
2. Key equations for each step
3. Calculations using the given specifications
4. Component selection criteria
5. Verification checks

Follow the methodology from the reference documents."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def explain_concept(self, concept: str) -> str:
        """Explain a power electronics concept using app note content.

        Args:
            concept: Concept to explain (e.g., "valley current mode control")

        Returns:
            Explanation with references
        """
        results = self.kb.search(
            query=f"{concept} explanation theory operation principle",
            n_results=8
        )

        context = self._build_context(results)

        user_prompt = f"""Explain: {concept}

**Reference Material:**
{context}

Provide:
1. Clear explanation of the concept
2. How it works / operating principle
3. Advantages and disadvantages
4. Typical applications
5. Key design considerations

Use the reference material for accurate technical details."""

        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return response.content[0].text

    def _build_context(self, results: List[Dict]) -> str:
        """Build context string from search results."""
        context_parts = []

        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            doc_name = metadata.get('part_number', 'Unknown')
            doc_type = metadata.get('doc_type', 'document')
            page = metadata.get('page', '?')

            context_parts.append(f"""
--- {doc_type.upper()}: {doc_name}, Page {page} ---
{result['text']}
""")

        return '\n'.join(context_parts)


# Common design questions
EXAMPLE_QUESTIONS = [
    "How do I select the switching frequency for a buck converter?",
    "What is the recommended dead time for synchronous rectification?",
    "How do I calculate the required output capacitance for voltage ripple?",
    "What are the trade-offs between CCM and DCM operation?",
    "How do I size the bootstrap capacitor for the high-side driver?",
    "What causes subharmonic oscillation in current mode control?",
    "How do I design the compensation network for voltage mode control?",
    "What are the layout guidelines for minimizing switching noise?",
]
```

---

## 6. Complete Example: Buck Converter Design Assistant

### Full RAG-Powered Design Tool

```python
# src/rag/buck_design_assistant.py
import anthropic
from typing import Dict, List, Optional
import json
import os
from dotenv import load_dotenv

from .ingestion import DatasheetIngestionPipeline
from .mosfet_selector import MOSFETSelectionAssistant
from .design_checker import DesignRuleChecker
from .appnote_qa import AppNoteQASystem

load_dotenv()


class BuckConverterDesignAssistant:
    """Complete RAG-powered buck converter design assistant.

    Integrates:
    - Component selection from datasheets
    - Design rule checking
    - Application note guidance
    - Interactive design refinement
    """

    def __init__(self, db_path: str = "./chroma_db"):
        # Initialize knowledge base
        self.kb = DatasheetIngestionPipeline(persist_directory=db_path)

        # Initialize sub-assistants
        self.mosfet_selector = MOSFETSelectionAssistant(self.kb)
        self.design_checker = DesignRuleChecker(self.kb)
        self.appnote_qa = AppNoteQASystem(self.kb)

        # Claude client for orchestration
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        self.conversation_history = []

    def start_design(self, specs: Dict) -> str:
        """Start a new converter design.

        Args:
            specs: Design specifications
                - v_in_min, v_in_max: Input voltage range (V)
                - v_out: Output voltage (V)
                - i_out: Output current (A)
                - v_ripple: Output voltage ripple (mV)
                - f_sw: Switching frequency (Hz)
                - efficiency_target: Target efficiency (0-1)
                - t_amb: Ambient temperature (°C)

        Returns:
            Initial design analysis and recommendations
        """
        # Validate specs
        required = ['v_in_min', 'v_in_max', 'v_out', 'i_out', 'f_sw']
        for key in required:
            if key not in specs:
                raise ValueError(f"Missing required specification: {key}")

        self.specs = specs

        # Calculate derived parameters
        v_in_nom = (specs['v_in_min'] + specs['v_in_max']) / 2
        d_min = specs['v_out'] / specs['v_in_max']
        d_max = specs['v_out'] / specs['v_in_min']
        p_out = specs['v_out'] * specs['i_out']

        # Get design guidance from app notes
        design_guidance = self.appnote_qa.ask(
            f"Buck converter design considerations for {specs['v_in_max']}V input "
            f"{specs['v_out']}V output {specs['i_out']}A at {specs['f_sw']/1e3:.0f}kHz"
        )

        # Get MOSFET recommendations
        mosfet_rec = self.mosfet_selector.select_for_buck(
            v_in=specs['v_in_max'],
            v_out=specs['v_out'],
            i_out=specs['i_out'],
            f_sw=specs['f_sw'],
            priorities=['efficiency']
        )

        # Calculate initial inductor value
        # L = (Vin - Vout) * D / (f_sw * delta_I)
        target_ripple_ratio = 0.3  # 30% ripple
        delta_i = specs['i_out'] * target_ripple_ratio
        l_value = (v_in_nom - specs['v_out']) * (specs['v_out']/v_in_nom) / (specs['f_sw'] * delta_i)

        # Search for suitable inductors
        inductor_results = self.kb.search(
            f"inductor {l_value*1e6:.1f}µH {specs['i_out']*1.5:.0f}A saturation low DCR",
            n_results=5,
            filter_metadata={"component_type": "inductor"} if False else None  # If tagged
        )

        # Build comprehensive report
        report = f"""# Buck Converter Design Analysis

## Specifications
- Input: {specs['v_in_min']}-{specs['v_in_max']}V
- Output: {specs['v_out']}V @ {specs['i_out']}A ({p_out}W)
- Switching frequency: {specs['f_sw']/1e3:.0f} kHz
- Efficiency target: {specs.get('efficiency_target', 0.95):.1%}
- Ambient temperature: {specs.get('t_amb', 25)}°C

## Calculated Parameters
- Duty cycle range: {d_min:.1%} to {d_max:.1%}
- Target inductor value: {l_value*1e6:.1f} µH
- Inductor ripple current: {delta_i:.2f} A (30% of Iout)

---

## Design Guidance from Application Notes

{design_guidance}

---

## MOSFET Recommendations

{mosfet_rec}

---

## Next Steps

1. **Confirm MOSFET selection** - Review the recommendations above
2. **Select inductor** - Need {l_value*1e6:.1f}µH, Isat > {specs['i_out']*1.3:.0f}A
3. **Calculate output capacitance** - For {specs.get('v_ripple', 50)}mV ripple
4. **Input capacitor selection** - RMS current handling
5. **Control loop design** - Compensation network

Would you like me to:
- Elaborate on any component selection?
- Calculate specific parameters?
- Check a proposed design?
"""

        # Save to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": report
        })

        return report

    def ask_design_question(self, question: str) -> str:
        """Ask a question about the current design.

        Args:
            question: Design question

        Returns:
            Answer using RAG context
        """
        # Add context about current design
        if hasattr(self, 'specs'):
            context_info = f"""
Current design: {self.specs['v_in_min']}-{self.specs['v_in_max']}V to {self.specs['v_out']}V @ {self.specs['i_out']}A
Switching frequency: {self.specs['f_sw']/1e3:.0f} kHz
"""
        else:
            context_info = ""

        # Route to appropriate sub-assistant
        question_lower = question.lower()

        if any(word in question_lower for word in ['mosfet', 'fet', 'switch', 'transistor']):
            answer = self.mosfet_selector.compare_parts(
                [],  # Would need part numbers
                f"buck converter {context_info}"
            )
        elif any(word in question_lower for word in ['check', 'verify', 'stress', 'margin']):
            answer = self.appnote_qa.ask(question)  # Simplified
        else:
            answer = self.appnote_qa.ask(f"{context_info}\n\n{question}")

        # Save to history
        self.conversation_history.append({
            "role": "user",
            "content": question
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": answer
        })

        return answer

    def verify_design(self, design: Dict) -> str:
        """Verify a complete design against datasheets.

        Args:
            design: Complete design with all components and operating conditions

        Returns:
            Verification report
        """
        return self.design_checker.full_design_review(design)

    def export_design(self, format: str = "json") -> str:
        """Export current design session.

        Args:
            format: Export format ("json", "markdown")

        Returns:
            Exported design data
        """
        export_data = {
            "specifications": self.specs if hasattr(self, 'specs') else {},
            "conversation": self.conversation_history
        }

        if format == "json":
            return json.dumps(export_data, indent=2)
        else:
            # Markdown format
            md = "# Buck Converter Design Session\n\n"
            if hasattr(self, 'specs'):
                md += "## Specifications\n"
                for k, v in self.specs.items():
                    md += f"- {k}: {v}\n"
                md += "\n"

            md += "## Design Discussion\n\n"
            for msg in self.conversation_history:
                role = "**User:**" if msg['role'] == 'user' else "**Assistant:**"
                md += f"{role}\n\n{msg['content']}\n\n---\n\n"

            return md


# Main entry point
def main():
    """Interactive design session."""
    print("Buck Converter Design Assistant")
    print("=" * 40)

    assistant = BuckConverterDesignAssistant()

    # Example design specs
    specs = {
        "v_in_min": 36,
        "v_in_max": 60,
        "v_out": 12,
        "i_out": 20,
        "f_sw": 200e3,
        "v_ripple": 50,  # mV
        "efficiency_target": 0.95,
        "t_amb": 85
    }

    # Start design
    print("\nStarting design with specifications:")
    for k, v in specs.items():
        print(f"  {k}: {v}")
    print()

    report = assistant.start_design(specs)
    print(report)

    # Interactive Q&A
    while True:
        print("\n" + "-" * 40)
        question = input("Question (or 'quit'): ").strip()

        if question.lower() in ['quit', 'exit', 'q']:
            break

        if not question:
            continue

        answer = assistant.ask_design_question(question)
        print("\n" + answer)


if __name__ == "__main__":
    main()
```

---

## Exercises

### Exercise 1: Build Datasheet KB (30 min)
1. Download 5 MOSFET datasheets (40-60V class)
2. Create metadata JSON file
3. Ingest into ChromaDB
4. Test search with various queries

### Exercise 2: Inductor Selector (45 min)
1. Create `InductorSelectionAssistant` similar to MOSFET selector
2. Search criteria: inductance, Isat, DCR, size
3. Test for 10µH, 25A application

### Exercise 3: Thermal Check (30 min)
1. Extend `DesignRuleChecker` for thermal analysis
2. Calculate junction temperature from losses
3. Check against Tj_max with margin

### Exercise 4: Multi-Doc Query (45 min)
1. Query across datasheet + app note for same topic
2. Compare information from multiple sources
3. Handle conflicting recommendations

### Exercise 5: Design Wizard (60 min)
1. Create step-by-step design flow
2. Each step uses RAG for guidance
3. Accumulate selections into complete BOM

---

## Pro Tips

1. **Chunk at section boundaries** - Preserves context for tables
2. **Include metadata** - Part numbers, page numbers for citation
3. **Deduplicate results** - Same content may appear multiple times
4. **Filter by doc type** - Datasheets vs app notes have different content
5. **Hybrid search** - Combine semantic + keyword for technical terms
6. **Cache embeddings** - Datasheets don't change often
7. **Version control** - Track which datasheet revision was indexed
8. **Validate extractions** - Cross-check critical parameters
9. **Log queries** - Understand what users need
10. **Update regularly** - New datasheets, revised app notes

---

## Next Steps

- **MCP Integration:** Expose RAG as MCP server for Claude Code
- **Module 7:** Use RAG in autonomous design agents
- **Production:** Add authentication, rate limiting, monitoring
