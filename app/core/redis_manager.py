from typing import Dict, Tuple

import redis.asyncio as redis  # Using async redis for FastAPI

from .config import settings
from .consistent_hash import ConsistentHash


class RedisManager:
    def __init__(self):
        self.clients: Dict[str, redis.Redis] = {}
        self.consistent_hash = None

        # Parse nodes
        nodes = [n.strip() for n in settings.REDIS_NODES.split(",") if n.strip()]
        
        # Initialize consistent hashing for Sharding (Task 5)
        if nodes:
            self.consistent_hash = ConsistentHash(nodes, settings.VIRTUAL_NODES)

        # Initialize clients for each node
        for node in nodes:
            self.clients[node] = redis.from_url(node, decode_responses=True)

    async def get_client(self, key: str) -> redis.Redis:
        """Return the correct Redis client based on the Sharding Key (poll_id)"""
        if not self.clients:
            raise ValueError("No Redis clients available")
        
        if self.consistent_hash:
            # Use consistent hashing to determine which node should handle this key
            node = self.consistent_hash.get_node(key)
            return self.clients[node]
        else:
            # Fallback to first client if consistent hashing not available
            return list(self.clients.values())[0]

    async def get_client_with_node(self, key: str) -> Tuple[redis.Redis, str]:
        """Return the correct Redis client and node URL based on the Sharding Key"""
        if not self.clients:
            raise ValueError("No Redis clients available")
        
        if self.consistent_hash:
            node = self.consistent_hash.get_node(key)
            return self.clients[node], node
        else:
            node = list(self.clients.keys())[0]
            return self.clients[node], node
    
    def get_node_port(self, node_url: str) -> str:
        """Extract a friendly port identifier from the node URL for served_via"""
        # Map internal docker ports to external ports for display
        if "redis-node-1" in node_url or node_url.endswith(":7000"):
            return "redis_7000"
        elif "redis-node-2" in node_url or node_url.endswith(":7001"):
            return "redis_7001"
        else:
            # Generic fallback
            return "redis"
