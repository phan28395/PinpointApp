# data/__init__.py
"""Data storage module for PinPoint."""

from .base_store import BaseStore
from .json_store import JSONStore

__all__ = ['BaseStore', 'JSONStore']