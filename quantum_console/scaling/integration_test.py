import asyncio
import logging
from datetime import datetime
import json
import random
from typing import Dict, List, Optional
import os
from pathlib import Path

from quantum_console.scaling.shard_manager import QuantumShardManager, ShardConfig
from .auto_scaler import AutoScaler, ScalingConfig
from ..visualization import MetricsVisualizer
from ..models import Entity, Zone
from ..spatial_auth import SphericalCoordinates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_test")

class ScalingTestHarness:
    """Test harness for scaling and sharding integration."""
    
    def __init__(self):
        # Initialize configurations
        self.shard_config = ShardConfig(
            min_shard_size=1024,
            max_shard_size=1024 * 1024,
            redundancy_factor=3,
            rebalance_threshold=0.2
        )
        
        self.scaling_config = ScalingConfig(
            min_nodes=3,
            max_nodes=10,
            cpu_threshold=0.8,
            memory_threshold=0.8,
            cooldown_period=60  # Shorter period for testing
        )
        
        # Initialize components
        self.shard_manager = QuantumShardManager(self.shard_config)
        self.auto_scaler = AutoScaler(self.scaling_config, self.shard_manager)
        self.visualizer = MetricsVisualizer()
        
        # Test metrics
        self.metrics = {
            'data_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'avg_latency': 0.0,
            'shard_distribution': {}
        }
        
        self.stored_data: Dict[str, List[str]] = {}  # data_id -> shard_locations
        
    async def run_load_test(self, duration: int = 300) -> None:
        """Run load test for specified duration."""
        logger = logging.getLogger("integration_test")
        logger.setLevel(logging.DEBUG)  # Enable debug logging
        logger.info("Starting load test...")
        
        start_time = datetime.utcnow()
        test_id = 0
        
        # Initialize metrics
        self.metrics = {
            'data_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'avg_latency': 0.0,
            'shard_distribution': {}
        }
        
        while (datetime.utcnow() - start_time).total_seconds() < duration:
            try:
                # Generate test data
                data_id = f"test_{test_id}"
                data = os.urandom(random.randint(1024, 1024 * 1024))  # 1KB to 1MB
                
                # Store data
                store_start = datetime.utcnow()
                success, locations = await self.shard_manager.store_data(data_id, data)
                store_latency = (datetime.utcnow() - store_start).total_seconds()
                
                # Track store operation
                self.metrics['data_operations'] += 1
                if success:
                    self.stored_data[data_id] = locations
                    self.metrics['successful_operations'] += 1
                    logger.info(f"Successfully stored data {data_id}")
                else:
                    self.metrics['failed_operations'] += 1
                    logger.warning(f"Failed to store data {data_id}")
                
                # Print current metrics after store
                logger.info(f"After store - Operations: {self.metrics['data_operations']}, "
                          f"Successes: {self.metrics['successful_operations']}")
                
                # Update visualization after store
                self._update_visualization(store_latency, 0)
                
                # Retrieve previously stored data
                if self.stored_data:
                    retrieve_id = random.choice(list(self.stored_data.keys()))
                    retrieve_start = datetime.utcnow()
                    retrieved_data = await self.shard_manager.retrieve_data(
                        retrieve_id,
                        self.stored_data[retrieve_id]
                    )
                    retrieve_latency = (datetime.utcnow() - retrieve_start).total_seconds()
                    
                    # Track retrieve operation
                    self.metrics['data_operations'] += 1
                    if retrieved_data is not None:
                        self.metrics['successful_operations'] += 1
                        logger.info(f"Successfully retrieved data {retrieve_id}")
                    else:
                        self.metrics['failed_operations'] += 1
                        logger.warning(f"Failed to retrieve data {retrieve_id}")
                    
                    # Print current metrics after retrieve
                    logger.info(f"After retrieve - Operations: {self.metrics['data_operations']}, "
                              f"Successes: {self.metrics['successful_operations']}")
                    
                    # Update visualization after retrieve
                    self._update_visualization(store_latency, retrieve_latency)
                
                test_id += 1
                await asyncio.sleep(1)  # Wait 1 second between operations
                
            except Exception as e:
                logger.error(f"Error in test iteration: {str(e)}")
                logger.exception("Detailed error:")
                
        logger.info("Load test completed")
        self._generate_test_report()

    def _update_visualization(self, store_latency: float, retrieve_latency: float) -> None:
        """Update visualization with current metrics."""
        try:
            # Update metrics
            avg_latency = (store_latency + retrieve_latency) / 2 if retrieve_latency > 0 else store_latency
            self.metrics['avg_latency'] = avg_latency
            self.metrics['shard_distribution'] = {
                node_id: len(shards)
                for node_id, shards in self.shard_manager.node_shards.items()
            }
            
            # Calculate success rate
            success_rate = (
                self.metrics['successful_operations'] / 
                max(self.metrics['data_operations'], 1)
            ) * 100
            
            logger.info(f"Success rate: {success_rate:.2f}%")
            
            # Update visualization
            self.visualizer.update_metrics({
                'test': self.metrics,
                'shard_manager': {
                    'total_shards': len(self.shard_manager.shards),
                    'nodes': self.shard_manager.nodes,
                    'total_storage': self.shard_manager.metrics['total_storage']
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to update visualization: {str(e)}")
            logger.exception("Detailed error:")

    def _generate_test_report(self) -> None:
        """Generate and save test report."""
        success_rate = (
            self.metrics['successful_operations'] /
            max(self.metrics['data_operations'], 1)
        ) * 100
        
        report = {
            'duration': datetime.utcnow().isoformat(),
            'operations': {
                'total': self.metrics['data_operations'],
                'successful': self.metrics['successful_operations'],
                'failed': self.metrics['failed_operations'],
                'success_rate': f"{success_rate:.2f}%"
            },
            'performance': {
                'avg_latency': f"{self.metrics['avg_latency']*1000:.2f}ms",
                'shard_distribution': self.metrics['shard_distribution']
            },
            'shard_manager': {
                'total_shards': self.shard_manager.metrics['total_shards'],
                'total_storage': self.shard_manager.metrics['total_storage'],
                'rebalance_operations': self.shard_manager.metrics['rebalance_operations']
            }
        }
        
        # Save report
        report_path = Path("test_reports")
        report_path.mkdir(exist_ok=True)
        
        with open(
            report_path / f"scaling_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json",
            'w'
        ) as f:
            json.dump(report, f, indent=2)

async def main():
    """Run the integration test."""
    test_harness = ScalingTestHarness()
    
    print("\nStarting Quantum OS Scaling Integration Test")
    print("===========================================")
    
    try:
        test_harness.visualizer.start()
        await test_harness.run_load_test(duration=300)  # 5 minutes
        
        print("\nTest Completed Successfully!")
        print("Check test_reports directory for detailed results")
        
    except Exception as e:
        print(f"\nTest failed: {str(e)}")
        
    finally:
        test_harness.visualizer.stop()

if __name__ == "__main__":
    asyncio.run(main()) 