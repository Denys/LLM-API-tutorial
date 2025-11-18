# Production Standalone Agent Application

A production-ready autonomous agent system with distributed task processing, monitoring, and resilience.

## Features

- ✅ **Autonomous Agent** with tool use
- ✅ **Task Queue** (Celery + Redis)
- ✅ **Background Processing** with multiple workers
- ✅ **State Persistence** in Redis
- ✅ **RESTful API** for task submission
- ✅ **Monitoring** (Prometheus + Grafana)
- ✅ **Celery Flower** for queue monitoring
- ✅ **Error Handling** with retry logic
- ✅ **Graceful Shutdown**
- ✅ **Docker Deployment**

## Quick Start

### 1. Set Up Environment

```bash
# Copy environment template
cp .env.template .env

# Add your API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
```

### 2. Start the System

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f worker
```

### 3. Submit a Task

```bash
# Submit via API
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "calculation",
    "description": "Calculate power in a 100 ohm resistor with 12V across it",
    "parameters": {"voltage": 12, "resistance": 100}
  }'

# Response:
# {"task_id": "uuid", "status": "submitted"}
```

### 4. Check Task Status

```bash
# Get task status
curl http://localhost:8001/tasks/{task_id}

# Response:
# {
#   "id": "uuid",
#   "status": "completed",
#   "result": "Power = 1.44W",
#   "iterations_used": 3,
#   "tokens_used": 250
# }
```

### 5. Monitor

- **API Docs:** http://localhost:8001/docs
- **Celery Flower:** http://localhost:5555
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP
       ▼
┌──────────────┐
│  FastAPI     │  Task submission API
│   (api.py)   │
└──────┬───────┘
       │
       │ Redis (broker)
       ▼
┌──────────────┐
│   Celery     │  Task queue
│    Queue     │
└──────┬───────┘
       │
  ┌────┴────┬────────┬────────┐
  │         │        │        │
  ▼         ▼        ▼        ▼
┌────┐   ┌────┐  ┌────┐   ┌────┐
│W 1 │   │W 2 │  │W 3 │   │W 4 │  Workers
└─┬──┘   └─┬──┘  └─┬──┘   └─┬──┘
  │         │        │        │
  └─────────┴────────┴────────┘
            │
            │ State
            ▼
       ┌─────────┐
       │  Redis  │  State storage
       └─────────┘
```

## API Endpoints

### POST /tasks

Submit a task to the agent.

**Request:**
```json
{
  "type": "design",
  "description": "Design a buck converter...",
  "parameters": {
    "input_voltage": 24,
    "output_voltage": 5,
    "output_current": 5
  },
  "max_iterations": 15,
  "timeout": 300
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "submitted",
  "message": "Task submitted successfully"
}
```

### GET /tasks/{task_id}

Get task status and results.

**Response:**
```json
{
  "id": "uuid",
  "type": "design",
  "status": "completed",
  "result": "Buck converter design...",
  "iterations_used": 8,
  "tokens_used": 2500,
  "created_at": "2024-01-15T10:00:00",
  "completed_at": "2024-01-15T10:02:30"
}
```

## Task Types

- **calculation**: Mathematical calculations
- **design**: Component/circuit design
- **analysis**: Circuit analysis
- **optimization**: Design optimization

## Scaling

### Horizontal Scaling

Add more workers:

```bash
docker-compose up -d --scale worker=10
```

### Worker Configuration

```yaml
worker:
  deploy:
    replicas: 10
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

## Monitoring

### Celery Flower

Web-based monitoring tool for Celery:
- Active tasks
- Task history
- Worker status
- Task rates

Access at: http://localhost:5555

### Prometheus Metrics

- `agent_tasks_submitted_total` - Tasks submitted
- `agent_tasks_completed_total` - Tasks completed (by status)
- `agent_task_duration_seconds` - Task duration
- `agent_active_tasks` - Currently running tasks
- `agent_tool_calls_total` - Tool calls (by tool and status)

### Grafana Dashboards

Pre-configured dashboards for:
- Task throughput
- Task latency
- Success/failure rates
- Worker utilization
- Queue depth

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start worker
celery -A agent worker --loglevel=info

# Start API (in another terminal)
uvicorn api:app --reload

# Test single task
python agent.py test
```

### Testing

Submit test tasks:

```bash
# Design task
curl -X POST http://localhost:8001/tasks/design/buck-converter \
  -H "Content-Type: application/json" \
  -d '{
    "input_voltage": 24,
    "output_voltage": 5,
    "output_current": 5,
    "efficiency_target": 0.9
  }'

# Calculation task
curl -X POST http://localhost:8001/tasks/calculate/resistor-power \
  -H "Content-Type: application/json" \
  -d '{"voltage": 12, "resistance": 100}'
```

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis (for state)
REDIS_URL=redis://localhost:6379/1

# Agent
AGENT_MODEL=claude-3-5-sonnet-20241022

# API
PORT=8001
```

### Celery Configuration

```python
app.conf.update(
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_prefetch_multiplier=1,  # Take 1 task at a time
    worker_max_tasks_per_child=100,  # Restart after 100 tasks
)
```

## Troubleshooting

### Tasks Not Processing

```bash
# Check worker status
docker-compose logs worker

# Check Celery Flower
open http://localhost:5555

# Check Redis
docker-compose exec redis redis-cli ping

# Purge queue
docker-compose exec worker celery -A agent purge
```

### High Memory Usage

```bash
# Reduce worker concurrency
docker-compose up -d --scale worker=2

# Or update docker-compose.yml:
command: celery -A agent worker --loglevel=info --concurrency=2
```

### Task Timeouts

Increase timeout in task submission:
```json
{
  "type": "design",
  "description": "...",
  "timeout": 600
}
```

## Production Best Practices

1. **Use multiple workers** for parallel processing
2. **Monitor queue depth** - scale workers as needed
3. **Set appropriate timeouts** for different task types
4. **Implement retry logic** for transient failures
5. **Use result expiration** to clean up old results
6. **Monitor worker health** and auto-restart on failure
7. **Log all task executions** for debugging
8. **Track costs** via token usage metrics

## License

MIT
