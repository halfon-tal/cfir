from typing import Dict, List, Optional, Set
import asyncio
import logging
from datetime import datetime
from threading import Lock
import numpy as np
from dataclasses import dataclass

from .autonomous_nav import AutonomousVehicle
from .smart_city import TrafficLight, SmartUtility
from cfir.entities import Entity, Zone
from ..spatial_auth import SphericalCoordinates

@dataclass
class SimulationConfig:
    """Simulation configuration parameters."""
    vehicle_count: int = 100
    traffic_light_count: int = 20
    utility_sensor_count: int = 50
    update_interval: float = 0.1  # seconds
    simulation_area: float = 1000.0  # meters
    max_velocity: float = 30.0  # m/s
    sensor_range: float = 100.0  # meters

class SimulationManager:
    """Manages real-world simulation scenarios."""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.entities: Dict[str, Entity] = {}
        self.zones: Dict[str, Zone] = {}
        self.running = False
        self._lock = Lock()
        self.logger = logging.getLogger("simulation")
        
        # Metrics tracking
        self.metrics = {
            'collision_alerts': 0,
            'traffic_congestion': 0.0,
            'utility_efficiency': 1.0,
            'update_count': 0
        }
        
        # Initialize simulation
        self._initialize_simulation()
        
    def _initialize_simulation(self) -> None:
        """Initialize simulation entities and zones."""
        try:
            # Create zones
            self._create_zones()
            
            # Create vehicles
            self._create_vehicles()
            
            # Create traffic infrastructure
            self._create_traffic_lights()
            
            # Create utility sensors
            self._create_utility_sensors()
            
            self.logger.info(
                f"Simulation initialized with "
                f"{len(self.entities)} entities in "
                f"{len(self.zones)} zones"
            )
            
        except Exception as e:
            self.logger.error(f"Simulation initialization failed: {str(e)}")
            raise
            
    def _create_zones(self) -> None:
        """Create city zones."""
        zone_size = self.config.simulation_area / 5  # 5x5 grid
        
        for i in range(5):
            for j in range(5):
                zone_id = f"zone_{i}_{j}"
                center = SphericalCoordinates(
                    r=np.sqrt(i*i + j*j) * zone_size,
                    theta=np.arctan2(j, i),
                    phi=0.0
                )
                
                zone = Zone(
                    zone_id=zone_id,
                    center=center,
                    radius=zone_size/2
                )
                self.zones[zone_id] = zone
                
    async def run(self) -> None:
        """Run the simulation."""
        self.running = True
        last_update = datetime.utcnow()
        
        try:
            while self.running:
                now = datetime.utcnow()
                delta_time = (now - last_update).total_seconds()
                
                if delta_time >= self.config.update_interval:
                    await self._update(delta_time)
                    last_update = now
                    
                await asyncio.sleep(self.config.update_interval / 10)
                
        except Exception as e:
            self.logger.error(f"Simulation run failed: {str(e)}")
            self.stop()
            raise
            
    async def _update(self, delta_time: float) -> None:
        """Update simulation state."""
        with self._lock:
            try:
                # Update all entities
                for entity in self.entities.values():
                    if isinstance(entity, AutonomousVehicle):
                        entity.update(delta_time)
                    elif isinstance(entity, (TrafficLight, SmartUtility)):
                        entity.update()
                
                # Update zones
                for zone in self.zones.values():
                    zone.update()
                
                # Update metrics
                self._update_metrics()
                
                self.metrics['update_count'] += 1
                
            except Exception as e:
                self.logger.error(f"Update cycle failed: {str(e)}")
                
    def _update_metrics(self) -> None:
        """Update simulation metrics."""
        try:
            # Calculate collision alerts
            collision_alerts = sum(
                1 for entity in self.entities.values()
                if isinstance(entity, AutonomousVehicle) and
                entity.state.collision_risk > 0.8
            )
            
            # Calculate traffic congestion
            traffic_lights = [
                entity for entity in self.entities.values()
                if isinstance(entity, TrafficLight)
            ]
            avg_congestion = np.mean([
                light.vehicle_count for light in traffic_lights
            ])
            
            # Calculate utility efficiency
            utilities = [
                entity for entity in self.entities.values()
                if isinstance(entity, SmartUtility)
            ]
            avg_efficiency = np.mean([
                utility.efficiency for utility in utilities
            ])
            
            # Update metrics
            self.metrics.update({
                'collision_alerts': collision_alerts,
                'traffic_congestion': avg_congestion,
                'utility_efficiency': avg_efficiency
            })
            
        except Exception as e:
            self.logger.error(f"Metrics update failed: {str(e)}")
            
    def get_metrics(self) -> Dict:
        """Get current simulation metrics."""
        with self._lock:
            return self.metrics.copy()
            
    def stop(self) -> None:
        """Stop the simulation."""
        self.running = False
        self.logger.info("Simulation stopped") 