"""
Database Models Package
Imports all models to ensure they're registered with SQLAlchemy
"""

from .buoy import Buoy
from .reading import Reading
from .alert import Alert, AlertType, AlertSeverity, AlertStatus
from .user import User

# Export all models for easy importing
__all__ = [
    "Buoy",
    "Reading", 
    "Alert",
    "AlertType",
    "AlertSeverity", 
    "AlertStatus",
    "User"
]