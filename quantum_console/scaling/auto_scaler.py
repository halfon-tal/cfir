from typing import Dict, List, Optional
import asyncio
import logging
from datetime import datetime
from threading import Lock
import numpy as np
from dataclasses import dataclass

from ..models import Entity, Zone
from .shard_manager import QuantumShardManager

@dataclass
class ScalingConfig:
    """Configuration for auto-scaling."""
    min_nodes: int = 3
    max_nodes: int = 20
    cpu_threshold: float = 0.8  # 80% CPU triggers scaling
    memory_threshold: float = 0.8  # 80% memory triggers scaling
    scale_up_factor: float = 1.5  # Increase capacity by 50%
    scale_down_factor: float = 0.5  # Decrease capacity by 50%
    cooldown_period: int = 300  # seconds between scaling operations

class AutoScaler:
    """Manages automated scaling of the platform."""
    
    def __init__(
        self,
        config: ScalingConfig,
        shard_manager: QuantumShardManager
    ):
        self.config = config
        self.shard_manager = shard_manager
        self._lock = Lock()
        self.logger = logging.getLogger("auto_scaler")
        
        self.last_scale_time = datetime.utcnow()
        self.scaling_in_progress = False
        
        # Metrics
        self.metrics = {
            'scale_up_operations': 0,
            'scale_down_operations': 0,
            'failed_scaling_attempts': 0
        }
        
    async def monitor(self) -> None:
        """Monitor system metrics and trigger scaling."""
        while True:
            try:
                await self._check_scaling_needs()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Monitoring failed: {str(e)}")
                
    async def _check_scaling_needs(self) -> None:
        """Check if scaling is needed."""
        with self._lock:
            try:
                if self.scaling_in_progress:
                    return
                    
                now = datetime.utcnow()
                if (now - self.last_scale_time).total_seconds() < self.config.cooldown_period:
                    return
                    
                metrics = self._collect_metrics()
                
                if self._should_scale_up(metrics):
                    await self._scale_up()
                elif self._should_scale_down(metrics):
                    await self._scale_down()
                    
            except Exception as e:
                self.logger.error(f"Scaling check failed: {str(e)}")
                
    def _should_scale_up(self, metrics: Dict) -> bool:
        """Determine if scaling up is needed."""
        return (
            metrics['avg_cpu'] > self.config.cpu_threshold or
            metrics['avg_memory'] > self.config.memory_threshold
        ) and len(self.shard_manager.nodes) < self.config.max_nodes
        
    def _should_scale_down(self, metrics: Dict) -> bool:
        """Determine if scaling down is needed."""
        return (
            metrics['avg_cpu'] < self.config.cpu_threshold / 2 and
            metrics['avg_memory'] < self.config.memory_threshold / 2
        ) and len(self.shard_manager.nodes) > self.config.min_nodes
        
    async def _scale_up(self) -> None:
        """Scale up the platform."""
        self.scaling_in_progress = True
        try:
            current_nodes = len(self.shard_manager.nodes)
            target_nodes = min(
                int(current_nodes * self.config.scale_up_factor),
                self.config.max_nodes
            )
            
            for i in range(current_nodes, target_nodes):
                node_id = f"node_{i}"
                success = await self.shard_manager.add_node(
                    node_id,
                    capacity=1024 * 1024 * 1024  # 1GB
                )
                if success:
                    self.metrics['scale_up_operations'] += 1
                    
            self.last_scale_time = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"Scale up failed: {str(e)}")
            self.metrics['failed_scaling_attempts'] += 1
            
        finally:
            self.scaling_in_progress = False 