from sqlalchemy import Column, String, Float, Integer, Enum, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PULLER = "puller"

class RideStatus(str, enum.Enum):
    PENDING = "pending"
    PULLER_ASSIGNED = "puller_assigned"
    CONFIRMED = "confirmed"
    PICKUP = "pickup"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"

class PullerStatus(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.PULLER)
    name = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rides = relationship("Ride", back_populates="user")

class Puller(Base):
    __tablename__ = "pullers"
    
    puller_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), unique=True)
    current_lat = Column(Float, default=0.0)
    current_lng = Column(Float, default=0.0)
    points = Column(Integer, default=0)
    status = Column(Enum(PullerStatus), default=PullerStatus.OFFLINE)
    total_rides = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
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
    dropoff_lat = Column(Float, nullable=True)
    dropoff_lng = Column(Float, nullable=True)
    points_awarded = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="rides")
    puller = relationship("Puller", back_populates="rides")
