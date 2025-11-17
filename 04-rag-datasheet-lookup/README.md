# Module 4: RAG - Datasheet Lookup & Knowledge Retrieval

**Duration:** 3-4 hours
**Difficulty:** Advanced
**Prerequisites:** Modules 1-3 completed

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Understand Retrieval-Augmented Generation (RAG) architecture
- ✅ Parse and index technical datasheets
- ✅ Create vector embeddings for semantic search
- ✅ Build a component specification lookup system
- ✅ Retrieve relevant application notes automatically
- ✅ Integrate RAG with the Power Electronics Assistant
- ✅ Implement caching and optimization strategies
- ✅ Use both Claude and OpenAI embeddings

## What is RAG?

**Retrieval-Augmented Generation (RAG)** combines:
1. **Information Retrieval** - Finding relevant documents from a knowledge base
2. **Language Generation** - Using LLMs to generate responses based on retrieved context

```
User Query → Retrieve Relevant Docs → Add to Context → LLM → Response
```

### Why RAG for Power Electronics?

Traditional LLMs have limitations:
- ❌ Training data cutoff (no recent datasheets)
- ❌ Cannot access proprietary component databases
- ❌ May hallucinate component specifications
- ❌ Limited knowledge of niche components

RAG solves this by:
- ✅ Accessing up-to-date datasheets
- ✅ Retrieving exact specifications
- ✅ Providing source references
- ✅ Supporting custom component libraries

---

## RAG Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      RAG SYSTEM                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. INDEXING PHASE (One-time setup)                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Datasheets  │ → │  Text         │ → │  Vector       │  │
│  │  App Notes   │    │  Chunking     │    │  Embeddings   │  │
│  │  Designs     │    │               │    │               │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                   │           │
│                                                   ▼           │
│                                          ┌──────────────┐    │
│                                          │  Vector DB   │    │
│                                          │  (ChromaDB)  │    │
│                                          └──────────────┘    │
│                                                               │
│  2. QUERY PHASE (Runtime)                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  User Query  │ → │  Embed        │ → │  Similarity   │  │
│  │              │    │  Query        │    │  Search       │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                   │           │
│                                                   ▼           │
│                                          ┌──────────────┐    │
│                                          │  Top-K Docs  │    │
│                                          └──────────────┘    │
│                                                   │           │
│                                                   ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Build       │ → │  Send to      │ → │  Response     │  │
│  │  Context     │    │  LLM          │    │               │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Exercise 4.1: Understanding Vector Embeddings

### What are Embeddings?

Embeddings convert text into numerical vectors that capture semantic meaning:

```python
"MOSFET for motor control" → [0.23, -0.45, 0.67, ..., 0.12]  # 1536 dimensions
"FET motor driver"         → [0.21, -0.43, 0.65, ..., 0.15]  # Similar vector!
"LED resistor"             → [-0.82, 0.34, -0.21, ..., 0.03] # Different vector
```

Similar concepts have similar vectors (measured by cosine similarity).

### Creating Embeddings

**Claude (Voyage AI):**
```python
import voyageai

vo = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))

# Embed text
result = vo.embed(
    ["MOSFET IRF540N datasheet specifications"],
    model="voyage-2"
)

embedding = result.embeddings[0]  # 1024-dim vector
```

**OpenAI:**
```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Embed text
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="MOSFET IRF540N datasheet specifications"
)

embedding = response.data[0].embedding  # 1536-dim vector
```

### Embedding Models Comparison

| Model | Provider | Dimensions | Cost (per 1M tokens) | Quality |
|-------|----------|-----------|---------------------|---------|
| `voyage-2` | Voyage AI | 1024 | $0.10 | Excellent |
| `text-embedding-3-small` | OpenAI | 1536 | $0.02 | Good |
| `text-embedding-3-large` | OpenAI | 3072 | $0.13 | Excellent |
| `text-embedding-ada-002` | OpenAI | 1536 | $0.10 | Good (legacy) |

---

## Exercise 4.2: Basic RAG Implementation

### Step 1: Install Dependencies

```bash
pip install chromadb voyageai pypdf sentence-transformers
```

### Step 2: Create Vector Database

