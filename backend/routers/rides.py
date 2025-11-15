from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from database import get_db
from models.db_models import Ride, RideStatus, User, Puller, Location
from models.schemas import RideRequest, RideStatusResponse, VerifyUserRequest, VerifyUserResponse
from services.alert_service import distribute_alerts
from utils.gps_utils import haversine_distance

router = APIRouter()

# MVP: User verification endpoint (laser + ultrasonic)
@router.post("/verify", response_model=VerifyUserResponse)
def verify_user(request: VerifyUserRequest, db: Session = Depends(get_db)):
    """
    Verify user via laser frequency and ultrasonic sensor
    Ultrasonic must detect presence for >= 3 seconds
    """
    # Check ultrasonic duration
    if request.ultrasonic_duration < 3.0:
        raise HTTPException(status_code=400, detail="Ultrasonic duration must be >= 3 seconds")
    
    # Check if user exists with this laser frequency
    user = db.query(User).filter(User.laser_frequency == request.laser_frequency).first()
    
    if not user:
        # Create new user with laser frequency
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        user = User(
            user_id=user_id,
            laser_frequency=request.laser_frequency
        )
        db.add(user)
        db.commit()
    
    return {
        "success": True,
        "user_id": user.user_id,
        "message": "User verified successfully"
    }

@router.post("/request", status_code=201)
def request_ride(request: RideRequest, db: Session = Depends(get_db)):
    """Create ride request and broadcast to nearby pullers"""
    ride_id = f"ride_{uuid.uuid4().hex[:8]}"
    
    ride = Ride(
        ride_id=ride_id,
        user_id=request.user_id,
        pickup=request.pickup_location,
        destination=request.destination,
        status=RideStatus.PENDING,
        requested_at=datetime.utcnow()
    )
    db.add(ride)
    db.commit()
    
    # Distribute alerts to nearby pullers
    distribute_alerts(ride_id, request.pickup_location, db)
    
    return {"success": True, "ride_id": ride_id}

@router.get("/{ride_id}/status", response_model=RideStatusResponse)
def get_ride_status(ride_id: str, db: Session = Depends(get_db)):
    """
    Get ride status for LED control (ESP32 polls this every 2-3 seconds)
    Returns LED states: Yellow (puller assigned), Red (timeout), Green (pickup confirmed)
    Also returns distance from puller to pickup location
    """
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    # LED logic based on status
    led_yellow = ride.status == RideStatus.PULLER_ASSIGNED
    led_red = ride.status == RideStatus.TIMEOUT
    led_green = ride.status == RideStatus.PICKUP_CONFIRMED
    
    # Calculate distance from puller to pickup if puller is assigned
    distance_to_pickup = None
    if ride.puller_id:
        puller = db.query(Puller).filter(Puller.puller_id == ride.puller_id).first()
        pickup_location = db.query(Location).filter(Location.name == ride.pickup).first()
        
        if puller and pickup_location and puller.current_lat and puller.current_lng:
            # Calculate straight-line distance in meters
            distance_to_pickup = haversine_distance(
                puller.current_lat,
                puller.current_lng,
                pickup_location.lat,
                pickup_location.lng
            )
    
    return {
        "status": ride.status.value,
        "led_yellow": led_yellow,
        "led_red": led_red,
        "led_green": led_green,
        "puller_id": ride.puller_id,
        "distance_to_pickup": distance_to_pickup
    }

@router.post("/{ride_id}/user-accept")
def user_accept_ride(ride_id: str, db: Session = Depends(get_db)):
    """User accepts the assigned puller (Green button pressed)"""
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.status != RideStatus.PULLER_ASSIGNED:
        raise HTTPException(status_code=400, detail="No puller assigned to accept")
    
    ride.status = RideStatus.PICKUP_CONFIRMED
    ride.pickup_confirmed_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}

@router.post("/{ride_id}/user-reject")
def user_reject_ride(ride_id: str, db: Session = Depends(get_db)):
    """User rejects the assigned puller (Red button pressed) - rebroadcasts to other pullers"""
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.status != RideStatus.PULLER_ASSIGNED:
        raise HTTPException(status_code=400, detail="No puller assigned to reject")
    
    # Reset ride to pending
    ride.status = RideStatus.PENDING
    ride.puller_id = None
    ride.accepted_at = None
    db.commit()
    
    # Re-distribute to remaining pullers
    distribute_alerts(ride_id, ride.pickup, db)
    
    return {"success": True}
