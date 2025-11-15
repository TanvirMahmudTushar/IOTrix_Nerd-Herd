"""
Fix puller locations in database to ensure distance display works
"""
from database import SessionLocal
from models.db_models import Puller, Location

def fix_puller_locations():
    db = SessionLocal()
    try:
        # Get all pullers
        pullers = db.query(Puller).all()
        
        print("Checking puller locations...")
        print()
        
        fixed_count = 0
        for puller in pullers:
            if not puller.current_lat or not puller.current_lng:
                # Set default location near CUET
                puller.current_lat = 22.4590
                puller.current_lng = 91.9710
                fixed_count += 1
                print(f"✅ Fixed {puller.puller_id} ({puller.name})")
                print(f"   Set location to: ({puller.current_lat}, {puller.current_lng})")
            else:
                print(f"✓  {puller.puller_id} ({puller.name})")
                print(f"   Location: ({puller.current_lat}, {puller.current_lng})")
        
        if fixed_count > 0:
            db.commit()
            print()
            print(f"✅ Fixed {fixed_count} puller(s)")
        else:
            print()
            print("✅ All pullers have location data")
        
        # Verify locations exist
        print()
        print("Checking locations...")
        locations = db.query(Location).all()
        for loc in locations:
            print(f"✓  {loc.name}: ({loc.lat}, {loc.lng})")
        
        if len(locations) == 0:
            print("❌ No locations found! Run: python seed_data.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Fixing puller locations for distance display...")
    print()
    fix_puller_locations()
    print()
    print("✅ Done! Try requesting a ride again.")

