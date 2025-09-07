"""
Buoy Station Database Model
Represents NOAA buoy monitoring stations with location and metadata
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import List, Optional
import uuid

from ..database import Base

class Buoy(Base):
    """
    NOAA Buoy Station Model
    
    Represents a physical buoy monitoring station with its location,
    operational status, and sensor capabilities. This is the foundation
    for organizing all sensor readings and alerts.
    
    Equivalent to a "security" or "ticker" in financial systems - the
    core entity around which all time-series data is organized.
    """
    __tablename__ = "buoys"
    
    # Primary identification
    id = Column(
        String(10), 
        primary_key=True,
        comment="NOAA station ID (e.g., '44025')"
    )
    
    # Basic information
    name = Column(
        String(255), 
        nullable=False,
        comment="Human-readable station name"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of station location and purpose"
    )
    
    # Geographic location (critical for spatial queries)
    latitude = Column(
        Float,
        nullable=False,
        comment="Station latitude in decimal degrees"
    )
    
    longitude = Column(
        Float,
        nullable=False,
        comment="Station longitude in decimal degrees"
    )
    
    # Water depth at station location
    water_depth_meters = Column(
        Float,
        nullable=True,
        comment="Water depth at station location in meters"
    )
    
    # Operational status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether station is currently operational"
    )
    
    status = Column(
        String(50),
        default="active",
        nullable=False,
        comment="Operational status: active, maintenance, discontinued"
    )
    
    # Station type and capabilities
    station_type = Column(
        String(50),
        nullable=True,
        comment="Type of station: buoy, fixed_platform, ship, etc."
    )
    
    # Sensor capabilities (JSON for flexibility)
    sensor_types = Column(
        JSON,
        nullable=True,
        comment="List of available sensors and their specifications"
    )
    
    # Data quality and reliability metrics
    data_quality_score = Column(
        Float,
        default=1.0,
        nullable=True,
        comment="Data quality score from 0.0 to 1.0"
    )
    
    last_maintenance = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last maintenance date"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )
    
    # Data availability tracking
    first_reading_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of first available reading"
    )
    
    last_reading_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of most recent reading"
    )
    
    # Administrative metadata
    owner_organization = Column(
        String(255),
        default="NOAA",
        nullable=True,
        comment="Organization that owns/operates the station"
    )
    
    contact_info = Column(
        JSON,
        nullable=True,
        comment="Contact information for station operators"
    )
    
    # Relationships
    readings = relationship(
        "Reading",
        back_populates="buoy",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Reading.timestamp.desc()"
    )
    
    alerts = relationship(
        "Alert",
        back_populates="buoy",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # Database indexes for performance
    __table_args__ = (
        # Geographic queries (finding nearby buoys)
        Index('idx_buoy_location', 'latitude', 'longitude'),
        
        # Status queries
        Index('idx_buoy_active_status', 'is_active', 'status'),
        
        # Data availability queries
        Index('idx_buoy_last_reading', 'last_reading_at'),
        
        # Composite index for active buoys with recent data
        Index('idx_buoy_active_recent', 'is_active', 'last_reading_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Buoy(id='{self.id}', name='{self.name}', lat={self.latitude}, lon={self.longitude})>"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.id})"
    
    @property
    def coordinate_tuple(self) -> tuple[float, float]:
        """Return coordinates as (latitude, longitude) tuple"""
        return (self.latitude, self.longitude)
    
    @property
    def is_reporting(self) -> bool:
        """Check if station has recent data (within last 24 hours)"""
        if not self.last_reading_at:
            return False
        
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        return self.last_reading_at > cutoff
    
    def distance_to(self, lat: float, lon: float) -> float:
        """
        Calculate distance to given coordinates in kilometers
        Uses Haversine formula for accuracy
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [self.latitude, self.longitude, lat, lon])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    def update_last_reading_timestamp(self, timestamp: DateTime):
        """Update the last reading timestamp"""
        self.last_reading_at = timestamp
        if not self.first_reading_at:
            self.first_reading_at = timestamp
    
    def get_sensor_capabilities(self) -> List[str]:
        """Get list of available sensor types"""
        if not self.sensor_types:
            return []
        
        if isinstance(self.sensor_types, list):
            return self.sensor_types
        elif isinstance(self.sensor_types, dict):
            return list(self.sensor_types.keys())
        else:
            return []
    
    def has_sensor(self, sensor_type: str) -> bool:
        """Check if station has specific sensor type"""
        return sensor_type in self.get_sensor_capabilities()
    
    @classmethod
    def create_from_noaa_data(cls, station_id: str, metadata: dict) -> "Buoy":
        """
        Factory method to create Buoy from NOAA station metadata
        Handles the mapping from NOAA data format to our model
        """
        return cls(
            id=station_id,
            name=metadata.get('name', f'Station {station_id}'),
            description=metadata.get('description'),
            latitude=float(metadata.get('lat', 0.0)),
            longitude=float(metadata.get('lon', 0.0)),
            water_depth_meters=metadata.get('depth'),
            station_type=metadata.get('type', 'buoy'),
            sensor_types=metadata.get('sensors', []),
            owner_organization=metadata.get('owner', 'NOAA'),
        )