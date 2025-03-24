from quantum_encryption import QuantumEncryption
from quantum_sharding import QuantumSharding
import json

def main():
    # Initialize sharding system with redundancy factor of 2
    sharding_system = QuantumSharding(redundancy_factor=2)
    
    # Generate quantum-resistant keypair
    keys = QuantumEncryption.generate_kyber_keypair()
    
    # Original data to be sharded
    original_data = {
        "sensitive_info": "This is sensitive data that needs to be sharded",
        "metadata": {
            "timestamp": "2024-03-20",
            "priority": "high"
        }
    }
    
    print("Original Data:", original_data)
    
    # Split data into shards
    shards = sharding_system.split_into_shards(json.dumps(original_data), shard_count=3)
    print(f"\nCreated {len(shards)} shards")
    
    # Encrypt shards
    encrypted_shards = sharding_system.encrypt_shards(shards, keys['public_key'])
    print(f"\nEncrypted all shards")
    
    # Distribute shards across nodes
    shard_locations = sharding_system.distribute_shards(encrypted_shards)
    print("\nShard Locations:")
    for shard_id, nodes in shard_locations.items():
        print(f"Shard {shard_id[:8]}: stored on nodes {', '.join(nodes)}")
    
    # Reconstruct data
    reconstructed_data = sharding_system.reconstruct_data(
        shard_locations, 
        keys['private_key']
    )
    
    print("\nReconstructed Data:", json.loads(reconstructed_data))

if __name__ == "__main__":
    main() 