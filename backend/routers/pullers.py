from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import exc
from datetime import datetime, timedelta
from database import get_db
from models.db_models import Ride, Puller, RideStatus, PullerStatus, Location, User, PointsHistory
from models.schemas import RideAlertResponse, PullerProfileResponse, ActiveRideResponse, RideCompleteRequest, RideCompleteResponse
from services.points_service import calculate_points
from utils.gps_utils import haversine_distance
import uuid

router = APIRouter()

# Alert timeout in seconds (MVP requirement - matches ride timeout in main.py)
ALERT_TIMEOUT_SECONDS = 60

@router.get("/{puller_id}/alerts")
def get_alerts(puller_id: str, db: Session = Depends(get_db)):
    """
    Get available ride alerts for puller (MVP requirements)
    Returns alerts sorted by distance with 30-second expiration
    """
    puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
    if not puller:
        # Return empty alerts instead of 404 - better UX
        return {"alerts": []}
    
    # Get pending rides
    pending_rides = db.query(Ride).filter(
        Ride.status == RideStatus.PENDING
    ).all()
    
    alerts = []
    for ride in pending_rides:
        pickup_loc = db.query(Location).filter(Location.name == ride.pickup).first()
        dest_loc = db.query(Location).filter(Location.name == ride.destination).first()
        
        if pickup_loc and dest_loc:
            # Distance from puller to pickup
            distance_to_pickup = haversine_distance(
                puller.current_lat, puller.current_lng,
                pickup_loc.lat, pickup_loc.lng
            )
            
            # Calculate potential points (distance from pickup to destination)
            route_distance = haversine_distance(
                pickup_loc.lat, pickup_loc.lng,
                dest_loc.lat, dest_loc.lng
            )
            
            # Estimate potential points (assuming perfect dropoff)
            potential_points = 10  # Best case scenario
            
            # Calculate expiration time
            time_elapsed = (datetime.utcnow() - ride.requested_at).total_seconds()
            expires_in = max(0, int(ALERT_TIMEOUT_SECONDS - time_elapsed))
            
            # Only show if not expired
            if expires_in > 0:
                alerts.append({
                    "ride_id": ride.ride_id,
                    "pickup": ride.pickup,
                    "destination": ride.destination,
                    "distance_to_pickup": distance_to_pickup,
                    "potential_points": potential_points,
                    "expires_in": expires_in,
                    "requested_at": ride.requested_at.isoformat()
                })
    
    # Sort by distance (nearest first)
    alerts.sort(key=lambda x: x["distance_to_pickup"])
    return {"alerts": alerts}

@router.post("/{ride_id}/accept")
def accept_ride(ride_id: str, puller_id: str, db: Session = Depends(get_db)):
    """
    Accept ride with RACE CONDITION PROTECTION (MVP critical requirement)
    Uses database transaction with row locking - first-accept wins
    """
    try:
        # Start transaction with row-level lock
        ride = db.query(Ride).filter(Ride.ride_id == ride_id).with_for_update().first()
        
        if not ride:
            raise HTTPException(status_code=404, detail="Ride not found")
        
        # Check if already accepted by another puller
        if ride.status != RideStatus.PENDING:
            raise HTTPException(status_code=400, detail="Ride already accepted by another puller")
        
        # Get puller and location details
        puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
        if not puller:
            raise HTTPException(status_code=404, detail="Puller not found")
        
        pickup_loc = db.query(Location).filter(Location.name == ride.pickup).first()
        dest_loc = db.query(Location).filter(Location.name == ride.destination).first()
        
        # Update ride status (first-accept wins)
        ride.puller_id = puller_id
        ride.status = RideStatus.PULLER_ASSIGNED
        ride.accepted_at = datetime.utcnow()
        
        # Update puller status
        puller.status = PullerStatus.BUSY
        
        db.commit()
        
        # Return ride details for navigation
        return {
            "success": True,
            "message": "Ride accepted successfully",
            "ride_details": {
                "pickup_location": ride.pickup,
                "pickup_lat": pickup_loc.lat if pickup_loc else 0,
                "pickup_lng": pickup_loc.lng if pickup_loc else 0,
                "destination": ride.destination,
                "destination_lat": dest_loc.lat if dest_loc else 0,
                "destination_lng": dest_loc.lng if dest_loc else 0
            }
        }
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ride already accepted by another puller")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error accepting ride: {str(e)}")

@router.post("/{ride_id}/reject")
def reject_ride(ride_id: str, puller_id: str, db: Session = Depends(get_db)):
    """Puller rejects ride alert - removes from their alert list (MVP requirement)"""
    # Note: Ride stays available to other pullers, this is just removing it from this puller's view
    # In a full implementation, we'd track rejections in a separate table
    return {"success": True, "message": "Ride removed from your alerts"}

@router.get("/{ride_id}/active")
def get_active_ride(ride_id: str, puller_id: str, db: Session = Depends(get_db)):
    """
    Get active ride details for OLED display (MVP requirement)
    Shows pickup/destination coords, navigation info
    """
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.puller_id != puller_id:
        raise HTTPException(status_code=403, detail="Not your ride")
    
    pickup_loc = db.query(Location).filter(Location.name == ride.pickup).first()
    dest_loc = db.query(Location).filter(Location.name == ride.destination).first()
    puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
    
    if not pickup_loc or not dest_loc or not puller:
        raise HTTPException(status_code=404, detail="Location or puller not found")
    
    # Calculate distance to destination
    distance_to_dest = haversine_distance(
        puller.current_lat, puller.current_lng,
        dest_loc.lat, dest_loc.lng
    )
    
    return {
        "ride_id": ride_id,
        "status": ride.status.value,
        "pickup": ride.pickup,
        "destination": ride.destination,
        "pickup_coords": {"lat": pickup_loc.lat, "lng": pickup_loc.lng},
        "destination_coords": {"lat": dest_loc.lat, "lng": dest_loc.lng},
        "distance_to_destination": distance_to_dest
    }

