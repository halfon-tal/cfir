import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from collections import deque, defaultdict
import numpy as np
from threading import Lock
import json
from datetime import datetime, timedelta

class AnomalyType(Enum):
    """Types of anomalies that can be detected."""
    ACCESS_FREQUENCY = "access_frequency"
    SPATIAL_VIOLATION = "spatial_violation"
    AUTH_FAILURE = "authentication_failure"
    SYNC_FAILURE = "synchronization_failure"
    DATA_PATTERN = "data_pattern"

class AlertSeverity(Enum):
    """Severity levels for anomaly alerts."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AnomalyAlert:
    """Represents an anomaly detection alert."""
    alert_id: str
    anomaly_type: AnomalyType
    severity: AlertSeverity
    timestamp: float
    details: Dict
    entity_id: str
    resolved: bool = False
    resolution_time: Optional[float] = None
    resolution_notes: Optional[str] = None

class AccessPattern:
    """Tracks and analyzes access patterns."""
    
    def __init__(
        self,
        window_size: int = 3600,  # 1 hour window
        max_frequency: int = 1000  # max requests per window
    ):
        self.window_size = window_size
        self.max_frequency = max_frequency
        self.access_times = deque()
        self.access_types = defaultdict(int)
        self._lock = Lock()
        
    def record_access(
        self,
        access_type: str,
        timestamp: Optional[float] = None
    ) -> None:
        """Record an access event."""
        with self._lock:
            now = timestamp or time.time()
            self.access_times.append(now)
            self.access_types[access_type] += 1
            
            # Clean old records
            self._cleanup(now)
    
    def _cleanup(self, current_time: float) -> None:
        """Remove records outside the window."""
        cutoff = current_time - self.window_size
        while self.access_times and self.access_times[0] < cutoff:
            self.access_times.popleft()
    
    def get_frequency(self) -> float:
        """Calculate current access frequency."""
        with self._lock:
            now = time.time()
            self._cleanup(now)
            window_duration = (
                now - self.access_times[0] if self.access_times
                else self.window_size
            )
            return len(self.access_times) / window_duration if window_duration > 0 else 0

class IntrusionDetector:
    """Detects anomalies in entity behavior."""
    
    def __init__(
        self,
        entity_id: str,
        config: Optional[Dict] = None
    ):
        """
        Initialize intrusion detector.
        
        Args:
            entity_id: ID of entity to monitor
            config: Optional configuration overrides
        """
        self.entity_id = entity_id
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
            
        # Initialize tracking
        self.access_pattern = AccessPattern(
            window_size=self.config['window_size'],
            max_frequency=self.config['max_frequency']
        )
        self.alerts: List[AnomalyAlert] = []
        self.alert_count = 0
        
        # Thread safety
        self._lock = Lock()
        
        # Logging
        self.logger = logging.getLogger(f"intrusion_detector_{entity_id}")
        
        # Statistical tracking
        self.stats = defaultdict(int)
        
    @staticmethod
    def _get_default_config() -> Dict:
        """Get default configuration."""
        return {
            'window_size': 3600,  # 1 hour
            'max_frequency': 1000,  # requests per window
            'auth_failure_threshold': 5,  # failures before alert
            'sync_failure_threshold': 3,  # failures before alert
            'spatial_violation_threshold': 2,  # violations before alert
            'alert_expiry': 86400,  # 24 hours
        }
    
    def monitor_access(
        self,
        access_type: str,
        coordinates: Optional['SphericalCoordinates'] = None,
        success: bool = True
    ) -> Optional[AnomalyAlert]:
        """
        Monitor an access attempt.
        
        Args:
            access_type: Type of access
            coordinates: Optional spatial coordinates
            success: Whether access was successful
            
        Returns:
            Optional[AnomalyAlert]: Alert if anomaly detected
        """
        try:
            self.access_pattern.record_access(access_type)
            
            alerts = []
            
            # Check frequency anomalies
            frequency = self.access_pattern.get_frequency()
            if frequency > self.config['max_frequency']:
                alerts.append(
                    self._create_alert(
                        AnomalyType.ACCESS_FREQUENCY,
                        AlertSeverity.HIGH,
                        {
                            'frequency': frequency,
                            'threshold': self.config['max_frequency']
                        }
                    )
                )
            
            # Track failures
            if not success:
                self.stats['failures'] += 1
                if (
                    self.stats['failures'] >= 
                    self.config['auth_failure_threshold']
                ):
                    alerts.append(
                        self._create_alert(
                            AnomalyType.AUTH_FAILURE,
                            AlertSeverity.CRITICAL,
                            {'failure_count': self.stats['failures']}
                        )
                    )
            
            return alerts[0] if alerts else None
            
        except Exception as e:
            self.logger.error(f"Monitor access failed: {str(e)}")
            return None
    
    def monitor_sync(
        self,
        success: bool,
        details: Optional[Dict] = None
    ) -> Optional[AnomalyAlert]:
        """Monitor synchronization attempts."""
        try:
            if not success:
                self.stats['sync_failures'] += 1
                if (
                    self.stats['sync_failures'] >= 
                    self.config['sync_failure_threshold']
                ):
                    return self._create_alert(
                        AnomalyType.SYNC_FAILURE,
                        AlertSeverity.HIGH,
                        {
                            'failure_count': self.stats['sync_failures'],
                            'details': details or {}
                        }
                    )
            return None
            
        except Exception as e:
            self.logger.error(f"Monitor sync failed: {str(e)}")
            return None
    
    def _create_alert(
        self,
        anomaly_type: AnomalyType,
        severity: AlertSeverity,
        details: Dict
    ) -> AnomalyAlert:
        """Create and record an alert."""
        with self._lock:
            self.alert_count += 1
            alert = AnomalyAlert(
                alert_id=f"{self.entity_id}_alert_{self.alert_count}",
                anomaly_type=anomaly_type,
                severity=severity,
                timestamp=time.time(),
                details=details,
                entity_id=self.entity_id
            )
            self.alerts.append(alert)
            
            self.logger.warning(
                f"Anomaly detected: {anomaly_type.value} "
                f"(Severity: {severity.name})"
            )
            
            return alert
    
    def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: str
    ) -> bool:
        """Mark an alert as resolved."""
        with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolution_time = time.time()
                    alert.resolution_notes = resolution_notes
                    return True
            return False
    
    def get_active_alerts(
        self,
        min_severity: AlertSeverity = AlertSeverity.LOW
    ) -> List[AnomalyAlert]:
        """Get unresolved alerts above severity threshold."""
        return [
            alert for alert in self.alerts
            if not alert.resolved and alert.severity.value >= min_severity.value
        ]
    
    def cleanup_old_alerts(self) -> None:
        """Remove expired alerts."""
        with self._lock:
            now = time.time()
            cutoff = now - self.config['alert_expiry']
            self.alerts = [
                alert for alert in self.alerts
                if alert.timestamp > cutoff or not alert.resolved
            ] 