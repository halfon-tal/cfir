import math
from zkp_auth import ProofChallenge, ProofResponse, ZeroKnowledgeAuthenticator
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict, Set
import numpy as np
import logging
from datetime import datetime, timedelta
import rtree
from functools import lru_cache
from threading import Lock
import json

class SpatialAuthError(Exception):
    """Base exception for spatial authentication errors."""
    pass

class OutOfBoundsError(SpatialAuthError):
    """Raised when attempting to access data outside spatial bounds."""
    pass

class ReceptorError(SpatialAuthError):
    """Raised for receptor-related errors."""
    pass

@dataclass(frozen=True)
class SphericalCoordinates:
    """Immutable spherical coordinates representation."""
    r: float      # radius (distance from center)
    theta: float  # polar angle (0 to π)
    phi: float    # azimuthal angle (0 to 2π)
    
    def __post_init__(self):
        """Validate coordinate ranges."""
        if self.r < 0:
            raise ValueError("Radius must be non-negative")
        if not 0 <= self.theta <= math.pi:
            raise ValueError("Theta must be between 0 and π")
        if not 0 <= self.phi <= 2 * math.pi:
            raise ValueError("Phi must be between 0 and 2π")
    
    @lru_cache(maxsize=1024)
    def to_cartesian(self) -> Tuple[float, float, float]:
        """Convert to cartesian coordinates with caching."""
        x = self.r * math.sin(self.theta) * math.cos(self.phi)
        y = self.r * math.sin(self.theta) * math.sin(self.phi)
        z = self.r * math.cos(self.theta)
        return (x, y, z)
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'r': self.r,
            'theta': self.theta,
            'phi': self.phi
        }

@dataclass
class Receptor:
    """A sensor that detects data within a specific range."""
    coordinates: SphericalCoordinates
    detection_radius: float
    data_type: str
    
    def __post_init__(self):
        """Validate receptor parameters."""
        if self.detection_radius <= 0:
            raise ValueError("Detection radius must be positive")
        if not self.data_type:
            raise ValueError("Data type must be specified")

class SpatialIndex:
    """R-tree based spatial index for efficient querying."""
    
    def __init__(self):
        self.index = rtree.index.Index()
        self.id_counter = 0
        self.id_to_object = {}
        self._lock = Lock()
        
    def insert(self, coords: SphericalCoordinates, obj: any) -> int:
        """Insert an object with its coordinates."""
        with self._lock:
            cart_coords = coords.to_cartesian()
            obj_id = self.id_counter
            self.id_counter += 1
            
            # Insert with a small bounding box around the point
            bbox = (
                cart_coords[0] - 0.0001,
                cart_coords[1] - 0.0001,
                cart_coords[2] - 0.0001,
                cart_coords[0] + 0.0001,
                cart_coords[1] + 0.0001,
                cart_coords[2] + 0.0001
            )
            self.index.insert(obj_id, bbox)
            self.id_to_object[obj_id] = obj
            return obj_id
            
    def query_radius(
        self, 
        center: SphericalCoordinates, 
        radius: float
    ) -> Set[any]:
        """Query objects within radius of center point."""
        cart_center = center.to_cartesian()
        bbox = (
            cart_center[0] - radius,
            cart_center[1] - radius,
            cart_center[2] - radius,
            cart_center[0] + radius,
            cart_center[1] + radius,
            cart_center[2] + radius
        )
        # Perform query and return results
        return {self.id_to_object[id] for id in self.index.intersection(bbox)}

