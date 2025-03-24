import threading
import time
import math
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging
from cfir.entities.sphere.sphere_entity import SphericalCoordinates

    
class SelfDestructingDataCell:
    """Self-destructing data cell with observer pattern."""
    
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
        self._observers: List[callable] = []
        
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
                self.destroy
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
                self.destroy()
                return False
                
            return True
            
    def check_spatial_boundaries(self) -> bool:
        """
        Check if the cell is within the allowed Horizon radius.
        
        Returns:
            bool: True if within boundaries, False if outside
        """
        return self.coordinates.r <= self.horizon_radius
        
    def destroy(self) -> None:
        """
        Destroy the data cell and clean up resources.
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
            
            self.logger.info("Data cell destroyed")
            
            self.notify_observers("Data cell destroyed")
            
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

    def add_observer(self, observer: callable) -> None:
        self._observers.append(observer)

    def notify_observers(self, message: str) -> None:
        for observer in self._observers:
            observer(message) 