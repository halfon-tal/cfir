from dataclasses import dataclass
from typing import Dict, List, Set, Optional
from datetime import datetime
import logging
from threading import Lock

from .entity import Entity
from ..spatial_auth import SphericalCoordinates

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
        
        self.entities: Set[Entity] = set()
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
            
    def add_entity(self, entity: Entity) -> bool:
        """Add entity to zone."""
        with self._lock:
            if entity not in self.entities:
                self.entities.add(entity)
                self.update()
                return True
            return False
            
    def remove_entity(self, entity: Entity) -> bool:
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