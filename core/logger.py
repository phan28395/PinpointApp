# core/logger.py
"""
Simple JSON logger for PinPoint.
Layer 3: Independent (no EventBus dependency).
"""

import json
import datetime
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from enum import Enum


class LogLevel(Enum):
    """Log levels in ascending order of severity."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Logger:
    """
    Simple JSON logger that writes to file and optionally console.
    Independent of EventBus to avoid circular dependencies.
    """
    
    def __init__(self, 
                 name: str,
                 log_file: Optional[Union[str, Path]] = None,
                 level: LogLevel = LogLevel.INFO,
                 console: bool = True):
        """
        Initialize logger.
        
        Args:
            name: Logger name (e.g., module name)
            log_file: Path to log file (optional)
            level: Minimum log level
            console: Whether to also print to console
        """
        self.name = name
        self.level = level
        self.console = console
        self.log_file = Path(log_file) if log_file else None
        
        # Ensure log directory exists
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _format_entry(self, level: LogLevel, message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format a log entry as a dictionary."""
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "logger": self.name,
            "level": level.name,
            "message": message
        }
        
        if data:
            entry["data"] = data
            
        return entry
    
    def _write_entry(self, entry: Dict[str, Any]) -> None:
        """Write a log entry to file and/or console."""
        # Console output
        if self.console:
            level = entry["level"]
            timestamp = entry["timestamp"]
            message = entry["message"]
            
            # Simple console format
            console_msg = f"[{timestamp}] {level}: {message}"
            if "data" in entry:
                console_msg += f" | {json.dumps(entry['data'])}"
            print(console_msg)
        
        # File output
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    json.dump(entry, f)
                    f.write('\n')
            except Exception as e:
                # If we can't write to log file, at least print to console
                if self.console:
                    print(f"Failed to write to log file: {e}")
    
    def log(self, level: LogLevel, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a message at the specified level.
        
        Args:
            level: Log level
            message: Log message
            data: Optional structured data
        """
        if level.value >= self.level.value:
            entry = self._format_entry(level, message, data)
            self._write_entry(entry)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug message."""
        self.log(LogLevel.DEBUG, message, data)
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an info message."""
        self.log(LogLevel.INFO, message, data)
    
    def warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a warning message."""
        self.log(LogLevel.WARNING, message, data)
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log an error message."""
        self.log(LogLevel.ERROR, message, data)
    
    def critical(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a critical message."""
        self.log(LogLevel.CRITICAL, message, data)
    
    def set_level(self, level: LogLevel) -> None:
        """Change the minimum log level."""
        self.level = level


# Global logger instance
_global_logger: Optional[Logger] = None


def get_logger(name: Optional[str] = None) -> Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name. If None, returns global logger.
        
    Returns:
        Logger instance
    """
    global _global_logger
    
    if name is None:
        # Return global logger
        if _global_logger is None:
            _global_logger = Logger("pinpoint")
        return _global_logger
    else:
        # Return named logger
        return Logger(name)


def configure_global_logger(log_file: Optional[Union[str, Path]] = None,
                          level: LogLevel = LogLevel.INFO,
                          console: bool = True) -> Logger:
    """
    Configure the global logger.
    
    Args:
        log_file: Path to log file
        level: Minimum log level
        console: Whether to print to console
        
    Returns:
        Configured global logger
    """
    global _global_logger
    _global_logger = Logger("pinpoint", log_file, level, console)
    return _global_logger