from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import Ride, RideStatus, Puller, User, PointsHistory, PullerStatus
from models.schemas import ResolveReviewRequest
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    """Get real-time admin overview (MVP requirement)"""
    active_rides = db.query(Ride).filter(
        Ride.status.in_([RideStatus.PENDING, RideStatus.PULLER_ASSIGNED, RideStatus.PICKUP_CONFIRMED])
    ).count()
    
    online_pullers = db.query(Puller).filter(
        Puller.status.in_([PullerStatus.AVAILABLE, PullerStatus.BUSY])
    ).count()
    
    pending_reviews = db.query(Ride).filter(
        Ride.status == RideStatus.PENDING_REVIEW
    ).count()
    
    return {
        "active_rides": active_rides,
        "online_pullers": online_pullers,
        "pending_reviews": pending_reviews
    }

@router.get("/reviews/pending")
def get_pending_reviews(db: Session = Depends(get_db)):
    """Get rides pending admin review (distance > 100m) - MVP requirement"""
    pending_rides = db.query(Ride).filter(
        Ride.status == RideStatus.PENDING_REVIEW
    ).all()
    
    reviews = []
    for ride in pending_rides:
        puller = db.query(Puller).filter(Puller.puller_id == ride.puller_id).first()
        
        reviews.append({
            "ride_id": ride.ride_id,
            "puller_name": puller.name if puller else "Unknown",
            "destination": ride.destination,
            "distance_error": ride.dropoff_distance_error or 0,
            "calculated_points": 0  # Would be adjusted by admin
        })
    
    return {"rides": reviews}

@router.post("/reviews/{ride_id}/resolve")
def resolve_review(ride_id: str, request: ResolveReviewRequest, db: Session = Depends(get_db)):
    """Approve or adjust points for pending review rides (MVP requirement)"""
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.status != RideStatus.PENDING_REVIEW:
        raise HTTPException(status_code=400, detail="Ride is not pending review")
    
    puller = db.query(Puller).filter(Puller.puller_id == ride.puller_id).first()
    if not puller:
        raise HTTPException(status_code=404, detail="Puller not found")
    
    if request.action == "approve":
        # Approve with 0 points (distance was > 100m)
        points = 0
        ride.points_awarded = points
        ride.status = RideStatus.COMPLETED
        
    elif request.action == "adjust":
        # Admin manually adjusts points
        if request.points_override is None:
            raise HTTPException(status_code=400, detail="points_override required for adjust action")
        
        points = request.points_override
        ride.points_awarded = points
        ride.status = RideStatus.COMPLETED
        
        # Update puller points
        puller.points += points
        puller.total_rides += 1
        
        # Create points history entry
        transaction = PointsHistory(
            transaction_id=f"txn_{uuid.uuid4().hex[:8]}",
            puller_id=ride.puller_id,
            ride_id=ride_id,
            points_change=points,
            reason=f"Admin adjustment for ride with {ride.dropoff_distance_error:.1f}m accuracy"
        )
        db.add(transaction)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'adjust'")
    
    db.commit()
    
    return {
        "success": True,
        "final_points": points
    }

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """Basic analytics (MVP requirement)"""
    total_rides = db.query(Ride).count()
    completed_rides = db.query(Ride).filter(Ride.status == RideStatus.COMPLETED).count()
    
    return {
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "completion_rate": (completed_rides / total_rides * 100) if total_rides > 0 else 0
    }
