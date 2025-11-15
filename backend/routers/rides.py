from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from database import get_db
from models.db_models import Ride, RideStatus, User
from models.schemas import RideRequest, RideStatusResponse
from services.alert_service import distribute_alerts

router = APIRouter()

@router.post("/request")
def request_ride(request: RideRequest, db: Session = Depends(get_db)):
    ride_id = f"ride_{uuid.uuid4().hex[:8]}"
    
    ride = Ride(
        ride_id=ride_id,
        user_id=request.user_id,
        pickup=request.user_location,
        destination=request.destination,
        status=RideStatus.PENDING
    )
    db.add(ride)
    db.commit()
    
    # Distribute alerts to nearby pullers
    distribute_alerts(ride_id, request.user_location, db)
    
    return {"success": True, "ride_id": ride_id}

@router.get("/{ride_id}/status", response_model=RideStatusResponse)
def get_ride_status(ride_id: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    return {
        "ride_id": ride_id,
        "status": ride.status.value,
        "price": 30,  # Fixed for now
        "puller_id": ride.puller_id
    }

@router.post("/{ride_id}/user-accept")
def user_accept_ride(ride_id: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    ride.status = RideStatus.CONFIRMED
    db.commit()
    
    return {"success": "accept"}

@router.post("/{ride_id}/user-reject")
def user_reject_ride(ride_id: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    ride.status = RideStatus.PENDING
    ride.puller_id = None
    db.commit()
    
    # Re-distribute to next puller
    distribute_alerts(ride_id, ride.pickup, db)
    
    return {"success": "reject"}
