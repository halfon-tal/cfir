import logging
import time
from sphere.self_destructing_cell import SelfDestructingDataCell, SphericalCoordinates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def demonstrate_spatial_destruction():
    """Demonstrate spatial-based self-destruction."""
    # Create a data cell within horizon
    initial_coords = SphericalCoordinates(r=5.0, theta=1.0, phi=2.0)
    cell = SelfDestructingDataCell(
        data="Sensitive data",
        coordinates=initial_coords,
        horizon_radius=10.0
    )
    
    print("\nSpatial Destruction Demo:")
    print(f"Initial data: {cell.get_data()}")
    
    # Move within horizon (should survive)
    new_coords = SphericalCoordinates(r=8.0, theta=1.0, phi=2.0)
    cell.update_coordinates(new_coords)
    print(f"After safe move: {cell.get_data()}")
    
    # Move beyond horizon (should trigger destruction)
    new_coords = SphericalCoordinates(r=15.0, theta=1.0, phi=2.0)
    cell.update_coordinates(new_coords)
    print(f"After boundary violation: {cell.get_data()}")

def demonstrate_timer_destruction():
    """Demonstrate timer-based self-destruction."""
    # Create a data cell with 3-second lifespan
    coords = SphericalCoordinates(r=5.0, theta=1.0, phi=2.0)
    cell = SelfDestructingDataCell(
        data="Time-sensitive data",
        coordinates=coords,
        horizon_radius=10.0,
        lifespan_seconds=3.0
    )
    
    print("\nTimer Destruction Demo:")
    print(f"Initial data: {cell.get_data()}")
    
    # Wait for 2 seconds (should still exist)
    time.sleep(2)
    print(f"After 2 seconds: {cell.get_data()}")
    
    # Wait for 2 more seconds (should be destroyed)
    time.sleep(2)
    print(f"After timeout: {cell.get_data()}")

def main():
    demonstrate_spatial_destruction()
    demonstrate_timer_destruction()

if __name__ == "__main__":
    main() 