**Python:**
```python
import chromadb
from chromadb.config import Settings

# Initialize ChromaDB
client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db"
))

# Create collection for datasheets
collection = client.create_collection(
    name="datasheets",
    metadata={"description": "Power electronics component datasheets"}
)

# Add documents
collection.add(
    documents=[
        "IRF540N: N-Channel MOSFET, 100V, 33A, 44mΩ Rds(on)",
        "LM7805: Voltage Regulator, 5V output, 1.5A max, TO-220 package"
    ],
    metadatas=[
        {"component": "IRF540N", "type": "MOSFET", "manufacturer": "Infineon"},
        {"component": "LM7805", "type": "Regulator", "manufacturer": "TI"}
    ],
    ids=["irf540n", "lm7805"]
)

# Query
results = collection.query(
    query_texts=["MOSFET for 12V 5A motor driver"],
    n_results=2
)

print(results['documents'][0])  # Best match
```

### Step 3: Integration with LLM

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# User query
user_query = "Recommend a MOSFET for 12V 5A motor driver"

# Retrieve relevant documents
results = collection.query(
    query_texts=[user_query],
    n_results=3
)

# Build context from retrieved docs
context = "\n\n".join(results['documents'][0])

# Send to Claude with context
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": f"""Based on the following component datasheets:

{context}

{user_query}

Provide a specific recommendation with justification."""
    }]
)

print(message.content[0].text)
```

---

## Exercise 4.3: Datasheet Parsing

### Parsing PDF Datasheets

**Python:**
```python
import pypdf
import re

def parse_datasheet(pdf_path: str) -> dict:
    """Extract key information from datasheet PDF."""

    with open(pdf_path, 'rb') as file:
        pdf = pypdf.PdfReader(file)

        text = ""
        for page in pdf.pages:
            text += page.extract_text()

    # Extract specifications using regex
    specs = {
        "part_number": extract_part_number(text),
        "voltage_rating": extract_voltage(text),
        "current_rating": extract_current(text),
        "resistance": extract_resistance(text),
        "package": extract_package(text)
    }

    return specs

def extract_voltage(text: str) -> str:
    """Extract voltage ratings."""
    match = re.search(r'V[DS]{1,2}.*?(\d+)\s*V', text, re.IGNORECASE)
    return match.group(1) + "V" if match else "Unknown"

# Example usage
specs = parse_datasheet("datasheets/IRF540N.pdf")
print(f"Voltage Rating: {specs['voltage_rating']}")
```

### Structured Datasheet Chunking

```python
def chunk_datasheet(text: str, chunk_size: int = 500) -> list:
    """
    Chunk datasheet intelligently by sections.

    Better than simple text splitting - preserves context.
    """

    # Split by common datasheet sections
    sections = {
        "Features": [],
        "Specifications": [],
        "Applications": [],
        "Pin Configuration": [],
        "Operating Conditions": [],
        "Electrical Characteristics": []
    }

    current_section = None

    for line in text.split('\n'):
        # Detect section headers
        for section_name in sections.keys():
            if section_name.lower() in line.lower():
                current_section = section_name
                break

        if current_section:
            sections[current_section].append(line)

    # Create chunks with section context
    chunks = []
    for section_name, lines in sections.items():
        if lines:
            chunk_text = f"[{section_name}]\n" + "\n".join(lines)
            chunks.append({
                "text": chunk_text,
                "section": section_name
            })

    return chunks
```

---

## Exercise 4.4: Component Specification Lookup

### Building a Component Database

**File:** `examples/component_database.py`

```python
class ComponentDatabase:
    """Vector database for component specifications."""

    def __init__(self, db_path: str = "./component_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="components",
            metadata={"description": "Power electronics components"}
        )

    def add_component(self, part_number: str, specs: dict):
        """Add component to database with embeddings."""

        # Create searchable text
        doc_text = f"""
