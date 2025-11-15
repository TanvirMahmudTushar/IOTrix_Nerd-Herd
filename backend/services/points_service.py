from models.db_models import Ride, Location
from sqlalchemy.orm import Session
from utils.gps_utils import haversine_distance

def calculate_points(ride: Ride, db: Session) -> int:
    """Calculate points based on distance from pickup block"""
    
    pickup_loc = db.query(Location).filter(Location.name == ride.pickup).first()
    destination_loc = db.query(Location).filter(Location.name == ride.destination).first()
    
    if not pickup_loc or not destination_loc:
        return 0
    
    # Calculate distance
    distance = haversine_distance(
        pickup_loc.lat, pickup_loc.lng,
        destination_loc.lat, destination_loc.lng
    )
    
    # Points formula: 10 - (distance / 10)
    points = max(0, int(10 - (distance / 10)))
    
    # If distance > 100m, needs admin review
    if distance > 100:
        ride.status = "pending_review"
    
    return points
