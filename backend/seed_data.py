"""
Seed database with required locations (MVP requirement)
Run this once after setting up the database to populate location data
"""
from database import SessionLocal, engine, Base
from models.db_models import Location, Puller, User, UserRole, Ride, RideStatus
from datetime import datetime, timedelta
import uuid
import bcrypt

# MVP Required Coordinates
LOCATIONS = [
    {"name": "CUET", "lat": 22.4599, "lng": 91.9712},
    {"name": "Pahartoli", "lat": 22.3569, "lng": 91.7832},
    {"name": "Noapara", "lat": 22.4673, "lng": 91.8870},
    {"name": "Raojan", "lat": 22.4500, "lng": 92.0600}
]

def seed_locations():
    """Seed location data"""
    db = SessionLocal()
    try:
        # Check if locations already exist
        existing = db.query(Location).count()
        if existing > 0:
            print(f"Locations already seeded ({existing} found). Skipping...")
            return
        
        # Add locations
        for loc_data in LOCATIONS:
            location = Location(**loc_data)
            db.add(location)
        
        db.commit()
        print(f"✅ Successfully seeded {len(LOCATIONS)} locations")
        
        # Print location data
        for loc in LOCATIONS:
            print(f"  - {loc['name']}: ({loc['lat']}, {loc['lng']})")
        
    except Exception as e:
        print(f"❌ Error seeding locations: {e}")
        db.rollback()
    finally:
        db.close()

def seed_test_accounts():
    """Seed specific test accounts for easy demo"""
    db = SessionLocal()
    try:
        # Check if test accounts already exist
        existing_user = db.query(User).filter(User.email == "user@user.com").first()
        existing_puller = db.query(User).filter(User.email == "puller@puller.com").first()
        
        if existing_user and existing_puller:
            print(f"Test accounts already seeded. Skipping...")
            return
        
        # Create test user account (for physical block user simulation)
        if not existing_user:
            user_password = bcrypt.hashpw("user".encode(), bcrypt.gensalt()).decode()
            test_user = User(
                user_id="user_test001",
                email="user@user.com",
                hashed_password=user_password,
                role=UserRole.USER,
                name="Test User",
                phone="01700000001",
                laser_frequency=650.5  # Match ESP32 default
            )
            db.add(test_user)
            print(f"  ✓ Created test user: user@user.com / user")
        
        # Create test puller account
        if not existing_puller:
            puller_password = bcrypt.hashpw("puller".encode(), bcrypt.gensalt()).decode()
            test_puller_user = User(
                user_id="user_testpuller",
                email="puller@puller.com",
                hashed_password=puller_password,
                role=UserRole.PULLER,
                name="Test Puller",
                phone="01700000002"
            )
            db.add(test_puller_user)
            db.flush()
            
            # Create corresponding puller record
            test_puller = Puller(
                puller_id="puller_testpuller",
                user_id="user_testpuller",
                name="Test Puller",
                phone="01700000002",
                current_lat=22.4590,  # Near CUET
                current_lng=91.9710,
                points=50,
                total_rides=5,
                status="available"
            )
            db.add(test_puller)
            print(f"  ✓ Created test puller: puller@puller.com / puller")
        
        db.commit()
        print(f"✅ Test accounts created successfully")
        print(f"   👤 User: user@user.com / user")
        print(f"   🚲 Puller: puller@puller.com / puller")
        
    except Exception as e:
        print(f"❌ Error seeding test accounts: {e}")
        db.rollback()
    finally:
        db.close()