Part Number: {part_number}
Type: {specs.get('type', 'Unknown')}
Voltage Rating: {specs.get('voltage', 'N/A')}
Current Rating: {specs.get('current', 'N/A')}
Package: {specs.get('package', 'N/A')}
Manufacturer: {specs.get('manufacturer', 'N/A')}
Applications: {specs.get('applications', 'N/A')}
Key Features: {specs.get('features', 'N/A')}
        """

        self.collection.add(
            documents=[doc_text],
            metadatas=[specs],
            ids=[part_number]
        )

    def search(self, query: str, n_results: int = 5):
        """Search for components matching query."""
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

# Example usage
db = ComponentDatabase()

# Add MOSFETs
db.add_component("IRF540N", {
    "type": "N-Channel MOSFET",
    "voltage": "100V",
    "current": "33A",
    "rds_on": "44mΩ",
    "package": "TO-220",
    "manufacturer": "Infineon",
    "applications": "Motor control, switching",
    "features": "Low on-resistance, fast switching"
})

# Search
results = db.search("MOSFET for 24V 10A motor driver")
print(results['documents'][0])
```

---

## Exercise 4.5: Application Note Retrieval

### Indexing Application Notes

Application notes contain valuable design patterns and examples.

**Structure:**
```
data/
├── application-notes/
│   ├── AN001_buck_converter_design.txt
│   ├── AN002_mosfet_gate_drive.txt
│   ├── AN003_thermal_management.txt
│   └── AN004_pcb_layout_tips.txt
```

**Python:**
```python
import os
from pathlib import Path

def index_application_notes(notes_dir: str):
    """Index all application notes."""

    client = chromadb.PersistentClient(path="./app_notes_db")
    collection = client.get_or_create_collection(name="application_notes")

    notes_path = Path(notes_dir)

    for note_file in notes_path.glob("*.txt"):
        with open(note_file, 'r') as f:
            content = f.read()

        # Extract metadata from filename
        note_id = note_file.stem  # e.g., "AN001_buck_converter_design"

        collection.add(
            documents=[content],
            metadatas=[{
                "filename": note_file.name,
                "topic": extract_topic(note_file.name)
            }],
            ids=[note_id]
        )

    return collection

def search_application_notes(query: str, collection):
    """Find relevant application notes."""
    results = collection.query(
        query_texts=[query],
        n_results=3
    )

    return results

# Example
collection = index_application_notes("data/application-notes")
results = search_application_notes(
    "How to design gate driver for MOSFET?",
    collection
)

for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
    print(f"Found in: {metadata['filename']}")
    print(f"Excerpt: {doc[:200]}...\n")
```

---

## Exercise 4.6: Enhanced Power Electronics Assistant with RAG

### Integration Architecture

```python
class RAGPowerElectronicsAssistant:
    """Enhanced assistant with datasheet lookup."""

    def __init__(self, provider: str = "claude"):
        # Initialize LLM
        self.provider = provider
        if provider == "claude":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-5-sonnet-20241022"
        else:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4-turbo"

        # Initialize databases
        self.component_db = ComponentDatabase()
        self.appnote_db = chromadb.PersistentClient(
            path="./app_notes_db"
        ).get_collection("application_notes")

    def chat(self, user_query: str) -> str:
        """Chat with RAG-enhanced context."""

        # Retrieve relevant components
        component_results = self.component_db.search(user_query, n_results=3)

        # Retrieve relevant application notes
        appnote_results = self.appnote_db.query(
            query_texts=[user_query],
            n_results=2
        )

        # Build context
        context = "COMPONENT DATABASE:\n"
        for doc in component_results['documents'][0]:
            context += f"\n{doc}\n"

        context += "\n\nAPPLICATION NOTES:\n"
        for doc in appnote_results['documents'][0]:
            context += f"\n{doc[:500]}...\n"

        # Send to LLM with context
        if self.provider == "claude":
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=f"""You are a power electronics expert with access to:
1. Component database (datasheets, specs)
2. Application notes (design guides)

Use the provided context to give accurate, specific recommendations.""",
                messages=[{
                    "role": "user",
                    "content": f"""Context from databases:

{context}

User question: {user_query}

