"""Agent memory system for storing and retrieving execution context."""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

from logger import get_logger

logger = get_logger("memory")


class MemoryItem(BaseModel):
    """Single memory item."""
    key: str
    value: Any
    timestamp: str
    ttl_minutes: Optional[int] = None  # Time-to-live in minutes
    metadata: Dict[str, Any] = {}


class AgentMemory:
    """In-memory storage for agent execution context."""
    
    def __init__(self, agent_id: str, memory_type: str = "short_term"):
        """
        Initialize agent memory.
        
        Args:
            agent_id: ID of the agent
            memory_type: "short_term" (session) or "long_term" (persistent)
        """
        self.agent_id = agent_id
        self.memory_type = memory_type
        self._store: Dict[str, MemoryItem] = {}
    
    def store(
        self,
        key: str,
        value: Any,
        ttl_minutes: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store a value in memory.
        
        Args:
            key: Memory key
            value: Value to store
            ttl_minutes: Optional time-to-live
            metadata: Optional metadata
        
        Returns:
            True if stored successfully
        """
        try:
            self._store[key] = MemoryItem(
                key=key,
                value=value,
                timestamp=datetime.now().isoformat(),
                ttl_minutes=ttl_minutes,
                metadata=metadata or {}
            )
            logger.debug(f"Stored memory: {key} for agent {self.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store memory {key}: {str(e)}")
            return False
    
    def retrieve(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from memory.
        
        Args:
            key: Memory key
        
        Returns:
            Value if found and not expired, None otherwise
        """
        if key not in self._store:
            logger.debug(f"Memory key not found: {key}")
            return None
        
        item = self._store[key]
        
        # Check if expired
        if item.ttl_minutes:
            stored_time = datetime.fromisoformat(item.timestamp)
            elapsed_minutes = (datetime.now() - stored_time).total_seconds() / 60
            if elapsed_minutes > item.ttl_minutes:
                del self._store[key]
                logger.debug(f"Memory expired: {key}")
                return None
        
        return item.value
    
    def delete(self, key: str) -> bool:
        """Delete a memory item."""
        if key in self._store:
            del self._store[key]
            logger.debug(f"Deleted memory: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all memory items."""
        self._store.clear()
        logger.info(f"Cleared all memory for agent {self.agent_id}")
    
    def search(self, pattern: str) -> Dict[str, Any]:
        """
        Search memory items by key pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards *)
        
        Returns:
            Dictionary of matching key-value pairs
        """
        import fnmatch
        results = {}
        for key, item in self._store.items():
            if fnmatch.fnmatch(key, pattern):
                results[key] = item.value
        return results
    
    def get_all(self) -> Dict[str, Any]:
        """Get all memory items."""
        return {key: item.value for key, item in self._store.items()}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "agent_id": self.agent_id,
            "memory_type": self.memory_type,
            "item_count": len(self._store),
            "items": [
                {
                    "key": key,
                    "stored_at": item.timestamp,
                    "ttl_minutes": item.ttl_minutes,
                    "metadata": item.metadata,
                }
                for key, item in self._store.items()
            ]
        }


class MemoryManager:
    """Manages memory for multiple agents."""
    
    def __init__(self):
        """Initialize memory manager."""
        self._agent_memories: Dict[str, Dict[str, AgentMemory]] = {}  # agent_id -> type -> memory
    
    def get_memory(self, agent_id: str, memory_type: str = "short_term") -> AgentMemory:
        """
        Get or create memory for an agent.
        
        Args:
            agent_id: Agent ID
            memory_type: "short_term" or "long_term"
        
        Returns:
            AgentMemory instance
        """
        if agent_id not in self._agent_memories:
            self._agent_memories[agent_id] = {}
        
        if memory_type not in self._agent_memories[agent_id]:
            self._agent_memories[agent_id][memory_type] = AgentMemory(agent_id, memory_type)
            logger.info(f"Created {memory_type} memory for agent {agent_id}")
        
        return self._agent_memories[agent_id][memory_type]
    
    def clear_agent_memory(self, agent_id: str, memory_type: Optional[str] = None) -> None:
        """
        Clear memory for an agent.
        
        Args:
            agent_id: Agent ID
            memory_type: Specific memory type to clear, or None for all
        """
        if agent_id not in self._agent_memories:
            return
        
        if memory_type:
            if memory_type in self._agent_memories[agent_id]:
                self._agent_memories[agent_id][memory_type].clear()
                logger.info(f"Cleared {memory_type} memory for agent {agent_id}")
        else:
            for mem in self._agent_memories[agent_id].values():
                mem.clear()
            logger.info(f"Cleared all memory for agent {agent_id}")
    
    def get_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get memory stats for agent."""
        stats = {"agent_id": agent_id, "memories": {}}
        
        if agent_id in self._agent_memories:
            for mem_type, memory in self._agent_memories[agent_id].items():
                stats["memories"][mem_type] = memory.get_stats()
        
        return stats


# Global memory manager instance
_memory_manager = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
