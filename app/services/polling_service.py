import asyncio
import time
from collections import defaultdict
from typing import Dict, Tuple

from app.core.config import settings
from app.core.redis_manager import RedisManager


class PollingService:
    # In-memory storage for Task 1 & Task 4 (Batch buffer)
    _memory_storage = defaultdict(lambda: defaultdict(int))
    
    # Application layer cache for Task 3 (TTL cache)
    _app_cache: Dict[str, Tuple[Dict[str, int], float]] = {}  # {poll_id: (results, timestamp)}
    _cache_ttl: float = 5.0  # 5 seconds TTL

    def __init__(self):
        self.redis_manager = RedisManager()

    async def vote(self, poll_id: str, option_id: str) -> None:
        """
        Registers a vote.
        Task 1: Store in memory.
        Task 2: Write to Redis immediately.
        Task 4: Buffer in memory (Batching).
        """
        # Buffer votes in memory (Task 4 - Batching)
        # This also serves Task 1 (in-memory storage)
        self._memory_storage[poll_id][option_id] += 1

    async def get_results(self, poll_id: str) -> Dict[str, int]:
        """
        Get results.
        Task 1: Read from memory.
        Task 2: Read from Redis.
        Task 3: Check App Cache -> Redis.
        Task 4: Redis + Memory Buffer.
        
        Returns: (results_dict, served_via_string)
        """
        # Combine Redis values with pending buffer values (Task 4)
        results = {}
        
        # Get from Redis (Task 2)
        client, node = await self.redis_manager.get_client_with_node(poll_id)
        redis_key = f"poll:{poll_id}"
        
        # Get all fields from the Redis hash
        redis_results = await client.hgetall(redis_key)
        for option, count in redis_results.items():
            results[option] = int(count)
        
        # Add pending buffer values (Task 4)
        if poll_id in self._memory_storage:
            for option, count in self._memory_storage[poll_id].items():
                results[option] = results.get(option, 0) + count
        
        return results

    async def get_results_with_source(self, poll_id: str) -> Tuple[Dict[str, int], str]:
        """
        Get results with source information for served_via field.
        Implements Task 3 (Application Layer Caching) with 5-second TTL.
        """
        current_time = time.time()
        
        # Task 3: Check application cache first
        if poll_id in self._app_cache:
            cached_results, cache_time = self._app_cache[poll_id]
            if current_time - cache_time < self._cache_ttl:
                # Cache hit - but still need to add pending buffer
                results = dict(cached_results)  # Copy cached results
                if poll_id in self._memory_storage:
                    for option, count in self._memory_storage[poll_id].items():
                        results[option] = results.get(option, 0) + count
                return results, "app_cache"
        
        # Cache miss - fetch from Redis
        client, node = await self.redis_manager.get_client_with_node(poll_id)
        redis_key = f"poll:{poll_id}"
        
        # Get all fields from the Redis hash
        redis_results = await client.hgetall(redis_key)
        redis_data = {}
        for option, count in redis_results.items():
            redis_data[option] = int(count)
        
        # Update app cache with Redis data
        self._app_cache[poll_id] = (redis_data, current_time)
        
        # Combine with pending buffer values (Task 4)
        results = dict(redis_data)
        if poll_id in self._memory_storage:
            for option, count in self._memory_storage[poll_id].items():
                results[option] = results.get(option, 0) + count
        
        # Determine served_via based on Redis node
        served_via = self.redis_manager.get_node_port(node)
        
        return results, served_via

    async def flush_batch(self):
        """
        Task 4: Background process to flush memory buffer to Redis.
        """
        while True:
            # Wait for BATCH_INTERVAL_SECONDS (10 seconds)
            await asyncio.sleep(settings.BATCH_INTERVAL_SECONDS)
            
            # Flush _memory_storage to Redis
            if self._memory_storage:
                # Swap in a fresh buffer before any await, so votes cast
                # during the flush go to the new buffer instead of being cleared
                polls_to_flush = self._memory_storage
                self._memory_storage = defaultdict(lambda: defaultdict(int))

                for poll_id, options in polls_to_flush.items():
                    if options:
                        client = await self.redis_manager.get_client(poll_id)
                        redis_key = f"poll:{poll_id}"

                        # Increment each option count in Redis
                        for option, count in options.items():
                            if count > 0:
                                await client.hincrby(redis_key, option, count)
                
                # Invalidate app cache after flushing (data has changed in Redis)
                self._app_cache.clear()
