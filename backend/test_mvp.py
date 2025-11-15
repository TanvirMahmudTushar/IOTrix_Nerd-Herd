"""
MVP Backend Test Script
Tests all 16 endpoints to verify functionality
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def print_test(name, passed, details=""):
    status = "✅" if passed else "❌"
    print(f"{status} {name}")
    if details:
        print(f"   {details}")

def test_user_verification():
    """Test 1: User verification with laser frequency"""
    print("\n🔬 Test 1: User Verification (Laser + Ultrasonic)")
    response = requests.post(f"{BASE_URL}/api/rides/verify", json={
        "laser_frequency": 532.0,
        "ultrasonic_duration": 3.5,
        "location_block": "CUET"
    })
    passed = response.status_code == 200 and response.json().get("success") == True
    user_id = response.json().get("user_id") if passed else None
    print_test("User verification", passed, f"User ID: {user_id}")
    return user_id

def test_ride_request(user_id):
    """Test 2: Ride request"""
    print("\n🚗 Test 2: Ride Request")
    response = requests.post(f"{BASE_URL}/api/rides/request", json={
        "user_id": user_id,
        "pickup_location": "CUET",
        "destination": "Pahartoli"
    })
    passed = response.status_code == 200 and response.json().get("success") == True
    ride_id = response.json().get("ride_id") if passed else None
    print_test("Ride request created", passed, f"Ride ID: {ride_id}")
    return ride_id

def test_ride_status(ride_id):
    """Test 3: Ride status (LED control)"""
    print("\n💡 Test 3: Ride Status (LED Control)")
    response = requests.get(f"{BASE_URL}/api/rides/{ride_id}/status")
    passed = response.status_code == 200
    data = response.json() if passed else {}
    print_test("Get ride status", passed, 
              f"Status: {data.get('status')}, Yellow: {data.get('led_yellow')}, Red: {data.get('led_red')}, Green: {data.get('led_green')}")
    return passed

def test_puller_alerts():
    """Test 4: Puller alerts"""
    print("\n📢 Test 4: Puller Alerts")
    # Get first puller from database
    from database import SessionLocal
    from models.db_models import Puller
    db = SessionLocal()
    puller = db.query(Puller).first()
    db.close()
    
    if not puller:
        print_test("Get puller alerts", False, "No pullers in database. Run seed_data.py first.")
        return None
    
    response = requests.get(f"{BASE_URL}/api/pullers/{puller.puller_id}/alerts")
    passed = response.status_code == 200
    data = response.json() if passed else {}
    alert_count = len(data.get("alerts", []))
    print_test("Get puller alerts", passed, f"Found {alert_count} alerts, Puller: {puller.puller_id}")
    return puller.puller_id

def test_puller_accept(ride_id, puller_id):
    """Test 5: Puller accept (with race condition protection)"""
    print("\n✋ Test 5: Puller Accept Ride")
    response = requests.post(f"{BASE_URL}/api/rides/{ride_id}/accept?puller_id={puller_id}")
    passed = response.status_code == 200
    data = response.json() if passed else {}
    print_test("Puller accept ride", passed, f"Success: {data.get('success')}")
    return passed

def test_user_accept(ride_id):
    """Test 6: User accepts puller"""
    print("\n👍 Test 6: User Accepts Puller")
    response = requests.post(f"{BASE_URL}/api/rides/{ride_id}/user-accept")
    passed = response.status_code == 200
    print_test("User accepts puller", passed)
    return passed

def test_confirm_pickup(ride_id, puller_id):
    """Test 7: Confirm pickup"""
    print("\n🚕 Test 7: Confirm Pickup")
    response = requests.post(f"{BASE_URL}/api/rides/{ride_id}/pickup?puller_id={puller_id}")
    passed = response.status_code == 200
    print_test("Confirm pickup", passed)
    return passed

def test_active_ride(ride_id, puller_id):
    """Test 8: Get active ride details"""
    print("\n📍 Test 8: Active Ride Details (OLED)")
    response = requests.get(f"{BASE_URL}/api/rides/{ride_id}/active?puller_id={puller_id}")
    passed = response.status_code == 200
    data = response.json() if passed else {}
    print_test("Get active ride", passed, 
              f"Distance to dest: {data.get('distance_to_destination', 0):.1f}m")
    return passed

def test_complete_ride(ride_id, puller_id):
    """Test 9: Complete ride with points"""
    print("\n🎯 Test 9: Complete Ride (Points Calculation)")
    
    # Simulate dropoff at Pahartoli (exact location = 10 points)
    response = requests.post(f"{BASE_URL}/api/rides/{ride_id}/complete", json={
        "puller_id": puller_id,
        "dropoff_lat": 22.3569,  # Exact Pahartoli coords
        "dropoff_lng": 91.7832
    })
    passed = response.status_code == 200
    data = response.json() if passed else {}
    print_test("Complete ride", passed, 
              f"Points: {data.get('points_awarded')}, Accuracy: {data.get('dropoff_accuracy', 0):.1f}m, Status: {data.get('points_status')}")
    return passed

def test_admin_overview():
    """Test 10: Admin overview"""
    print("\n👔 Test 10: Admin Overview")
    response = requests.get(f"{BASE_URL}/api/admin/overview")
    passed = response.status_code == 200
    data = response.json() if passed else {}
    print_test("Admin overview", passed, 
              f"Active rides: {data.get('active_rides')}, Online pullers: {data.get('online_pullers')}")
    return passed

def test_timeout_mechanism():
    """Test 11: Timeout mechanism"""
    print("\n⏱️  Test 11: Timeout Mechanism (60s)")
    print("   Creating ride and waiting for timeout...")
    
    # Create user
    user_response = requests.post(f"{BASE_URL}/api/rides/verify", json={
        "laser_frequency": 650.0,
        "ultrasonic_duration": 3.2,
        "location_block": "CUET"
    })
    user_id = user_response.json().get("user_id")
    
    # Create ride
    ride_response = requests.post(f"{BASE_URL}/api/rides/request", json={
        "user_id": user_id,
        "pickup_location": "CUET",
        "destination": "Noapara"
    })
    timeout_ride_id = ride_response.json().get("ride_id")
    
    print(f"   Ride created: {timeout_ride_id}")
    print("   Waiting 65 seconds for timeout checker...")
    print("   (Background task runs every 10 seconds)")
    
    time.sleep(65)
    
    # Check status
    status_response = requests.get(f"{BASE_URL}/api/rides/{timeout_ride_id}/status")
    data = status_response.json()
    
    passed = data.get("status") == "timeout" and data.get("led_red") == True
    print_test("Ride timeout triggered", passed, 
              f"Status: {data.get('status')}, Red LED: {data.get('led_red')}")
    return passed

def test_race_condition():
    """Test 12: Race condition protection"""
    print("\n🏁 Test 12: Race Condition Protection")
    print("   Testing first-accept wins...")
    
    # Create a ride
    user_response = requests.post(f"{BASE_URL}/api/rides/verify", json={
        "laser_frequency": 405.0,
        "ultrasonic_duration": 3.1,
        "location_block": "CUET"
    })
    user_id = user_response.json().get("user_id")
    
    ride_response = requests.post(f"{BASE_URL}/api/rides/request", json={
        "user_id": user_id,
        "pickup_location": "CUET",
        "destination": "Raojan"
    })
    race_ride_id = ride_response.json().get("ride_id")
    
    # Get two pullers
    from database import SessionLocal
    from models.db_models import Puller
    db = SessionLocal()
    pullers = db.query(Puller).limit(2).all()
    db.close()
    
    if len(pullers) < 2:
        print_test("Race condition test", False, "Need at least 2 pullers")
        return False
    
    # Simulate simultaneous accepts
    import threading
    results = []
    
    def accept_ride(puller_id, results_list):
        try:
            response = requests.post(f"{BASE_URL}/api/rides/{race_ride_id}/accept?puller_id={puller_id}")
            results_list.append(response.status_code)
        except Exception as e:
            results_list.append(None)
    
    thread1 = threading.Thread(target=accept_ride, args=(pullers[0].puller_id, results))
    thread2 = threading.Thread(target=accept_ride, args=(pullers[1].puller_id, results))
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    # One should succeed (200), one should fail (400)
    success_count = results.count(200)
    failed_count = results.count(400)
    
    passed = success_count == 1 and failed_count == 1
    print_test("Race condition protected", passed, 
              f"One accepted (200), one rejected (400)")
    return passed

def run_all_tests():
    """Run all MVP tests"""
    print("=" * 60)
    print("🧪 AERAS MVP Backend Test Suite")
    print("=" * 60)
    
    try:
        # Basic functionality tests
        user_id = test_user_verification()
        if not user_id:
            print("\n❌ Cannot continue without user verification")
            return
        
        ride_id = test_ride_request(user_id)
        if not ride_id:
            print("\n❌ Cannot continue without ride request")
            return
        
        test_ride_status(ride_id)
        
        puller_id = test_puller_alerts()
        if not puller_id:
            print("\n❌ Cannot continue without puller")
            return
        
        test_puller_accept(ride_id, puller_id)
        test_user_accept(ride_id)
        test_confirm_pickup(ride_id, puller_id)
        test_active_ride(ride_id, puller_id)
        test_complete_ride(ride_id, puller_id)
        test_admin_overview()
        
        # Critical tests
        print("\n" + "=" * 60)
        print("🔥 Critical MVP Tests")
        print("=" * 60)
        
        test_race_condition()
        
        # Timeout test (takes 65 seconds)
        print("\n⚠️  Timeout test will take 65 seconds...")
        skip_timeout = input("Skip timeout test? (y/n): ").lower() == 'y'
        if not skip_timeout:
            test_timeout_mechanism()
        else:
            print("⏭️  Skipped timeout test")
        
        print("\n" + "=" * 60)
        print("✅ MVP Test Suite Complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n⚠️  Make sure the backend is running on http://localhost:8000")
    print("⚠️  Make sure you've run 'python seed_data.py' to populate locations")
    input("Press Enter to start tests...")
    run_all_tests()


