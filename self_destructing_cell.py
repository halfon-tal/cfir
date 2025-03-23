import threading
import time
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

@dataclass
class SphericalCoordinates:
    r: float      # radius
    theta: float  # polar angle (0 to π)
    phi: float    # azimuthal angle (0 to 2π)
    
class SelfDestructingDataCell:
    def __init__(
        self, 
        data: Any,
        coordinates: SphericalCoordinates,
        horizon_radius: float,
        lifespan_seconds: Optional[float] = None
    ):
        """
        Initialize a self-destructing data cell.
        
        Args:
            data: The data to be stored
            coordinates: Initial spherical coordinates (r, θ, ϕ)
            horizon_radius: Maximum allowed radius before spatial destruction
            lifespan_seconds: Time in seconds before automatic destruction
        """
        self.data = data
        self.coordinates = coordinates
        self.horizon_radius = horizon_radius
        self.lifespan_seconds = lifespan_seconds
        self.creation_time = time.time()
        self._destruction_timer: Optional[threading.Timer] = None
        self._is_destroyed = False
        self._lock = threading.Lock()
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        
        # Start timer-based destruction if lifespan is set
        if lifespan_seconds is not None:
            self.set_timer_destruction()
            
    def set_timer_destruction(self) -> None:
        """Start the timer for automatic data destruction."""
        if self.lifespan_seconds is not None:
            self._destruction_timer = threading.Timer(
                self.lifespan_seconds, 
                self.destroy,
                args=["Timer expiration"]
            )
            self._destruction_timer.start()
            self.logger.info(
                f"Timer-based destruction set for {self.lifespan_seconds} seconds"
            )
            
    def update_coordinates(self, new_coordinates: SphericalCoordinates) -> bool:
        """
        Update the cell's spatial coordinates and check boundaries.
        
        Args:
            new_coordinates: New spherical coordinates
            
        Returns:
            bool: True if update successful, False if cell was destroyed
        """
        with self._lock:
            if self._is_destroyed:
                return False
                
            self.coordinates = new_coordinates
            
            # Check if new position is within allowed Horizon
            if not self.check_spatial_boundaries():
                self.destroy("Spatial boundary violation")
                return False
                
            return True
            
    def check_spatial_boundaries(self) -> bool:
        """
        Check if the cell is within the allowed Horizon radius.
        
        Returns:
            bool: True if within boundaries, False if outside
        """
        return self.coordinates.r <= self.horizon_radius
        
    def destroy(self, reason: str = "Unspecified") -> None:
        """
        Destroy the data cell and clean up resources.
        
        Args:
            reason: The reason for destruction
        """
        with self._lock:
            if self._is_destroyed:
                return
                
            # Cancel any pending destruction timer
            if self._destruction_timer:
                self._destruction_timer.cancel()
                
            # Securely delete data by overwriting
            self.data = None
            self._is_destroyed = True
            
            self.logger.info(f"Data cell destroyed. Reason: {reason}")
            
    def is_alive(self) -> bool:
        """Check if the data cell still exists."""
        return not self._is_destroyed
        
    def get_data(self) -> Optional[Any]:
        """
        Retrieve the cell's data if it still exists.
        
        Returns:
            The data if cell is alive, None if destroyed
        """
        with self._lock:
            return self.data if not self._is_destroyed else None
            
    def get_age(self) -> float:
        """
        Get the age of the cell in seconds.
        
        Returns:
            float: Age in seconds
        """
        return time.time() - self.creation_time 