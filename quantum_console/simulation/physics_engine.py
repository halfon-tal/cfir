"""
Quantum-enhanced physics engine for simulating real-world dynamics.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ..models import Entity, Zone
from ..spatial_auth import SphericalCoordinates

logger = logging.getLogger(__name__)

@dataclass
class PhysicalProperties:
    """Physical properties of an entity."""
    mass: float  # kg
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))  # m/s in [x,y,z]
    acceleration: np.ndarray = field(default_factory=lambda: np.zeros(3))  # m/s^2 in [x,y,z]
    friction_coefficient: float = 0.3  # μ
    elasticity: float = 0.8  # 0-1 coefficient of restitution
    density: float = 1.0  # kg/m^3
    
    def __post_init__(self):
        """Validate physical properties."""
        if self.mass <= 0:
            raise ValueError("Mass must be positive")
        if not (0 <= self.friction_coefficient <= 1):
            raise ValueError("Friction coefficient must be between 0 and 1")
        if not (0 <= self.elasticity <= 1):
            raise ValueError("Elasticity must be between 0 and 1")
        if self.density <= 0:
            raise ValueError("Density must be positive")
    
@dataclass 
class EnvironmentalConditions:
    """Environmental conditions affecting physics."""
    gravity: float = 9.81  # m/s^2
    air_density: float = 1.225  # kg/m^3
    temperature: float = 293.15  # K
    wind_velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))  # m/s in [x,y,z]
    humidity: float = 0.5  # 0-1 relative humidity
    surface_type: str = "default"
    
    def __post_init__(self):
        """Validate environmental conditions."""
        if self.gravity < 0:
            raise ValueError("Gravity must be non-negative")
        if self.air_density < 0:
            raise ValueError("Air density must be non-negative")
        if self.temperature < 0:
            raise ValueError("Temperature must be non-negative")
        if not (0 <= self.humidity <= 1):
            raise ValueError("Humidity must be between 0 and 1")

class PhysicsEngine:
    """Real-time physics simulation engine."""
    
    def __init__(self, thread_pool_size: int = 4):
        """Initialize physics engine with optional thread pool size."""
        self.entities: Dict[str, Tuple[Entity, PhysicalProperties]] = {}
        self.zones: Dict[str, Tuple[Zone, EnvironmentalConditions]] = {}
        self.timestep = 0.016  # ~60 FPS
        self.logger = logging.getLogger("physics_engine")
        self._thread_pool = ThreadPoolExecutor(max_workers=thread_pool_size)
        self._running = False
        self._stats = {
            'updates': 0,
            'collisions': 0,
            'avg_update_time': 0.0
        }
        
    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return self._stats.copy()
        
    def add_entity(self, 
                   entity: Entity, 
                   properties: PhysicalProperties) -> None:
        """Add an entity to the physics simulation."""
        if entity.id in self.entities:
            raise ValueError(f"Entity {entity.id} already exists")
        self.entities[entity.id] = (entity, properties)
        
    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from the simulation."""
        if entity_id in self.entities:
            del self.entities[entity_id]
            
    def add_zone(self,
                 zone: Zone,
                 conditions: Optional[EnvironmentalConditions] = None) -> None:
        """Add a zone with environmental conditions."""
        if zone.id in self.zones:
            raise ValueError(f"Zone {zone.id} already exists")
        if conditions is None:
            conditions = EnvironmentalConditions()
        self.zones[zone.id] = (zone, conditions)
        
    def remove_zone(self, zone_id: str) -> None:
        """Remove a zone from the simulation."""
        if zone_id in self.zones:
            del self.zones[zone_id]
            
    async def start(self) -> None:
        """Start the physics simulation loop."""
        self._running = True
        self.logger.info("Starting physics simulation")
        while self._running:
            try:
                await self.update()
                await asyncio.sleep(self.timestep)
            except Exception as e:
                self.logger.error(f"Simulation loop error: {str(e)}")
                self.logger.exception("Detailed error:")
                
    def stop(self) -> None:
        """Stop the physics simulation loop."""
        self._running = False
        self.logger.info("Stopping physics simulation")
        self._thread_pool.shutdown(wait=True)
        
    async def update(self) -> None:
        """Update physics simulation for one timestep."""
        try:
            # Update each entity's physics
            for entity_id, (entity, properties) in self.entities.items():
                # Find containing zone
                zone, conditions = self._get_containing_zone(entity)
                
                # Apply environmental forces
                self._apply_environmental_forces(properties, conditions)
                
                # Update position
                new_position = self._calculate_new_position(
                    entity.coordinates,
                    properties.velocity,
                    properties.acceleration,
                    self.timestep
                )
                
                # Check for collisions
                collisions = self._detect_collisions(entity, new_position)
                if collisions:
                    self._resolve_collisions(properties, collisions)
                else:
                    entity.coordinates = new_position
                
                # Update velocity
                properties.velocity += properties.acceleration * self.timestep
                
                # Apply friction
                self._apply_friction(properties, conditions)
                
        except Exception as e:
            self.logger.error(f"Physics update failed: {str(e)}")
            self.logger.exception("Detailed error:")
            
    def _get_containing_zone(self, 
                            entity: Entity) -> Tuple[Zone, EnvironmentalConditions]:
        """Find the zone containing an entity."""
        for zone_id, (zone, conditions) in self.zones.items():
            if zone.contains(entity.coordinates):
                return zone, conditions
        # Return default zone if none found
        return Zone("default", SphericalCoordinates(0,0,0)), EnvironmentalConditions()
        
    def _apply_environmental_forces(self,
                                  properties: PhysicalProperties,
                                  conditions: EnvironmentalConditions) -> None:
        """Apply environmental forces to an entity."""
        # Gravity
        properties.acceleration[1] -= conditions.gravity
        
        # Air resistance
        velocity_squared = np.square(properties.velocity)
        drag_force = -0.5 * conditions.air_density * velocity_squared
        properties.acceleration += drag_force / properties.mass
        
        # Wind forces
        wind_force = conditions.wind_velocity - properties.velocity
        properties.acceleration += wind_force * 0.1  # Simplified wind effect
        
    def _calculate_new_position(self,
                              current_pos: SphericalCoordinates,
                              velocity: np.ndarray,
                              acceleration: np.ndarray,
                              dt: float) -> SphericalCoordinates:
        """Calculate new position using verlet integration."""
        # Convert to cartesian for physics
        x = current_pos.radius * np.cos(current_pos.latitude) * np.cos(current_pos.longitude)
        y = current_pos.radius * np.cos(current_pos.latitude) * np.sin(current_pos.longitude)
        z = current_pos.radius * np.sin(current_pos.latitude)
        pos = np.array([x, y, z])
        
        # Update position
        new_pos = pos + velocity * dt + 0.5 * acceleration * dt * dt
        
        # Convert back to spherical
        r = np.linalg.norm(new_pos)
        lat = np.arcsin(new_pos[2] / r)
        lon = np.arctan2(new_pos[1], new_pos[0])
        
        return SphericalCoordinates(lat, lon, r)
        
    def _detect_collisions(self,
                          entity: Entity,
                          new_pos: SphericalCoordinates) -> List[Entity]:
        """Detect collisions with other entities."""
        collisions = []
        for other_id, (other, _) in self.entities.items():
            if other_id != entity.id:
                if self._check_collision(new_pos, other.coordinates):
                    collisions.append(other)
        return collisions
        
    def _check_collision(self,
                        pos1: SphericalCoordinates,
                        pos2: SphericalCoordinates) -> bool:
        """Check if two positions are colliding."""
        # Simple distance-based collision
        dx = pos1.radius * np.cos(pos1.latitude) * np.cos(pos1.longitude) - \
             pos2.radius * np.cos(pos2.latitude) * np.cos(pos2.longitude)
        dy = pos1.radius * np.cos(pos1.latitude) * np.sin(pos1.longitude) - \
             pos2.radius * np.cos(pos2.latitude) * np.sin(pos2.longitude)
        dz = pos1.radius * np.sin(pos1.latitude) - \
             pos2.radius * np.sin(pos2.latitude)
        
        distance = np.sqrt(dx*dx + dy*dy + dz*dz)
        return distance < 1.0  # Collision threshold
        
    def _resolve_collisions(self,
                          properties: PhysicalProperties,
                          collisions: List[Entity]) -> None:
        """Resolve collisions with elastic collision physics."""
        for other in collisions:
            # Simplified elastic collision
            other_props = self.entities[other.id][1]
            
            # Relative velocity
            v_rel = properties.velocity - other_props.velocity
            
            # Normal vector between entities
            normal = (properties.velocity - other_props.velocity)
            normal = normal / np.linalg.norm(normal)
            
            # Elastic collision impulse
            j = -(1 + properties.elasticity) * np.dot(v_rel, normal)
            j = j / (1/properties.mass + 1/other_props.mass)
            
            # Update velocities
            properties.velocity += j * normal / properties.mass
            other_props.velocity -= j * normal / other_props.mass
            
    def _apply_friction(self,
                       properties: PhysicalProperties,
                       conditions: EnvironmentalConditions) -> None:
        """Apply friction forces."""
        # Ground friction
        if abs(properties.velocity[1]) < 0.1:  # Near ground
            friction = -properties.friction_coefficient * conditions.gravity
            properties.acceleration[0] += friction * np.sign(properties.velocity[0])
            properties.acceleration[2] += friction * np.sign(properties.velocity[2]) 