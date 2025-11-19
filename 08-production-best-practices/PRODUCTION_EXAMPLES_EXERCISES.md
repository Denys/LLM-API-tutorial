# Production Best Practices - Examples & Exercises

Power electronics-focused examples and exercises for deploying LLM applications at production scale.

---

## Example 1: Production-Grade Converter Design Service (75 min)

A complete production service with rate limiting, caching, monitoring, and graceful degradation for power converter design assistance.

### Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────>│  Rate Limiter │────>│   Cache     │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │ miss
                                                v
                    ┌──────────────┐     ┌─────────────┐
                    │   Metrics    │<────│  LLM Service│
                    └──────────────┘     └──────┬──────┘
                                                │
                                                v
                                        ┌─────────────┐
                                        │   Claude    │
                                        └─────────────┘
```

### Complete Implementation

```python
# production_converter_service.py
"""
Production-grade power converter design service with:
- Token bucket rate limiting
- Redis caching with TTL
- Prometheus metrics
- Circuit breaker pattern
- Structured logging
- Graceful degradation
"""

import os
import json
import time
import asyncio
import hashlib
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

import anthropic
import redis.asyncio as redis
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import Response

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class ServiceConfig:
    """Service configuration with sensible defaults."""
    # API settings
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    # Rate limiting
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window: int = 60     # seconds

    # Caching
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 3600           # 1 hour

    # Circuit breaker
    failure_threshold: int = 5
    recovery_timeout: int = 30      # seconds

    # Timeouts
    request_timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "ServiceConfig":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=os.getenv("MODEL", "claude-sonnet-4-20250514"),
            rate_limit_requests=int(os.getenv("RATE_LIMIT", "100")),
            cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        )

config = ServiceConfig.from_env()

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("converter_service")

# ============================================================================
# Metrics
# ============================================================================

