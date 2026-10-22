# Distributed Live Polling System

A backend for real-time voting (like live polls during a TV show), built with **FastAPI**, **Redis** and **Docker Compose**.

- Votes are **buffered in memory and flushed to Redis in batches**.
- Results are served through a **short-lived application cache**.
- Polls are **sharded across two Redis nodes** using a custom **consistent hashing** ring.

> Built as a course assignment at Scaler School of Technology (see `ASSIGNMENT.md`). The FastAPI app skeleton and `docker-compose.yml` were provided. I wrote the consistent hashing, sharding, caching and batching logic.

## Architecture

```
                         ┌──────────────────────── FastAPI app (:8000) ────────────────────────┐
POST /vote/{poll_id} ──▶ │ in-memory vote buffer ──(background task, every 10 s)──▶ HINCRBY ───┼──┐
                         │                                                                     │  │
GET /results/{poll_id} ─▶│ app cache (5 s TTL) ──miss──▶ HGETALL ──────────────────────────────┼──┤
                         │      + pending buffer counts                                        │  │
                         └─────────────────────────────────────────────────────────────────────┘  │
                                         consistent hash ring: poll_id ──▶ Redis node             │
                                                                                                  ▼
                                                              redis-node-1 (:7000)   redis-node-2 (:7001)
```

Both Redis nodes run with AOF persistence (`--appendonly yes`) and Docker volumes, so votes survive restarts.

## How it works

### Write path: write-behind batching
1. `POST /api/v1/vote/{poll_id}` only increments a counter in an in-memory buffer. There is no Redis call on the request path.
2. The vote also invalidates that poll's cached results.
3. A background task, started when the app starts, runs every 10 seconds (`BATCH_INTERVAL_SECONDS`). For each buffered poll it:
   - finds the poll's Redis node on the hash ring,
   - runs `HINCRBY poll:{poll_id} {option} {count}`,
   - clears the buffer.

   After the flush, the results cache is cleared.

### Read path: application cache
1. `GET /api/v1/results/{poll_id}` first checks an in-memory cache with a 5-second TTL. A hit returns `served_via: "app_cache"`.
2. On a miss, it reads `HGETALL poll:{poll_id}` from the poll's Redis node and caches the result. That returns `served_via: "redis_7000"` or `"redis_7001"`.
3. In both cases, votes still waiting in the buffer are added on top, so results include unflushed votes.

### Sharding: consistent hashing
- `app/core/consistent_hash.py` places each Redis node on a ring **100 times** (virtual nodes), using the MD5 hash of `"{node}:{i}"`.
- A poll is routed by hashing its `poll_id` and taking the first virtual node clockwise. This is a binary search with `bisect_right` that wraps around to the start of the ring.
- Virtual nodes spread polls evenly across nodes. Adding a node only remaps the polls in that node's ranges. With `hash(poll_id) % N`, almost every poll would move.

### Data model
One Redis **hash** per poll: key `poll:{poll_id}`, field = option id, value = vote count.

## Trade-offs
- **A crash can lose up to 10 s of votes.** That's the price of write-behind batching, which in return cuts Redis writes dramatically.
- **The buffer and cache live inside one process.** The design assumes a single app instance. With several instances, each would hold its own pending votes.
- **No rebalancing.** Adding a Redis node changes where some polls are routed, but their existing data isn't migrated.

## API

| Method | Endpoint | Body | Response |
|---|---|---|---|
| `GET` | `/` | – | `{"status": "healthy"}` |
| `POST` | `/api/v1/vote/{poll_id}` | `{"option_id": "A"}` | `{"status": "success", "message": "Vote accepted"}` |
| `GET` | `/api/v1/results/{poll_id}` | – | `{"poll_id": "100", "results": {"A": 3}, "served_via": "app_cache"}` |

## Running it

Prerequisite: Docker & Docker Compose.

```bash
git clone https://github.com/Sushant9473/distributed-polling-system.git
cd distributed-polling-system
docker compose up --build
```

This starts the API at http://localhost:8000 and the Redis nodes at `localhost:7000` and `localhost:7001`.

## Trying it

```bash
# Cast a vote (option A in poll 100)
curl -X POST http://localhost:8000/api/v1/vote/100 \
  -H "Content-Type: application/json" \
  -d '{"option_id": "A"}'

# Get results
curl http://localhost:8000/api/v1/results/100
```

To watch batching happen, cast a vote and check Redis straight away: the count hasn't changed yet. Check again after 10 seconds and it has.

```bash
docker compose exec redis-node-1 redis-cli keys "*"
docker compose exec redis-node-2 redis-cli keys "*"
```

## Project structure

```
app/
├── api/v1/endpoints/polls.py   # Routes; starts the batch-flush task on startup
├── core/
│   ├── config.py               # Settings (Redis nodes, virtual nodes, batch interval)
│   ├── consistent_hash.py      # Hash ring with virtual nodes
│   └── redis_manager.py        # One client per Redis node; routes poll_id to its node
├── schemas/poll.py             # Request/response models
├── services/polling_service.py # Vote buffer, results cache, batch flush
└── main.py                     # App entry point + health check
docker-compose.yml              # App + two Redis nodes
Dockerfile
```
