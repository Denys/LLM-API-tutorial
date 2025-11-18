# Python Primer for LLM API Development

**Duration:** 2-3 hours | **Level:** Beginner to Intermediate | **Prerequisites:** Basic Python syntax

## Overview

This express tutorial covers Python patterns essential for LLM API development. Skip what you know, focus on gaps.

**What this IS:** Targeted coverage of patterns used in Modules 1-9
**What this ISN'T:** Comprehensive Python course (see Part 2 for that)

## Learning Path

| Section | Duration | Topics | LLM API Relevance |
|---------|----------|--------|-------------------|
| [1. Environment & Config](./01-environment/) | 15 min | dotenv, env vars, config patterns | API key management |
| [2. JSON & Data Handling](./02-json-handling/) | 20 min | Parsing, nested structures, serialization | Request/response handling |
| [3. HTTP Fundamentals](./03-http-fundamentals/) | 20 min | httpx, headers, status codes | Understanding SDK internals |
| [4. Async/Await](./04-async-await/) | 25 min | asyncio, concurrent requests | Streaming, parallel calls |
| [5. Error Handling](./05-error-handling/) | 20 min | try/except, retries, custom exceptions | Rate limits, timeouts |
| [6. Type Hints & Pydantic](./06-type-hints-pydantic/) | 25 min | Annotations, validation, models | Structured outputs, tool schemas |
| [7. Generators & Streaming](./07-generators-streaming/) | 20 min | yield, iterators, async generators | Token streaming |
| [8. Decorators & Context Managers](./08-decorators-context-managers/) | 15 min | @decorator, with statements | Caching, retries, cleanup |

**Total:** ~2.5 hours (less if skipping familiar sections)

## Quick Assessment

Answer these to identify gaps:

```python
# 1. Can you explain what this does?
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

# 2. What's the output type?
import json
data = json.loads('{"model": "claude-3", "tokens": 100}')

# 3. What does 'async' enable here?
async def call_api():
    response = await client.messages.create(...)
    return response

# 4. What happens if the API returns 429?
try:
    response = client.messages.create(...)
except anthropic.RateLimitError as e:
    # ???

# 5. What's the purpose of this type hint?
def create_message(content: str, max_tokens: int = 1024) -> dict:
    ...

# 6. How does this stream tokens?
for chunk in client.messages.stream(...):
    yield chunk.text
```

**Score yourself:**
- 6/6 correct: Skip to [Module 1](../01-basic-api/)
- 4-5 correct: Skim sections, focus on exercises
- <4 correct: Work through all sections

## Setup

```bash
# From repository root
cd python-primer

# Create virtual environment (if not using global)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install python-dotenv httpx pydantic anthropic
```

## How to Use This Tutorial

### Each Section Contains:
1. **Concepts** - Brief explanation with LLM context
2. **Examples** - Working code you can run
3. **Exercise** - Practice problem
4. **Hints** - Graduated help (try without first)
5. **Pro Tips** - Production patterns

### Recommended Approach:
1. Read concepts (5 min)
2. Run examples, modify them (5 min)
3. Attempt exercise without hints (10 min)
4. Check hints only if stuck
5. Compare with solution

## File Structure

```
python-primer/
├── README.md                          # This file
├── 01-environment/
│   ├── README.md                      # Concepts + exercise
│   └── examples/
│       ├── config_basic.py
│       ├── config_advanced.py
│       └── exercise_solution.py
├── 02-json-handling/
│   └── ...
├── ...
└── exercises/
    ├── hints/
    │   └── HINTS.md                   # All hints in one place
    └── capstone/
        └── llm_client_mini.py         # Combines all concepts
```

## Capstone Mini-Project

After completing all sections, build a minimal LLM client that:
- Loads config from environment
- Makes API requests with proper error handling
- Streams responses
- Tracks token usage

See [exercises/capstone/](./exercises/capstone/) after completing sections.

## Dependencies

```txt
python-dotenv>=1.0.0
httpx>=0.25.0
pydantic>=2.0.0
anthropic>=0.34.0
```

## Next Steps

After this primer:
- **Ready for APIs:** Continue to [Module 1: Basic API](../01-basic-api/)
- **Need more Python:** See [Part 2: Deep Dive](./part2-deep-dive/) for OOP, Testing, Data Science, and Web Integration
- **Want practice:** Try the capstone mini-project

### Part 2: Deep Dive (Optional)

For deeper Python knowledge, choose one or more specialized tracks:

| Track | Topics | Duration |
|-------|--------|----------|
| [A. Deep Python](./part2-deep-dive/track-a-deep-python/) | OOP, Testing, Packaging | 3-4 hours |
| [B. Data Science](./part2-deep-dive/track-b-data-science/) | NumPy, Pandas | 2-3 hours |
| [C. Web Integration](./part2-deep-dive/track-c-web-integration/) | FastAPI, Databases | 3-4 hours |

---

## Quick Reference Card

### Environment
```python
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv("VAR", "default")
```

### JSON
```python
import json
data = json.loads(json_string)      # str -> dict
text = json.dumps(data, indent=2)   # dict -> str
```

### Async
```python
import asyncio
async def main():
    result = await async_function()
asyncio.run(main())
```

### Error Handling
```python
try:
    risky_operation()
except SpecificError as e:
    handle_error(e)
finally:
    cleanup()
```

### Type Hints
```python
def func(param: str, opt: int = 10) -> dict:
    ...
```

### Pydantic
```python
from pydantic import BaseModel
class Config(BaseModel):
    api_key: str
    max_tokens: int = 1024
```

### Generators
```python
def stream():
    for item in source:
        yield process(item)
```

### Decorators
```python
@retry(max_attempts=3)
def api_call():
    ...
```

### Context Managers
```python
with open("file.txt") as f:
    content = f.read()
```
