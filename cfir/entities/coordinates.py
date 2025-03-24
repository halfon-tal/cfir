from dataclasses import dataclass
from typing import Dict
import math

@dataclass
class SphericalCoordinates:
    """Represents a point in spherical coordinates."""
    r: float      # radius (distance from origin)
    theta: float  # polar angle (0 to π)
    phi: float    # azimuthal angle (0 to 2π)
    
    def __post_init__(self):
        """Validate and normalize coordinates."""
        # Ensure radius is non-negative
        if self.r < 0:
            raise ValueError("Radius must be non-negative")
            
        # Normalize angles to their proper ranges
        self.theta = self.theta % math.pi
        self.phi = self.phi % (2 * math.pi)
        
    def distance_to(self, other: 'SphericalCoordinates') -> float:
        """Calculate distance to another point."""
        # Convert to Cartesian coordinates for distance calculation
        x1, y1, z1 = self.to_cartesian()
        x2, y2, z2 = other.to_cartesian()
        
        return math.sqrt(
            (x2 - x1)**2 + 
            (y2 - y1)**2 + 
            (z2 - z1)**2
        )
        
    def to_cartesian(self) -> tuple[float, float, float]:
        """Convert to Cartesian coordinates."""
        x = self.r * math.sin(self.theta) * math.cos(self.phi)
        y = self.r * math.sin(self.theta) * math.sin(self.phi)
        z = self.r * math.cos(self.theta)
        return (x, y, z)
        
    @classmethod
    def from_cartesian(cls, x: float, y: float, z: float) -> 'SphericalCoordinates':
        """Create from Cartesian coordinates."""
        r = math.sqrt(x*x + y*y + z*z)
        if r == 0:
            return cls(0, 0, 0)
            
        theta = math.acos(z/r)
        phi = math.atan2(y, x)
        
        return cls(r, theta, phi)
        
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'r': self.r,
            'theta': self.theta,
            'phi': self.phi
        }
        
    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, SphericalCoordinates):
            return NotImplemented
        return (
            abs(self.r - other.r) < 1e-10 and
            abs(self.theta - other.theta) < 1e-10 and
            abs(self.phi - other.phi) < 1e-10
        ) 