def seed_demo_pullers():
    """Seed demo puller accounts for testing (with User accounts)"""
    db = SessionLocal()
    try:
        # Check if pullers already exist
        existing = db.query(Puller).count()
        if existing >= 4:  # Including test puller
            print(f"Pullers already seeded ({existing} found). Skipping...")
            return
        
        # Create 4 demo pullers with consistent IDs and varied locations
        demo_pullers = [
            {
                "id_suffix": "demo001",
                "name": "Karim Rahman",
                "email": "karim@demo.com",
                "phone": "01712345678",
                "lat": 22.4580,
                "lng": 91.9700,
                "points": 150,
                "total_rides": 12
            },
            {
                "id_suffix": "demo002",
                "name": "Abdul Jabbar",
                "email": "abdul@demo.com",
                "phone": "01812345679",
                "lat": 22.3550,
                "lng": 91.7820,
                "points": 95,
                "total_rides": 8
            },
            {
                "id_suffix": "demo003",
                "name": "Rahim Mia",
                "email": "rahim@demo.com",
                "phone": "01912345680",
                "lat": 22.4660,
                "lng": 91.8860,
                "points": 220,
                "total_rides": 20
            },
            {
                "id_suffix": "demo004",
                "name": "Mofiz Uddin",
                "email": "mofiz@demo.com",
                "phone": "01612345681",
                "lat": 22.4510,
                "lng": 92.0590,
                "points": 75,
                "total_rides": 6
            }
        ]
        
        # Default password for all demo accounts: "demo123"
        hashed_password = bcrypt.hashpw("demo123".encode(), bcrypt.gensalt()).decode()
        
        for puller_data in demo_pullers:
            # Check if this specific puller exists
            user_id = f"user_{puller_data['id_suffix']}"
            existing = db.query(User).filter(User.user_id == user_id).first()
            if existing:
                continue
                
            puller_id = f"puller_{puller_data['id_suffix']}"
            
            # Create User account first
            user = User(
                user_id=user_id,
                email=puller_data["email"],
                hashed_password=hashed_password,
                role=UserRole.PULLER,
                name=puller_data["name"],
                phone=puller_data["phone"]
            )
            db.add(user)
            db.flush()  # Ensure user_id is available
            
            # Create Puller record
            puller = Puller(
                puller_id=puller_id,
                user_id=user_id,
                name=puller_data["name"],
                phone=puller_data["phone"],
                current_lat=puller_data["lat"],
                current_lng=puller_data["lng"],
                points=puller_data["points"],
                total_rides=puller_data["total_rides"],
                status="available"
            )
            db.add(puller)
        
        db.commit()
        print(f"✅ Successfully seeded {len(demo_pullers)} demo pullers with user accounts")
        print(f"   📧 Default password: demo123")
        for puller in demo_pullers:
            print(f"  - {puller['name']} ({puller['email']}) - {puller['points']} pts, {puller['total_rides']} rides")
        
    except Exception as e:
        print(f"❌ Error seeding pullers: {e}")
        db.rollback()
    finally:
        db.close()

def seed_sample_rides():
    """Seed some sample completed rides for demo purposes"""
    db = SessionLocal()
    try:
        # Check if rides already exist
        existing = db.query(Ride).count()
        if existing > 0:
            print(f"Rides already seeded ({existing} found). Skipping...")
            return
        
        # Get test user and pullers
        test_user = db.query(User).filter(User.email == "user@user.com").first()
        pullers = db.query(Puller).limit(3).all()
        
        if not test_user or len(pullers) < 2:
            print("⚠️  Skipping sample rides - missing users or pullers")
            return
        
        # Create some completed rides
        sample_rides = [
            {
                "pickup": "CUET",
                "destination": "Pahartoli",
                "puller": pullers[0],
                "points": 10,
                "days_ago": 2
            },
            {
                "pickup": "Noapara",
                "destination": "CUET",
                "puller": pullers[1],
                "points": 8,
                "days_ago": 1
            },
            {
                "pickup": "CUET",
                "destination": "Raojan",
                "puller": pullers[0],
                "points": 10,
                "days_ago": 0
            }
        ]
        
        for ride_data in sample_rides:
            ride_time = datetime.utcnow() - timedelta(days=ride_data["days_ago"])
            ride = Ride(
                ride_id=f"ride_{uuid.uuid4().hex[:8]}",
                user_id=test_user.user_id,
                puller_id=ride_data["puller"].puller_id,
                pickup=ride_data["pickup"],
                destination=ride_data["destination"],
                status=RideStatus.COMPLETED,
                requested_at=ride_time,
                accepted_at=ride_time + timedelta(seconds=15),
                pickup_confirmed_at=ride_time + timedelta(minutes=5),
                completed_at=ride_time + timedelta(minutes=20),
                points_awarded=ride_data["points"],
                dropoff_distance_error=5.0
            )
            db.add(ride)
        
        db.commit()
        print(f"✅ Successfully seeded {len(sample_rides)} sample rides")
        
    except Exception as e:
        print(f"❌ Error seeding sample rides: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding database with MVP data...")
    print()
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Seed locations
    seed_locations()
    print()
    
    # Seed test accounts (user@user.com and puller@puller.com)
    seed_test_accounts()
    print()
    
    # Seed demo pullers
    seed_demo_pullers()
    print()
    
    # Seed sample rides
    seed_sample_rides()
    print()
    
    print("✅ Database seeding complete!")
    print()
    print("=" * 60)
    print("QUICK LOGIN CREDENTIALS:")
    print("=" * 60)
    print("👤 Test User (Physical Block):")
    print("   Email: user@user.com")
    print("   Password: user")
    print()
    print("🚲 Test Puller:")
    print("   Email: puller@puller.com")
    print("   Password: puller")
    print()
    print("🚲 Demo Pullers:")
    print("   All demo pullers use password: demo123")
    print("   - karim@demo.com")
    print("   - abdul@demo.com")
    print("   - rahim@demo.com")
    print("   - mofiz@demo.com")
    print("=" * 60)


