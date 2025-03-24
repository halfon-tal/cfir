import math
import logging
from spatial_auth import (
    SphericalCoordinates,
    SpatialEntity,
    Receptor,
    SpatialAuthError,
    OutOfBoundsError,
    ReceptorError
)
from zkp_auth import ZeroKnowledgeAuthenticator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def demonstrate_spatial_auth():
    """Demonstrate spatial boundary checking with authentication."""
    try:
        # Create an entity at the origin with audit logging
        entity_coords = SphericalCoordinates(r=0, theta=0, phi=0)
        entity = SpatialEntity(
            coordinates=entity_coords,
            name="SpatialBot",
            secret_credential="spatial_secret",
            audit_log_path="spatial_audit.log"
        )
        
        # Add receptors with different data types
        entity.add_receptor(
            SphericalCoordinates(r=5, theta=math.pi/4, phi=0),
            detection_radius=5.0,
            data_type="temperature"
        )
        
        entity.add_receptor(
            SphericalCoordinates(r=3, theta=math.pi/2, phi=math.pi),
            detection_radius=7.0,
            data_type="humidity"
        )
        
        print("\nSpatial Authentication Demo:")
        print(f"Entity maximum horizon radius: {entity.horizon._max_radius}")
        
        # Test points at different distances
        test_points = [
            (
                "Near Temperature Point",
                SphericalCoordinates(r=7, theta=math.pi/4, phi=0),
                "temperature"
            ),
            (
                "Far Point",
                SphericalCoordinates(r=15, theta=math.pi/4, phi=0),
                "temperature"
            ),
            (
                "Near Humidity Point",
                SphericalCoordinates(r=5, theta=math.pi/2, phi=math.pi),
                "humidity"
            )
        ]
        
        # Create verifier for ZKP
        verifier = ZeroKnowledgeAuthenticator("verifier_secret")
        
        for name, point, data_type in test_points:
            print(f"\nTesting {name}:")
            print(f"Distance from origin: {point.r}")
            print(f"Data type: {data_type}")
            
            try:
                # Generate challenge and proof
                challenge = verifier.generate_challenge("test_ip")
                proof = entity.authenticator.generate_proof(challenge)
                
                # Check access with both spatial and ZKP verification
                can_access = entity.can_access_data(
                    point,
                    data_type=data_type,
                    proof_response=proof,
                    challenge=challenge
                )
                print(f"Access granted: {can_access}")
                
                if can_access:
                    # Show nearby receptors
                    nearby = entity.horizon.get_nearby_receptors(
                        point,
                        data_type
                    )
                    print(
                        f"Found {len(nearby)} nearby receptors "
                        f"for {data_type}"
                    )
                    
            except SpatialAuthError as e:
                print(f"Access check failed: {str(e)}")
                
    except Exception as e:
        print(f"Demo failed: {str(e)}")

def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    try:
        # Try to create invalid coordinates
        print("\nTesting Invalid Coordinates:")
        try:
            coords = SphericalCoordinates(r=-1, theta=0, phi=0)
        except ValueError as e:
            print(f"Caught invalid coordinates: {str(e)}")
        
        # Try to create invalid receptor
        print("\nTesting Invalid Receptor:")
        entity = SpatialEntity(
            SphericalCoordinates(r=0, theta=0, phi=0),
            "ErrorBot",
            "test_secret"
        )
        try:
            entity.add_receptor(
                SphericalCoordinates(r=1, theta=0, phi=0),
                detection_radius=-1,
                data_type="test"
            )
        except ReceptorError as e:
            print(f"Caught invalid receptor: {str(e)}")
            
    except Exception as e:
        print(f"Error handling demo failed: {str(e)}")

def main():
    demonstrate_spatial_auth()
    demonstrate_error_handling()

if __name__ == "__main__":
    main() 