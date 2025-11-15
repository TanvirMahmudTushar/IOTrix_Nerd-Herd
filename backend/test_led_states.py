"""
Quick test script to manually trigger LED states for testing
Run this after requesting a ride from ESP32
"""
import requests
import sys

BACKEND_URL = "http://localhost:8000"

def test_yellow_led(ride_id, puller_id="puller_testpuller"):
    """Trigger Yellow LED by accepting ride"""
    url = f"{BACKEND_URL}/api/pullers/{ride_id}/accept"
    response = requests.post(url, params={"puller_id": puller_id})
    if response.status_code == 200:
        print("✅ Yellow LED should turn ON - Puller accepted ride")
        print(f"   Status: {response.json()}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

def test_green_led(ride_id):
    """Trigger Green LED by confirming pickup"""
    url = f"{BACKEND_URL}/api/rides/{ride_id}/user-accept"
    response = requests.post(url)
    if response.status_code == 200:
        print("✅ Green LED should turn ON - Pickup confirmed")
        print(f"   Status: {response.json()}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")

def test_red_led(ride_id):
    """Trigger Red LED by manually setting timeout"""
    # This requires direct database manipulation
    # For testing, we'll use a workaround
    print("🔴 Red LED Testing:")
    print("   Method 1: Wait 60 seconds without accepting ride")
    print("   Method 2: Run SQL manually:")
    print(f"      UPDATE rides SET status='TIMEOUT' WHERE ride_id='{ride_id}'")

def check_status(ride_id):
    """Check current ride status"""
    url = f"{BACKEND_URL}/api/rides/{ride_id}/status"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("\n📊 Current Status:")
        print(f"   Status: {data['status']}")
        print(f"   🟡 Yellow LED: {data['led_yellow']}")
        print(f"   🟢 Green LED: {data['led_green']}")
        print(f"   🔴 Red LED: {data['led_red']}")
        if data.get('distance_to_pickup'):
            print(f"   📍 Distance: {data['distance_to_pickup']:.1f}m")
    else:
        print(f"❌ Failed to get status: {response.status_code}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_led_states.py <ride_id> [action]")
        print("\nActions:")
        print("  status  - Check current LED states (default)")
        print("  yellow  - Trigger Yellow LED (puller accepts)")
        print("  green   - Trigger Green LED (pickup confirmed)")
        print("  red     - Show how to trigger Red LED (timeout)")
        print("\nExample:")
        print("  python test_led_states.py ride_abc123 status")
        print("  python test_led_states.py ride_abc123 yellow")
        print("  python test_led_states.py ride_abc123 green")
        sys.exit(1)
    
    ride_id = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "status"
    
    print(f"🧪 Testing LED States for Ride: {ride_id}\n")
    
    if action == "yellow":
        test_yellow_led(ride_id)
        print("\nWait 2-4 seconds for ESP32 to poll and update...")
        
    elif action == "green":
        test_green_led(ride_id)
        print("\nWait 2-4 seconds for ESP32 to poll and update...")
        
    elif action == "red":
        test_red_led(ride_id)
        
    elif action == "status":
        check_status(ride_id)
        
    else:
        print(f"❌ Unknown action: {action}")
        print("   Use: status, yellow, green, or red")

