import logging
import time
from quantum_encryption import QuantumEncryption
from spatial_auth import SphericalCoordinates, SpatialEntity
from quantum_console.spatial_auth.anomaly_detection import IntrusionDetector, AccessFrequencyDetection, AnomalyType, AlertSeverity
from sphere.self_destructing_cell import SelfDestructingDataCell

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def demo_quantum_encryption():
    """Demonstrate quantum encryption capabilities."""
    print("=== Quantum Encryption Demo ===")
    
    # Generate keypair
    keys = QuantumEncryption.generate_kyber_keypair()
    print("Generated Keys:")
    print(f"Public Key: {keys['public_key'][:32]}...")
    print(f"Private Key: {keys['private_key'][:32]}...")

    # Example data to encrypt
    message = "Sensitive quantum data"
    
    # Encrypt the data
    encrypted = QuantumEncryption.encrypt_data(keys['public_key'], message)
    print("\nEncrypted Data:")
    print(f"Ciphertext: {encrypted['ciphertext'][:32]}...")
    
    # Decrypt the data
    decrypted_secret = QuantumEncryption.decrypt_data(
        keys['private_key'], 
        encrypted['ciphertext']
    )
    print("\nDecrypted Data:")
    print(f"Secret: {decrypted_secret[:32]}...")

def demo_anomaly_detection():
    """Demonstrate anomaly detection capabilities."""
    print("\n=== Anomaly Detection Demo ===")
    
    # Create an entity with anomaly detection
    entity = SpatialEntity(
        coordinates=SphericalCoordinates(r=0, theta=0, phi=0),
        name="TestEntity",
        secret_credential="spatial_secret"
    )
    
    # Set up intrusion detector with access frequency detection
    access_frequency_detector = AccessFrequencyDetection(max_frequency=5)
    intrusion_detector = IntrusionDetector(entity_id="TestEntity", strategies=[access_frequency_detector])
    
    # Simulate normal access
    for i in range(5):
        intrusion_detector.monitor_access(access_type="normal_access", success=True)
        time.sleep(1)
    
    # Simulate rapid access (potential anomaly)
    for i in range(10):
        intrusion_detector.monitor_access(access_type="rapid_access", success=False)
    
    # Check for alerts
    alerts = intrusion_detector.get_active_alerts(min_severity=AlertSeverity.LOW)
    print("\nActive Alerts:")
    for alert in alerts:
        print(f"Alert Type: {alert.anomaly_type.value}, Severity: {alert.severity.name}")

def demo_self_destructing_data_cell():
    """Demonstrate self-destructing data cell capabilities."""
    print("\n=== Self-Destructing Data Cell Demo ===")
    
    # Create a self-destructing data cell
    initial_coords = SphericalCoordinates(r=5.0, theta=1.0, phi=2.0)
    cell = SelfDestructingDataCell(
        data="Sensitive data",
        coordinates=initial_coords,
        horizon_radius=10.0,
        lifespan_seconds=5.0  # Self-destruct after 5 seconds
    )
    
    print(f"Initial data: {cell.get_data()}")
    
    # Wait for 6 seconds (should be destroyed)
    time.sleep(6)
    print(f"After timeout: {cell.get_data()}")  # Should return None

def main():
    print("=== Investor Presentation Demo ===")
    demo_quantum_encryption()
    demo_anomaly_detection()
    demo_self_destructing_data_cell()

if __name__ == "__main__":
    main() 