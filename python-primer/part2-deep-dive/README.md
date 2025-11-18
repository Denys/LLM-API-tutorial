# Python Primer Part 2: Deep Dive

**Prerequisites:** Complete [Part 1](../README.md) or pass the assessment
**Choose Your Track:** Select based on your goals

## Overview

Part 2 offers three specialized tracks. Complete one or more based on your needs.

| Track | Focus | Duration | Best For |
|-------|-------|----------|----------|
| [A. Deep Python](#track-a-deep-python) | OOP, Testing, Packaging | 3-4 hours | Building production libraries |
| [B. Data Science](#track-b-data-science) | NumPy, Pandas | 2-3 hours | Embeddings, analytics, RAG |
| [C. Web Integration](#track-c-web-integration) | FastAPI, Databases | 3-4 hours | Building LLM-powered APIs |

## Track Selection Guide

### Choose Track A if you want to:
- Build reusable LLM client libraries
- Write comprehensive tests for AI applications
- Distribute your tools as packages
- Apply design patterns to complex AI systems

### Choose Track B if you want to:
- Work with vector embeddings efficiently
- Analyze token usage and costs
- Build RAG systems with similarity search
- Process and visualize LLM metrics

### Choose Track C if you want to:
- Build REST APIs powered by LLMs
- Create streaming endpoints
- Store conversations in databases
- Deploy production AI services

---

## Track A: Deep Python

**Duration:** 3-4 hours | **Level:** Intermediate-Advanced

### Sections

| Section | Topics | LLM API Relevance |
|---------|--------|-------------------|
| [1. OOP](./track-a-deep-python/01-oop/) | Classes, patterns, composition | Extensible client libraries |
| [2. Testing](./track-a-deep-python/02-testing/) | pytest, mocking, async tests | Reliable AI applications |
| [3. Packaging](./track-a-deep-python/03-packaging/) | pyproject.toml, distribution | Shareable tools |

### What You'll Build
- Abstract LLM provider interface
- Complete test suite with mocked APIs
- Installable package with CLI

---

## Track B: Data Science

**Duration:** 2-3 hours | **Level:** Intermediate

### Sections

| Section | Topics | LLM API Relevance |
|---------|--------|-------------------|
| [1. NumPy](./track-b-data-science/01-numpy/) | Arrays, vectors, math | Embeddings, similarity |
| [2. Pandas](./track-b-data-science/02-pandas/) | DataFrames, analysis | Usage tracking, reporting |

### What You'll Build
- Embedding similarity search
- Token usage analytics dashboard
- Cost optimization reports

---

## Track C: Web Integration

**Duration:** 3-4 hours | **Level:** Intermediate-Advanced

### Sections

| Section | Topics | LLM API Relevance |
|---------|--------|-------------------|
| [1. FastAPI](./track-c-web-integration/01-fastapi/) | Routes, streaming, middleware | LLM-powered APIs |
| [2. Database](./track-c-web-integration/02-database/) | SQLAlchemy, caching | Conversation storage |

### What You'll Build
- Streaming chat API endpoint
- Conversation history storage
- Response caching system

---

## Exercise Levels

Each section includes exercises at three levels:

| Level | Description | Time |
|-------|-------------|------|
| **Simple** | Apply basic concept | 5-10 min |
| **Intermediate** | Combine multiple concepts | 15-20 min |
| **Advanced** | Production-ready implementation | 30-45 min |

All exercises include:
- Clear requirements
- Graduated hints
- Complete solutions
- Pro tips

---

## Dependencies

```bash
# Track A: Deep Python
pip install pytest pytest-asyncio pytest-mock build twine

# Track B: Data Science
pip install numpy pandas matplotlib

# Track C: Web Integration
pip install fastapi uvicorn sqlalchemy aiosqlite
```

Or install all:
```bash
pip install -r requirements.txt
```

---

## Recommended Path

1. **New to Python OOP?** → Track A first
2. **Building RAG systems?** → Track B first
3. **Deploying APIs?** → Track C first
4. **Full stack AI dev?** → All three tracks

After completing your chosen track(s), proceed to [Module 1: Basic API](../../01-basic-api/).
