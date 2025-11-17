# Sample Documents for Tutorial Exercises

This directory contains sample documents used throughout the tutorial for various exercises, particularly for RAG (Retrieval-Augmented Generation) in Module 4.

## Files

### 1. `python_basics.txt`
**Purpose:** General knowledge document about Python programming
**Size:** ~2,000 tokens
**Use Cases:**
- RAG exercises in Module 4
- Testing document chunking
- Question-answering demonstrations
- Context injection examples

**Sample Questions:**
- "What are the key features of Python?"
- "What is the difference between lists and dictionaries in Python?"
- "Name some common Python libraries and their purposes."

---

### 2. `ai_ml_concepts.txt`
**Purpose:** Comprehensive overview of AI and Machine Learning
**Size:** ~3,000 tokens
**Use Cases:**
- RAG pipeline testing
- Multi-document retrieval
- Hierarchical chunking
- Topic-based search

**Sample Questions:**
- "What is the difference between supervised and unsupervised learning?"
- "What are Large Language Models?"
- "What are the main types of neural network architectures?"

---

### 3. `climate_change_facts.txt`
**Purpose:** Factual information about climate change
**Size:** ~3,500 tokens
**Use Cases:**
- RAG with citations
- Factual question answering
- Source attribution
- Semantic search demonstration

**Sample Questions:**
- "What are the main causes of climate change?"
- "How much has global temperature risen?"
- "What are some solutions to climate change?"

---

## Usage Examples

### Basic RAG Query (Module 4)

```python
# Load document
with open('assets/sample-documents/python_basics.txt') as f:
    content = f.read()

# Create chunks
chunks = create_chunks(content, chunk_size=500)

# Generate embeddings
embeddings = embed_chunks(chunks)

# Query
query = "What are Python's key features?"
results = search(query, embeddings)

# Answer with Claude
answer = claude_answer(query, results)
```

### Multi-Document Search

```python
# Load all documents
documents = [
    'python_basics.txt',
    'ai_ml_concepts.txt',
    'climate_change_facts.txt'
]

# Index them
for doc in documents:
    index_document(doc)

# Search across all
results = search_all("machine learning with Python")
```

---

## Creating Your Own Test Documents

### Guidelines:

1. **Size:** Aim for 1,000-5,000 tokens per document
2. **Structure:** Use clear sections and headings
3. **Content:** Include factual, verifiable information
4. **Diversity:** Mix different topics and writing styles

### Format:

```
Title

Section 1: Introduction
Brief overview...

Section 2: Main Content
Detailed information...
- Bullet points
- Lists
- Examples

Section 3: Conclusion
Summary...
```

---

## Token Estimates

| File | Approximate Tokens | Cost to Embed* |
|------|-------------------|----------------|
| python_basics.txt | ~2,000 | $0.0005 |
| ai_ml_concepts.txt | ~3,000 | $0.0007 |
| climate_change_facts.txt | ~3,500 | $0.0008 |

*Using Voyage AI or similar embedding service

---

## Adding More Documents

To add your own documents for practice:

1. Create a `.txt` file in this directory
2. Add structured content (2,000+ tokens recommended)
3. Update this README with file description
4. Test with the RAG examples in Module 4

**Suggested Topics:**
- Company handbook or policies
- Technical documentation
- Product information
- Historical events
- Scientific concepts
- Legal documents (simplified)

---

## Notes

- These documents are intentionally concise for tutorial purposes
- Real-world RAG systems typically handle much larger documents
- Use these as starting points for your own projects
- Check Module 4 for advanced document processing techniques

---

## Related Modules

- **Module 4:** RAG implementation using these documents
- **Module 2:** Token counting with sample texts
- **Module 7:** Agent systems that search these documents

---

**Last Updated:** November 2025
