# data/json_store.py
"""
JSON file-based storage implementation.
Simple and portable storage backend.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import os

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.exceptions import StorageError
from data.base_store import BaseStore


class JSONStore(BaseStore):
    """
    JSON file-based storage implementation.
    Stores data in a human-readable JSON file.
    """
    
    def __init__(self, path: Optional[Path] = None):
        """
        Initialize JSON store.
        
        Args:
            path: Path to JSON file. If None, uses default.
        """
        if path is None:
            # Default to user's home directory
            from core.constants import USER_DATA_DIR, DEFAULT_DATA_FILE
            path = Path.home() / USER_DATA_DIR / DEFAULT_DATA_FILE
            
        super().__init__(Path(path))
        
        # Ensure directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> Dict[str, Any]:
        """
        Load data from JSON file.
        
        Returns:
            Dictionary containing stored data
            
        Raises:
            StorageError: If file cannot be read or parsed
        """
        if not self.exists():
            return {}
        
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Ensure we always return a dict
            if not isinstance(data, dict):
                raise StorageError(
                    message=f"Invalid data format in {self.path}",
                    details={"expected": "dict", "got": type(data).__name__}
                )
                
            return data
            
        except json.JSONDecodeError as e:
            raise StorageError(
                message=f"Failed to parse JSON from {self.path}",
                details={"error": str(e), "line": e.lineno, "column": e.colno}
            )
        except IOError as e:
            raise StorageError(
                message=f"Failed to read from {self.path}",
                details={"error": str(e)}
            )
    
    def save(self, data: Dict[str, Any]) -> None:
        """
        Save data to JSON file.
        
        Args:
            data: Dictionary to save
            
        Raises:
            StorageError: If file cannot be written
        """
        if not isinstance(data, dict):
            raise StorageError(
                message="Data must be a dictionary",
                details={"type": type(data).__name__}
            )
        
        try:
            # Write to temporary file first for safety
            temp_path = self.path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename (on most systems)
            temp_path.replace(self.path)
            
        except (IOError, OSError) as e:
            raise StorageError(
                message=f"Failed to write to {self.path}",
                details={"error": str(e)}
            )
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except:
                    pass
            raise StorageError(
                message=f"Unexpected error saving to {self.path}",
                details={"error": str(e)}
            )
    
    def exists(self) -> bool:
        """
        Check if JSON file exists.
        
        Returns:
            True if file exists, False otherwise
        """
        return self.path.exists() and self.path.is_file()
    
    def clear(self) -> None:
        """
        Clear storage by saving empty dict.
        
        Raises:
            StorageError: If clearing fails
        """
        self.save({})
    
    def backup(self, suffix: str = "backup") -> Path:
        """
        Create a backup of the current data file.
        
        Args:
            suffix: Suffix to add to backup filename
            
        Returns:
            Path to backup file
            
        Raises:
            StorageError: If backup fails
        """
        if not self.exists():
            raise StorageError(
                message="Cannot backup non-existent file",
                details={"path": str(self.path)}
            )
        
        backup_path = self.path.with_suffix(f'.{suffix}.json')
        
        try:
            import shutil
            shutil.copy2(self.path, backup_path)
            return backup_path
        except Exception as e:
            raise StorageError(
                message=f"Failed to create backup",
                details={"error": str(e), "backup_path": str(backup_path)}
            )