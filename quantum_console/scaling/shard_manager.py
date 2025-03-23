from typing import Dict, List, Set, Optional, Tuple
import asyncio
import logging
from datetime import datetime
from threading import Lock
import numpy as np
from dataclasses import dataclass
import hashlib
import json
import base64

from ..core.quantum_encryption import QuantumEncryption
from ..models import Entity, Zone
from ..spatial_auth import SphericalCoordinates

@dataclass
class ShardConfig:
    """Configuration for shard management."""
    min_shard_size: int = 1024  # bytes
    max_shard_size: int = 1024 * 1024  # 1MB
    redundancy_factor: int = 3
    rebalance_threshold: float = 0.2  # 20% imbalance triggers rebalancing
    encryption_strength: str = "kyber1024"  # Post-quantum encryption level

@dataclass
class NodeMetrics:
    """Metrics for a storage node."""
    shard_count: int
    storage_used: int
    storage_capacity: int
    cpu_usage: float
    memory_usage: float
    network_latency: float
    last_heartbeat: datetime

class QuantumShardManager:
    """Manages distributed quantum data sharding."""
    
    def __init__(self, config: ShardConfig):
        self.config = config
        self.nodes: Dict[str, NodeMetrics] = {}
        self.shards: Dict[str, Dict] = {}
        self.node_shards: Dict[str, Set[str]] = {}
        self._lock = Lock()
        self.logger = logging.getLogger("shard_manager")
        
        # Initialize encryption
        self.encryption = QuantumEncryption()
        
        # Metrics
        self.metrics = {
            'total_shards': 0,
            'total_storage': 0,
            'rebalance_operations': 0,
            'failed_nodes': 0
        }
        
        # Initialize with minimum required nodes
        self._initialize_nodes()
        
    def _initialize_nodes(self) -> None:
        """Initialize minimum required nodes."""
        try:
            for i in range(self.config.redundancy_factor):
                node_id = f"node_{i}"
                self.nodes[node_id] = NodeMetrics(
                    shard_count=0,
                    storage_used=0,
                    storage_capacity=1024 * 1024 * 1024,  # 1GB
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    network_latency=0.0,
                    last_heartbeat=datetime.utcnow()
                )
                self.node_shards[node_id] = set()
                
            self.logger.info(f"Initialized {len(self.nodes)} nodes")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize nodes: {str(e)}")
            raise

    async def add_node(
        self,
        node_id: str,
        capacity: int
    ) -> bool:
        """Add a new storage node."""
        with self._lock:
            try:
                if node_id in self.nodes:
                    return False
                    
                self.nodes[node_id] = NodeMetrics(
                    shard_count=0,
                    storage_used=0,
                    storage_capacity=capacity,
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    network_latency=0.0,
                    last_heartbeat=datetime.utcnow()
                )
                
                self.node_shards[node_id] = set()
                
                # Trigger rebalancing if needed
                if len(self.nodes) > 1:
                    await self._rebalance_shards()
                    
                self.logger.info(f"Added node {node_id} with capacity {capacity}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add node {node_id}: {str(e)}")
                return False
                
    async def remove_node(self, node_id: str) -> bool:
        """Remove a storage node."""
        with self._lock:
            try:
                if node_id not in self.nodes:
                    return False
                    
                # Redistribute shards before removal
                affected_shards = self.node_shards[node_id]
                await self._redistribute_shards(node_id, affected_shards)
                
                del self.nodes[node_id]
                del self.node_shards[node_id]
                
                self.logger.info(f"Removed node {node_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to remove node {node_id}: {str(e)}")
                return False
                
    async def store_data(
        self,
        data_id: str,
        data: bytes
    ) -> Tuple[bool, List[str]]:
        """Store data with quantum sharding."""
        try:
            # Generate shards
            shards = self._create_shards(data)
            
            # Encrypt shards
            encrypted_shards = []
            for shard in shards:
                keys = self.encryption.generate_kyber_keypair()
                encrypted = self.encryption.encrypt_data(
                    keys['public_key'],
                    shard
                )
                encrypted_shards.append({
                    'data': encrypted,  # Now a base64 string
                    'key': keys['private_key']  # base64 string
                })
            
            # Distribute shards
            shard_locations = await self._distribute_shards(
                data_id,
                encrypted_shards
            )
            
            self.metrics['total_shards'] += len(shards)
            self.metrics['total_storage'] += len(data)
            
            return True, shard_locations
            
        except Exception as e:
            self.logger.error(f"Failed to store data {data_id}: {str(e)}")
            return False, []
            
    async def retrieve_data(
        self,
        data_id: str,
        shard_locations: List[str]
    ) -> Optional[bytes]:
        """Retrieve and reconstruct data from shards."""
        try:
            # Collect shards
            shards = []
            for location in shard_locations:
                shard = await self._retrieve_shard(data_id, location)
                if shard:
                    shards.append(shard)
                    
            if len(shards) < len(shard_locations):
                self.logger.error(
                    f"Failed to retrieve all shards for {data_id}"
                )
                return None
                
            # Decrypt and combine shards
            data = self._reconstruct_data(shards)
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve data {data_id}: {str(e)}")
            return None 

    def _create_shards(self, data: bytes) -> List[bytes]:
        """Split data into shards."""
        try:
            # Calculate optimal shard size
            total_size = len(data)
            num_nodes = max(len(self.nodes), 1)  # Prevent division by zero
            
            shard_size = min(
                max(
                    self.config.min_shard_size,
                    total_size // (num_nodes * 2)  # Ensure at least 2 shards per node
                ),
                self.config.max_shard_size
            )
            
            # Ensure shard size is at least 1 byte
            shard_size = max(shard_size, 1)
            
            # Split data into shards
            shards = []
            for i in range(0, total_size, shard_size):
                shard = data[i:i + shard_size]
                shards.append(shard)
                
            # Ensure minimum number of shards for redundancy
            while len(shards) < self.config.redundancy_factor:
                shards.append(shards[-1] if shards else b'')  # Handle empty data case
                
            return shards
            
        except Exception as e:
            self.logger.error(f"Failed to create shards: {str(e)}")
            raise
            
    async def _distribute_shards(
        self,
        data_id: str,
        encrypted_shards: List[Dict[str, str]]
    ) -> List[str]:
        """Distribute shards across nodes."""
        try:
            if not self.nodes:
                raise ValueError("No nodes available")
                
            # Get list of node IDs
            node_ids = list(self.nodes.keys())
            shard_locations = []
            
            # Distribute shards across nodes
            for i, shard in enumerate(encrypted_shards):
                # Select node using consistent hashing
                node_idx = hash(f"{data_id}_{i}") % len(node_ids)
                node_id = node_ids[node_idx]
                
                # Store shard location
                location = f"{node_id}:{i}"
                shard_locations.append(location)
                
                # Update node metrics
                self.nodes[node_id].shard_count += 1
                self.nodes[node_id].storage_used += len(shard['data'])
                
                # Track shard
                self.shards[location] = shard
                self.node_shards[node_id].add(location)
                
            return shard_locations
            
        except Exception as e:
            self.logger.error(f"Failed to distribute shards: {str(e)}")
            raise
            
    async def _retrieve_shard(
        self,
        data_id: str,
        location: str
    ) -> Optional[bytes]:
        """Retrieve a shard from a node."""
        try:
            node_id, shard_idx = location.split(':')
            
            if node_id not in self.nodes:
                raise ValueError(f"Node {node_id} not found")
                
            if location not in self.shards:
                raise ValueError(f"Shard {location} not found")
                
            # Get encrypted shard
            encrypted_shard = self.shards[location]
            
            # Simulate network latency
            await asyncio.sleep(0.01)
            
            return encrypted_shard
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve shard: {str(e)}")
            return None
            
    async def _redistribute_shards(
        self,
        node_id: str,
        affected_shards: Set[str]
    ) -> None:
        """Redistribute shards from a failed/removed node."""
        try:
            if not affected_shards:
                return
                
            remaining_nodes = set(self.nodes.keys()) - {node_id}
            if not remaining_nodes:
                raise ValueError("No nodes available for redistribution")
                
            # Redistribute each shard
            for location in affected_shards:
                if location not in self.shards:
                    continue
                    
                shard = self.shards[location]
                
                # Select new node
                new_node = min(
                    remaining_nodes,
                    key=lambda n: self.nodes[n].shard_count
                )
                
                # Update location
                _, shard_idx = location.split(':')
                new_location = f"{new_node}:{shard_idx}"
                
                # Update tracking
                self.shards[new_location] = shard
                self.node_shards[new_node].add(new_location)
                del self.shards[location]
                
                # Update metrics
                self.nodes[new_node].shard_count += 1
                self.nodes[new_node].storage_used += len(shard['data'])
                
            self.metrics['rebalance_operations'] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to redistribute shards: {str(e)}")
            raise 

    def _reconstruct_data(self, encrypted_shards: List[Dict[str, str]]) -> bytes:
        """Reconstruct original data from shards."""
        try:
            # Decrypt shards
            decrypted_shards = []
            for shard in encrypted_shards:
                try:
                    # Decrypt using private key
                    decrypted = self.encryption.decrypt_data(
                        shard['key'],  # base64 string
                        shard['data']  # base64 string
                    )
                    decrypted_shards.append(base64.b64decode(decrypted))
                except Exception as e:
                    self.logger.error(f"Failed to decrypt shard: {str(e)}")
                    continue
            
            if not decrypted_shards:
                raise ValueError("No shards could be decrypted")
            
            # Combine shards
            # Remove duplicates (from redundancy)
            unique_shards = list(dict.fromkeys(decrypted_shards))
            
            # Concatenate in order
            reconstructed_data = b''.join(unique_shards)
            
            return reconstructed_data
            
        except Exception as e:
            self.logger.error(f"Failed to reconstruct data: {str(e)}")
            raise 