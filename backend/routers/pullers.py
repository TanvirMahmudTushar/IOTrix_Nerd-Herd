from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models.db_models import Ride, Puller, RideStatus, PullerStatus, Location
from models.schemas import RideAlertResponse, PullerProfileResponse
from services.points_service import calculate_points
from utils.gps_utils import haversine_distance
import uuid

router = APIRouter()

@router.get("/{puller_id}/alerts", response_model=list)
def get_alerts(puller_id: str, db: Session = Depends(get_db)):
    puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
    if not puller:
        raise HTTPException(status_code=404, detail="Puller not found")
    
    # Get pending rides, sorted by distance
    pending_rides = db.query(Ride).filter(
        Ride.status == RideStatus.PENDING
    ).all()
    
    pickup_loc = db.query(Location).filter(Location.name == pending_rides[0].pickup if pending_rides else None).first()
    
    alerts = []
    for ride in pending_rides:
        pickup_loc = db.query(Location).filter(Location.name == ride.pickup).first()
        if pickup_loc:
            distance = haversine_distance(
                puller.current_lat, puller.current_lng,
                pickup_loc.lat, pickup_loc.lng
            )
            alerts.append({
                "ride_id": ride.ride_id,
                "user_id": ride.user_id,
                "pickup": ride.pickup,
                "destination": ride.destination,
                "distance_meters": distance
            })
    
    alerts.sort(key=lambda x: x["distance_meters"])
    return alerts

@router.post("/{ride_id}/accept")
def accept_ride(ride_id: str, puller_id: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.status != RideStatus.PENDING:
        raise HTTPException(status_code=400, detail="Ride already assigned")
    
    ride.puller_id = puller_id
    ride.status = RideStatus.PULLER_ASSIGNED
    db.commit()
    
    return {"success": "accepted"}

@router.post("/{ride_id}/pickup")
def confirm_pickup(ride_id: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    ride.status = RideStatus.PICKUP
    db.commit()
    
    return {"success": True}

@router.post("/{ride_id}/complete")
def complete_ride(ride_id: str, dropoff_lat: float, dropoff_lng: float, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    ride.dropoff_lat = dropoff_lat
    ride.dropoff_lng = dropoff_lng
    ride.status = RideStatus.COMPLETED
    ride.completed_at = datetime.utcnow()
    
    # Calculate points
    points = calculate_points(ride, db)
    ride.points_awarded = points
    
    # Update puller points
    puller = db.query(Puller).filter(Puller.puller_id == ride.puller_id).first()
    puller.points += points
    puller.total_rides += 1
    
    db.commit()
    
    return {"success": True, "points_awarded": points}

@router.put("/{puller_id}/location")
def update_location(puller_id: str, lat: float, lng: float, db: Session = Depends(get_db)):
    puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
    if not puller:
        raise HTTPException(status_code=404, detail="Puller not found")
    
    puller.current_lat = lat
    puller.current_lng = lng
    db.commit()
    
    return {"success": True}

@router.get("/{puller_id}/history")
def get_history(puller_id: str, db: Session = Depends(get_db)):
    rides = db.query(Ride).filter(Ride.puller_id == puller_id).all()
    return rides

@router.get("/{puller_id}/profile", response_model=PullerProfileResponse)
def get_profile(puller_id: str, db: Session = Depends(get_db)):
    puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
    if not puller:
        raise HTTPException(status_code=404, detail="Puller not found")
    
    user = db.query(User).filter(User.user_id == puller.user_id).first()
    
    return {
        "puller_id": puller_id,
        "name": user.name if user else "Unknown",
        "points": puller.points,
        "total_rides": puller.total_rides,
        "rating": puller.rating,
        "status": puller.status.value
    }