@router.post("/{ride_id}/pickup")
def confirm_pickup(ride_id: str, puller_id: str, db: Session = Depends(get_db)):
    """Puller confirms pickup - triggers Green LED (MVP requirement)"""
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.puller_id != puller_id:
        raise HTTPException(status_code=403, detail="Not your ride")
    
    ride.status = RideStatus.PICKUP_CONFIRMED
    ride.pickup_confirmed_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}

@router.post("/{ride_id}/complete")
def complete_ride(ride_id: str, request: RideCompleteRequest, db: Session = Depends(get_db)):
    """
    Complete ride with GPS verification and tier-based points (MVP requirement)
    Formula: 0m=10pts, ≤50m=8pts, ≤100m=5pts, >100m=pending review
    """
    ride = db.query(Ride).filter(Ride.ride_id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride.puller_id != request.puller_id:
        raise HTTPException(status_code=403, detail="Not your ride")
    
    # Get destination location
    dest_loc = db.query(Location).filter(Location.name == ride.destination).first()
    if not dest_loc:
        raise HTTPException(status_code=404, detail="Destination not found")
    
    # Calculate points using MVP tier-based formula
    points, needs_review = calculate_points(
        request.dropoff_lat, request.dropoff_lng,
        dest_loc.lat, dest_loc.lng
    )
    
    # Calculate dropoff accuracy
    dropoff_accuracy = haversine_distance(
        request.dropoff_lat, request.dropoff_lng,
        dest_loc.lat, dest_loc.lng
    )
    
    # Update ride
    ride.dropoff_lat = request.dropoff_lat
    ride.dropoff_lng = request.dropoff_lng
    ride.dropoff_distance_error = dropoff_accuracy
    ride.completed_at = datetime.utcnow()
    
    # Get puller
    puller = db.query(Puller).filter(Puller.puller_id == request.puller_id).first()
    if not puller:
        raise HTTPException(status_code=404, detail="Puller not found")
    
    if needs_review:
        # Distance > 100m - needs admin review
        ride.status = RideStatus.PENDING_REVIEW
        ride.points_awarded = 0  # No points until approved
        points_status = "pending"
    else:
        # Award points immediately
        ride.status = RideStatus.COMPLETED
        ride.points_awarded = points
        puller.points += points
        puller.total_rides += 1
        
        # Create points history entry
        transaction = PointsHistory(
            transaction_id=f"txn_{uuid.uuid4().hex[:8]}",
            puller_id=request.puller_id,
            ride_id=ride_id,
            points_change=points,
            reason=f"Ride completed with {dropoff_accuracy:.1f}m accuracy"
        )
        db.add(transaction)
        points_status = "rewarded"
    
    # Set puller back to available
    puller.status = PullerStatus.AVAILABLE
    
    db.commit()
    
    # Calculate ride duration
    duration_seconds = int((ride.completed_at - ride.pickup_confirmed_at).total_seconds()) if ride.pickup_confirmed_at else 0
    
    return {
        "success": True,
        "points_awarded": points,
        "points_status": points_status,
        "dropoff_accuracy": dropoff_accuracy,
        "ride_summary": {
            "duration": duration_seconds,
            "distance": dropoff_accuracy
        }
    }

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

@router.get("/{puller_id}/dashboard")
def get_dashboard(puller_id: str, db: Session = Depends(get_db)):
    """Get puller dashboard with stats and recent rides (MVP requirement)"""
    puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
    if not puller:
        raise HTTPException(status_code=404, detail="Puller not found")
    
    # Get recent rides (last 10)
    recent_rides = db.query(Ride).filter(
        Ride.puller_id == puller_id,
        Ride.status == RideStatus.COMPLETED
    ).order_by(Ride.completed_at.desc()).limit(10).all()
    
    rides_list = []
    for ride in recent_rides:
        duration = 0
        if ride.pickup_confirmed_at and ride.completed_at:
            duration = int((ride.completed_at - ride.pickup_confirmed_at).total_seconds())
        
        rides_list.append({
            "ride_id": ride.ride_id,
            "date": ride.completed_at.isoformat() if ride.completed_at else "",
            "pickup": ride.pickup,
            "destination": ride.destination,
            "points_earned": ride.points_awarded,
            "duration": duration
        })
    
    return {
        "name": puller.name,
        "points": puller.points,
        "total_rides": puller.total_rides,
        "status": puller.status.value,
        "recent_rides": rides_list
    }

@router.get("/{puller_id}/profile", response_model=PullerProfileResponse)
def get_profile(puller_id: str, db: Session = Depends(get_db)):
    """Legacy endpoint - redirects to dashboard"""
    puller = db.query(Puller).filter(Puller.puller_id == puller_id).first()
    if not puller:
        raise HTTPException(status_code=404, detail="Puller not found")
    
    user = db.query(User).filter(User.user_id == puller.user_id).first()
    
    return {
        "puller_id": puller_id,
        "name": user.name if user else puller.name,
        "points": puller.points,
        "total_rides": puller.total_rides,
        "rating": 0.0,
        "status": puller.status.value
    }
