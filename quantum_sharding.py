from quantum_encryption import QuantumEncryption
import hashlib
import json
import random
from typing import List, Dict, Any
from cryptography.fernet import Fernet
import base64

class QuantumSharding:
    def __init__(self, redundancy_factor: int = 2):
        """
        Initialize the QuantumSharding system.
        
        Args:
            redundancy_factor (int): Number of copies to maintain for each shard
        """
        self.quantum_encryption = QuantumEncryption()
        self.redundancy_factor = redundancy_factor
        self.simulated_nodes = {}  # Simulated distributed storage
        
    def split_into_shards(self, data: str, shard_count: int) -> List[str]:
        """
        Split data into multiple shards.
        
        Args:
            data (str): Data to be sharded
            shard_count (int): Number of shards to create
            
        Returns:
            List[str]: List of data shards
        """
        if not isinstance(data, str):
            data = json.dumps(data)
            
        # Convert to bytes if not already
        data_bytes = data.encode('utf-8')
        shard_size = len(data_bytes) // shard_count
        
        shards = []
        for i in range(shard_count):
            start = i * shard_size
            end = start + shard_size if i < shard_count - 1 else len(data_bytes)
            shard = data_bytes[start:end]
            shards.append(base64.b64encode(shard).decode('utf-8'))
            
        return shards

    def encrypt_shards(self, shards: List[str], public_key: str) -> List[Dict[str, Any]]:
        """
        Encrypt each shard using quantum-resistant encryption.
        
        Args:
            shards (List[str]): List of data shards
            public_key (str): Quantum public key for encryption
            
        Returns:
            List[Dict]: List of encrypted shards with metadata
        """
        encrypted_shards = []
        
        for shard_index, shard in enumerate(shards):
            # Generate a unique shard ID
            shard_id = hashlib.sha256(f"{shard}{random.random()}".encode()).hexdigest()
            
            # Encrypt the shard
            encrypted_data = self.quantum_encryption.encrypt_data(public_key, shard)
            
            encrypted_shards.append({
                'shard_id': shard_id,
                'shard_index': shard_index,
                'total_shards': len(shards),
                'ciphertext': encrypted_data['ciphertext'],
                'shared_secret': encrypted_data['shared_secret']
            })
            
        return encrypted_shards

    def distribute_shards(self, encrypted_shards: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Distribute encrypted shards across simulated nodes with redundancy.
        
        Args:
            encrypted_shards (List[Dict]): List of encrypted shards
            
        Returns:
            Dict[str, List[str]]: Mapping of shard IDs to node locations
        """
        shard_locations = {}
        
        for shard in encrypted_shards:
            # Generate simulated node IDs for redundant storage
            node_ids = []
            for _ in range(self.redundancy_factor):
                node_id = f"node_{hashlib.sha256(str(random.random()).encode()).hexdigest()[:8]}"
                
                # Store shard in simulated node
                if node_id not in self.simulated_nodes:
                    self.simulated_nodes[node_id] = {}
                self.simulated_nodes[node_id][shard['shard_id']] = shard
                
                node_ids.append(node_id)
            
            shard_locations[shard['shard_id']] = node_ids
            
        return shard_locations

    def reconstruct_data(self, shard_locations: Dict[str, List[str]], 
                        private_key: str) -> str:
        """
        Retrieve and reconstruct the original data from shards.
        
        Args:
            shard_locations (Dict[str, List[str]]): Mapping of shard IDs to node locations
            private_key (str): Quantum private key for decryption
            
        Returns:
            str: Reconstructed original data
        """
        # Collect all shards
        collected_shards = []
        
        for shard_id, node_ids in shard_locations.items():
            # Try each redundant location until we find the shard
            for node_id in node_ids:
                if node_id in self.simulated_nodes and shard_id in self.simulated_nodes[node_id]:
                    shard = self.simulated_nodes[node_id][shard_id]
                    collected_shards.append(shard)
                    break
            else:
                raise Exception(f"Shard {shard_id} not found in any location")
        
        # Sort shards by index
        collected_shards.sort(key=lambda x: x['shard_index'])
        
        # Decrypt and combine shards
        decrypted_shards = []
        for shard in collected_shards:
            decrypted_secret = self.quantum_encryption.decrypt_data(
                private_key, 
                shard['ciphertext']
            )
            decrypted_shard = base64.b64decode(decrypted_secret).decode('utf-8')
            decrypted_shards.append(decrypted_shard)
        
        # Combine shards
        return ''.join(decrypted_shards) 