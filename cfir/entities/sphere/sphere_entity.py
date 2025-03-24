import logging
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Any, Optional, Set, List
from threading import Lock
import json
from datetime import datetime
from enum import Enum
import hashlib
from concurrent.futures import ThreadPoolExecutor
import asyncio
from collections import defaultdict

from spatial_auth import SphericalCoordinates, SpatialAuthError
from quantum_encryption import QuantumEncryption
from quantum_console.core.hybrid_executer import HybridExecutionManager, Task, TaskPriority
from quantum_console.spatial_auth.anomaly_detection import IntrusionDetector, AnomalyType, AlertSeverity

class SyncStatus(Enum):
    """Synchronization status of data."""
    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"

class DataOperation(Enum):
    """Types of data operations."""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    QUERY = "query"

@dataclass
class DataRecord:
    """Represents a data record with metadata."""
    value: Any
    timestamp: float
    version: int
    sync_status: SyncStatus
    last_modified: float
    checksum: str
    
    @classmethod
    def create(cls, value: Any) -> 'DataRecord':
        """Create a new data record."""
        now = time.time()
        return cls(
            value=value,
            timestamp=now,
            version=1,
            sync_status=SyncStatus.PENDING,
            last_modified=now,
            checksum=cls._calculate_checksum(value)
        )
    
    @staticmethod
    def _calculate_checksum(value: Any) -> str:
        """Calculate checksum for value."""
        return hashlib.sha256(
            json.dumps(value, sort_keys=True).encode()
        ).hexdigest()
    
    def update(self, new_value: Any) -> None:
        """Update record with new value."""
        self.value = new_value
        self.version += 1
        self.last_modified = time.time()
        self.sync_status = SyncStatus.PENDING
        self.checksum = self._calculate_checksum(new_value)

class SyncOperation:
    """Represents a synchronization operation."""
    
    def __init__(
        self,
        operation: DataOperation,
        key: str,
        value: Optional[Any] = None,
        timestamp: Optional[float] = None
    ):
        self.operation = operation
        self.key = key
        self.value = value
        self.timestamp = timestamp or time.time()
        self.retries = 0
        self.max_retries = 3
        self.status = SyncStatus.PENDING

