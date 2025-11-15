from sqlalchemy.orm import Session
from models.db_models import Puller, Location, PullerStatus

def distribute_alerts(ride_id: str, pickup_location: str, db: Session):
    """Distribute ride alerts to nearby available pullers"""
    
    # Get pickup location coordinates
    pickup_loc = db.query(Location).filter(Location.name == pickup_location).first()
    if not pickup_loc:
        return
    
    # Get all available pullers
    available_pullers = db.query(Puller).filter(
        Puller.status == PullerStatus.AVAILABLE
    ).all()
    
    # Sort by distance (simple version - in production use Haversine)
    from utils.gps_utils import haversine_distance
    pullers_by_distance = []
    
    for puller in available_pullers:
        distance = haversine_distance(
            puller.current_lat, puller.current_lng,
            pickup_loc.lat, pickup_loc.lng
        )
        pullers_by_distance.append((puller, distance))
    
    pullers_by_distance.sort(key=lambda x: x[1])
    
    # In production, broadcast to multiple pullers via WebSocket
    # For now, this is just the infrastructure
    return pullers_by_distance[:5]  # Return top 5 nearest pullers
