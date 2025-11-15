from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import Ride, RideStatus

router = APIRouter()

@router.get("/rides/pending-review")
def get_pending_review(db: Session = Depends(get_db)):
    rides = db.query(Ride).filter(Ride.status == RideStatus.PENDING_REVIEW).all()
    return rides

@router.post("/rides/{ride_id}/approve")
def approve_ride(ride_id: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    ride.status = RideStatus.COMPLETED
    db.commit()
    
    return {"success": True}

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_rides = db.query(Ride).count()
    completed_rides = db.query(Ride).filter(Ride.status == RideStatus.COMPLETED).count()
    
    return {
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "completion_rate": (completed_rides / total_rides * 100) if total_rides > 0 else 0
    }
