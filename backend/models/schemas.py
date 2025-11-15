from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    PULLER = "puller"

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

class RideRequest(BaseModel):
    user_id: str
    user_location: str
    destination: str

class RideStatusResponse(BaseModel):
    ride_id: str
    status: str
    price: int
    puller_id: Optional[str] = None

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
    user_id: str
    pickup: str
    destination: str
    distance_meters: float
