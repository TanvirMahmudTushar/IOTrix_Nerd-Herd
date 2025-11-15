from sqlalchemy import Column, String, Float, Integer, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PULLER = "puller"
    USER = "user"  # For physical block users (senior citizens)

class RideStatus(str, enum.Enum):
    PENDING = "pending"
    PULLER_ASSIGNED = "puller_assigned"
    PICKUP_CONFIRMED = "pickup_confirmed"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    PENDING_REVIEW = "pending_review"

class PullerStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    laser_frequency = Column(Float, unique=True, nullable=True)  # For physical block users
    email = Column(String, unique=True, index=True, nullable=True)  # For puller/admin accounts
    hashed_password = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)  # Default to USER for physical block users
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rides = relationship("Ride", back_populates="user")

class Puller(Base):
    __tablename__ = "pullers"
    
    puller_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True, nullable=True)
    name = Column(String)
    phone = Column(String)
    current_lat = Column(Float, default=0.0)
    current_lng = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    status = Column(Enum(PullerStatus), default=PullerStatus.OFFLINE)
    total_rides = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    rides = relationship("Ride", back_populates="puller")

class Location(Base):
    __tablename__ = "locations"
    
    name = Column(String, primary_key=True, index=True)
    lat = Column(Float)
    lng = Column(Float)

class Ride(Base):
    __tablename__ = "rides"
    
    ride_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    puller_id = Column(String, ForeignKey("pullers.puller_id"), nullable=True)
    pickup = Column(String)  # Location name
    destination = Column(String)  # Location name
    status = Column(Enum(RideStatus), default=RideStatus.PENDING)
    requested_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    pickup_confirmed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lng = Column(Float, nullable=True)
    dropoff_distance_error = Column(Float, nullable=True)  # Distance from destination in meters
    points_awarded = Column(Integer, default=0)
    
    user = relationship("User", back_populates="rides")
    puller = relationship("Puller", back_populates="rides")

class PointsHistory(Base):
    __tablename__ = "points_history"
    
    transaction_id = Column(String, primary_key=True, index=True)
    puller_id = Column(String, ForeignKey("pullers.puller_id"))
    ride_id = Column(String, ForeignKey("rides.ride_id"), nullable=True)
    points_change = Column(Integer)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    puller = relationship("Puller")
    ride = relationship("Ride")
