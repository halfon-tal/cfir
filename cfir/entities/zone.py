from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from datetime import datetime
import logging
from threading import Lock

from quantum_console.spatial_auth import SphericalCoordinates

class Zone:
    """Represents a spatial zone in the quantum system."""
    
    def __init__(
        self,
        zone_id: str,
        center: SphericalCoordinates,
        radius: float
    ):
        self.zone_id = zone_id
        self.center = center
        self.radius = radius
        
        self.entities: Set['Entity'] = set()  # Reference to Entity class
        self._lock = Lock()
        self.logger = logging.getLogger(f"zone.{zone_id}")
        
        # Zone metrics
        self.metrics = {
            'entity_count': 0,
            'last_update': datetime.utcnow()
        }
        
    def update(self) -> None:
        """Update zone state."""
        with self._lock:
            self.metrics['entity_count'] = len(self.entities)
            self.metrics['last_update'] = datetime.utcnow()
            
    def add_entity(self, entity: 'Entity') -> bool:
        """Add entity to zone."""
        with self._lock:
            if entity not in self.entities:
                self.entities.add(entity)
                self.update()
                return True
            return False
            
    def remove_entity(self, entity: 'Entity') -> bool:
        """Remove entity from zone."""
        with self._lock:
            if entity in self.entities:
                self.entities.remove(entity)
                self.update()
                return True
            return False
            
    @classmethod
    def get_all(cls) -> List['Zone']:
        """Get all zones."""
        # This would typically query a database
        # For testing, return empty list
        return []
        
    def to_dict(self) -> Dict:
        """Convert zone to dictionary."""
        return {
            'zone_id': self.zone_id,
            'center': self.center.to_dict(),
            'radius': self.radius,
            'entity_count': self.metrics['entity_count'],
            'last_update': self.metrics['last_update'].isoformat()
        }

    def query_zone_data(self, universe_data, data_type=None):
        """Queries data from the entire Zone by aggregating data from all Entities' Horizons."""
        aggregated_data = []
        for entity in self.entities:
            horizon = entity.horizon  # Assuming each entity has a Horizon attribute
            detected_data = horizon.detect_all_data(universe_data)
            if data_type:
                detected_data = [d for d in detected_data if d[3] == data_type]  # Assuming data point has type as the fourth element
            aggregated_data.extend(detected_data)
        return aggregated_data

    def aggregate_data_summary(self, universe_data, data_type):
        """Provides aggregated summary statistics for specific data types within the Zone."""
        data_points = self.query_zone_data(universe_data, data_type)
        if not data_points:
            return None
        
        values = [d[2] for d in data_points]  # Assuming the data point has a value as the third element
        return {
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'count': len(values)
        }

    def visualize_zone(self):
        """Provides a simplified visual representation of Entities and their spatial coverage within the Zone."""
        # This could be a placeholder for actual visualization logic
        print(f"Zone: {self.zone_id}")
        for entity in self.entities:
            print(f" - Entity ID: {entity.entity_id}, Coordinates: {entity.coordinates}") 