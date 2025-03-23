import asyncio
import logging
from typing import Dict, Any, Optional, Set
from threading import Lock
import time
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class GlobalRecord:
    """Global data record."""
    value: Any
    entity_id: str
    timestamp: float
    version: int

class Universe:
    """Global universe managing entity synchronization."""
    
    def __init__(self):
        """Initialize the universe."""
        self.global_storage: Dict[str, Dict[str, GlobalRecord]] = defaultdict(dict)
        self._storage_lock = Lock()
        self.loop = asyncio.new_event_loop()
        self.logger = logging.getLogger("universe")
        
        # Track entity registrations
        self.entities: Dict[str, 'SphereEntity'] = {}
        self._entity_lock = Lock()
        
        # Start event loop
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
    
    def register_entity(self, entity: 'SphereEntity') -> None:
        """Register an entity with the universe."""
        with self._entity_lock:
            self.entities[entity.entity_id] = entity
            self.logger.info(f"Registered entity: {entity.entity_id}")
    
    def unregister_entity(self, entity_id: str) -> None:
        """Unregister an entity."""
        with self._entity_lock:
            if entity_id in self.entities:
                del self.entities[entity_id]
                self.logger.info(f"Unregistered entity: {entity_id}")
    
    async def sync_insert(
        self,
        entity_id: str,
        key: str,
        value: Any
    ) -> None:
        """
        Synchronize an insert operation.
        
        Args:
            entity_id: Source entity ID
            key: Data key
            value: Data value
        """
        try:
            with self._storage_lock:
                entity_storage = self.global_storage[entity_id]
                
                if key in entity_storage:
                    record = entity_storage[key]
                    record.value = value
                    record.version += 1
                    record.timestamp = time.time()
                else:
                    entity_storage[key] = GlobalRecord(
                        value=value,
                        entity_id=entity_id,
                        timestamp=time.time(),
                        version=1
                    )
                    
        except Exception as e:
            self.logger.error(
                f"Sync insert failed for {entity_id}/{key}: {str(e)}"
            )
            raise
    
    async def sync_delete(self, entity_id: str, key: str) -> None:
        """
        Synchronize a delete operation.
        
        Args:
            entity_id: Source entity ID
            key: Data key to delete
        """
        try:
            with self._storage_lock:
                if key in self.global_storage[entity_id]:
                    del self.global_storage[entity_id][key]
                    
        except Exception as e:
            self.logger.error(
                f"Sync delete failed for {entity_id}/{key}: {str(e)}"
            )
            raise
    
    def query_global(
        self,
        entity_id: str,
        key: str
    ) -> Optional[GlobalRecord]:
        """Query global storage."""
        with self._storage_lock:
            return self.global_storage[entity_id].get(key)
    
    def shutdown(self) -> None:
        """Clean shutdown of universe."""
        self.loop.stop()
        for entity in self.entities.values():
            entity.shutdown() 