REQUEST_COUNT = Counter(
    'converter_requests_total',
    'Total requests',
    ['endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'converter_request_latency_seconds',
    'Request latency',
    ['endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

CACHE_HITS = Counter(
    'converter_cache_hits_total',
    'Cache hits'
)

CACHE_MISSES = Counter(
    'converter_cache_misses_total',
    'Cache misses'
)

CIRCUIT_STATE = Gauge(
    'converter_circuit_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)'
)

TOKEN_USAGE = Counter(
    'converter_tokens_total',
    'Token usage',
    ['type']  # input, output
)

RATE_LIMIT_REJECTIONS = Counter(
    'converter_rate_limit_rejections_total',
    'Rate limit rejections',
    ['client_id']
)

# ============================================================================
# Request/Response Models
# ============================================================================

class ConverterType(str, Enum):
    BUCK = "buck"
    BOOST = "boost"
    BUCK_BOOST = "buck_boost"
    FLYBACK = "flyback"
    FORWARD = "forward"

class DesignRequest(BaseModel):
    """Power converter design request."""
    converter_type: ConverterType
    v_in_min: float = Field(..., gt=0, description="Min input voltage (V)")
    v_in_max: float = Field(..., gt=0, description="Max input voltage (V)")
    v_out: float = Field(..., gt=0, description="Output voltage (V)")
    i_out_max: float = Field(..., gt=0, description="Max output current (A)")
    f_sw: float = Field(default=100e3, gt=0, description="Switching frequency (Hz)")
    ripple_current_ratio: float = Field(default=0.3, gt=0, lt=1)
    ripple_voltage_ratio: float = Field(default=0.01, gt=0, lt=0.1)
    efficiency_target: float = Field(default=0.95, gt=0.5, le=1.0)

    def cache_key(self) -> str:
        """Generate cache key from request parameters."""
        key_data = self.model_dump_json()
        return f"design:{hashlib.sha256(key_data.encode()).hexdigest()}"

class ComponentSpec(BaseModel):
    """Component specification."""
    type: str
    value: str
    rating: str
    part_number: Optional[str] = None
    notes: Optional[str] = None

class DesignResponse(BaseModel):
    """Power converter design response."""
    converter_type: str
    components: list[ComponentSpec]
    calculated_values: Dict[str, Any]
    efficiency_estimate: float
    thermal_considerations: list[str]
    layout_recommendations: list[str]
    warnings: list[str] = []
    cached: bool = False
    latency_ms: float = 0

# ============================================================================
# Rate Limiter
# ============================================================================

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter with Redis backend.
    Allows burst traffic while maintaining average rate.
    """

    def __init__(self, redis_client: redis.Redis, config: ServiceConfig):
        self.redis = redis_client
        self.max_tokens = config.rate_limit_requests
        self.refill_rate = config.rate_limit_requests / config.rate_limit_window

    async def acquire(self, client_id: str) -> bool:
        """
        Attempt to acquire a token for the client.
        Returns True if allowed, False if rate limited.
        """
        key = f"ratelimit:{client_id}"
        now = time.time()

        # Lua script for atomic token bucket operation
        lua_script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
        local tokens = tonumber(bucket[1]) or max_tokens
        local last_update = tonumber(bucket[2]) or now

        -- Refill tokens
        local elapsed = now - last_update
        tokens = math.min(max_tokens, tokens + elapsed * refill_rate)

        -- Try to consume
        if tokens >= 1 then
            tokens = tokens - 1
            redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
            redis.call('EXPIRE', key, 120)
            return 1
        else
            redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
            redis.call('EXPIRE', key, 120)
            return 0
        end
        """

        result = await self.redis.eval(
            lua_script, 1, key,
            self.max_tokens, self.refill_rate, now
        )

        if not result:
            RATE_LIMIT_REJECTIONS.labels(client_id=client_id).inc()
            logger.warning(f"Rate limit exceeded for client: {client_id}")

        return bool(result)

# ============================================================================
# Circuit Breaker
# ============================================================================

class CircuitState(Enum):
    CLOSED = 0      # Normal operation
    OPEN = 1        # Failing, reject requests
    HALF_OPEN = 2   # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker pattern for LLM service protection.
    Prevents cascade failures during API outages.
    """

    def __init__(self, config: ServiceConfig):
        self.failure_threshold = config.failure_threshold
        self.recovery_timeout = config.recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self.state = CircuitState.HALF_OPEN
                    CIRCUIT_STATE.set(2)
                    logger.info("Circuit breaker: HALF_OPEN, attempting recovery")
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="Service temporarily unavailable (circuit open)"
                    )

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                CIRCUIT_STATE.set(0)
                logger.info("Circuit breaker: CLOSED, service recovered")

    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                CIRCUIT_STATE.set(1)
                logger.warning("Circuit breaker: OPEN, recovery failed")
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                CIRCUIT_STATE.set(1)
                logger.warning(
                    f"Circuit breaker: OPEN after {self.failure_count} failures"
                )

# ============================================================================
# LLM Service
# ============================================================================

class ConverterDesignService:
    """
    Production LLM service for power converter design.
    """

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)

    async def design_converter(self, request: DesignRequest) -> Dict[str, Any]:
        """
        Generate power converter design using Claude.
        Returns structured design data.
        """
        system_prompt = """You are a senior power electronics engineer specializing in
        switching converter design. Provide detailed, production-ready designs with:
        - Specific component values with ratings and tolerances
        - Real part numbers from major manufacturers (TI, Infineon, Vishay, etc.)
        - Efficiency calculations with loss breakdown
        - Thermal considerations and derating
        - PCB layout recommendations

        Always respond with valid JSON matching the requested schema."""

        user_prompt = f"""Design a {request.converter_type.value} converter with these specifications:

Input Voltage: {request.v_in_min}V - {request.v_in_max}V
Output Voltage: {request.v_out}V
Max Output Current: {request.i_out_max}A
Switching Frequency: {request.f_sw/1e3:.0f}kHz
Target Ripple Current: {request.ripple_current_ratio*100:.0f}%
Target Ripple Voltage: {request.ripple_voltage_ratio*100:.1f}%
Efficiency Target: {request.efficiency_target*100:.0f}%

Provide your response as JSON with this structure:
{{
    "components": [
        {{"type": "...", "value": "...", "rating": "...", "part_number": "...", "notes": "..."}}
    ],
    "calculated_values": {{
        "duty_cycle": ...,
        "inductor_ripple_current": ...,
        "output_ripple_voltage": ...,
        "peak_switch_current": ...,
        "rms_capacitor_current": ...
    }},
    "efficiency_estimate": ...,
    "thermal_considerations": ["..."],
    "layout_recommendations": ["..."],
    "warnings": ["..."]
}}"""

        start_time = time.time()

        response = await asyncio.wait_for(
            self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            ),
            timeout=self.config.request_timeout
        )

        # Track token usage
        TOKEN_USAGE.labels(type="input").inc(response.usage.input_tokens)
        TOKEN_USAGE.labels(type="output").inc(response.usage.output_tokens)

        # Parse response
        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)
        result["latency_ms"] = (time.time() - start_time) * 1000

        logger.info(
            f"Design generated in {result['latency_ms']:.0f}ms, "
            f"tokens: {response.usage.input_tokens}+{response.usage.output_tokens}"
        )

        return result

# ============================================================================
# FastAPI Application
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    app.state.redis = redis.from_url(config.redis_url)
    app.state.rate_limiter = TokenBucketRateLimiter(app.state.redis, config)
    app.state.circuit_breaker = CircuitBreaker(config)
    app.state.llm_service = ConverterDesignService(config)

    logger.info("Service started")
    CIRCUIT_STATE.set(0)

    yield

    # Shutdown
    await app.state.redis.close()
    logger.info("Service stopped")

app = FastAPI(
    title="Power Converter Design Service",
    description="Production-grade LLM service for power converter design",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# Endpoints
# ============================================================================

async def get_client_id(request: Request) -> str:
    """Extract client ID from request."""
    # Use API key, user ID, or IP as client identifier
    return request.headers.get("X-API-Key", request.client.host)

@app.post("/design", response_model=DesignResponse)
async def design_converter(
    request: DesignRequest,
    http_request: Request,
    client_id: str = Depends(get_client_id)
):
    """
    Design a power converter based on specifications.

    Rate limited, cached, with circuit breaker protection.
    """
    start_time = time.time()

    # Rate limiting
    if not await http_request.app.state.rate_limiter.acquire(client_id):
        REQUEST_COUNT.labels(endpoint="/design", status="rate_limited").inc()
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please retry later."
        )

    # Check cache
    cache_key = request.cache_key()
    redis_client = http_request.app.state.redis

    cached_result = await redis_client.get(cache_key)
    if cached_result:
        CACHE_HITS.inc()
        REQUEST_COUNT.labels(endpoint="/design", status="cache_hit").inc()

        result = json.loads(cached_result)
        result["cached"] = True
        result["latency_ms"] = (time.time() - start_time) * 1000

        REQUEST_LATENCY.labels(endpoint="/design").observe(
            time.time() - start_time
        )

        return DesignResponse(converter_type=request.converter_type.value, **result)

    CACHE_MISSES.inc()

    # Call LLM with circuit breaker
    try:
        result = await http_request.app.state.circuit_breaker.call(
            http_request.app.state.llm_service.design_converter,
            request
        )

        # Cache result
        await redis_client.setex(
            cache_key,
            config.cache_ttl,
            json.dumps(result)
        )

        REQUEST_COUNT.labels(endpoint="/design", status="success").inc()
        REQUEST_LATENCY.labels(endpoint="/design").observe(
            time.time() - start_time
        )

        return DesignResponse(
            converter_type=request.converter_type.value,
            cached=False,
            **result
        )

    except asyncio.TimeoutError:
        REQUEST_COUNT.labels(endpoint="/design", status="timeout").inc()
        logger.error("Request timeout")
        raise HTTPException(status_code=504, detail="Request timeout")

    except json.JSONDecodeError as e:
        REQUEST_COUNT.labels(endpoint="/design", status="parse_error").inc()
        logger.error(f"JSON parse error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse LLM response")

    except Exception as e:
        REQUEST_COUNT.labels(endpoint="/design", status="error").inc()
        logger.error(f"Design error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )

@app.get("/health")
async def health(request: Request):
    """Health check endpoint."""
    circuit_state = request.app.state.circuit_breaker.state.name

    # Check Redis connection
    try:
        await request.app.state.redis.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    return {
        "status": "healthy" if circuit_state != "OPEN" else "degraded",
        "circuit_breaker": circuit_state,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  converter-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_URL=redis://redis:6379
      - RATE_LIMIT=100
      - CACHE_TTL=3600
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  redis_data:
```

### Test Client

```python
# test_client.py
import asyncio
import httpx
import time

async def test_service():
    """Test the converter design service."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Test design endpoint
        request = {
            "converter_type": "buck",
            "v_in_min": 36,
            "v_in_max": 72,
            "v_out": 12,
            "i_out_max": 10,
            "f_sw": 200000,
            "ripple_current_ratio": 0.3,
            "ripple_voltage_ratio": 0.01,
            "efficiency_target": 0.95
        }

        # First request (cache miss)
        start = time.time()
        response = await client.post("/design", json=request)
        first_latency = (time.time() - start) * 1000

        result = response.json()
        print(f"First request: {first_latency:.0f}ms, cached={result['cached']}")
        print(f"Efficiency: {result['efficiency_estimate']*100:.1f}%")
        print(f"Components: {len(result['components'])}")

        # Second request (cache hit)
        start = time.time()
        response = await client.post("/design", json=request)
        second_latency = (time.time() - start) * 1000

        result = response.json()
        print(f"Second request: {second_latency:.0f}ms, cached={result['cached']}")

        # Check health
        health = await client.get("/health")
        print(f"Health: {health.json()}")

if __name__ == "__main__":
    asyncio.run(test_service())
```

---

## Example 2: Load Testing and Performance Optimization (60 min)

Comprehensive load testing framework for LLM services with performance analysis and optimization strategies.

### Load Testing Framework

```python
# load_test_framework.py
"""
Load testing framework for LLM-powered services.
Generates realistic power electronics design workloads.
"""

import asyncio
import time
import random
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import httpx
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

console = Console()

# ============================================================================
# Workload Generation
# ============================================================================

@dataclass
class WorkloadConfig:
    """Load test configuration."""
    base_url: str = "http://localhost:8000"
    total_requests: int = 100
    concurrent_users: int = 10
    ramp_up_time: float = 5.0      # seconds
    think_time_min: float = 0.5    # seconds between requests
    think_time_max: float = 2.0
    timeout: float = 60.0

class ConverterWorkloadGenerator:
    """
    Generates realistic power converter design requests.
    Follows typical engineering design patterns.
    """

    # Common converter configurations
    TOPOLOGIES = [
        # (type, v_in_range, v_out, i_out_range, freq_range)
        ("buck", (36, 72), 12, (5, 20), (100e3, 500e3)),       # Telecom
        ("buck", (18, 36), 5, (1, 10), (200e3, 1e6)),          # Point of load
        ("buck", (100, 400), 48, (10, 50), (50e3, 200e3)),     # Server PSU
        ("boost", (3, 5), 12, (0.5, 3), (500e3, 2e6)),         # Battery boost
        ("buck_boost", (9, 18), 12, (1, 5), (200e3, 800e3)),   # Automotive
        ("flyback", (85, 265), 24, (1, 5), (65e3, 150e3)),     # AC-DC adapter
    ]

    def generate_request(self) -> Dict[str, Any]:
        """Generate a random but realistic design request."""
        topology = random.choice(self.TOPOLOGIES)

        v_in_nom = random.uniform(topology[1][0], topology[1][1])
        v_in_min = v_in_nom * random.uniform(0.8, 0.95)
        v_in_max = v_in_nom * random.uniform(1.05, 1.2)

        return {
            "converter_type": topology[0],
            "v_in_min": round(v_in_min, 1),
            "v_in_max": round(v_in_max, 1),
            "v_out": topology[2],
            "i_out_max": round(random.uniform(topology[3][0], topology[3][1]), 1),
            "f_sw": random.choice([100e3, 200e3, 300e3, 500e3]),
            "ripple_current_ratio": round(random.uniform(0.2, 0.4), 2),
            "ripple_voltage_ratio": round(random.uniform(0.005, 0.02), 3),
            "efficiency_target": round(random.uniform(0.9, 0.97), 2)
        }

# ============================================================================
# Metrics Collection
# ============================================================================

@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    request_id: int
    start_time: float
    end_time: float
    latency_ms: float
    status_code: int
    success: bool
    cached: bool = False
    error: Optional[str] = None

@dataclass
class LoadTestResults:
    """Aggregated load test results."""
    config: WorkloadConfig
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    cache_hits: int

    latencies: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0

    @property
    def cache_hit_rate(self) -> float:
        return self.cache_hits / self.successful_requests if self.successful_requests > 0 else 0

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()

    @property
    def requests_per_second(self) -> float:
        return self.total_requests / self.duration_seconds if self.duration_seconds > 0 else 0

    def latency_percentile(self, p: float) -> float:
        if not self.latencies:
            return 0
        return np.percentile(self.latencies, p)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_requests": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests,
                "success_rate": f"{self.success_rate*100:.1f}%",
                "cache_hit_rate": f"{self.cache_hit_rate*100:.1f}%",
                "duration_seconds": round(self.duration_seconds, 1),
                "requests_per_second": round(self.requests_per_second, 2)
            },
            "latency_ms": {
                "min": round(min(self.latencies), 1) if self.latencies else 0,
                "max": round(max(self.latencies), 1) if self.latencies else 0,
                "mean": round(statistics.mean(self.latencies), 1) if self.latencies else 0,
                "median": round(statistics.median(self.latencies), 1) if self.latencies else 0,
                "p95": round(self.latency_percentile(95), 1),
                "p99": round(self.latency_percentile(99), 1)
            },
            "errors": self.errors[:10] if self.errors else []
        }

# ============================================================================
# Load Test Runner
# ============================================================================

class LoadTestRunner:
    """
    Executes load tests with configurable concurrency and workload patterns.
    """

    def __init__(self, config: WorkloadConfig):
        self.config = config
        self.workload_gen = ConverterWorkloadGenerator()
        self.metrics: List[RequestMetrics] = []
        self._request_counter = 0

    async def run(self) -> LoadTestResults:
        """Execute the load test."""
        console.print(f"\n[bold blue]Starting load test[/bold blue]")
        console.print(f"  Target: {self.config.base_url}")
        console.print(f"  Requests: {self.config.total_requests}")
        console.print(f"  Concurrent users: {self.config.concurrent_users}")
        console.print(f"  Ramp-up: {self.config.ramp_up_time}s\n")

        start_time = datetime.now()

        # Create user tasks
        requests_per_user = self.config.total_requests // self.config.concurrent_users
        extra_requests = self.config.total_requests % self.config.concurrent_users

        tasks = []
        for i in range(self.config.concurrent_users):
            user_requests = requests_per_user + (1 if i < extra_requests else 0)
            ramp_delay = (i / self.config.concurrent_users) * self.config.ramp_up_time
            tasks.append(self._run_user(i, user_requests, ramp_delay))

        # Run with progress tracking
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task_id = progress.add_task("Running load test...", total=self.config.total_requests)

            # Update progress as requests complete
            async def progress_tracker():
                last_count = 0
                while last_count < self.config.total_requests:
                    await asyncio.sleep(0.1)
                    current_count = len(self.metrics)
                    if current_count > last_count:
                        progress.update(task_id, advance=current_count - last_count)
                        last_count = current_count

            # Run users and progress tracker
            await asyncio.gather(
                asyncio.gather(*tasks),
                progress_tracker()
            )

        end_time = datetime.now()

        # Aggregate results
        results = LoadTestResults(
            config=self.config,
            start_time=start_time,
            end_time=end_time,
            total_requests=len(self.metrics),
            successful_requests=sum(1 for m in self.metrics if m.success),
            failed_requests=sum(1 for m in self.metrics if not m.success),
            cache_hits=sum(1 for m in self.metrics if m.cached),
            latencies=[m.latency_ms for m in self.metrics if m.success],
            errors=[m.error for m in self.metrics if m.error]
        )

        return results

    async def _run_user(self, user_id: int, num_requests: int, ramp_delay: float):
        """Simulate a single user making requests."""
        await asyncio.sleep(ramp_delay)

        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=self.config.timeout
        ) as client:
            for _ in range(num_requests):
                await self._make_request(client)

                # Think time between requests
                think_time = random.uniform(
                    self.config.think_time_min,
                    self.config.think_time_max
                )
                await asyncio.sleep(think_time)

    async def _make_request(self, client: httpx.AsyncClient):
        """Make a single design request and record metrics."""
        request_id = self._request_counter
        self._request_counter += 1

        request_data = self.workload_gen.generate_request()
        start_time = time.time()

        try:
            response = await client.post("/design", json=request_data)
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            cached = False
            if response.status_code == 200:
                result = response.json()
                cached = result.get("cached", False)

            metrics = RequestMetrics(
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                latency_ms=latency_ms,
                status_code=response.status_code,
                success=response.status_code == 200,
                cached=cached,
                error=None if response.status_code == 200 else f"HTTP {response.status_code}"
            )

        except Exception as e:
            end_time = time.time()
            metrics = RequestMetrics(
                request_id=request_id,
                start_time=start_time,
                end_time=end_time,
                latency_ms=(end_time - start_time) * 1000,
                status_code=0,
                success=False,
                error=str(e)
            )

        self.metrics.append(metrics)

