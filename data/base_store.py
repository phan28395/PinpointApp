# data/base_store.py
"""
Abstract base class for storage implementations.
Defines the interface that all storage backends must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path


class BaseStore(ABC):
    """
    Abstract base class for storage implementations.
    All storage backends must implement these methods.
    """
    
    def __init__(self, path: Optional[Path] = None):
        """
        Initialize the store.
        
        Args:
            path: Optional path for file-based stores
        """
        self.path = path
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """
        Load all data from storage.
        
        Returns:
            Dictionary containing all stored data
            
        Raises:
            StorageError: If loading fails
        """
        pass
    
    @abstractmethod
    def save(self, data: Dict[str, Any]) -> None:
        """
        Save all data to storage.
        
        Args:
            data: Dictionary containing all data to store
            
        Raises:
            StorageError: If saving fails
        """
        pass
    
    @abstractmethod
    def exists(self) -> bool:
        """
        Check if storage exists.
        
        Returns:
            True if storage exists, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """
        Clear all data from storage.
        
        Raises:
            StorageError: If clearing fails
        """
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value by key.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            
        Returns:
            Value for key or default
        """
        data = self.load()
        return data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value by key.
        
        Args:
            key: Key to set
            value: Value to store
        """
        data = self.load()
        data[key] = value
        self.save(data)
    
    def delete(self, key: str) -> None:
        """
        Delete a key from storage.
        
        Args:
            key: Key to delete
        """
        data = self.load()
        if key in data:
            del data[key]
            self.save(data)
    
    def keys(self) -> List[str]:
        """
        Get all keys in storage.
        
        Returns:
            List of all keys
        """
        data = self.load()
        return list(data.keys())