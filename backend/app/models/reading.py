"""
Sensor Reading Database Model
Time-series data from NOAA buoy sensors - the core data of our system
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from ..database import Base

class Reading(Base):
    """
    Sensor Reading Model
    
    Represents a single time-stamped measurement from a buoy station.
    This is our core time-series data - equivalent to price/trade data
    in financial systems.
    
    Optimized for:
    - High-frequency inserts (6-minute intervals from all buoys)
    - Fast time-range queries (dashboard charts)
    - Aggregation queries (trend analysis)
    - Real-time access (latest readings)
    """
    __tablename__ = "readings"
    
    # Primary key - UUID for global uniqueness and performance
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for this reading"
    )
    
    # Foreign key to buoy station
    buoy_id = Column(
        String(10),
        ForeignKey("buoys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="NOAA station ID this reading belongs to"
    )
    
    # Timestamp - critical for time-series queries
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When this measurement was taken (UTC)"
    )
    
    # === WAVE DATA ===
    # Significant wave height (most important for safety)
    wave_height = Column(
        Float,
        nullable=True,
        comment="Significant wave height in meters"
    )
    
    # Dominant wave period
    wave_period = Column(
        Float,
        nullable=True,
        comment="Dominant wave period in seconds"
    )
    
    # Wave direction
    wave_direction = Column(
        Float,
        nullable=True,
        comment="Wave direction in degrees (0-360)"
    )
    
    # === WIND DATA ===
    # Wind speed (critical for weather alerts)
    wind_speed = Column(
        Float,
        nullable=True,
        comment="Wind speed in meters per second"
    )
    
    # Wind direction
    wind_direction = Column(
        Float,
        nullable=True,
        comment="Wind direction in degrees (0-360)"
    )
    
    # Wind gust speed
    wind_gust = Column(
        Float,
        nullable=True,
        comment="Wind gust speed in meters per second"
    )
    
    # === ATMOSPHERIC DATA ===
    # Atmospheric pressure (predictor of weather changes)
    atmospheric_pressure = Column(
        Float,
        nullable=True,
        comment="Atmospheric pressure in millibars"
    )
    
    # Air temperature
    air_temperature = Column(
        Float,
        nullable=True,
        comment="Air temperature in degrees Celsius"
    )
    
    # Water temperature
    water_temperature = Column(
        Float,
        nullable=True,
        comment="Water temperature in degrees Celsius"
    )
    
    # Visibility
    visibility = Column(
        Float,
        nullable=True,
        comment="Visibility in nautical miles"
    )
    
    # === ADDITIONAL MEASUREMENTS ===
    # Humidity
    humidity = Column(
        Float,
        nullable=True,
        comment="Relative humidity as percentage"
    )
    
    # Dew point
    dew_point = Column(
        Float,
        nullable=True,
        comment="Dew point temperature in degrees Celsius"
    )
    
    # Sea level pressure
    sea_level_pressure = Column(
        Float,
        nullable=True,
        comment="Sea level pressure in millibars"
    )
    
    # === DATA QUALITY METADATA ===
    # Data quality flags for each measurement
    quality_flags = Column(
        JSON,
        nullable=True,
        comment="Quality control flags for each measurement"
    )
    
    # Overall data quality score
    quality_score = Column(
        Float,
        default=1.0,
        nullable=True,
        comment="Overall quality score from 0.0 to 1.0"
    )
    
    # Whether this reading passed validation
    is_valid = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether reading passed data validation"
    )
    
    # Source information
    source = Column(
        String(50),
        default="NOAA_REALTIME",
        nullable=True,
        comment="Data source identifier"
    )
    
    # === PROCESSING METADATA ===
    # When this record was created in our system
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this record was inserted"
    )
    
    # Processing timestamp
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this reading was processed/validated"
    )
    
    # Raw data from NOAA (for debugging and reprocessing)
    raw_data = Column(
        JSON,
        nullable=True,
        comment="Original raw data from NOAA API"
    )
    
    # Calculated/derived fields
    derived_data = Column(
        JSON,
        nullable=True,
        comment="Calculated fields like trends, anomalies, etc."
    )
    
    # Relationships
    buoy = relationship("Buoy", back_populates="readings")
    
    # Performance indexes
    __table_args__ = (
        # Most common query: latest readings for a buoy
        Index('idx_reading_buoy_timestamp', 'buoy_id', 'timestamp'),
        
        # Time-range queries for charts
        Index('idx_reading_timestamp', 'timestamp'),
        
        # Quality filtering
        Index('idx_reading_valid', 'is_valid'),
        
        # Composite index for dashboard queries
        Index('idx_reading_buoy_valid_time', 'buoy_id', 'is_valid', 'timestamp'),
        
        # Wave height queries for alerts
        Index('idx_reading_wave_height', 'wave_height'),
        
        # Wind speed queries for alerts  
        Index('idx_reading_wind_speed', 'wind_speed'),
        
        # Source tracking
        Index('idx_reading_source', 'source'),
    )
    
    def __repr__(self) -> str:
        return f"<Reading(buoy_id='{self.buoy_id}', timestamp='{self.timestamp}', waves={self.wave_height}m)>"
    
    def __str__(self) -> str:
        return f"Reading from {self.buoy_id} at {self.timestamp}"
    
    @property
    def age_minutes(self) -> float:
        """Get age of this reading in minutes"""
        if not self.timestamp:
            return float('inf')
        
        delta = datetime.utcnow().replace(tzinfo=self.timestamp.tzinfo) - self.timestamp
        return delta.total_seconds() / 60
    
    @property
    def is_recent(self) -> bool:
        """Check if reading is from last hour"""
        return self.age_minutes <= 60
    
    @property
    def conditions_summary(self) -> str:
        """Generate human-readable conditions summary"""
        parts = []
        
        if self.wave_height is not None:
            parts.append(f"Waves: {self.wave_height:.1f}m")
        
        if self.wind_speed is not None:
            # Convert m/s to mph for readability
            wind_mph = self.wind_speed * 2.237
            parts.append(f"Wind: {wind_mph:.0f} mph")
        
        if self.water_temperature is not None:
            # Convert Celsius to Fahrenheit
            temp_f = (self.water_temperature * 9/5) + 32
            parts.append(f"Water: {temp_f:.0f}°F")
        
        return ", ".join(parts) if parts else "No data"
    
    def to_dict(self, include_metadata: bool = False) -> Dict[str, Any]:
        """Convert reading to dictionary for API responses"""
        data = {
            "buoy_id": self.buoy_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "wave_height": self.wave_height,
            "wave_period": self.wave_period,
            "wave_direction": self.wave_direction,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "wind_gust": self.wind_gust,
            "atmospheric_pressure": self.atmospheric_pressure,
            "air_temperature": self.air_temperature,
            "water_temperature": self.water_temperature,
            "visibility": self.visibility,
            "conditions_summary": self.conditions_summary,
        }
        
        if include_metadata:
            data.update({
                "id": str(self.id),
                "quality_score": self.quality_score,
                "is_valid": self.is_valid,
                "source": self.source,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "age_minutes": self.age_minutes,
            })
        
        return data
    
    def check_alert_conditions(self) -> list[str]:
        """Check if this reading triggers any alert conditions"""
        alerts = []
        
        # High wave alert
        if self.wave_height and self.wave_height > 4.0:
            alerts.append("HIGH_WAVES")
        
        # High wind alert  
        if self.wind_speed and self.wind_speed > 12.5:  # ~28 mph
            alerts.append("HIGH_WIND")
        
        # Low pressure alert (storm indicator)
        if self.atmospheric_pressure and self.atmospheric_pressure < 1000:
            alerts.append("LOW_PRESSURE")
        
        # Extreme conditions
        if self.wave_height and self.wave_height > 8.0:
            alerts.append("EXTREME_WAVES")
        
        if self.wind_speed and self.wind_speed > 25.0:  # ~56 mph
            alerts.append("EXTREME_WIND")
        
        return alerts
    
    @classmethod
    def create_from_noaa_data(cls, buoy_id: str, timestamp: datetime, raw_data: dict) -> "Reading":
        """
        Factory method to create Reading from NOAA data
        Handles the parsing and validation of NOAA's data format
        """
        return cls(
            buoy_id=buoy_id,
            timestamp=timestamp,
            wave_height=raw_data.get('WVHT'),  # Wave height
            wave_period=raw_data.get('DPD'),   # Dominant wave period
            wave_direction=raw_data.get('MWD'), # Wave direction
            wind_speed=raw_data.get('WSPD'),   # Wind speed
            wind_direction=raw_data.get('WDIR'), # Wind direction
            wind_gust=raw_data.get('GST'),     # Wind gust
            atmospheric_pressure=raw_data.get('PRES'), # Pressure
            air_temperature=raw_data.get('ATMP'),      # Air temp
            water_temperature=raw_data.get('WTMP'),    # Water temp
            visibility=raw_data.get('VIS'),            # Visibility
            raw_data=raw_data,
            source="NOAA_REALTIME"
        )