"""
User Database Model
Represents users who can access the climate dashboard and configure alerts
"""

from sqlalchemy import Column, String, Boolean, DateTime, Float, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import hashlib

from ..database import Base

class User(Base):
    """
    User Model
    
    Represents users of the climate dashboard system. Users can:
    - View buoy data and dashboards
    - Configure personalized alerts
    - Save favorite locations
    - Access historical data
    
    This demonstrates user management patterns common in enterprise systems.
    """
    __tablename__ = "users"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for this user"
    )
    
    # Authentication
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address (used for login)"
    )
    
    username = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        comment="Optional username"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Hashed password (never store plaintext)"
    )
    
    # Profile information
    first_name = Column(
        String(100),
        nullable=True,
        comment="User's first name"
    )
    
    last_name = Column(
        String(100),
        nullable=True,
        comment="User's last name"
    )
    
    # Account status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether user account is active"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user's email is verified"
    )
    
    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user has admin privileges"
    )
    
    # Location preferences (for finding nearby buoys)
    default_latitude = Column(
        Float,
        nullable=True,
        comment="User's default latitude for location-based features"
    )
    
    default_longitude = Column(
        Float,
        nullable=True,
        comment="User's default longitude for location-based features"
    )
    
    location_name = Column(
        String(255),
        nullable=True,
        comment="Human-readable name for default location"
    )
    
    # Alert preferences
    alert_preferences = Column(
        JSON,
        nullable=True,
        comment="User's alert configuration and notification preferences"
    )
    
    # Saved locations and favorite buoys
    favorite_buoys = Column(
        JSON,
        nullable=True,
        comment="List of user's favorite buoy IDs"
    )
    
    saved_locations = Column(
        JSON,
        nullable=True,
        comment="User's saved locations with custom names"
    )
    
    # Dashboard customization
    dashboard_config = Column(
        JSON,
        nullable=True,
        comment="User's dashboard layout and widget preferences"
    )
    
    # Usage tracking
    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When user last logged in"
    )
    
    login_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of logins"
    )
    
    # Contact preferences
    phone_number = Column(
        String(20),
        nullable=True,
        comment="User's phone number for SMS alerts"
    )
    
    timezone = Column(
        String(50),
        default="UTC",
        nullable=False,
        comment="User's preferred timezone"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When user account was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When user account was last updated"
    )
    
    # Email verification
    verification_token = Column(
        String(255),
        nullable=True,
        comment="Token for email verification"
    )
    
    verification_sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When verification email was sent"
    )
    
    # Password reset
    reset_token = Column(
        String(255),
        nullable=True,
        comment="Token for password reset"
    )
    
    reset_token_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When password reset token expires"
    )
    
    # Performance indexes
    __table_args__ = (
        # Login queries
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        
        # Active user queries
        Index('idx_user_active', 'is_active'),
        
        # Admin queries
        Index('idx_user_admin', 'is_admin'),
        
        # Location-based queries
        Index('idx_user_location', 'default_latitude', 'default_longitude'),
        
        # Verification status
        Index('idx_user_verified', 'is_verified'),
    )
    
    def __repr__(self) -> str:
        return f"<User(id='{self.id}', email='{self.email}')>"
    
    def __str__(self) -> str:
        return self.email
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]  # Fallback to email username
    
    @property
    def display_name(self) -> str:
        """Get name suitable for display in UI"""
        return self.username or self.full_name
    
    @property
    def has_location(self) -> bool:
        """Check if user has set a default location"""
        return self.default_latitude is not None and self.default_longitude is not None
    
    @property
    def coordinate_tuple(self) -> Optional[tuple[float, float]]:
        """Get user's coordinates as tuple"""
        if self.has_location:
            return (self.default_latitude, self.default_longitude)
        return None
    
    def get_favorite_buoy_ids(self) -> List[str]:
        """Get list of user's favorite buoy IDs"""
        if not self.favorite_buoys:
            return []
        
        if isinstance(self.favorite_buoys, list):
            return self.favorite_buoys
        else:
            return []
    
    def add_favorite_buoy(self, buoy_id: str):
        """Add a buoy to user's favorites"""
        favorites = self.get_favorite_buoy_ids()
        if buoy_id not in favorites:
            favorites.append(buoy_id)
            self.favorite_buoys = favorites
    
    def remove_favorite_buoy(self, buoy_id: str):
        """Remove a buoy from user's favorites"""
        favorites = self.get_favorite_buoy_ids()
        if buoy_id in favorites:
            favorites.remove(buoy_id)
            self.favorite_buoys = favorites
    
    def get_alert_preferences(self) -> Dict[str, Any]:
        """Get user's alert preferences with defaults"""
        defaults = {
            "email_alerts": True,
            "sms_alerts": False,
            "wave_height_threshold": 4.0,
            "wind_speed_threshold": 25.0,
            "pressure_threshold": 1000.0,
            "alert_radius_km": 50.0,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "06:00",
        }
        
        if not self.alert_preferences:
            return defaults
        
        # Merge user preferences with defaults
        preferences = defaults.copy()
        preferences.update(self.alert_preferences)
        return preferences
    
    def update_alert_preferences(self, new_preferences: Dict[str, Any]):
        """Update user's alert preferences"""
        current = self.get_alert_preferences()
        current.update(new_preferences)
        self.alert_preferences = current
    
    def set_location(self, latitude: float, longitude: float, name: Optional[str] = None):
        """Set user's default location"""
        self.default_latitude = latitude
        self.default_longitude = longitude
        if name:
            self.location_name = name
    
    def verify_email(self):
        """Mark user's email as verified"""
        self.is_verified = True
        self.verification_token = None
        self.verification_sent_at = None
    
    def record_login(self):
        """Record a user login"""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1
    
    def can_receive_alerts(self) -> bool:
        """Check if user can receive alerts"""
        return self.is_active and self.is_verified
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary for API responses"""
        data = {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_admin": self.is_admin,
            "default_latitude": self.default_latitude,
            "default_longitude": self.default_longitude,
            "location_name": self.location_name,
            "has_location": self.has_location,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "login_count": self.login_count,
            "favorite_buoys": self.get_favorite_buoy_ids(),
        }
        
        if include_sensitive:
            data.update({
                "phone_number": self.phone_number,
                "alert_preferences": self.get_alert_preferences(),
                "dashboard_config": self.dashboard_config,
                "saved_locations": self.saved_locations,
            })
        
        return data
    
    @classmethod
    def create_user(
        cls,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        username: Optional[str] = None
    ) -> "User":
        """Factory method to create a new user"""
        return cls(
            email=email.lower().strip(),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            username=username,
        )