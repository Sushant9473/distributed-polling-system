import hashlib
from bisect import bisect_right
from typing import List


class ConsistentHash:
    def __init__(self, nodes: List[str], virtual_nodes: int = 100):
        self.virtual_nodes = virtual_nodes
        self.hash_ring = {}
        self.sorted_keys = []

        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        """Helper to create a deterministic hash"""
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node: str) -> None:
        """Add a new node to the hash ring"""
        # Create virtual nodes for the new physical node
        for i in range(self.virtual_nodes):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.hash_ring[hash_value] = node
        
        # Update sorted_keys
        self.sorted_keys = sorted(self.hash_ring.keys())

    def get_node(self, key: str) -> str:
        """Get the node responsible for the given key"""
        if not self.hash_ring:
            raise ValueError("Hash ring is empty")

        # Calculate hash of the key
        key_hash = self._hash(key)
        
        # Find the first node in the ring that comes after the key's hash
        idx = bisect_right(self.sorted_keys, key_hash)
        
        # If no such node exists, wrap around to the first node
        if idx >= len(self.sorted_keys):
            idx = 0
        
        return self.hash_ring[self.sorted_keys[idx]]
