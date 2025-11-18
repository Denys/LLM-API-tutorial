# Quick Start - Module 9: Capstone Projects

Get started with your capstone project in 15 minutes!

## Choose Your Project

Pick the project that best matches your goals:

| Project | Time | Difficulty | Best For |
|---------|------|------------|----------|
| **1. Documentation Assistant** | 4-5 hrs | 🟢 Medium | RAG & Search |
| **2. Customer Support** | 5-6 hrs | 🟡 Med-High | Multi-Agent Systems |
| **3. Code Review** | 6-8 hrs | 🔴 Advanced | DevOps Tools |
| **4. Power Electronics** | 4-6 hrs | 🟡 Med-High | Engineering Apps |

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd 09-capstone
pip install -r requirements.txt
```

### 2. Set API Keys

```bash
# Copy template
cp .env.template .env

# Edit .env and add your keys
nano .env
```

Required:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Optional (for specific projects):
```
OPENAI_API_KEY=sk-your-key-here  # For Project 2, 3
DIGIKEY_CLIENT_ID=your-id        # For Project 4
DIGIKEY_CLIENT_SECRET=your-secret  # For Project 4
VOYAGE_API_KEY=your-key          # For RAG projects
```

### 3. Verify Setup

```bash
# Test imports
python -c "import anthropic, fastapi, chromadb; print('✅ All imports OK')"

# Test API key
python -c "from anthropic import Anthropic; Anthropic().messages.create(model='claude-3-5-haiku-20241022', max_tokens=10, messages=[{'role':'user','content':'hi'}]); print('✅ API key works')"
```

## Project Quick Starts

### Project 1: Documentation Assistant

**Goal:** Build RAG-powered docs search in 4 hours

**Quick Path:**
```bash
cd project-1-documentation-assistant

# Phase 1 (1h): Basic RAG
python starter_code/ingest_docs.py --dir /path/to/docs
python starter_code/simple_search.py "how to authenticate"

# Phase 2 (1.5h): Add Claude
python examples/rag_chat.py

# Phase 3 (1h): Build API
python api/main.py

# Phase 4 (0.5h): Test & docs
pytest tests/
```

**What You'll Build:**
- Document ingestion pipeline
- Vector search with ChromaDB
- Claude-powered Q&A
- REST API for queries

**Key Files:**
- `starter_code/` - Working examples
- `HINTS.md` - Step-by-step help
- `README.md` - Full specs

---

### Project 2: Customer Support System

**Goal:** Multi-agent support system in 5 hours

**Quick Path:**
```bash
cd project-2-customer-support

# Phase 1 (1.5h): Intent classification
python agents/intent_classifier.py

# Phase 2 (1.5h): Knowledge base agent
python agents/kb_agent.py

# Phase 3 (1h): Ticket management
python agents/ticket_agent.py

# Phase 4 (1h): Orchestrator
python main.py
```

**What You'll Build:**
- Intent classification agent
- RAG knowledge base agent
- Ticket creation/routing
- Multi-agent orchestrator
- Analytics dashboard

**Key Files:**
- `agents/` - Agent implementations
- `HINTS.md` - Agent patterns
- `docker-compose.yml` - Full deployment

---

### Project 3: Code Review System

**Goal:** Automated code review in 6 hours

**Advanced! Start here if you're experienced.

**Quick Path:**
```bash
cd project-3-code-review

# Phase 1 (2h): GitHub integration
python integrations/github_client.py

# Phase 2 (2h): Code analysis
python analyzers/security_analyzer.py
python analyzers/style_analyzer.py

# Phase 3 (1h): Review agent
python agents/reviewer.py

# Phase 4 (1h): MCP server
python mcp_server/code_review_server.py
```

**What You'll Build:**
- GitHub PR integration
- AST-based code analysis
- Security vulnerability detection
- AI-powered review comments
- MCP server for IDE

**Key Files:**
- `analyzers/` - Static analysis
- `agents/` - Review agent
- `mcp_server/` - IDE integration
- `HINTS.md` - Advanced techniques

---

### Project 4: Power Electronics Assistant

**Goal:** Complete design tool in 4-6 hours

**Recommended! Well-structured and practical.**

**Quick Path:**
```bash
cd project-4-power-electronics

# Phase 1 (1.5h): Core calculations
python starter_code/calculators/buck.py
pytest tests/test_buck.py

# Phase 2 (1h): Component selection
python starter_code/components/selector.py

# Phase 3 (1.5h): Multi-agent review
python agents/thermal_agent.py
python agents/design_orchestrator.py

