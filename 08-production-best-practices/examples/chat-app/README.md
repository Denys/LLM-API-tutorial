# Production Chat Application

A production-ready chat application with complete monitoring, caching, and deployment setup.

## Features

- ✅ **FastAPI Backend** with async support
- ✅ **WebSocket Support** for streaming responses
- ✅ **PostgreSQL Database** for conversation persistence
- ✅ **Redis Caching** for response caching
- ✅ **Prometheus Metrics** for monitoring
- ✅ **Structured Logging** with JSON output
- ✅ **Rate Limiting** to prevent abuse
- ✅ **Health Checks** for Kubernetes/Docker
- ✅ **Docker Deployment** with docker-compose
- ✅ **Nginx Reverse Proxy** with load balancing
- ✅ **Security Best Practices** (input validation, CORS, etc.)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Anthropic API key

### 1. Set Up Environment

```bash
# Copy environment template
cp .env.template .env

# Edit .env and add your API key
nano .env
```

Add your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 2. Start the Stack

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Chat request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Calculate the resistor value for a 12V LED with 2.1V forward voltage and 20mA current"
  }'
```

### 4. Access Monitoring

- **Application:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)
- **Metrics:** http://localhost:8000/metrics

## Architecture

```
┌─────────────┐
│   Nginx     │  Reverse proxy, load balancing, rate limiting
└──────┬──────┘
       │
┌──────▼──────┐
│  FastAPI    │  Application server (4 workers)
│   (App)     │
└──┬────┬────┬┘
   │    │    │
   │    │    └────────┐
   │    │             │
┌──▼────▼─┐      ┌───▼─────┐
│  Redis  │      │PostgreSQL│  Persistence
│ (Cache) │      │   (DB)   │
└─────────┘      └──────────┘

┌────────────┐   ┌──────────┐
│Prometheus  │   │ Grafana  │  Monitoring
└────────────┘   └──────────┘
```

## API Endpoints

### POST /chat

Chat with the AI assistant.

**Request:**
```json
{
  "message": "Your question here",
  "conversation_id": "optional-conversation-id",
  "use_cache": true,
  "stream": false
}
```

**Response:**
```json
{
  "response": "AI response here",
  "conversation_id": "uuid",
  "tokens_used": 150,
  "latency_ms": 1234.5,
  "cached": false
}
```

### WebSocket /ws/chat

Streaming chat interface.

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "Calculate power in a 100Ω resistor with 5V",
    conversation_id: "optional-id"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'chunk') {
    console.log(data.content);
  } else if (data.type === 'complete') {
    console.log('Done:', data.conversation_id);
  }
};
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "services": {
    "database": true,
    "redis": true,
    "anthropic": true
  }
}
```

### GET /metrics

Prometheus metrics endpoint.

## Database Schema

The application uses PostgreSQL with the following main tables:

- **conversations** - Conversation metadata
- **messages** - Individual messages
- **users** - User accounts (optional)
- **api_keys** - API key management (optional)
- **usage_tracking** - Token usage and cost tracking
- **feedback** - User feedback on responses

See `schema.sql` for complete schema.

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis
REDIS_URL=redis://host:port

# Application
PORT=8000
LOG_LEVEL=INFO
WORKERS=4

# Security (optional)
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=20

# Caching
CACHE_TTL=3600  # 1 hour
```

## Monitoring

### Prometheus Metrics

The application exposes the following metrics:

- `chat_requests_total` - Total chat requests (by status)
- `chat_latency_seconds` - Request latency histogram
- `tokens_used_total` - Token usage (by model and type)
- `active_websocket_connections` - Active WebSocket connections
- `cache_hits_total` - Cache hits
- `cache_misses_total` - Cache misses

### Grafana Dashboards

Pre-configured dashboards for:
- Request rate and latency
- Token usage and cost
- Cache hit rate
- Error rate
- Database performance

### Structured Logging

All logs are in JSON format for easy parsing:

```json
{
  "event": "chat_request",
  "level": "info",
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "request_id": "uuid",
  "conversation_id": "uuid",
  "message_length": 50,
  "use_cache": true
}
```

## Security

### Input Validation

- Message length limits (1-10,000 characters)
- Conversation ID format validation
- Prompt injection detection (logged, not blocked)

### Rate Limiting

- 20 requests per minute per IP
- Configurable per-user limits with API keys
- Burst allowance for legitimate traffic

### Authentication (Optional)

Implement JWT-based authentication:

```python
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/chat")
async def chat(
    msg: ChatMessage,
    credentials = Depends(security)
):
    # Verify token
    user = verify_token(credentials.credentials)
    # ...
