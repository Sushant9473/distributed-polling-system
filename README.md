# Distributed Live Polling System

This is the starter codebase for the "Distributed Live Polling System" assignment.

You will implement a high-throughput backend service using FastAPI, Redis, and Docker, simulating a real-time voting platform for live events.

## Architecture Overview

The system consists of the following components:

1. **FastAPI Application:** Handles HTTP requests (`POST /vote`, `GET /results`).
2. **Redis Cluster _(Simulated)_:** Two distinct Redis instances (ports 7000, 7001) to demonstrate sharding.
3. **Consistent Hashing:** A custom implementation to distribute Poll IDs across Redis nodes.
4. **Batch Processing:** A background worker to aggregate votes in memory before flushing to Redis.

## Prerequisites

- Docker & Docker Compose
- Python 3.14+ (if running locally without Docker)
- Postman (or `curl`) for testing

## Setup Instructions

1. Clone this repository
    ```bash
    git clone https://github.com/AgarwalPragy/distributed-live-polling-system.git
   cd distributed-live-polling-system && ls -la
    ```
2. Start the infrastructure:
    ```bash
    docker compose up --build
    ```
    This will start:
    - The API server at http://localhost:8000
    - Redis Node 1 at `localhost:7000`
    - Redis Node 2 at `localhost:7001`

3. Verify Health:
    Visit http://localhost:8000/ to see
    ```json
    {"status": "healthy"}
   ```

## Project Structure

```
.
├── app/
│   ├── api/v1/endpoints/      # API Route definitions
│   ├── core/
│   │   ├── config.py          # Settings (Redis URLs, Batch intervals)
│   │   ├── consistent_hash.py # TODO: Implement Ring Topology here
│   │   └── redis_manager.py   # TODO: Implement Sharding logic here
│   ├── services/
│   │   └── polling_service.py # TODO: Implement Caching & Batching here
│   └── main.py                # App entry point
├── docker-compose.yml         # Defines Redis shards and App container
├── Dockerfile
└── requirements.txt
```

## Quick Start Testing

You can interact with the API using `curl`:

```bash
# Cast a vote (Option 'A' in Poll '100')
curl -X POST http://localhost:8000/api/v1/vote/100 \
  -H "Content-Type: application/json" \
  -d '{"option_id": "A"}'

# Get Results
curl http://localhost:8000/api/v1/results/100
```

## Debugging

- **Logs:** The docker container streams logs to stdout. Watch them to see when the batch flushes occur:
    ```bash
    docker logs -f distributed_live_polling_system-app-1
    ```
- **Redis CLI:** You can inspect specific shards directly to verify data distribution.
    ```bash
    # Check Node 1 (Port 7000)
    docker exec -it distributed_live_polling_system-redis-node-1-1 redis-cli keys "*"

    # Check Node 2 (Port 7001)
    docker exec -it distributed_live_polling_system-redis-node-2-1 redis-cli keys "*"
    ```