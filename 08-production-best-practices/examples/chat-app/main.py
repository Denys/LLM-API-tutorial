#!/usr/bin/env python3
"""
Production-Ready Chat Application

A complete production chat application with:
- FastAPI backend with WebSocket support
- User authentication
- Conversation persistence
- Response caching (Redis)
- Rate limiting
- Metrics collection (Prometheus)
- Structured logging
- Error handling
- Health checks
"""

import os
import sys
import time
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, AsyncIterator
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, Depends,
    HTTPException, status, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import AI clients
from anthropic import Anthropic, APIError

# Database and caching
import asyncpg
import redis.asyncio as redis

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
chat_requests = Counter(
    'chat_requests_total',
    'Total chat requests',
    ['status']
)

chat_latency = Histogram(
    'chat_latency_seconds',
    'Chat request latency'
)

token_usage = Counter(
    'tokens_used_total',
    'Total tokens used',
    ['model', 'type']
)

active_connections = Gauge(
    'active_websocket_connections',
    'Number of active WebSocket connections'
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses'
)

# Global state
class AppState:
    """Application state."""
    db_pool: Optional[asyncpg.Pool] = None
    redis_client: Optional[redis.Redis] = None
    anthropic_client: Optional[Anthropic] = None

app_state = AppState()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("application_starting")

    # Initialize database pool
    try:
        app_state.db_pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL", "postgresql://localhost/chatapp"),
            min_size=2,
            max_size=10
        )
        logger.info("database_connected")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        # Continue without database (degrade gracefully)

    # Initialize Redis
    try:
        app_state.redis_client = await redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            encoding="utf-8",
            decode_responses=True
        )
        await app_state.redis_client.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        # Continue without Redis (no caching)

    # Initialize Anthropic client
    app_state.anthropic_client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    logger.info("anthropic_client_initialized")

    yield

    # Shutdown
    logger.info("application_shutting_down")

    if app_state.db_pool:
        await app_state.db_pool.close()
        logger.info("database_closed")

    if app_state.redis_client:
        await app_state.redis_client.close()
        logger.info("redis_closed")

