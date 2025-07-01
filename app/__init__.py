# app/__init__.py
"""
PinPoint application module.
Main application integration layer.
"""

from .application import PinPointApplication, get_app

__all__ = [
    'PinPointApplication',
    'get_app'
]