class SpatialHorizon:
    """Defines the spatial boundary for data access."""
    
    def __init__(self, center: SphericalCoordinates):
        self.center = center
        self.receptors: List[Receptor] = []
        self._max_radius: float = 0.0
        self._spatial_index = SpatialIndex()
        self._lock = Lock()
        self.logger = logging.getLogger(__name__)
        
    def add_receptor(self, receptor: Receptor) -> None:
        """Add a receptor and update the horizon radius."""
        with self._lock:
            try:
                self.receptors.append(receptor)
                self._spatial_index.insert(receptor.coordinates, receptor)
                
                # Update max radius
                total_radius = receptor.coordinates.r + receptor.detection_radius
                self._max_radius = max(self._max_radius, total_radius)
                
                self.logger.info(
                    f"Added receptor type={receptor.data_type} "
                    f"radius={receptor.detection_radius}"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to add receptor: {str(e)}")
                raise ReceptorError(f"Failed to add receptor: {str(e)}")
    
    @lru_cache(maxsize=1024)
    def contains_point(self, point: SphericalCoordinates) -> bool:
        """Check if a point falls within the horizon."""
        try:
            center_cart = self.center.to_cartesian()
            point_cart = point.to_cartesian()
            
            # Calculate Euclidean distance
            distance = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(center_cart, point_cart))
            )
            
            within_bounds = distance <= self._max_radius
            
            # Log access attempt
            self.logger.debug(
                f"Spatial check: point={point.to_dict()} "
                f"distance={distance:.2f} allowed={within_bounds}"
            )
            
            return within_bounds
            
        except Exception as e:
            self.logger.error(f"Error in spatial check: {str(e)}")
            raise SpatialAuthError(f"Spatial check failed: {str(e)}")
    
    def get_nearby_receptors(
        self, 
        point: SphericalCoordinates, 
        data_type: Optional[str] = None
    ) -> List[Receptor]:
        """Get receptors that could detect a point."""
        try:
            nearby = self._spatial_index.query_radius(
                point, 
                self._max_radius
            )
            
            if data_type:
                nearby = [r for r in nearby if r.data_type == data_type]
                
            return list(nearby)
            
        except Exception as e:
            self.logger.error(f"Error querying receptors: {str(e)}")
            raise SpatialAuthError(f"Receptor query failed: {str(e)}")

class SpatialEntity:
    """An entity with spatial awareness and data access control."""
    
    def __init__(
        self,
        coordinates: SphericalCoordinates,
        name: str,
        secret_credential: str,
        audit_log_path: Optional[str] = None
    ):
        self.horizon = SpatialHorizon(coordinates)
        self.name = name
        
        # Initialize ZKP authenticator
        self.authenticator = ZeroKnowledgeAuthenticator(secret_credential)
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        if audit_log_path:
            audit_handler = logging.FileHandler(audit_log_path)
            audit_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
            self.logger.addHandler(audit_handler)
        
        self.logger.info(f"Initialized spatial entity: {name}")
        
    def add_receptor(
        self, 
        relative_coords: SphericalCoordinates,
        detection_radius: float,
        data_type: str
    ) -> None:
        """Add a receptor at coordinates relative to entity."""
        try:
            receptor = Receptor(relative_coords, detection_radius, data_type)
            self.horizon.add_receptor(receptor)
            
            self.logger.info(
                f"Added receptor: type={data_type} "
                f"radius={detection_radius} "
                f"coords={relative_coords.to_dict()}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to add receptor: {str(e)}")
            raise ReceptorError(f"Failed to add receptor: {str(e)}")
    
    def can_access_data(
        self, 
        data_location: SphericalCoordinates,
        data_type: Optional[str] = None,
        proof_response: Optional['ProofResponse'] = None,
        challenge: Optional['ProofChallenge'] = None
    ) -> bool:
        """Check if entity can access data at given location."""
        try:
            # First check spatial boundary
            if not self.horizon.contains_point(data_location):
                self.logger.warning(
                    f"Spatial access denied: {data_location.to_dict()}"
                )
                return False
            
            # Check if any appropriate receptors are in range
            if data_type:
                nearby_receptors = self.horizon.get_nearby_receptors(
                    data_location,
                    data_type
                )
                if not nearby_receptors:
                    self.logger.warning(
                        f"No receptors for type {data_type} near "
                        f"{data_location.to_dict()}"
                    )
                    return False
            
            # If ZKP proof is provided, verify it
            if proof_response and challenge:
                try:
                    zkp_valid = self.authenticator.verify_proof(
                        proof_response,
                        challenge,
                        self.authenticator.commitment,
                        "spatial_check"
                    )
                    if not zkp_valid:
                        self.logger.warning("ZKP verification failed")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"ZKP verification error: {str(e)}")
                    return False
            
            self.logger.info(
                f"Access granted: location={data_location.to_dict()} "
                f"type={data_type}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Access check failed: {str(e)}")
            raise SpatialAuthError(f"Access check failed: {str(e)}") 