class SphereEntity:
    """An entity in the spherical universe with embedded data storage."""
    
    def __init__(
        self,
        coordinates: SphericalCoordinates,
        name: str,
        universe: 'Universe',
        encryption_key: Optional[str] = None,
        max_local_storage: int = 1000
    ):
        """
        Initialize a sphere entity.
        
        Args:
            coordinates: Entity's position in spherical coordinates
            name: Entity identifier
            universe: Reference to global universe
            encryption_key: Optional encryption key for data
            max_local_storage: Maximum number of local records
        """
        self.entity_id = str(uuid.uuid4())
        self.coordinates = coordinates
        self.name = name
        self.universe = universe
        self.encryption_key = encryption_key
        self.max_local_storage = max_local_storage
        self._local_storage: Dict[str, DataRecord] = {}
        self._pending_syncs: Set[str] = set()
        self._storage_lock = Lock()
        self.logger = logging.getLogger(f"SphereEntity.{self.entity_id}")
        
        # Initialize storage and sync queue
        self._sync_queue: asyncio.Queue = asyncio.Queue()
        self._sync_lock = Lock()
        
        # Initialize encryption
        self.encryption = QuantumEncryption()
        if encryption_key:
            self.encryption_key = encryption_key
        else:
            # Generate new key pair
            keys = self.encryption.generate_kyber_keypair()
            self.encryption_key = keys['private_key']
        
        # Initialize task executor
        self.executor = HybridExecutionManager(
            cpu_count=2,
            qpu_count=1
        )
        
        # Start sync worker
        self._start_sync_worker()
        
        # Add intrusion detector
        self.intrusion_detector = IntrusionDetector(
            self.entity_id,
            config={
                'window_size': 3600,
                'max_frequency': 1000
            }
        )
    
    def _start_sync_worker(self) -> None:
        """Start the background sync worker."""
        self._sync_worker = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix=f"sync_{self.entity_id}"
        )
        self._sync_worker.submit(self._sync_loop)
    
    async def _sync_loop(self) -> None:
        """Background sync loop."""
        while True:
            try:
                operation = await self._sync_queue.get()
                await self._process_sync_operation(operation)
                self._sync_queue.task_done()
            except Exception as e:
                self.logger.error(f"Sync error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_sync_operation(
        self,
        operation: SyncOperation
    ) -> None:
        """Process a sync operation."""
        try:
            if operation.operation == DataOperation.INSERT:
                await self.universe.sync_insert(
                    self.entity_id,
                    operation.key,
                    operation.value
                )
            elif operation.operation == DataOperation.DELETE:
                await self.universe.sync_delete(
                    self.entity_id,
                    operation.key
                )
            
            with self._storage_lock:
                if operation.key in self._local_storage:
                    record = self._local_storage[operation.key]
                    record.sync_status = SyncStatus.SYNCED
            
            self._pending_syncs.remove(operation.key)
            
        except Exception as e:
            self.logger.error(
                f"Sync operation failed for {operation.key}: {str(e)}"
            )
            operation.retries += 1
            
            if operation.retries < operation.max_retries:
                # Requeue for retry
                await self._sync_queue.put(operation)
            else:
                self.logger.error(
                    f"Max retries exceeded for {operation.key}"
                )
                with self._storage_lock:
                    if operation.key in self._local_storage:
                        record = self._local_storage[operation.key]
                        record.sync_status = SyncStatus.FAILED
    
    def insert_data(self, key: str, value: Any) -> bool:
        """
        Insert data into local storage.
        
        Args:
            key: Data key
            value: Data value
            
        Returns:
            bool: True if successful
        """
        try:
            with self._storage_lock:
                # Check storage limit
                if (
                    len(self._local_storage) >= self.max_local_storage and 
                    key not in self._local_storage
                ):
                    self.logger.warning("Local storage limit reached")
                    return False
                
                # Create or update record
                if key in self._local_storage:
                    self._local_storage[key].update(value)
                else:
                    self._local_storage[key] = DataRecord.create(value)
                
                # Queue for sync
                operation = SyncOperation(
                    DataOperation.INSERT,
                    key,
                    value
                )
                asyncio.run_coroutine_threadsafe(
                    self._sync_queue.put(operation),
                    self.universe.loop
                )
                self._pending_syncs.add(key)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Insert failed for key {key}: {str(e)}")
            return False
    
    def query_data(self, key: str) -> Optional[Any]:
        """Query data with anomaly detection."""
        try:
            # Monitor access attempt
            alert = self.intrusion_detector.monitor_access(
                'query',
                coordinates=self.coordinates
            )
            
            if alert:
                self.logger.warning(
                    f"Anomaly detected during query: {alert.anomaly_type.value}"
                )
            
            with self._storage_lock:
                record = self._local_storage.get(key)
                success = record is not None
                
                # Monitor result
                self.intrusion_detector.monitor_access(
                    'query_result',
                    success=success
                )
                
                if record:
                    return record.value
                return None
                
        except Exception as e:
            self.logger.error(f"Query failed for key {key}: {str(e)}")
            self.intrusion_detector.monitor_access(
                'query_error',
                success=False
            )
            return None
    
    def delete_data(self, key: str) -> bool:
        """
        Delete data from local storage.
        
        Args:
            key: Data key
            
        Returns:
            bool: True if successful
        """
        try:
            with self._storage_lock:
                if key in self._local_storage:
                    del self._local_storage[key]
                    
                    # Queue for sync
                    operation = SyncOperation(
                        DataOperation.DELETE,
                        key
                    )
                    asyncio.run_coroutine_threadsafe(
                        self._sync_queue.put(operation),
                        self.universe.loop
                    )
                    self._pending_syncs.add(key)
                    
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"Delete failed for key {key}: {str(e)}")
            return False
    
    def get_sync_status(self, key: str) -> Optional[SyncStatus]:
        """Get sync status for a key."""
        with self._storage_lock:
            record = self._local_storage.get(key)
            if record:
                return record.sync_status
            return None
    
    def get_pending_syncs(self) -> Set[str]:
        """Get set of keys pending synchronization."""
        return self._pending_syncs.copy()
    
    def shutdown(self) -> None:
        """Clean shutdown of entity."""
        self._sync_worker.shutdown(wait=True)
        self.executor.shutdown() 