```

### CORS

Configure for your domain in production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Performance Optimization

### Caching

Responses are cached in Redis with:
- 1-hour TTL by default
- SHA-256 hash of messages as key
- Automatic cache invalidation

Disable caching per-request:
```json
{"message": "...", "use_cache": false}
```

### Connection Pooling

- Database: 2-10 connections
- Redis: Persistent connections
- HTTP client: Connection reuse

### Worker Processes

Run multiple Uvicorn workers:
```bash
uvicorn main:app --workers 4
```

Or use Gunicorn:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Cost Management

Track costs with the `usage_tracking` table:

```sql
-- Daily cost by user
SELECT
    DATE(created_at) as date,
    user_id,
    SUM(cost) as total_cost,
    SUM(input_tokens + output_tokens) as total_tokens
FROM usage_tracking
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), user_id;
```

Set budget limits:
```python
class BudgetMiddleware:
    async def __call__(self, request: Request, call_next):
        user_id = get_user_id(request)
        if await is_over_budget(user_id):
            raise HTTPException(429, "Budget exceeded")
        return await call_next(request)
```

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t chat-app:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  chat-app:latest
```

### Kubernetes Deployment

See `kubernetes/` directory for manifests:

```bash
# Create namespace
kubectl create namespace chat-app

# Create secret
kubectl create secret generic llm-secrets \
  --from-literal=anthropic-api-key=sk-ant-... \
  -n chat-app

# Deploy
kubectl apply -f kubernetes/ -n chat-app

# Check status
kubectl get pods -n chat-app
```

### Cloud Platforms

#### AWS (Elastic Beanstalk)

```bash
eb init -p python-3.11 chat-app
eb create production-env
eb deploy
```

#### Google Cloud Run

```bash
gcloud run deploy chat-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure (Container Instances)

```bash
az container create \
  --resource-group chat-app-rg \
  --name chat-app \
  --image chat-app:latest \
  --dns-name-label chat-app \
  --ports 8000
```

## Scaling

### Horizontal Scaling

Add more application instances:

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 4
```

Or in Kubernetes:
```yaml
spec:
  replicas: 10
  ...
```

### Database Scaling

- Read replicas for queries
- Connection pooling
- Partitioning for large tables

### Redis Scaling

- Redis Cluster for high availability
- Read replicas for caching
- Separate caches per service

## Troubleshooting

### High Latency

Check:
- Database query performance
- Redis connection
- LLM API latency
- Worker count

### Memory Issues

- Reduce worker count
- Increase memory limits
- Check for memory leaks
- Monitor with Prometheus

### Database Errors

```bash
# Check connections
docker-compose exec db psql -U chatuser -d chatdb -c "\
  SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
docker-compose exec db psql -U chatuser -d chatdb -c "\
  SELECT query, calls, mean_exec_time \
  FROM pg_stat_statements \
  ORDER BY mean_exec_time DESC LIMIT 10;"
```

### Cache Issues

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Monitor cache stats
docker-compose exec redis redis-cli info stats

# Clear cache
docker-compose exec redis redis-cli FLUSHALL
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run database
docker-compose up -d db redis

# Run application
uvicorn main:app --reload

# Run tests
pytest

# Format code
black .
ruff check .

# Type checking
mypy .
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Only unit tests
pytest tests/unit/

# Only integration tests
pytest tests/integration/
```

## License

MIT

## Support

For issues and questions:
- GitHub Issues
- Documentation: See main README
- Email: support@example.com
