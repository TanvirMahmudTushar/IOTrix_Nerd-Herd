from models.db_models import Ride, Location, RideStatus
from sqlalchemy.orm import Session
from utils.gps_utils import haversine_distance

def calculate_points(dropoff_lat: float, dropoff_lng: float, destination_lat: float, destination_lng: float) -> tuple[int, bool]:
    """
    Calculate points based on dropoff accuracy (MVP tier-based formula)
    
    Returns: (points, needs_review)
    """
    distance_error = haversine_distance(dropoff_lat, dropoff_lng, destination_lat, destination_lng)
    
    # Tier-based point allocation (MVP requirements)
    if distance_error == 0:
        return 10, False
    elif distance_error <= 50:
        return 8, False
    elif distance_error <= 100:
        return 5, False
    else:
        return 0, True  # Needs admin review
