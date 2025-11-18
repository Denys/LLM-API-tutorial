# Quick Start - Module 8: Production & Best Practices

Get your production LLM applications running in 10 minutes!

## What You'll Deploy

1. **Production Chat App** - Full-stack chat with monitoring
2. **Autonomous Agent System** - Background task processing
3. **API Wrapper Service** - Clean abstraction layer

## Quick Deployment

### Option 1: Chat Application

```bash
cd 08-production-best-practices/examples/chat-app

# Set API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key" > .env

# Start everything
docker-compose up -d

# Test
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Calculate 12V / 100Ω power"}'
```

**Access:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### Option 2: Agent System

```bash
cd 08-production-best-practices/examples/agent-app

# Set API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key" > .env

# Start everything
docker-compose up -d

# Submit task
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "calculation",
    "description": "Calculate power in 100Ω resistor with 12V"
  }'

# Get task status (use task_id from response)
curl http://localhost:8001/tasks/{task_id}
```

**Access:**
- API: http://localhost:8001/docs
- Celery Flower: http://localhost:5555
- Grafana: http://localhost:3000

### Option 3: API Wrapper (Local)

```bash
cd 08-production-best-practices/examples/api-wrapper

# Install dependencies
pip install anthropic openai redis python-dotenv structlog

# Set API keys
export ANTHROPIC_API_KEY=sk-ant-your-key
export OPENAI_API_KEY=sk-your-key  # Optional for fallback

# Run example
python llm_service.py
```

## Testing

### Run Unit Tests

```bash
cd 08-production-best-practices

# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest testing/ -v

# With coverage
pytest testing/ --cov --cov-report=html
```

### Run Integration Tests

```bash
# Requires API keys
export ANTHROPIC_API_KEY=sk-ant-your-key

# Run integration tests
pytest testing/ -v -m integration
```

## Monitoring

### View Metrics

```bash
# Prometheus
open http://localhost:9090

# Grafana
open http://localhost:3000
# Login: admin/admin
```

### View Logs

```bash
# Chat app
docker-compose -f examples/chat-app/docker-compose.yml logs -f app

# Agent system
docker-compose -f examples/agent-app/docker-compose.yml logs -f worker
```

## Production Checklist

Before deploying to production:

- [ ] Set strong passwords (PostgreSQL, Grafana, etc.)
- [ ] Configure HTTPS/SSL
- [ ] Set up proper CORS origins
- [ ] Configure rate limits for your use case
- [ ] Set up alerting rules in Prometheus
- [ ] Configure log aggregation
- [ ] Set up backup strategy for database
- [ ] Configure auto-scaling policies
- [ ] Set budget limits and cost alerts
- [ ] Enable authentication/authorization
- [ ] Review security settings
- [ ] Configure proper secret management
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring dashboards
- [ ] Set up error tracking (Sentry, etc.)

## Common Tasks

### Scale Workers

```bash
# Chat app - add more uvicorn workers
docker-compose up -d --scale app=4

# Agent system - add more Celery workers
docker-compose up -d --scale worker=10
```

### View Database

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U chatuser -d chatdb

# Run query
SELECT * FROM conversations LIMIT 10;
```

### Clear Cache

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

### Restart Services

```bash
# Restart specific service
docker-compose restart app

# Restart all
docker-compose restart
```

## Troubleshooting

### Services won't start

```bash
# Check logs
docker-compose logs

# Check if ports are in use
sudo lsof -i :8000
sudo lsof -i :5432
```

### Database connection errors

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify credentials in .env
cat .env
```

### High memory usage

```bash
# Check resource usage
docker stats

# Reduce workers
docker-compose up -d --scale app=2 --scale worker=2
```

## Next Steps

1. **Explore Examples**
   - Review code in `examples/`
   - Understand architecture patterns
   - Check monitoring dashboards

2. **Run Exercises**
   - Complete exercises in `exercises/`
   - Build custom applications
   - Practice deployment

3. **Production Deployment**
   - Choose cloud platform (AWS, GCP, Azure)
   - Set up CI/CD
   - Configure monitoring
   - Deploy!

## Resources

- **Full Documentation:** [README.md](README.md)
- **Chat App:** [examples/chat-app/README.md](examples/chat-app/README.md)
- **Agent System:** [examples/agent-app/README.md](examples/agent-app/README.md)
- **Testing Guide:** [testing/README.md](testing/README.md)

## Get Help

- Check logs: `docker-compose logs -f`
- View API docs: http://localhost:8000/docs
- Monitor queues: http://localhost:5555 (Flower)
- View metrics: http://localhost:9090 (Prometheus)

---

**Ready to deploy? Start with the chat app:**

```bash
cd examples/chat-app && docker-compose up -d
```