# ============================================================================
# Results Display
# ============================================================================

def display_results(results: LoadTestResults):
    """Display load test results in formatted tables."""
    console.print("\n[bold green]Load Test Complete[/bold green]\n")

    # Summary table
    summary = Table(title="Summary")
    summary.add_column("Metric", style="cyan")
    summary.add_column("Value", justify="right")

    data = results.to_dict()
    for key, value in data["summary"].items():
        summary.add_row(key.replace("_", " ").title(), str(value))

    console.print(summary)

    # Latency table
    latency = Table(title="\nLatency Distribution (ms)")
    latency.add_column("Percentile", style="cyan")
    latency.add_column("Value", justify="right")

    for key, value in data["latency_ms"].items():
        latency.add_row(key.upper(), f"{value:.1f}")

    console.print(latency)

    # Errors
    if results.errors:
        console.print(f"\n[bold red]Errors ({len(results.errors)}):[/bold red]")
        for error in results.errors[:5]:
            console.print(f"  - {error}")

# ============================================================================
# Performance Analysis
# ============================================================================

class PerformanceAnalyzer:
    """
    Analyzes load test results and provides optimization recommendations.
    """

    @staticmethod
    def analyze(results: LoadTestResults) -> List[str]:
        """Generate performance recommendations based on results."""
        recommendations = []

        # Check success rate
        if results.success_rate < 0.99:
            recommendations.append(
                f"⚠️  Success rate {results.success_rate*100:.1f}% below 99% target. "
                "Consider: increasing timeouts, adding retries, or scaling capacity."
            )

        # Check latency
        p95 = results.latency_percentile(95)
        if p95 > 5000:  # 5 seconds
            recommendations.append(
                f"⚠️  P95 latency {p95:.0f}ms exceeds 5s threshold. "
                "Consider: model optimization, prompt caching, or response streaming."
            )

        # Check cache performance
        if results.cache_hit_rate < 0.2 and results.total_requests > 50:
            recommendations.append(
                f"📊 Cache hit rate {results.cache_hit_rate*100:.1f}% is low. "
                "Consider: normalizing request parameters, semantic caching, or longer TTL."
            )

        # Check throughput
        if results.requests_per_second < 1:
            recommendations.append(
                f"📈 Throughput {results.requests_per_second:.2f} req/s is low. "
                "Consider: increasing concurrency, optimizing prompts, or horizontal scaling."
            )

        # Check error patterns
        timeout_errors = sum(1 for e in results.errors if "timeout" in e.lower())
        if timeout_errors > results.total_requests * 0.05:
            recommendations.append(
                f"⏱️  {timeout_errors} timeout errors detected. "
                "Consider: increasing timeout limits, implementing streaming, or queue-based processing."
            )

        rate_limit_errors = sum(1 for e in results.errors if "429" in e)
        if rate_limit_errors > 0:
            recommendations.append(
                f"🚦 {rate_limit_errors} rate limit errors. "
                "Consider: implementing request queuing, backoff strategies, or higher rate limits."
            )

        if not recommendations:
            recommendations.append("✅ Performance looks good! No immediate optimizations needed.")

        return recommendations

# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run load test with analysis."""
    config = WorkloadConfig(
        base_url="http://localhost:8000",
        total_requests=50,
        concurrent_users=5,
        ramp_up_time=3.0
    )

    runner = LoadTestRunner(config)
    results = await runner.run()

    display_results(results)

    # Performance analysis
    console.print("\n[bold blue]Performance Analysis[/bold blue]")
    recommendations = PerformanceAnalyzer.analyze(results)
    for rec in recommendations:
        console.print(f"  {rec}")

    # Save results
    with open("load_test_results.json", "w") as f:
        json.dump(results.to_dict(), f, indent=2, default=str)
    console.print("\nResults saved to load_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
```

### Running the Load Test

```bash
# Install dependencies
pip install httpx numpy rich

# Start the service
docker-compose up -d

# Run load test
python load_test_framework.py

# Example output:
# Summary
# ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
# ┃ Metric               ┃  Value ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
# │ Total Requests       │     50 │
# │ Successful           │     48 │
# │ Failed               │      2 │
# │ Success Rate         │ 96.0%  │
# │ Cache Hit Rate       │ 24.0%  │
# │ Duration Seconds     │   45.3 │
# │ Requests Per Second  │   1.10 │
# └──────────────────────┴────────┘
```

---

## Exercise 1: Resilient LLM Service with Circuit Breaker (90 min)

**Objective:** Implement a production-grade thermal analysis service with advanced resilience patterns.

### Requirements

1. **Core Service Features:**
   - Analyze component thermal performance using Claude
   - Input: Component list with power dissipation and thermal resistances
   - Output: Junction temperatures, thermal margins, cooling recommendations

2. **Resilience Patterns:**
   - **Circuit breaker** with configurable thresholds
   - **Bulkhead isolation** - separate pools for different request priorities
   - **Retry with exponential backoff** and jitter
   - **Fallback responses** when service degraded

3. **Request Priority System:**
   - High priority: Safety-critical thermal checks (immediate)
   - Normal priority: Design optimization (queued)
   - Low priority: Documentation generation (best effort)

4. **Monitoring:**
   - Per-priority metrics (latency, success rate)
   - Circuit breaker state transitions
   - Queue depth and wait times

### Starter Code

```python
# thermal_analysis_service.py
"""
Exercise: Implement resilient thermal analysis service.
"""

import asyncio
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

import anthropic
from pydantic import BaseModel, Field

class Priority(Enum):
    HIGH = 1    # Safety-critical, immediate processing
    NORMAL = 2  # Standard design work
    LOW = 3     # Background tasks

@dataclass
class BulkheadConfig:
    """Configuration for bulkhead isolation."""
    high_priority_slots: int = 5
    normal_priority_slots: int = 10
    low_priority_slots: int = 3

class ThermalRequest(BaseModel):
    """Thermal analysis request."""
    components: list[Dict[str, Any]]  # name, power_w, rth_jc, rth_cs
    ambient_temp_c: float = 25.0
    max_junction_temp_c: float = 125.0
    priority: Priority = Priority.NORMAL

class ThermalResponse(BaseModel):
    """Thermal analysis response."""
    component_temps: list[Dict[str, float]]
    thermal_margins: list[Dict[str, float]]
    cooling_recommendations: list[str]
    warnings: list[str]
    priority: str
    queue_wait_ms: float
    processing_ms: float

class Bulkhead:
    """
    TODO: Implement bulkhead pattern for request isolation.

    Requirements:
    - Separate semaphores for each priority level
    - Prevent low-priority requests from starving high-priority
    - Track queue depth per priority
    """

    def __init__(self, config: BulkheadConfig):
        self.config = config
        # TODO: Create semaphores for each priority
        # TODO: Track queue depths
        pass

    async def acquire(self, priority: Priority) -> bool:
        """
        TODO: Acquire slot for given priority.
        Returns True if acquired, False if bulkhead full.
        """
        pass

    async def release(self, priority: Priority):
        """TODO: Release slot back to pool."""
        pass

class RetryPolicy:
    """
    TODO: Implement exponential backoff with jitter.

    Requirements:
    - Configurable max retries and base delay
    - Exponential backoff: delay = base * 2^attempt
    - Add random jitter to prevent thundering herd
    - Only retry on transient errors (timeout, 5xx)
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(self, func, *args, **kwargs):
        """
        TODO: Execute function with retry logic.
        """
        pass

class ThermalAnalysisService:
    """
    TODO: Complete the thermal analysis service.
    """

    def __init__(self):
        self.client = anthropic.AsyncAnthropic()
        self.bulkhead = Bulkhead(BulkheadConfig())
        self.retry = RetryPolicy()
        # TODO: Add circuit breaker
        # TODO: Add metrics

    async def analyze(self, request: ThermalRequest) -> ThermalResponse:
        """
        TODO: Implement thermal analysis with resilience patterns.

        Steps:
        1. Check circuit breaker state
        2. Acquire bulkhead slot (with timeout based on priority)
        3. Execute with retry policy
        4. Return result or fallback
        """
        pass

    async def _call_llm(self, request: ThermalRequest) -> Dict[str, Any]:
        """
        TODO: Make LLM call for thermal analysis.

        Prompt should request:
        - Junction temperature calculations
        - Thermal margin analysis
        - Cooling recommendations
        - Safety warnings
        """
        pass

    def _fallback_response(self, request: ThermalRequest) -> ThermalResponse:
        """
        TODO: Generate fallback response when service degraded.

        Use conservative estimates:
        - Assume worst-case thermal resistance
        - Flag all components as needing review
        - Recommend maximum cooling
        """
        pass

# FastAPI endpoints
# TODO: Implement /analyze endpoint with priority routing
# TODO: Implement /health endpoint with bulkhead status
# TODO: Implement /metrics endpoint
```

### Test Cases

```python
# test_thermal_service.py

import pytest
import asyncio

@pytest.mark.asyncio
async def test_high_priority_not_blocked():
    """High priority requests should not be blocked by low priority queue."""
    # Fill low priority bulkhead
    # Submit high priority request
    # Verify high priority completes quickly
    pass

@pytest.mark.asyncio
async def test_circuit_breaker_opens():
    """Circuit breaker should open after threshold failures."""
    # Inject failures
    # Verify circuit opens
    # Verify requests fail fast
    # Verify recovery after timeout
    pass

@pytest.mark.asyncio
async def test_fallback_on_degradation():
    """Should return fallback response when circuit open."""
    pass

@pytest.mark.asyncio
async def test_retry_with_backoff():
    """Should retry transient failures with exponential backoff."""
    pass
```

### Deliverables

1. Complete `ThermalAnalysisService` implementation
2. Working bulkhead and retry policies
3. Fallback response logic
4. All test cases passing
5. Metrics showing priority isolation

---

## Exercise 2: Monitoring Dashboard for LLM Service (75 min)

**Objective:** Build a real-time monitoring dashboard for the power converter design service.

### Requirements

1. **Metrics Collection:**
   - Request latency (p50, p95, p99)
   - Token usage (input/output)
   - Cache hit/miss rates
   - Error rates by type
   - Circuit breaker state

2. **Dashboard Components:**
   - Real-time latency chart
   - Token usage over time
   - Cache effectiveness
   - Error breakdown
   - Service health status

3. **Alerting Rules:**
   - P99 latency > 10s
   - Error rate > 5%
   - Cache hit rate < 10%
   - Circuit breaker open

### Starter Code

```python
# monitoring_dashboard.py
"""
Exercise: Build monitoring dashboard for LLM service.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import deque

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
import httpx

console = Console()

class MetricsCollector:
    """
    TODO: Collect metrics from Prometheus endpoint.

    Requirements:
    - Poll /metrics endpoint periodically
    - Parse Prometheus format
    - Store time series data (last N minutes)
    - Calculate aggregations (rate, percentiles)
    """

    def __init__(self, base_url: str, history_minutes: int = 10):
        self.base_url = base_url
        self.history = deque(maxlen=history_minutes * 60)  # 1 sample/sec

    async def collect(self):
        """TODO: Fetch and parse metrics."""
        pass

    def get_latency_percentiles(self) -> Dict[str, float]:
        """TODO: Calculate p50, p95, p99 from histogram."""
        pass

    def get_request_rate(self) -> float:
        """TODO: Calculate requests per second."""
        pass

    def get_error_rate(self) -> float:
        """TODO: Calculate error percentage."""
        pass

    def get_cache_hit_rate(self) -> float:
        """TODO: Calculate cache hit percentage."""
        pass

class AlertManager:
    """
    TODO: Manage alerting rules and notifications.

    Requirements:
    - Define alert thresholds
    - Track alert state (firing, resolved)
    - Avoid alert fatigue (debounce)
    """

    def __init__(self):
        self.alerts: Dict[str, bool] = {}
        self.rules = {
            "high_latency": lambda m: m.get_latency_percentiles().get("p99", 0) > 10000,
            "high_error_rate": lambda m: m.get_error_rate() > 0.05,
            "low_cache_hit": lambda m: m.get_cache_hit_rate() < 0.1,
            # TODO: Add more rules
        }

    def check_alerts(self, metrics: MetricsCollector) -> List[str]:
        """TODO: Check all rules and return firing alerts."""
        pass

class DashboardRenderer:
    """
    TODO: Render monitoring dashboard using Rich.
    """

    def __init__(self, metrics: MetricsCollector, alerts: AlertManager):
        self.metrics = metrics
        self.alerts = alerts

    def render_latency_panel(self) -> Panel:
        """
        TODO: Render latency metrics panel.

        Show:
        - Current p50, p95, p99
        - Trend indicator (↑↓→)
        - Mini sparkline if possible
        """
        pass

    def render_throughput_panel(self) -> Panel:
        """
        TODO: Render throughput panel.

        Show:
        - Requests per second
        - Token usage rate
        """
        pass

    def render_cache_panel(self) -> Panel:
        """
        TODO: Render cache performance panel.

        Show:
        - Hit rate percentage
        - Hits vs misses
        """
        pass

    def render_errors_panel(self) -> Panel:
        """
        TODO: Render error breakdown panel.

        Show:
        - Error rate
        - Breakdown by type (timeout, rate limit, etc.)
        """
        pass

    def render_health_panel(self) -> Panel:
        """
        TODO: Render service health panel.

        Show:
        - Circuit breaker state
        - Redis connection
        - Active alerts
        """
        pass

    def render(self) -> Layout:
        """TODO: Compose all panels into dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=5)
        )

        # TODO: Add panels to layout

        return layout

async def main():
    """
    TODO: Main dashboard loop.

    Requirements:
    - Collect metrics every second
    - Update display with Live context
    - Check alerts and display notifications
    - Handle keyboard interrupt gracefully
    """

    metrics = MetricsCollector("http://localhost:8000")
    alerts = AlertManager()
    dashboard = DashboardRenderer(metrics, alerts)

    with Live(console=console, refresh_per_second=1) as live:
        while True:
            await metrics.collect()
            firing = alerts.check_alerts(metrics)

            # Update display
            live.update(dashboard.render())

            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped[/yellow]")
```

### Expected Dashboard Output

```
┌─────────────────────────────────────────────────────────┐
│ Power Converter Design Service Monitor    [HEALTHY]     │
└─────────────────────────────────────────────────────────┘
┌─────────────────────┬─────────────────────┬─────────────┐
│ Latency (ms)        │ Throughput          │ Cache       │
├─────────────────────┼─────────────────────┼─────────────┤
│ P50:   450 →        │ 2.3 req/s           │ Hit: 34%    │
│ P95:  1200 →        │ 1.2k tokens/s       │ ████░░░░░░  │
│ P99:  3400 ↑        │                     │             │
└─────────────────────┴─────────────────────┴─────────────┘
┌─────────────────────┬──────────────────────────────────┐
│ Errors              │ Health                           │
├─────────────────────┼──────────────────────────────────┤
│ Rate: 1.2%          │ Circuit: CLOSED                  │
│ Timeout: 3          │ Redis: Connected                 │
│ Rate Limit: 0       │ Alerts: None                     │
│ Parse: 1            │                                  │
└─────────────────────┴──────────────────────────────────┘
```

### Deliverables

1. Working metrics collection from Prometheus endpoint
2. Dashboard with all required panels
3. Alert rules with proper debouncing
4. Screenshot of running dashboard
5. Documentation of alert thresholds and reasoning

---

## Summary

| Pattern | Use Case | Key Benefit |
|---------|----------|-------------|
| **Rate Limiting** | Prevent API abuse | Cost control, fair usage |
| **Caching** | Repeated queries | Latency reduction, cost savings |
| **Circuit Breaker** | API failures | Fail fast, prevent cascade |
| **Bulkhead** | Priority isolation | Guaranteed capacity |
| **Retry + Backoff** | Transient failures | Improved reliability |
| **Load Testing** | Capacity planning | Find limits before production |
| **Monitoring** | Operational visibility | Early problem detection |

### Production Checklist

- [ ] Rate limiting configured for all endpoints
- [ ] Caching strategy defined (TTL, invalidation)
- [ ] Circuit breaker thresholds tuned
- [ ] Retry policies with jitter
- [ ] Prometheus metrics exposed
- [ ] Alerts configured for SLOs
- [ ] Load tested at 2x expected traffic
- [ ] Fallback responses for degraded mode
- [ ] Structured logging with correlation IDs
- [ ] Health checks for dependencies