Provide detailed answer with component recommendations."""
                }]
            )
            return message.content[0].text

        else:  # OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": "You are a power electronics expert with access to component databases and application notes."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
                ]
            )
            return response.choices[0].message.content
```

**See:** `examples/rag_assistant.py` for complete implementation.

---

## Advanced Topics

### Hybrid Search (Keyword + Semantic)

Combine traditional keyword search with vector similarity:

```python
def hybrid_search(query: str, collection, alpha: float = 0.5):
    """
    Hybrid search combining:
    - Vector similarity (semantic)
    - Keyword matching (BM25)

    alpha: weight for semantic search (1.0 = pure semantic)
    """

    # Semantic search
    semantic_results = collection.query(
        query_texts=[query],
        n_results=10
    )

    # Keyword search
    keyword_results = collection.query(
        query_texts=[query],
        n_results=10,
        where_document={"$contains": extract_keywords(query)}
    )

    # Combine and re-rank
    combined = merge_results(semantic_results, keyword_results, alpha)
    return combined
```

### Re-ranking with Cross-Encoders

Improve retrieval quality:

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

def rerank_results(query: str, documents: list) -> list:
    """Re-rank documents for better relevance."""

    # Score each document
    pairs = [[query, doc] for doc in documents]
    scores = model.predict(pairs)

    # Sort by score
    ranked = sorted(
        zip(documents, scores),
        key=lambda x: x[1],
        reverse=True
    )

    return [doc for doc, score in ranked]
```

### Caching Retrieved Context

Reduce API costs with context caching:

```python
# Use Claude's prompt caching for retrieved context
cached_context = [{
    "type": "text",
    "text": retrieved_docs_text,
    "cache_control": {"type": "ephemeral"}  # Cache for 5 min
}]

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    system=cached_context,  # Cached!
    messages=[{"role": "user", "content": user_query}]
)
```

---

## Real-World Example: Complete Datasheet RAG System

**See:** `examples/complete_rag_system.py`

Features:
- PDF datasheet parsing
- Automatic spec extraction
- Vector database with ChromaDB
- Semantic search
- Integration with Claude/OpenAI
- Caching for performance
- Cost tracking

---

## Performance Optimization

### 1. Chunking Strategy

```python
# ❌ Poor: Fixed-size chunking
chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]

# ✅ Better: Semantic chunking
chunks = split_by_section(text)  # Preserve context

# ✅ Best: Recursive chunking with overlap
chunks = recursive_chunk(text, size=500, overlap=50)
```

### 2. Embedding Batch Processing

```python
# ❌ Slow: One at a time
for doc in documents:
    embedding = embed(doc)

# ✅ Fast: Batch processing
embeddings = embed(documents)  # All at once
```

### 3. Vector Database Optimization

```python
# Use appropriate distance metric
collection = client.create_collection(
    name="datasheets",
    metadata={"hnsw:space": "cosine"}  # cosine, l2, or ip
)

# Index for faster search
collection.create_index()
```

---

## Cost Analysis

### RAG System Costs

| Operation | Provider | Cost |
|-----------|----------|------|
| Embed 1M tokens | OpenAI (small) | $0.02 |
| Embed 1M tokens | Voyage AI | $0.10 |
| Query (with context) | Claude Sonnet | $3-15/1M |
| Query (with context) | GPT-4 | $10-30/1M |

**Example: 1000 component lookups**
- Embedding cost: ~$0.01 (one-time)
- Query cost: ~$0.03 (with caching)
- **Total: ~$0.04**

Much cheaper than training custom models!

---

## Self-Assessment

Before moving to Module 5, ensure you can:

- [ ] Explain RAG architecture and benefits
- [ ] Create vector embeddings from text
- [ ] Set up and query ChromaDB
- [ ] Parse PDF datasheets
- [ ] Build a component specification database
- [ ] Integrate RAG with LLM applications
- [ ] Optimize for performance and cost
- [ ] Implement caching strategies

---

## Additional Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Voyage AI Models](https://docs.voyageai.com/)
- [RAG Best Practices](https://www.anthropic.com/index/retrieval-augmented-generation-rag)

---

## Next Steps

Ready to integrate multiple data sources? Continue to:

**[Module 5: MCP - Model Context Protocol →](../05-mcp-integration/README.md)**

Learn about standardized tool integration and SPICE simulation!

---

**Questions or issues?** Open a GitHub issue or check the examples.
