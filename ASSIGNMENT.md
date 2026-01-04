
# Implement Distributed Live Polling System

- **Release Date:** 22nd December, 2025
- **Due Date:** `11.59 pm`, 4th January, 2026 _(last day of winter break)_
- **Total Points:** 100

## Overview
In this assignment, you will implement the backend for a **Live Polling System** used for real-time voting (like in reality TV shows).

You are required to implement application caching, use Redis for persistence, and handle system scaling via Sharding and Batching.

## Learning Objectives
By completing this assignment, you will:
1. Implement **Read-Through** and **Write-Behind** caching strategies
2. Work with Redis for efficient data storage.
3. Design a scalable system using **Sharding** and **Consistent Hashing**.

_(unless you use chatgpt, in which case you will only learn how to prompt it better)_

---

## Tasks & Scoring

### Task 1: Basic In-Memory Polling `(20 points)`

**Objective:** Implement a basic API to cast votes and view results. Keep the data in memory.

- **Requirements:**
    - Implement `POST /vote/{poll_id}` to increment a counter for a specific option.
    - Implement `GET /results/{poll_id}` to return total votes.
    - Store data in a Python dictionary (In-Memory).
- **Response Format:**
    ```json
    {
        "poll_id": "100",
        "results": {
            "A": 1
        },
        "served_via": "in_memory"
    }
    ```
- **Testing Criteria:**
    - Votes must be counted correctly for different options.
    - Restart the Docker container: all vote data should be lost.

### Task 2: Persistence with Redis `(20 points)`

**Objective:** Modify the system to store data in Redis so votes survive server restarts.
- **Requirements:**
    - Connect `app/core/redis_manager.py` to Redis.
    - Updates should happen directly in Redis (no buffering yet).
- **Response Format:**
    ```json
    {
        "poll_id": "100",
        "results": {
            "A": 1
        },
        "served_via": "redis"
    }
    ```
- **Testing Criteria:**
    - Restart the application: previous votes must remain visible.

### Task 3: Application Layer Caching `(20 points)`

**Objective:** Reduce Redis read load by implementing a localized TTL cache.
- **Requirements:**
    - Implement an in-memory map in `PollingService` to cache results for **5 seconds**.
    - On `GET /results`, check cache first. If missing/expired, fetch from Redis and update cache.
    - Writes still go directly to Redis.
- **Response Format:**
    - Cache Hit: `served_via: "app_cache"`
    - Cache Miss: `served_via: "redis"`

### Task 4: Batching Writes `(20 points)`

**Objective:** Optimize write performance by buffering votes in memory and flushing periodically.
- **Requirements:**
    - Modify `vote()` to store counts in an in-memory buffer instead of Redis.
    - Implement `flush_batch()` to push data to Redis every **10 seconds**.
    - `GET /results` must return `(Redis Value + Pending Buffer Value)`.
- **Testing Criteria:**
    - Cast a vote. Check Redis CLI immediately: value should NOT change.
    - Wait 10 seconds. Check Redis CLI: value SHOULD change.

### Task 5: Redis Sharding `(20 points)`

**Objective:** Scale the system by distributing polls across two Redis instances (Ports 7000 & 7001).
- **Requirements:**
    - Implement Consistent Hashing in `app/core/consistent_hash.py`.
    - Route requests to the correct Redis node based on `poll_id`.
    - Use the provided `docker-compose.yml` which spins up `redis-node-1` and `redis-node-2`.
- **Response Format:**
    - `served_via: "redis_7000"` or `served_via: "redis_7001"` (debug field).
- **Testing Criteria:**
    - Verify different Poll IDs land on different Redis nodes consistently.

---

## Grading Rubric

| Task                | Points  |
|:--------------------|:--------|
| Basic Polling API   | 20      |
| Redis Persistence   | 20      |
| Application Caching | 20      |
| Batching Writes     | 20      |
| Redis Sharding      | 20      |
| **Total**           | **100** |

## Submission Guidelines

1. Submit your code via the form: https://forms.gle/dCGQwnHFNbpTUNt29
2. GitHub Repository MUST be **Private**.  
   Provide read access to: [AgarwalPragy](https://github.com/AgarwalPragy) and [anshumansingh](https://github.com/anshumansingh).
3. Include a `README.md` with setup instructions. Remember to document any specific setup steps if you deviated from the boilerplate.
4. **Due Date:** `11.59 pm`, 4th January, 2026 _(last day of winter break)_