# Phase 4 (1h): API & deploy
uvicorn api.main:app --reload
docker-compose up
```

**What You'll Build:**
- Multi-topology converter design
- Real-time component selection
- Thermal analysis
- Multi-agent design review
- BOM generation
- Documentation export

**Key Files:**
- `starter_code/` - Working calculators
- `models.py` - Data structures
- `HINTS.md` - Detailed solutions
- `README.md` - Complete guide

---

## Development Workflow

### Recommended Approach

1. **Day 1: Core Functionality** (2-3 hours)
   - Get basic features working
   - Focus on one flow end-to-end
   - Don't worry about perfection

2. **Day 2: Integration** (2-3 hours)
   - Add multi-module integration
   - Implement error handling
   - Add tests

3. **Day 3: Production** (1-2 hours)
   - Docker deployment
   - Monitoring
   - Documentation

### Testing Strategy

Test incrementally:

```bash
# Unit tests
pytest tests/test_module.py -v

# Integration tests
pytest tests/test_integration.py -v

# With coverage
pytest --cov=. --cov-report=html
```

### Debugging Tips

Use logging:
```python
import structlog
logger = structlog.get_logger()

logger.info("processing_request", user_id=123, query="test")
```

Use breakpoints:
```python
import pdb; pdb.set_trace()  # Pause here
```

Check hints:
```bash
# Each project has detailed hints
cat project-X/HINTS.md | grep "your issue"
```

## Common Issues

### Import Errors

```bash
# Make sure you're in the right directory
cd 09-capstone

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### API Key Errors

```bash
# Verify .env file exists
cat .env

# Test API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ANTHROPIC_API_KEY'))"
```

### Vector Database Errors

```bash
# Reset ChromaDB
rm -rf chroma_db/

# Reingest documents
python ingest_docs.py
```

## Hints System

Each project has comprehensive hints:

### General Hints
- `hints/setup-hints.md` - Setup issues
- `hints/rag-hints.md` - RAG implementation
- `hints/agent-hints.md` - Agent patterns
- `hints/troubleshooting.md` - Common problems

### Project-Specific
- `project-X/HINTS.md` - Detailed solutions
- `project-X/README.md` - Full specifications
- `project-X/starter_code/` - Working code

### How to Use Hints

1. **Try First** - Attempt to solve yourself
2. **Check General Hints** - Common patterns
3. **Check Project Hints** - Specific solutions
4. **Review Examples** - See working code
5. **Ask Specific Questions** - Get targeted help

## Success Metrics

You're on track when you can:

### After 2 Hours
- [ ] Core functionality working
- [ ] Basic test passes
- [ ] One end-to-end flow works

### After 4 Hours
- [ ] Major features implemented
- [ ] Integration with ≥3 modules
- [ ] Basic error handling
- [ ] Some tests passing

### After 6 Hours
- [ ] All core features done
- [ ] Production error handling
- [ ] Tests at 60%+ coverage
- [ ] Documentation started
- [ ] Deployment working

### Project Complete
- [ ] All requirements met
- [ ] Tests passing (60%+ coverage)
- [ ] Docker deployment works
- [ ] Documentation complete
- [ ] Self-evaluation score ≥80%

## Getting Help

### Before Asking

1. Check project HINTS.md
2. Review relevant modules (1-8)
3. Search existing code examples
4. Try debugging systematically

### Resources

- **Project README** - Full specifications
- **Project HINTS** - Step-by-step solutions
- **Starter Code** - Working examples
- **Module Docs** - Modules 1-8 for reference
- **Evaluation Rubric** - Know what's expected

## Next Steps

1. **Choose Project** - Pick one that excites you
2. **Set Up Environment** - Install dependencies
3. **Read Project README** - Understand requirements
4. **Check Hints** - Skim to know what's available
5. **Start Building** - Begin with Phase 1
6. **Test Incrementally** - Don't wait until the end
7. **Deploy** - Get it running in production
8. **Evaluate** - Use the rubric
9. **Iterate** - Improve based on feedback

## Time-Saving Tips

1. **Use Starter Code** - Don't start from scratch
2. **Copy from Modules** - Reuse patterns from 1-8
3. **Focus on Core** - Get basics working first
4. **Test Early** - Catch issues quickly
5. **Use Hints Liberally** - They're there to help
6. **Deploy Early** - Don't wait for perfection

## Pro Tips

### For Speed
- Use Haiku for testing (faster, cheaper)
- Cache aggressively
- Mock external APIs during development
- Write tests first for clarity

### For Quality
- Type hint everything
- Log all operations
- Handle errors explicitly
- Document as you go

### For Learning
- Understand before copying
- Try variants of solutions
- Read related module docs
- Experiment with improvements

---

**Ready to build something amazing?**

```bash
# Choose your project
cd project-4-power-electronics  # Recommended

# Start building!
python starter_code/calculators/buck.py
```

**Good luck with your capstone project!** 🚀