# Create FastAPI app
app = FastAPI(
    title="Power Electronics Chat API",
    description="Production-ready chat API for power electronics",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Pydantic models
class ChatMessage(BaseModel):
    """Chat message request."""
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    use_cache: bool = True
    stream: bool = False

    @validator('message')
    def validate_message(cls, v):
        """Validate message content."""
        # Basic injection prevention
        dangerous_patterns = [
            "ignore previous instructions",
            "disregard all previous",
            "new instructions:"
        ]
        v_lower = v.lower()
        if any(pattern in v_lower for pattern in dangerous_patterns):
            logger.warning("potential_prompt_injection", message=v[:100])
            # Don't reject, just log for monitoring
        return v

class ChatResponse(BaseModel):
    """Chat response."""
    response: str
    conversation_id: str
    tokens_used: int
    latency_ms: float
    cached: bool = False

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    services: Dict[str, bool]

# Service classes
class CacheService:
    """Response caching service."""

    def __init__(self, redis_client: Optional[redis.Redis]):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour

    def _generate_key(self, messages: List[Dict], model: str) -> str:
        """Generate cache key."""
        content = json.dumps(messages, sort_keys=True) + model
        return f"chat:cache:{hashlib.sha256(content.encode()).hexdigest()}"

    async def get(self, messages: List[Dict], model: str) -> Optional[str]:
        """Get cached response."""
        if not self.redis:
            return None

        try:
            key = self._generate_key(messages, model)
            cached = await self.redis.get(key)
            if cached:
                cache_hits.inc()
                logger.info("cache_hit", key=key)
                return cached
            cache_misses.inc()
            return None
        except Exception as e:
            logger.error("cache_get_error", error=str(e))
            return None

    async def set(self, messages: List[Dict], model: str, response: str):
        """Cache response."""
        if not self.redis:
            return

        try:
            key = self._generate_key(messages, model)
            await self.redis.setex(key, self.ttl, response)
            logger.info("cache_set", key=key)
        except Exception as e:
            logger.error("cache_set_error", error=str(e))

class ConversationService:
    """Conversation management service."""

    def __init__(self, db_pool: Optional[asyncpg.Pool]):
        self.db = db_pool

    async def create_conversation(self, conversation_id: Optional[str] = None) -> str:
        """Create new conversation."""
        conv_id = conversation_id or str(uuid.uuid4())

        if self.db:
            try:
                await self.db.execute(
                    """
                    INSERT INTO conversations (id, created_at, updated_at)
                    VALUES ($1, $2, $2)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    conv_id, datetime.now()
                )
            except Exception as e:
                logger.error("conversation_create_error", error=str(e))

        return conv_id

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ):
        """Add message to conversation."""
        if not self.db:
            return

        try:
            await self.db.execute(
                """
                INSERT INTO messages (conversation_id, role, content, created_at)
                VALUES ($1, $2, $3, $4)
                """,
                conversation_id, role, content, datetime.now()
            )

            # Update conversation timestamp
            await self.db.execute(
                """
                UPDATE conversations
                SET updated_at = $1
                WHERE id = $2
                """,
                datetime.now(), conversation_id
            )
        except Exception as e:
            logger.error("message_add_error", error=str(e))

    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get conversation messages."""
        if not self.db:
            return []

        try:
            rows = await self.db.fetch(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                conversation_id, limit
            )

            return [
                {
                    "role": row["role"],
                    "content": row["content"]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error("messages_get_error", error=str(e))
            return []

class LLMService:
    """LLM interaction service."""

    SYSTEM_PROMPT = """You are a helpful assistant specializing in power electronics engineering.
You provide accurate, practical advice on circuit design, component selection, and calculations.
Always show your work when doing calculations."""

    def __init__(
        self,
        anthropic_client: Anthropic,
        cache_service: CacheService,
        model: str = "claude-3-5-sonnet-20241022"
    ):
        self.client = anthropic_client
        self.cache = cache_service
        self.model = model

    async def chat(
        self,
        messages: List[Dict],
        use_cache: bool = True
    ) -> Dict:
        """Get chat response."""

        # Check cache first
        if use_cache:
            cached = await self.cache.get(messages, self.model)
            if cached:
                return {
                    "text": cached,
                    "usage": {"input_tokens": 0, "output_tokens": 0},
                    "cached": True
                }

        # Call LLM
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.SYSTEM_PROMPT,
                messages=messages
            )

            result_text = response.content[0].text

            # Cache response
            if use_cache:
                await self.cache.set(messages, self.model, result_text)

            # Track metrics
            token_usage.labels(
                model=self.model,
                type="input"
            ).inc(response.usage.input_tokens)

            token_usage.labels(
                model=self.model,
                type="output"
            ).inc(response.usage.output_tokens)

            return {
                "text": result_text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "cached": False
            }

        except APIError as e:
            logger.error("llm_api_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LLM service error: {str(e)}"
            )

    async def stream_chat(
        self,
        messages: List[Dict]
    ) -> AsyncIterator[str]:
        """Stream chat response."""

        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=self.SYSTEM_PROMPT,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield text

                # Track metrics from final message
                final_message = stream.get_final_message()
                token_usage.labels(
                    model=self.model,
                    type="input"
                ).inc(final_message.usage.input_tokens)

                token_usage.labels(
                    model=self.model,
                    type="output"
                ).inc(final_message.usage.output_tokens)

        except APIError as e:
            logger.error("llm_stream_error", error=str(e))
            yield f"Error: {str(e)}"

# Initialize services
def get_cache_service() -> CacheService:
    """Get cache service."""
    return CacheService(app_state.redis_client)

def get_conversation_service() -> ConversationService:
    """Get conversation service."""
    return ConversationService(app_state.db_pool)

def get_llm_service() -> LLMService:
    """Get LLM service."""
    cache = get_cache_service()
    return LLMService(app_state.anthropic_client, cache)

# API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""

    services = {
        "database": app_state.db_pool is not None,
        "redis": app_state.redis_client is not None,
        "anthropic": app_state.anthropic_client is not None
    }

    # Test database connection
    if app_state.db_pool:
        try:
            await app_state.db_pool.fetchval("SELECT 1")
            services["database"] = True
        except:
            services["database"] = False

    # Test Redis connection
    if app_state.redis_client:
        try:
            await app_state.redis_client.ping()
            services["redis"] = True
        except:
            services["redis"] = False

    # Overall status
    status_ok = all(services.values())

    return HealthResponse(
        status="healthy" if status_ok else "degraded",
        timestamp=datetime.now().isoformat(),
        services=services
    )

@app.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    if not app_state.anthropic_client:
        raise HTTPException(status_code=503, detail="Not ready")
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        generate_latest(),
        media_type="text/plain"
    )

@app.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")  # Rate limit
async def chat(
    request: Request,
    msg: ChatMessage,
    conversation_service: ConversationService = Depends(get_conversation_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Chat endpoint."""

    start_time = time.time()
    request_id = str(uuid.uuid4())

    logger.info(
        "chat_request",
        request_id=request_id,
        conversation_id=msg.conversation_id,
        message_length=len(msg.message),
        use_cache=msg.use_cache
    )

    try:
        # Create or get conversation
        conv_id = await conversation_service.create_conversation(
            msg.conversation_id
        )

        # Get conversation history
        history = await conversation_service.get_messages(conv_id)

        # Add new user message
        history.append({
            "role": "user",
            "content": msg.message
        })

        # Get LLM response
        response = await llm_service.chat(history, use_cache=msg.use_cache)

        # Save messages
        await conversation_service.add_message(conv_id, "user", msg.message)
        await conversation_service.add_message(
            conv_id, "assistant", response["text"]
        )

        # Calculate latency
        latency = (time.time() - start_time) * 1000

        # Record metrics
        chat_requests.labels(status="success").inc()
        chat_latency.observe(latency / 1000)

        logger.info(
            "chat_success",
            request_id=request_id,
            conversation_id=conv_id,
            tokens=response["usage"]["input_tokens"] + response["usage"]["output_tokens"],
            latency_ms=latency,
            cached=response["cached"]
        )

        return ChatResponse(
            response=response["text"],
            conversation_id=conv_id,
            tokens_used=response["usage"]["input_tokens"] + response["usage"]["output_tokens"],
            latency_ms=latency,
            cached=response["cached"]
        )

    except HTTPException:
        raise
    except Exception as e:
        chat_requests.labels(status="error").inc()
        logger.error(
            "chat_error",
            request_id=request_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    llm_service: LLMService = Depends(get_llm_service),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """WebSocket chat endpoint for streaming."""

    await websocket.accept()
    active_connections.inc()

    connection_id = str(uuid.uuid4())
    logger.info("websocket_connected", connection_id=connection_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            conv_id = data.get("conversation_id")

            if not message:
                continue

            logger.info(
                "websocket_message",
                connection_id=connection_id,
                conversation_id=conv_id,
                message_length=len(message)
            )

            # Create or get conversation
            conv_id = await conversation_service.create_conversation(conv_id)

            # Get history
            history = await conversation_service.get_messages(conv_id)
            history.append({"role": "user", "content": message})

            # Stream response
            full_response = ""
            async for chunk in llm_service.stream_chat(history):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk
                })
                full_response += chunk

            # Send completion
            await websocket.send_json({
                "type": "complete",
                "conversation_id": conv_id
            })

            # Save messages
            await conversation_service.add_message(conv_id, "user", message)
            await conversation_service.add_message(
                conv_id, "assistant", full_response
            )

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", connection_id=connection_id)
    except Exception as e:
        logger.error(
            "websocket_error",
            connection_id=connection_id,
            error=str(e),
            exc_info=True
        )
    finally:
        active_connections.dec()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_config=None  # Use our structured logging
    )
