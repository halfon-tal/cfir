from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from threading import Lock

from ..spatial_auth import SphericalCoordinates

class Entity:
    """Base class for all entities in the quantum system."""
    
    def __init__(
        self,
        coordinates: SphericalCoordinates,
        name: str,
        entity_type: str
    ):
        self.coordinates = coordinates
        self.name = name
        self.entity_type = entity_type
        self.entity_id = f"{entity_type}_{name}_{datetime.utcnow().timestamp()}"
        
        self._lock = Lock()
        self.logger = logging.getLogger(f"entity.{self.entity_id}")
        
        # Entity state
        self.active = True
        self.last_update = datetime.utcnow()
        
    def update(self) -> None:
        """Update entity state."""
        with self._lock:
            self.last_update = datetime.utcnow()
            
    @classmethod
    def count_active(cls) -> int:
        """Get count of active entities."""
        # This would typically query a database
        # For testing, return simulated count
        return 10
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            'entity_id': self.entity_id,
            'name': self.name,
            'type': self.entity_type,
            'coordinates': self.coordinates.to_dict(),
            'active': self.active,
            'last_update': self.last_update.isoformat()
        } 