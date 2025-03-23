import logging
import time
from sphere_entity import SphereEntity
from sphere_universe import Universe
from spatial_auth import SphericalCoordinates
from anomaly_detection import AlertSeverity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demonstrate_anomaly_detection():
    """Demonstrate anomaly detection capabilities."""
    
    # Create universe and entity
    universe = Universe()
    entity = SphereEntity(
        SphericalCoordinates(r=0, theta=0, phi=0),
        "TestEntity",
        universe
    )
    
    # Insert some test data
    entity.insert_data("test_key", "test_value")
    
    print("\nTesting Normal Access:")
    # Normal access pattern
    for i in range(5):
        result = entity.query_data("test_key")
        print(f"Query {i + 1}: {result}")
        time.sleep(1)
    
    print("\nTesting Rapid Access:")
    # Simulate rapid access (potential anomaly)
    for i in range(100):
        entity.query_data("test_key")
    
    # Check for alerts
    alerts = entity.intrusion_detector.get_active_alerts(
        min_severity=AlertSeverity.MEDIUM
    )
    
    print("\nActive Alerts:")
    for alert in alerts:
        print(f"Alert Type: {alert.anomaly_type.value}")
        print(f"Severity: {alert.severity.name}")
        print(f"Details: {alert.details}")
    
    # Cleanup
    universe.shutdown()

def main():
    demonstrate_anomaly_detection()

if __name__ == "__main__":
    main() 