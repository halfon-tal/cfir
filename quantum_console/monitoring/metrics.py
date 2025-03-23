import psutil
import time
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class SystemMetrics:
    """System-wide metrics."""
    cpu_usage: float
    memory_usage: float
    active_entities: int
    alert_count: int
    qpu_utilization: float
    timestamp: datetime

class MetricsCollector:
    """Collects and aggregates system metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            return SystemMetrics(
                cpu_usage=psutil.cpu_percent(),
                memory_usage=psutil.virtual_memory().percent,
                active_entities=self._count_active_entities(),
                alert_count=self._count_active_alerts(),
                qpu_utilization=self._get_qpu_utilization(),
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {str(e)}")
            raise
            
    def _count_active_entities(self) -> int:
        """Count active entities."""
        from ..models import Entity
        return Entity.count_active()
        
    def _count_active_alerts(self) -> int:
        """Count active alerts."""
        from ..models import Alert
        return Alert.count_active()
        
    def _get_qpu_utilization(self) -> float:
        """Get QPU utilization percentage."""
        # In production, integrate with actual QPU metrics
        return 0.0  # Placeholder 