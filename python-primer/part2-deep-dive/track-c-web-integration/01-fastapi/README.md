# Track C, Section 1: FastAPI for LLM Services

**Duration:** 60-90 minutes | **Level:** Intermediate-Advanced

## Why This Matters for LLM APIs

FastAPI enables you to build:
- **Chat APIs:** Expose LLM capabilities via REST
- **Streaming endpoints:** Server-sent events for real-time responses
- **Middleware:** Rate limiting, authentication, logging
- **Async processing:** Handle many concurrent requests

## Concepts

### Basic FastAPI Structure

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 1024

class ChatResponse(BaseModel):
    response: str
    tokens_used: int

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Call LLM
    return ChatResponse(response="Hello", tokens_used=10)
```

### Streaming Responses

```python
from fastapi.responses import StreamingResponse

@app.post("/stream")
async def stream_chat(request: ChatRequest):
    async def generate():
        async for chunk in llm_stream(request.message):
            yield f"data: {chunk}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## Examples

### Complete Chat API

```python
# examples/chat_api.py
"""Complete LLM chat API with FastAPI."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from anthropic import Anthropic, AsyncAnthropic
from dotenv import load_dotenv
import json
import os

load_dotenv()

app = FastAPI(
    title="LLM Chat API",
    description="REST API for Claude",
    version="1.0.0"
)

# Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(default="claude-sonnet-4-20250514")
    max_tokens: int = Field(default=1024, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0, le=1)
    stream: bool = Field(default=False)

class ChatResponse(BaseModel):
    response: str
    model: str
    usage: dict

class ErrorResponse(BaseModel):
    error: str
    detail: str

# Dependencies
def get_client():
    return AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, client: AsyncAnthropic = Depends(get_client)):
    """Send a message and get a response."""
    if request.stream:
        raise HTTPException(400, "Use /stream endpoint for streaming")

    try:
        response = await client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.message}]
        )

        return ChatResponse(
            response=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        )

    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/stream")
async def stream_chat(request: ChatRequest, client: AsyncAnthropic = Depends(get_client)):
    """Stream a chat response using Server-Sent Events."""

    async def generate():
        try:
            async with client.messages.stream(
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                messages=[{"role": "user", "content": request.message}]
            ) as stream:
                async for text in stream.text_stream:
                    data = json.dumps({"text": text})
                    yield f"data: {data}\n\n"

                # Send final message with usage
                final = stream.get_final_message()
                data = json.dumps({
                    "done": True,
                    "usage": {
                        "input_tokens": final.usage.input_tokens,
                        "output_tokens": final.usage.output_tokens
                    }
                })
                yield f"data: {data}\n\n"

        except Exception as e:
            data = json.dumps({"error": str(e)})
            yield f"data: {data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Rate Limiting Middleware

```python
# examples/rate_limiting.py
"""Rate limiting middleware for LLM API."""

from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict

app = FastAPI()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting by IP."""

    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Clean old requests
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < 60
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                429,
                "Rate limit exceeded. Try again later."
            )

        # Record request
        self.requests[client_ip].append(now)

        return await call_next(request)

# Apply middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=20)
```

### Authentication

```python
# examples/auth.py
"""API key authentication."""

from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
import os

app = FastAPI()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key from header."""
    if not api_key:
        raise HTTPException(401, "API key required")

    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    if api_key not in valid_keys:
        raise HTTPException(403, "Invalid API key")

    return api_key

@app.post("/chat")
async def chat(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Protected endpoint requiring API key."""
    # ... implementation
    pass
```

---

## Exercises

### Simple: Basic Chat Endpoint

**Task:** Create a FastAPI app with:
1. POST `/chat` endpoint
2. Request/response models with validation
3. Health check endpoint

<details>
<summary>Solution</summary>

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    max_tokens: int = Field(default=100, ge=1, le=1000)

class ChatResponse(BaseModel):
    response: str
    tokens: int

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Mock response
    return ChatResponse(
        response=f"Echo: {request.message}",
        tokens=len(request.message.split())
    )

@app.get("/health")
async def health():
    return {"status": "ok"}
```
</details>

---

### Intermediate: Streaming Endpoint

**Task:** Add a streaming endpoint:
1. POST `/stream` with SSE response
2. Yield chunks with proper formatting
3. Send final usage stats

<details>
<summary>Solution</summary>

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json
import asyncio

@app.post("/stream")
async def stream(request: ChatRequest):
    async def generate():
        # Simulate streaming
        words = f"Response to: {request.message}".split()
        for word in words:
            await asyncio.sleep(0.1)
            data = json.dumps({"text": word + " "})
            yield f"data: {data}\n\n"

        # Final message
        data = json.dumps({"done": True, "tokens": len(words)})
        yield f"data: {data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```
</details>

---

### Advanced: Production-Ready API

**Task:** Build a complete API with:
1. Rate limiting middleware
2. API key authentication
3. Request logging
4. Error handling
5. CORS support

<details>
<summary>Solution</summary>

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            f"{request.method} {request.url.path} "
            f"{response.status_code} {duration:.2f}s"
        )
        return response

app.add_middleware(LoggingMiddleware)

# Rate limiting (from previous example)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Auth
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_key(key: str = Depends(api_key_header)):
    if key != os.getenv("API_KEY"):
        raise HTTPException(403, "Invalid key")
    return key

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

@app.post("/chat")
async def chat(request: ChatRequest, key: str = Depends(verify_key)):
    # Implementation
    pass
```
</details>

---

## Pro Tips

### 1. Use Depends for Reusable Logic

```python
async def get_user(token: str = Depends(oauth2_scheme)):
    return decode_token(token)

@app.post("/chat")
async def chat(request: ChatRequest, user: User = Depends(get_user)):
    # user automatically injected
    pass
```

### 2. Background Tasks

```python
from fastapi import BackgroundTasks

@app.post("/chat")
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    response = await generate_response(request)

    # Log usage in background
    background_tasks.add_task(log_usage, request, response)

    return response
```

### 3. Lifespan Events

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.client = AsyncAnthropic()
    yield
    # Shutdown
    await app.state.client.close()

app = FastAPI(lifespan=lifespan)
```

### 4. OpenAPI Documentation

```python
app = FastAPI(
    title="LLM API",
    description="API for Claude interactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

---

## Running the API

```bash
# Development
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## Next Section

[Section 2: Database Integration →](../02-database/)
