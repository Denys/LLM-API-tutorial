# Module 8: Production & Best Practices

Take your LLM applications from prototype to production with professional deployment, monitoring, and maintenance strategies.

## Table of Contents

1. [Overview](#overview)
2. [Production Architecture](#production-architecture)
3. [Encapsulation Patterns](#encapsulation-patterns)
4. [Standalone Applications](#standalone-applications)
5. [Deployment Strategies](#deployment-strategies)
6. [Monitoring & Observability](#monitoring--observability)
7. [Security Best Practices](#security-best-practices)
8. [Performance Optimization](#performance-optimization)
9. [Cost Management](#cost-management)
10. [Testing Strategies](#testing-strategies)
11. [Examples](#examples)
12. [Exercises](#exercises)

## Overview

This module covers the critical aspects of deploying LLM applications to production:

- **Production-Ready Code:** Error handling, logging, graceful degradation
- **Encapsulation:** Clean APIs, modular design, reusable components
- **Deployment:** Docker, Kubernetes, cloud platforms
- **Monitoring:** Logging, metrics, tracing, alerting
- **Security:** API key management, rate limiting, input validation
- **Performance:** Caching, batching, prompt optimization
- **Cost:** Token tracking, budget controls, cost optimization
- **Testing:** Unit tests, integration tests, load tests

### What You'll Build

1. **Production Chat Application** - Full-featured chat with monitoring
2. **Standalone Agent System** - Deployable autonomous agent
3. **API Wrapper Service** - Encapsulated LLM service
4. **Monitoring Dashboard** - Real-time metrics and logging
5. **Docker Deployment** - Containerized applications
6. **CI/CD Pipeline** - Automated testing and deployment

## Production Architecture

### Typical Production Stack

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                       │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴──────────┬─────────────┐
         │                      │             │
┌────────▼────────┐  ┌─────────▼────────┐   │
│  Application    │  │   Application    │   │
│  Instance 1     │  │   Instance 2     │  ...
└────────┬────────┘  └──────────┬───────┘
         │                      │
         └──────────┬───────────┘
                    │
         ┌──────────▼──────────┐
         │   Cache Layer       │
         │   (Redis)           │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │   Database          │
         │   (PostgreSQL)      │
         └─────────────────────┘

         ┌─────────────────────┐
         │   Monitoring        │
         │   (Prometheus)      │
         └─────────────────────┘

         ┌─────────────────────┐
         │   Logging           │
         │   (ELK Stack)       │
         └─────────────────────┘
```

### Key Components

1. **Application Layer**
   - FastAPI/Flask web servers
   - Worker processes for async tasks
   - Health check endpoints

2. **Cache Layer**
   - Redis for response caching
   - Prompt cache for repeated queries
   - Session management

3. **Database Layer**
   - PostgreSQL for persistent data
   - Conversation history
   - User management
   - Analytics data

4. **Monitoring Layer**
   - Prometheus for metrics
   - Grafana for visualization
   - ELK stack for logging
   - Sentry for error tracking

## Encapsulation Patterns

### 1. Client Wrapper Pattern

Encapsulate AI provider details behind clean interface:

```python
class LLMClient:
    """Abstract LLM client interface."""

    def __init__(self, config: Config):
        self.config = config
        self._client = self._initialize_client()

    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """Send chat messages and get response."""
        pass

    @abstractmethod
    def stream_chat(self, messages: List[Dict], **kwargs) -> Iterator[str]:
        """Stream chat response."""
        pass


class ClaudeClient(LLMClient):
    """Claude-specific implementation."""

    def chat(self, messages: List[Dict], **kwargs) -> str:
        response = self._client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            messages=messages,
            **kwargs
        )
        return response.content[0].text


class UnifiedLLMClient:
    """Unified client supporting multiple providers."""

    def __init__(self, provider: str = "claude"):
        self.client = self._create_client(provider)

    def chat(self, messages: List[Dict]) -> str:
        return self.client.chat(messages)
```

**Benefits:**
- Provider-agnostic application code
- Easy provider switching
- Simplified testing with mocks
- Centralized configuration

### 2. Service Layer Pattern

Separate business logic from AI integration:

```python
class PowerElectronicsService:
    """Business logic for power electronics calculations."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.calculator = ComponentCalculator()

    def design_converter(self, specs: ConverterSpecs) -> ConverterDesign:
        """Design converter with AI assistance."""

        # Step 1: Calculate component values
        components = self.calculator.calculate(specs)

        # Step 2: Get AI recommendations
        recommendations = self.llm.chat([
            {"role": "user", "content": f"Review design: {components}"}
        ])

        # Step 3: Combine results
        return ConverterDesign(
            components=components,
            recommendations=recommendations,
            specs=specs
        )
```

**Benefits:**
- Clear separation of concerns
- Easier testing
- Reusable business logic
- Better maintainability

### 3. Repository Pattern

Encapsulate data access:

```python
class ConversationRepository:
    """Manage conversation persistence."""

    def __init__(self, db_connection):
        self.db = db_connection

    def save_conversation(self, conversation: Conversation):
        """Save conversation to database."""
        self.db.execute(
            "INSERT INTO conversations (id, user_id, messages) VALUES (?, ?, ?)",
            (conversation.id, conversation.user_id,
             json.dumps(conversation.messages))
        )

    def get_conversation(self, conversation_id: str) -> Conversation:
        """Retrieve conversation by ID."""
        row = self.db.query(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        return Conversation.from_dict(row)
```

### 4. Factory Pattern

Create objects based on configuration:

```python
class LLMFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create(provider: str, config: Dict) -> LLMClient:
        """Create LLM client based on provider."""

        if provider == "claude":
            return ClaudeClient(config)
        elif provider == "openai":
            return OpenAIClient(config)
        elif provider == "gemini":
            return GeminiClient(config)
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Usage
client = LLMFactory.create(
    provider=os.getenv("LLM_PROVIDER", "claude"),
    config=load_config()
)
```

## Standalone Applications

### Chat Application Architecture

```python
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

app = FastAPI(title="Power Electronics Chat")

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.post("/chat")
async def chat(msg: ChatMessage):
    """Chat endpoint with conversation management."""

    # Get or create conversation
    conversation = conversation_service.get_or_create(
        msg.conversation_id
    )

    # Add user message
    conversation.add_message("user", msg.message)

    # Get AI response
    response = llm_service.chat(
        messages=conversation.messages,
        system_prompt=POWER_ELECTRONICS_PROMPT
    )

    # Add assistant response
    conversation.add_message("assistant", response)

    # Save conversation
    conversation_repo.save(conversation)

    # Track metrics
    metrics.record_chat(
        tokens=response.usage.total_tokens,
        latency=response.latency
    )

    return {
        "response": response.text,
        "conversation_id": conversation.id,
        "tokens_used": response.usage.total_tokens
    }

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Stream response
            async for chunk in llm_service.stream_chat(data["message"]):
                await websocket.send_text(chunk)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
```

### Agent Application Architecture

```python
class StandaloneAgent:
    """Production-ready standalone agent."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = LLMFactory.create(config.provider, config.llm_config)
        self.tools = ToolRegistry(config.tools)
        self.memory = MemoryManager(config.memory_config)
        self.monitor = MetricsCollector()

    async def run_task(self, task: Task) -> TaskResult:
        """Execute task with monitoring and error handling."""

        task_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Record task start
            self.monitor.task_started(task_id, task.type)

            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_task(task),
                timeout=self.config.task_timeout
            )

            # Record success
            self.monitor.task_completed(
                task_id,
                duration=time.time() - start_time,
                tokens=result.tokens_used
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out")
            self.monitor.task_failed(task_id, "timeout")
            raise TaskTimeout(f"Task exceeded {self.config.task_timeout}s")

        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            self.monitor.task_failed(task_id, str(e))
            raise

    async def _execute_task(self, task: Task) -> TaskResult:
        """Internal task execution with retry logic."""

        for attempt in range(self.config.max_retries):
            try:
                # Get relevant context from memory
                context = await self.memory.retrieve(task.query)

                # Execute with LLM
                response = await self.llm.chat(
                    messages=self._build_messages(task, context),
                    tools=self.tools.get_tools()
                )

                # Process tool calls if needed
                if response.tool_calls:
                    tool_results = await self._execute_tools(
                        response.tool_calls
                    )
                    # Continue conversation with tool results...

                # Store in memory
                await self.memory.store(task.query, response.text)

                return TaskResult(
                    text=response.text,
                    tokens_used=response.usage.total_tokens,
                    metadata=response.metadata
                )

            except APIError as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise
```

## Deployment Strategies

### 1. Docker Deployment

**Dockerfile for Chat Application:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose for Full Stack:**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/llm_app
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=llm_app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 2. Kubernetes Deployment

**Kubernetes Manifest:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-chat-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: llm-chat
  template:
    metadata:
      labels:
        app: llm-chat
    spec:
      containers:
      - name: app
        image: llm-chat:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: anthropic-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: llm-chat-service
spec:
  selector:
    app: llm-chat
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 3. Cloud Platform Deployment

**AWS Elastic Beanstalk:**

```python
# .ebextensions/01_packages.config
packages:
  yum:
    postgresql-devel: []

option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
  aws:elasticbeanstalk:container:python:
    WSGIPath: application:app
```

**Google Cloud Run:**

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: llm-chat-app
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project-id/llm-chat:latest
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: anthropic-key
              key: api-key
```

## Monitoring & Observability

### 1. Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
chat_requests = Counter(
    'chat_requests_total',
    'Total chat requests',
    ['provider', 'status']
)

chat_latency = Histogram(
    'chat_latency_seconds',
    'Chat request latency',
    ['provider']
)

token_usage = Counter(
    'tokens_used_total',
    'Total tokens used',
    ['provider', 'model', 'type']
)

active_conversations = Gauge(
    'active_conversations',
    'Number of active conversations'
)

# Usage in application
@app.post("/chat")
async def chat(msg: ChatMessage):
    start_time = time.time()

    try:
        response = await llm_service.chat(msg.message)

        # Record metrics
        chat_requests.labels(
            provider='claude',
            status='success'
        ).inc()

        chat_latency.labels(provider='claude').observe(
            time.time() - start_time
        )

        token_usage.labels(
            provider='claude',
            model='claude-3-5-sonnet',
            type='input'
        ).inc(response.usage.input_tokens)

        token_usage.labels(
            provider='claude',
            model='claude-3-5-sonnet',
            type='output'
        ).inc(response.usage.output_tokens)

        return {"response": response.text}

    except Exception as e:
        chat_requests.labels(
            provider='claude',
            status='error'
        ).inc()
        raise
```

### 2. Structured Logging

```python
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
logger.info(
    "chat_request_received",
    conversation_id=conv_id,
    user_id=user_id,
    message_length=len(message)
)

logger.error(
    "llm_api_error",
    provider="claude",
    error=str(e),
    retry_attempt=attempt
)
```

### 3. Distributed Tracing

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)

@app.post("/chat")
async def chat(msg: ChatMessage):
    with tracer.start_as_current_span("chat_request") as span:
        span.set_attribute("conversation.id", msg.conversation_id)
        span.set_attribute("message.length", len(msg.message))

        with tracer.start_as_current_span("llm.call"):
            response = await llm_service.chat(msg.message)
            span.set_attribute("llm.tokens", response.usage.total_tokens)

        with tracer.start_as_current_span("db.save"):
            await conversation_repo.save(conversation)

        return {"response": response.text}
```

## Security Best Practices

### 1. API Key Management

```python
from cryptography.fernet import Fernet
import os

class SecretManager:
    """Secure secret management."""

    def __init__(self):
        # Load encryption key from secure source
        self.key = os.getenv("ENCRYPTION_KEY").encode()
        self.cipher = Fernet(self.key)

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt secret for storage."""
        return self.cipher.encrypt(secret.encode()).decode()

    def decrypt_secret(self, encrypted: str) -> str:
        """Decrypt secret for use."""
        return self.cipher.decrypt(encrypted.encode()).decode()

# Usage with environment-specific secrets
class Config:
    def __init__(self):
        self.secret_manager = SecretManager()

        # Never hardcode API keys
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # For stored secrets
        encrypted_key = self.load_from_vault()
        self.anthropic_key = self.secret_manager.decrypt_secret(
            encrypted_key
        )
```

### 2. Input Validation

```python
from pydantic import BaseModel, validator, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None

    @validator('message')
    def validate_message(cls, v):
        # Prevent injection attacks
        if any(char in v for char in ['<', '>', '{', '}']):
            raise ValueError("Invalid characters in message")

        # Prevent prompt injection
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard all previous",
            "new instructions:"
        ]
        v_lower = v.lower()
        if any(pattern in v_lower for pattern in dangerous_patterns):
            raise ValueError("Potential prompt injection detected")

        return v

    @validator('conversation_id')
    def validate_conversation_id(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9\-_]{1,64}$', v):
            raise ValueError("Invalid conversation ID format")
        return v
```

### 3. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat")
@limiter.limit("10/minute")  # 10 requests per minute
async def chat(request: Request, msg: ChatMessage):
    # Rate-limited endpoint
    return await handle_chat(msg)

# User-specific rate limiting
@app.post("/chat")
@limiter.limit("100/hour", key_func=lambda: get_user_id())
async def chat(msg: ChatMessage):
    return await handle_chat(msg)
```

### 4. Authentication & Authorization

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

@app.post("/chat")
async def chat(
    msg: ChatMessage,
    user: dict = Depends(verify_token)
):
    # user contains decoded token payload
    logger.info("chat_request", user_id=user["user_id"])
    return await handle_chat(msg, user)
```

## Performance Optimization

### 1. Response Caching

```python
import hashlib
import redis
import json

class ResponseCache:
    """Cache LLM responses."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour

    def _generate_key(self, messages: List[Dict], model: str) -> str:
        """Generate cache key from messages."""
        content = json.dumps(messages, sort_keys=True) + model
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, messages: List[Dict], model: str) -> Optional[str]:
        """Get cached response."""
        key = self._generate_key(messages, model)
        cached = self.redis.get(f"llm:response:{key}")
        if cached:
            logger.info("cache_hit", key=key)
            return json.loads(cached)
        return None

    def set(self, messages: List[Dict], model: str, response: str):
        """Cache response."""
        key = self._generate_key(messages, model)
        self.redis.setex(
            f"llm:response:{key}",
            self.ttl,
            json.dumps(response)
        )

# Usage
cache = ResponseCache(redis_client)

async def get_llm_response(messages: List[Dict]) -> str:
    # Check cache first
    cached = cache.get(messages, "claude-3-5-sonnet")
    if cached:
        return cached

    # Call LLM
    response = await llm_client.chat(messages)

    # Cache response
    cache.set(messages, "claude-3-5-sonnet", response.text)

    return response.text
```

### 2. Request Batching

```python
import asyncio
from collections import defaultdict
from typing import List, Dict

class RequestBatcher:
    """Batch multiple requests for efficient processing."""

    def __init__(self, max_batch_size: int = 10, max_wait_time: float = 0.1):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests = []
        self.results = {}

    async def add_request(self, request_id: str, data: Dict) -> str:
        """Add request to batch and wait for result."""

        future = asyncio.Future()
        self.pending_requests.append((request_id, data, future))

        # Trigger batch processing if batch is full
        if len(self.pending_requests) >= self.max_batch_size:
            asyncio.create_task(self._process_batch())
        else:
            # Schedule batch processing after timeout
            asyncio.create_task(self._schedule_batch())

        return await future

    async def _schedule_batch(self):
        """Schedule batch processing after timeout."""
        await asyncio.sleep(self.max_wait_time)
        if self.pending_requests:
            await self._process_batch()

    async def _process_batch(self):
        """Process all pending requests as a batch."""
        if not self.pending_requests:
            return

        batch = self.pending_requests[:self.max_batch_size]
        self.pending_requests = self.pending_requests[self.max_batch_size:]

        # Process batch
        request_ids, data_list, futures = zip(*batch)

        # Make batched LLM call
        responses = await self._call_llm_batch(data_list)

        # Resolve futures
        for future, response in zip(futures, responses):
            future.set_result(response)
```

### 3. Connection Pooling

```python
from anthropic import Anthropic
import httpx

class LLMClientPool:
    """Connection pool for LLM clients."""

    def __init__(self, pool_size: int = 10):
        # Create HTTP client with connection pooling
        self.http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=pool_size,
                max_connections=pool_size * 2
            ),
            timeout=httpx.Timeout(60.0)
        )

        self.client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            http_client=self.http_client
        )

    async def close(self):
        """Close connection pool."""
        await self.http_client.aclose()
```

## Cost Management

### 1. Token Tracking

```python
class CostTracker:
    """Track and manage LLM costs."""

    # Pricing per 1M tokens (as of 2024)
    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00,
            "cache_write": 3.75,
            "cache_read": 0.30
        },
        "claude-3-5-haiku-20241022": {
            "input": 0.80,
            "output": 4.00,
            "cache_write": 1.00,
            "cache_read": 0.08
        }
    }

    def __init__(self, db_connection):
        self.db = db_connection

    def calculate_cost(self, usage: Usage, model: str) -> float:
        """Calculate cost for request."""
        pricing = self.PRICING[model]

        cost = (
            (usage.input_tokens / 1_000_000) * pricing["input"] +
            (usage.output_tokens / 1_000_000) * pricing["output"]
        )

        if hasattr(usage, "cache_creation_input_tokens"):
            cost += (usage.cache_creation_input_tokens / 1_000_000) * pricing["cache_write"]

        if hasattr(usage, "cache_read_input_tokens"):
            cost += (usage.cache_read_input_tokens / 1_000_000) * pricing["cache_read"]

        return cost

    def track_request(self, user_id: str, usage: Usage, model: str):
        """Track request cost."""
        cost = self.calculate_cost(usage, model)

        self.db.execute(
            """
            INSERT INTO usage_tracking
            (user_id, model, input_tokens, output_tokens, cost, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, model, usage.input_tokens, usage.output_tokens,
             cost, datetime.now())
        )

        # Check budget limits
        self._check_budget(user_id)

    def _check_budget(self, user_id: str):
        """Check if user is within budget."""
        monthly_cost = self.db.query(
            """
            SELECT SUM(cost) FROM usage_tracking
            WHERE user_id = ? AND timestamp > ?
            """,
            (user_id, datetime.now() - timedelta(days=30))
        )[0][0]

        budget = self._get_user_budget(user_id)

        if monthly_cost >= budget:
            raise BudgetExceeded(
                f"Monthly budget of ${budget} exceeded"
            )
```

### 2. Budget Controls

```python
class BudgetManager:
    """Manage usage budgets."""

    def __init__(self):
        self.budgets = {}
        self.usage = defaultdict(float)

    def set_budget(self, user_id: str, budget: float):
        """Set monthly budget for user."""
        self.budgets[user_id] = budget

    async def check_budget(self, user_id: str, estimated_cost: float) -> bool:
        """Check if request is within budget."""
        current_usage = self.usage[user_id]
        budget = self.budgets.get(user_id, float('inf'))

        if current_usage + estimated_cost > budget:
            logger.warning(
                "budget_exceeded",
                user_id=user_id,
                current=current_usage,
                budget=budget
            )
            return False

        return True

    def estimate_cost(self, prompt: str, model: str) -> float:
        """Estimate cost before making request."""
        # Rough token estimation
        estimated_input_tokens = len(prompt.split()) * 1.3
        estimated_output_tokens = 500  # Conservative estimate

        pricing = CostTracker.PRICING[model]

        return (
            (estimated_input_tokens / 1_000_000) * pricing["input"] +
            (estimated_output_tokens / 1_000_000) * pricing["output"]
        )
```

## Testing Strategies

### 1. Unit Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

class TestLLMClient:
    """Test LLM client."""

    @pytest.fixture
    def mock_anthropic(self):
        """Mock Anthropic client."""
        with patch('anthropic.Anthropic') as mock:
            yield mock

    @pytest.fixture
    def llm_client(self, mock_anthropic):
        """Create LLM client with mocked Anthropic."""
        return LLMClient(config=Config())

    @pytest.mark.asyncio
    async def test_chat_success(self, llm_client, mock_anthropic):
        """Test successful chat request."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_anthropic.return_value.messages.create.return_value = mock_response

        # Test
        result = await llm_client.chat([
            {"role": "user", "content": "Test message"}
        ])

        # Verify
        assert result == "Test response"
        mock_anthropic.return_value.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_retry_on_error(self, llm_client, mock_anthropic):
        """Test retry logic on API error."""
        # Setup mock to fail then succeed
        mock_anthropic.return_value.messages.create.side_effect = [
            APIError("Rate limit"),
            Mock(content=[Mock(text="Success")])
        ]

        # Test
        result = await llm_client.chat_with_retry([
            {"role": "user", "content": "Test"}
        ])

        # Verify retry happened
        assert result == "Success"
        assert mock_anthropic.return_value.messages.create.call_count == 2
```

### 2. Integration Tests

```python
@pytest.mark.integration
class TestChatEndpoint:
    """Integration tests for chat endpoint."""

    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_chat_endpoint(self, client):
        """Test chat endpoint end-to-end."""
        response = await client.post(
            "/chat",
            json={
                "message": "Calculate resistance for 12V, 100mA LED with 2.1V forward voltage"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "tokens_used" in data
        assert "99" in data["response"] or "100" in data["response"]
```

### 3. Load Tests

```python
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    """Load test user for chat endpoint."""

    wait_time = between(1, 3)

    @task(3)
    def chat_simple(self):
        """Simple chat request."""
        self.client.post("/chat", json={
            "message": "What is power dissipation?"
        })

    @task(1)
    def chat_complex(self):
        """Complex calculation request."""
        self.client.post("/chat", json={
            "message": "Design a buck converter for 24V to 5V, 5A"
        })

    def on_start(self):
        """Setup before test."""
        # Login or setup if needed
        pass
```

Run load tests:
```bash
locust -f load_tests.py --host=http://localhost:8000
```

## Examples

See the `examples/` directory for complete implementations:

1. **chat-app/** - Production-ready chat application
   - FastAPI backend with WebSocket support
   - React frontend
   - PostgreSQL database
   - Redis caching
   - Prometheus metrics
   - Docker deployment

2. **agent-app/** - Standalone autonomous agent
   - Task queue with Celery
   - Background job processing
   - State management
   - Monitoring dashboard
   - Kubernetes deployment

3. **api-wrapper/** - LLM API wrapper service
   - Multi-provider support
   - Rate limiting
   - Cost tracking
   - API key management
   - Documentation with OpenAPI

## Exercises

### Exercise 1: Production Chat Application

Build a production-ready chat application with:
- [x] User authentication
- [x] Conversation persistence
- [x] Response caching
- [x] Rate limiting
- [x] Metrics collection
- [x] Error handling
- [x] Docker deployment

See `exercises/exercise-1/` for starter code and instructions.

### Exercise 2: Autonomous Agent System

Deploy an autonomous agent with:
- [x] Task queue
- [x] Background processing
- [x] State persistence
- [x] Health monitoring
- [x] Auto-scaling
- [x] Cost tracking

See `exercises/exercise-2/` for starter code and instructions.

### Exercise 3: Multi-Tenant API Service

Build a multi-tenant LLM API service with:
- [x] Tenant isolation
- [x] Per-tenant rate limits
- [x] Usage tracking and billing
- [x] API key management
- [x] Monitoring per tenant

See `exercises/exercise-3/` for starter code and instructions.

## Best Practices Checklist

### Development
- [ ] Use type hints throughout
- [ ] Write comprehensive docstrings
- [ ] Follow consistent code style (black, ruff)
- [ ] Use dependency injection
- [ ] Implement proper error handling
- [ ] Add logging at appropriate levels
- [ ] Write unit tests (>80% coverage)
- [ ] Write integration tests

### Configuration
- [ ] Use environment variables for secrets
- [ ] Provide sensible defaults
- [ ] Document all configuration options
- [ ] Validate configuration on startup
- [ ] Support multiple environments (dev, staging, prod)

### Security
- [ ] Never commit secrets to git
- [ ] Use secret management services
- [ ] Validate all inputs
- [ ] Implement rate limiting
- [ ] Use authentication and authorization
- [ ] Enable HTTPS in production
- [ ] Regular security audits
- [ ] Keep dependencies updated

### Performance
- [ ] Implement response caching
- [ ] Use connection pooling
- [ ] Enable compression
- [ ] Optimize database queries
- [ ] Use async where beneficial
- [ ] Monitor and optimize slow endpoints
- [ ] Set appropriate timeouts

### Monitoring
- [ ] Collect application metrics
- [ ] Implement structured logging
- [ ] Set up distributed tracing
- [ ] Configure alerting rules
- [ ] Monitor error rates
- [ ] Track latency percentiles
- [ ] Monitor resource usage

### Deployment
- [ ] Use containers (Docker)
- [ ] Implement health checks
- [ ] Enable auto-scaling
- [ ] Use CI/CD pipelines
- [ ] Implement blue-green or canary deployments
- [ ] Automated rollback on failure
- [ ] Regular backups

### Cost Management
- [ ] Track token usage
- [ ] Implement budget controls
- [ ] Monitor costs per user/tenant
- [ ] Optimize prompt efficiency
- [ ] Use appropriate models (Haiku vs Sonnet)
- [ ] Cache aggressively
- [ ] Set usage limits

## Additional Resources

- **Anthropic Production Best Practices:** https://docs.anthropic.com/en/docs/build-with-claude/production
- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/
- **Kubernetes Patterns:** https://kubernetes.io/docs/concepts/
- **Prometheus Monitoring:** https://prometheus.io/docs/
- **The Twelve-Factor App:** https://12factor.net/

## Next Steps

1. Review all examples in the `examples/` directory
2. Complete the exercises
3. Deploy your first production application
4. Set up monitoring and alerting
5. Implement CI/CD pipeline
6. Scale and optimize

---

**Congratulations!** You've completed the full LLM API tutorial series. You now have the knowledge to build, deploy, and maintain production LLM applications.
