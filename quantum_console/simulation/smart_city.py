from dataclasses import dataclass
from typing import List, Dict, Optional, Any
import numpy as np
import logging
from datetime import datetime
from threading import Lock
import json

from cfir.entities import Entity, Zone
from ..spatial_auth import SphericalCoordinates
from quantum_encryption import QuantumEncryption

@dataclass
class SensorReading:
    """IoT sensor reading."""
    sensor_id: str
    sensor_type: str
    value: float
    timestamp: datetime
    coordinates: SphericalCoordinates
    confidence: float

class IoTSensor(Entity):
    """Base class for IoT sensors."""
    
    def __init__(
        self,
        sensor_id: str,
        sensor_type: str,
        position: SphericalCoordinates,
        update_interval: float = 1.0,  # seconds
        encryption_key: Optional[str] = None
    ):
        super().__init__(
            coordinates=position,
            name=f"{sensor_type}_{sensor_id}",
            entity_type="iot_sensor"
        )
        
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.update_interval = update_interval
        self.last_update = datetime.utcnow()
        
        # Initialize encryption
        self.encryption = QuantumEncryption()
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            keys = self.encryption.generate_kyber_keypair()
            self.encryption_key = keys['private_key']
        
        # Thread safety
        self._reading_lock = Lock()
        
        # Logging
        self.logger = logging.getLogger(f"iot_{sensor_id}")
        
    def update(self) -> Optional[SensorReading]:
        """Update sensor reading."""
        now = datetime.utcnow()
        if (now - self.last_update).total_seconds() < self.update_interval:
            return None
            
        with self._reading_lock:
            try:
                reading = self._take_reading()
                self.last_update = now
                
                # Encrypt and store reading
                encrypted_data = self.encrypt_reading(reading)
                self.insert_data(
                    f"reading_{now.timestamp()}",
                    encrypted_data
                )
                
                return reading
                
            except Exception as e:
                self.logger.error(f"Sensor update failed: {str(e)}")
                return None
                
    def _take_reading(self) -> SensorReading:
        """Take a sensor reading."""
        raise NotImplementedError
        
    def encrypt_reading(self, reading: SensorReading) -> Dict:
        """Encrypt sensor reading."""
        try:
            data = {
                'sensor_id': reading.sensor_id,
                'sensor_type': reading.sensor_type,
                'value': reading.value,
                'timestamp': reading.timestamp.isoformat(),
                'coordinates': reading.coordinates.to_dict(),
                'confidence': reading.confidence
            }
            
            encrypted = self.encryption.encrypt_data(
                self.encryption_key,
                json.dumps(data)
            )
            
            return {
                'encrypted_data': encrypted['ciphertext'],
                'metadata': {
                    'sensor_id': reading.sensor_id,
                    'timestamp': reading.timestamp.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise

class TrafficLight(IoTSensor):
    """Traffic light with embedded sensors."""
    
    def __init__(
        self,
        light_id: str,
        position: SphericalCoordinates,
        initial_state: str = 'red'
    ):
        super().__init__(
            sensor_id=light_id,
            sensor_type='traffic_light',
            position=position,
            update_interval=0.1
        )
        
        self.state = initial_state
        self.vehicle_count = 0
        self.wait_times: Dict[str, float] = {}
        
    def _take_reading(self) -> SensorReading:
        """Monitor traffic conditions."""
        try:
            # Detect vehicles
            nearby = self.scan_environment()
            self.vehicle_count = len(nearby)
            
            # Update wait times
            self._update_wait_times(nearby)
            
            return SensorReading(
                sensor_id=self.sensor_id,
                sensor_type=self.sensor_type,
                value=self.vehicle_count,
                timestamp=datetime.utcnow(),
                coordinates=self.coordinates,
                confidence=0.95
            )
            
        except Exception as e:
            self.logger.error(f"Traffic monitoring failed: {str(e)}")
            raise
            
    def _update_wait_times(self, nearby_vehicles: List[Entity]) -> None:
        """Update vehicle wait times."""
        now = datetime.utcnow()
        
        # Add new vehicles
        for vehicle in nearby_vehicles:
            if vehicle.entity_id not in self.wait_times:
                self.wait_times[vehicle.entity_id] = now.timestamp()
        
        # Remove departed vehicles
        departed = set(self.wait_times.keys()) - {
            v.entity_id for v in nearby_vehicles
        }
        for vehicle_id in departed:
            del self.wait_times[vehicle_id]

class SmartUtility(IoTSensor):
    """Smart utility sensor (power, water, etc.)."""
    
    def __init__(
        self,
        utility_id: str,
        utility_type: str,
        position: SphericalCoordinates,
        capacity: float,
        update_interval: float = 5.0
    ):
        super().__init__(
            sensor_id=utility_id,
            sensor_type=f"utility_{utility_type}",
            position=position,
            update_interval=update_interval
        )
        
        self.utility_type = utility_type
        self.capacity = capacity
        self.current_load = 0.0
        self.efficiency = 1.0
        
    def _take_reading(self) -> SensorReading:
        """Monitor utility metrics."""
        try:
            # Simulate load and efficiency changes
            self._update_load()
            self._update_efficiency()
            
            return SensorReading(
                sensor_id=self.sensor_id,
                sensor_type=self.sensor_type,
                value=self.current_load,
                timestamp=datetime.utcnow(),
                coordinates=self.coordinates,
                confidence=self.efficiency
            )
            
        except Exception as e:
            self.logger.error(f"Utility monitoring failed: {str(e)}")
            raise
            
    def _update_load(self) -> None:
        """Update current load."""
        # Implement realistic load simulation here
        self.current_load = min(
            self.capacity,
            max(0, self.current_load + np.random.normal(0, 0.1))
        )
        
    def _update_efficiency(self) -> None:
        """Update system efficiency."""
        # Implement efficiency calculation here
        load_factor = self.current_load / self.capacity
        self.efficiency = 1.0 - (load_factor ** 2) * 0.2 