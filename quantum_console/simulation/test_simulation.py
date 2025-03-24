"""
Test simulation for the physics engine.
"""

import asyncio
import logging
import numpy as np
from typing import List, Tuple
import random
from .physics_engine import PhysicsEngine, PhysicalProperties, EnvironmentalConditions
from cfir.entities import Entity, Zone
from ..spatial_auth import SphericalCoordinates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhysicsSimulation:
    """Test simulation for physics engine."""
    
    def __init__(self, num_entities: int = 10):
        self.engine = PhysicsEngine()
        self.num_entities = num_entities
        
    def _create_random_entity(self, entity_id: str) -> Tuple[Entity, PhysicalProperties]:
        """Create a random entity with physical properties."""
        try:
            # Random position on sphere (using degrees for easier visualization)
            lat = random.uniform(-90, 90)  # Latitude in degrees (-90 to 90)
            lon = random.uniform(-180, 180)  # Longitude in degrees (-180 to 180)
            r = float(100.0)  # Ensure float type
            
            # Convert to radians for SphericalCoordinates
            lat_rad = float(np.radians(lat))
            lon_rad = float(np.radians(lon))
            
            # Print debug values before creation
            print(f"DEBUG - Creating coordinates with: lat={lat_rad}, lon={lon_rad}, r={r}")
            print(f"DEBUG - Types: lat={type(lat_rad)}, lon={type(lon_rad)}, r={type(r)}")
            
            # Create coordinates step by step
            try:
                coords = SphericalCoordinates(lat_rad, lon_rad, r)
            except ValueError as ve:
                print(f"DEBUG - Coordinate creation failed with values:")
                print(f"  lat_rad: {lat_rad} ({type(lat_rad)})")
                print(f"  lon_rad: {lon_rad} ({type(lon_rad)})")
                print(f"  r: {r} ({type(r)})")
                raise
            
            # Create entity
            entity = Entity(entity_id, coords)
            
            properties = PhysicalProperties(
                mass=random.uniform(1.0, 10.0),
                velocity=np.array([
                    random.uniform(-5, 5),
                    random.uniform(-5, 5),
                    random.uniform(-5, 5)
                ]),
                friction_coefficient=random.uniform(0.1, 0.9),
                elasticity=random.uniform(0.5, 0.95),
                density=random.uniform(0.5, 2.0)
            )
            
            return entity, properties
            
        except Exception as e:
            logger.error(f"Failed to create entity: {str(e)}")
            raise
        
    def _create_zones(self) -> List[Tuple[Zone, EnvironmentalConditions]]:
        """Create test zones with different conditions."""
        try:
            zones = []
            
            # High gravity zone at equator - using explicit float values
            high_grav = EnvironmentalConditions(
                gravity=15.0,
                wind_velocity=np.array([2.0, 0.0, 0.0])
            )
            
            print("DEBUG - Creating equator zone coordinates")
            equator_coords = SphericalCoordinates(
                float(0.0),  # Explicit float conversion
                float(0.0), 
                float(100.0)
            )
            
            zones.append((
                Zone("high_gravity", equator_coords),
                high_grav
            ))
            
            # Low friction zone
            low_fric = EnvironmentalConditions(
                gravity=9.81,
                air_density=0.5,
                surface_type="ice"
            )
            
            print("DEBUG - Creating mid-latitude zone coordinates")
            mid_lat = float(np.radians(45.0))
            mid_lon = float(np.radians(45.0))
            mid_r = float(100.0)
            
            print(f"DEBUG - Mid zone values: lat={mid_lat}, lon={mid_lon}, r={mid_r}")
            mid_coords = SphericalCoordinates(mid_lat, mid_lon, mid_r)
            
            zones.append((
                Zone("low_friction", mid_coords),
                low_fric
            ))
            
            return zones
            
        except Exception as e:
            logger.error(f"Failed to create zones: {str(e)}")
            raise
        
    async def run(self, duration: float = 10.0) -> None:
        """Run the simulation for specified duration."""
        try:
            # Create and add entities
            for i in range(self.num_entities):
                entity, props = self._create_random_entity(f"entity_{i}")
                self.engine.add_entity(entity, props)
                
            # Create and add zones
            for zone, conditions in self._create_zones():
                self.engine.add_zone(zone, conditions)
                
            logger.info(f"Starting simulation with {self.num_entities} entities")
            
            # Start physics engine
            engine_task = asyncio.create_task(self.engine.start())
            
            # Monitor simulation
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < duration:
                stats = self.engine.stats
                logger.info(
                    f"Simulation stats - Updates: {stats['updates']}, "
                    f"Collisions: {stats['collisions']}, "
                    f"Avg update time: {stats['avg_update_time']*1000:.2f}ms"
                )
                await asyncio.sleep(1.0)
                
            # Stop simulation
            self.engine.stop()
            await engine_task
            
        except Exception as e:
            logger.error(f"Simulation failed: {str(e)}")
            logger.exception("Detailed error:")
            
async def main():
    """Run test simulation."""
    sim = PhysicsSimulation(num_entities=20)
    await sim.run(duration=30.0)
    
def test_coordinates():
    """Test coordinate creation."""
    print("\nTesting coordinate creation...")
    
    # Test case 1: Simple positive values
    try:
        print("\nTest 1: Simple positive values")
        coords = SphericalCoordinates(0.0, 0.0, 100.0)
        print(f"Success! Created coordinates: {coords}")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Test case 2: With numpy values
    try:
        print("\nTest 2: Numpy values")
        coords = SphericalCoordinates(
            np.float64(0.0),
            np.float64(0.0),
            np.float64(100.0)
        )
        print(f"Success! Created coordinates: {coords}")
    except Exception as e:
        print(f"Failed: {e}")
    
    # Test case 3: With explicit Python floats
    try:
        print("\nTest 3: Explicit floats")
        coords = SphericalCoordinates(
            float(0.0),
            float(0.0),
            float(100.0)
        )
        print(f"Success! Created coordinates: {coords}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_coordinates()
    asyncio.run(main()) 