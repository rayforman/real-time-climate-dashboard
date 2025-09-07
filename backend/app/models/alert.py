"""
Alert Database Model
Represents weather alerts and warnings generated from sensor data
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, ForeignKey, Index, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import enum

from ..database import Base

class AlertType(enum.Enum):
    """Alert type enumeration"""
    HIGH_WAVES = "HIGH_WAVES"
    EXTREME_WAVES = "EXTREME_WAVES"
    HIGH_WIND = "HIGH_WIND"
    EXTREME_WIND = "EXTREME_WIND"
    LOW_PRESSURE = "LOW_PRESSURE"
    STORM_WARNING = "STORM_WARNING"
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    DATA_ANOMALY = "DATA_ANOMALY"

class AlertSeverity(enum.Enum):
    """Alert severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertStatus(enum.Enum):
    """Alert status"""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"

class Alert(Base):
    """
    Weather Alert Model
    
    Represents automated alerts generated from sensor readings when
    dangerous or unusual conditions are detected. Similar to trading
    alerts in financial systems that trigger on price movements or
    risk thresholds.
    """
    __tablename__ = "alerts"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier for this alert"
    )
    
    # Foreign key to buoy station
    buoy_id = Column(
        String(10),
        ForeignKey("buoys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="NOAA station ID this alert relates to"
    )
    
    # Alert classification
    alert_type = Column(
        Enum(AlertType),
        nullable=False,
        comment="Type of alert condition detected"
    )
    
    severity = Column(
        Enum(AlertSeverity),
        nullable=False,
        comment="Severity level of the alert"
    )
    
    status = Column(
        Enum(AlertStatus),
        default=AlertStatus.ACTIVE,
        nullable=False,
        comment="Current status of the alert"
    )
    
    # Alert content
    title = Column(
        String(255),
        nullable=False,
        comment="Brief alert title/summary"
    )
    
    description = Column(
        Text,
        nullable=False,
        comment="Detailed alert description"
    )
    
    # Threshold information
    threshold_value = Column(
        Float,
        nullable=True,
        comment="Threshold value that triggered this alert"
    )
    
    measured_value = Column(
        Float,
        nullable=True,
        comment="Actual measured value that exceeded threshold"
    )
    
    measurement_unit = Column(
        String(20),
        nullable=True,
        comment="Unit of measurement (m, mph, mb, etc.)"
    )
    
    # Temporal information
    detected_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="When the alert condition was first detected"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this alert automatically expires"
    )
    
    acknowledged_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this alert was acknowledged by a user"
    )
    
    resolved_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the alert condition was resolved"
    )
    
    # Geographic context
    latitude = Column(
        Float,
        nullable=True,
        comment="Latitude where alert condition exists"
    )
    
    longitude = Column(
        Float,
        nullable=True,
        comment="Longitude where alert condition exists"
    )
    
    # Impact radius (for area-based alerts)
    impact_radius_km = Column(
        Float,
        nullable=True,
        comment="Radius of impact area in kilometers"
    )
    
    # User interaction
    acknowledged_by = Column(
        String(255),
        nullable=True,
        comment="User ID who acknowledged this alert"
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment="User notes about this alert"
    )
    
    # Alert delivery tracking
    notification_sent = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether notification was sent for this alert"
    )
    
    notification_channels = Column(
        String(255),
        nullable=True,
        comment="Comma-separated list of notification channels used"
    )
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="When this alert record was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When this alert record was last updated"
    )
    
    # Source reading that triggered this alert
    trigger_reading_id = Column(
        UUID(as_uuid=True),
        ForeignKey("readings.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reading that triggered this alert"
    )
    
    # Additional context data
    context_data = Column(
        String,  # JSON stored as string for PostgreSQL compatibility
        nullable=True,
        comment="Additional context about alert conditions"
    )
    
    # Relationships
    buoy = relationship("Buoy", back_populates="alerts")
    trigger_reading = relationship("Reading", foreign_keys=[trigger_reading_id])
    
    # Performance indexes
    __table_args__ = (
        # Active alerts for a buoy
        Index('idx_alert_buoy_status', 'buoy_id', 'status'),
        
        # Alert type queries
        Index('idx_alert_type_severity', 'alert_type', 'severity'),
        
        # Time-based queries
        Index('idx_alert_detected_at', 'detected_at'),
        
        # Active alerts dashboard
        Index('idx_alert_active', 'status', 'detected_at'),
        
        # Geographic queries
        Index('idx_alert_location', 'latitude', 'longitude'),
        
        # Severity-based queries
        Index('idx_alert_severity_time', 'severity', 'detected_at'),
        
        # Notification tracking
        Index('idx_alert_notification', 'notification_sent'),
    )
    
    def __repr__(self) -> str:
        return f"<Alert(id='{self.id}', type='{self.alert_type}', severity='{self.severity}', buoy='{self.buoy_id}')>"
    
    def __str__(self) -> str:
        return f"{self.alert_type.value} alert for {self.buoy_id}: {self.title}"
    
    @property
    def is_active(self) -> bool:
        """Check if alert is currently active"""
        return self.status == AlertStatus.ACTIVE
    
    @property
    def is_expired(self) -> bool:
        """Check if alert has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow().replace(tzinfo=self.expires_at.tzinfo) > self.expires_at
    
    @property
    def age_minutes(self) -> float:
        """Get age of alert in minutes"""
        if not self.detected_at:
            return 0
        
        delta = datetime.utcnow().replace(tzinfo=self.detected_at.tzinfo) - self.detected_at
        return delta.total_seconds() / 60
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Get duration of alert in minutes (if resolved)"""
        if not self.resolved_at or not self.detected_at:
            return None
        
        delta = self.resolved_at - self.detected_at
        return delta.total_seconds() / 60
    
    @property
    def severity_color(self) -> str:
        """Get color code for alert severity"""
        colors = {
            AlertSeverity.LOW: "#FFC107",      # Yellow
            AlertSeverity.MEDIUM: "#FF9800",  # Orange  
            AlertSeverity.HIGH: "#F44336",    # Red
            AlertSeverity.CRITICAL: "#9C27B0" # Purple
        }
        return colors.get(self.severity, "#757575")
    
    @property
    def priority_score(self) -> int:
        """Calculate priority score for sorting alerts"""
        base_scores = {
            AlertSeverity.LOW: 10,
            AlertSeverity.MEDIUM: 20,
            AlertSeverity.HIGH: 30,
            AlertSeverity.CRITICAL: 40
        }
        
        score = base_scores.get(self.severity, 0)
        
        # Boost score for recent alerts
        if self.age_minutes < 60:
            score += 10
        
        # Boost score for active alerts
        if self.is_active:
            score += 5
            
        return score
    
    def acknowledge(self, user_id: str, notes: Optional[str] = None):
        """Acknowledge this alert"""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = user_id
        if notes:
            self.notes = notes
    
    def resolve(self, notes: Optional[str] = None):
        """Mark alert as resolved"""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        if notes:
            self.notes = notes if not self.notes else f"{self.notes}\n{notes}"
    
    def cancel(self, reason: Optional[str] = None):
        """Cancel this alert"""
        self.status = AlertStatus.CANCELLED
        self.resolved_at = datetime.utcnow()
        if reason:
            self.notes = reason if not self.notes else f"{self.notes}\nCancelled: {reason}"
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert alert to dictionary for API responses"""
        data = {
            "id": str(self.id),
            "buoy_id": self.buoy_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "threshold_value": self.threshold_value,
            "measured_value": self.measured_value,
            "measurement_unit": self.measurement_unit,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "impact_radius_km": self.impact_radius_km,
            "acknowledged_by": self.acknowledged_by,
            "notes": self.notes,
            "notification_sent": self.notification_sent,
            "age_minutes": self.age_minutes,
            "duration_minutes": self.duration_minutes,
            "severity_color": self.severity_color,
            "priority_score": self.priority_score,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
        }
        
        if include_relationships and self.buoy:
            data["buoy_name"] = self.buoy.name
            data["buoy_location"] = {
                "latitude": self.buoy.latitude,
                "longitude": self.buoy.longitude
            }
        
        return data
    
    @classmethod
    def create_from_reading(
        cls, 
        reading, 
        alert_type: AlertType, 
        severity: AlertSeverity,
        threshold_value: float,
        measured_value: float,
        measurement_unit: str
    ) -> "Alert":
        """
        Factory method to create alert from a sensor reading
        """
        # Generate appropriate title and description
        titles = {
            AlertType.HIGH_WAVES: f"High Wave Alert",
            AlertType.EXTREME_WAVES: f"Extreme Wave Warning",
            AlertType.HIGH_WIND: f"High Wind Alert", 
            AlertType.EXTREME_WIND: f"Extreme Wind Warning",
            AlertType.LOW_PRESSURE: f"Low Pressure Alert",
            AlertType.STORM_WARNING: f"Storm Warning",
        }
        
        descriptions = {
            AlertType.HIGH_WAVES: f"Wave height of {measured_value:.1f}m exceeds threshold of {threshold_value:.1f}m",
            AlertType.EXTREME_WAVES: f"Extreme wave conditions: {measured_value:.1f}m waves detected",
            AlertType.HIGH_WIND: f"Wind speed of {measured_value:.1f} {measurement_unit} exceeds threshold",
            AlertType.EXTREME_WIND: f"Extreme wind conditions: {measured_value:.1f} {measurement_unit}",
            AlertType.LOW_PRESSURE: f"Atmospheric pressure of {measured_value:.1f}mb below normal",
            AlertType.STORM_WARNING: f"Storm conditions detected with multiple threshold exceedances",
        }
        
        return cls(
            buoy_id=reading.buoy_id,
            alert_type=alert_type,
            severity=severity,
            title=titles.get(alert_type, f"{alert_type.value} Alert"),
            description=descriptions.get(alert_type, f"Alert condition detected"),
            threshold_value=threshold_value,
            measured_value=measured_value,
            measurement_unit=measurement_unit,
            detected_at=reading.timestamp,
            latitude=reading.buoy.latitude if reading.buoy else None,
            longitude=reading.buoy.longitude if reading.buoy else None,
            trigger_reading_id=reading.id,
        )