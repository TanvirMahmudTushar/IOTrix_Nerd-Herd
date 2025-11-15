from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    PULLER = "puller"
    USER = "user"

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str
    role: UserRole

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str
    puller_id: Optional[str] = None  # For puller accounts

# MVP: Laser frequency verification
class VerifyUserRequest(BaseModel):
    laser_frequency: float
    ultrasonic_duration: float  # seconds
    location_block: str

class VerifyUserResponse(BaseModel):
    success: bool
    user_id: str
    message: Optional[str] = None

class RideRequest(BaseModel):
    user_id: str
    pickup_location: str
    destination: str

class RideStatusResponse(BaseModel):
    status: str
    led_yellow: bool
    led_red: bool
    led_green: bool
    puller_id: Optional[str] = None
    distance_to_pickup: Optional[float] = None  # Distance from puller to pickup in meters

class RideAcceptRejectRequest(BaseModel):
    action: str  # "accept" or "reject"

class LocationResponse(BaseModel):
    name: str
    lat: float
    lng: float

class PullerProfileResponse(BaseModel):
    puller_id: str
    name: str
    points: int
    total_rides: int
    rating: float
    status: str

class RideAlertResponse(BaseModel):
    ride_id: str
    pickup: str
    destination: str
    distance_to_pickup: float  # meters
    potential_points: int
    expires_in: int  # seconds
    requested_at: str

class ActiveRideResponse(BaseModel):
    ride_id: str
    status: str
    pickup: str
    destination: str
    pickup_coords: dict
    destination_coords: dict
    distance_to_destination: float

class RideCompleteRequest(BaseModel):
    puller_id: str
    dropoff_lat: float
    dropoff_lng: float

class RideCompleteResponse(BaseModel):
    success: bool
    points_awarded: int
    dropoff_accuracy: float
    ride_summary: dict

class PendingReviewRide(BaseModel):
    ride_id: str
    puller_name: str
    destination: str
    distance_error: float
    calculated_points: int

class ResolveReviewRequest(BaseModel):
    action: str  # "approve" or "adjust"
    points_override: Optional[int] = None
