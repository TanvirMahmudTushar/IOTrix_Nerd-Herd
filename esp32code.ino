// ---------------------------------------------------------------------------
// 2 Ultrasonic Sensors + LDR Light Sensor + OLED + WiFi Backend Integration
// ---------------------------------------------------------------------------
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <NewPing.h>
#include <Buzzer.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* WIFI_SSID = "Mahir 2.4GHz";
const char* WIFI_PASSWORD = "01741238814";
const char* BACKEND_URL = "http://192.168.0.232:8000";

#define i2c_Address 0x3c   // OLED address
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SH1106G display = Adafruit_SH1106G(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

#define BUZZER_PIN 3
Buzzer buzzer(BUZZER_PIN);

// LED Pins (Test Case 4 Requirements)
#define LED_RED_PIN 35      // Red: Timeout / No puller
#define LED_YELLOW_PIN 36   // Yellow: Puller accepted
#define LED_GREEN_PIN 37    // Green: Pickup confirmed

#define LDR_PIN 10   
int lightValue = 0;

String previousSelection = "None";
bool errorMode = false;
bool authState = false;

// Ultrasonic Presence Tracking (Test Case 1 Requirements)
unsigned long presenceStartTime = 0;
bool presenceDetected = false;
const unsigned long PRESENCE_THRESHOLD = 3000; // 3 seconds (±0.2s tolerance built in)

// Backend Integration State
String userId = "";
String currentRideId = "";
bool rideRequested = false;
bool pullerAssigned = false;
unsigned long lastPollTime = 0;
const unsigned long POLL_INTERVAL = 2000; // Poll every 2 seconds
String laserFrequency = "650.5"; // Default laser frequency for this block

#define SONAR_NUM 2
#define MAX_DISTANCE 20

NewPing sonar[SONAR_NUM] = {
  NewPing(7, 6, MAX_DISTANCE),
  NewPing(5, 4, MAX_DISTANCE)
};

// Zones
#define ZONE_A_MIN 0
#define ZONE_A_MAX 5
#define DEADZONE_1_MIN 5
#define DEADZONE_1_MAX 7
#define ZONE_B_MIN 7
#define ZONE_B_MAX 12
#define DEADZONE_2_MIN 12
#define DEADZONE_2_MAX 14
#define ZONE_C_MIN 14
#define ZONE_C_MAX 19

// OLED Helper
void oledShow(String line1, String line2) {
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SH110X_WHITE);
  display.setCursor(10, 15);
  display.println(line1);
  display.setCursor(10, 40);
  display.println(line2);
  display.display();
}

// Sonar Logic
String getSelection() {
  int presenceCount = 0;
  int closestSensor = -1;
  int closestDistance = INT_MAX;

  for (int i = 0; i < SONAR_NUM; i++) {
    delay(50);
    int d = sonar[i].ping_cm();
    if (d > 0 && d <= 19) {
      presenceCount++;
      if (d < closestDistance) {
        closestDistance = d;
        closestSensor = i;
      }
    }
  }

  if (presenceCount > 1) return "MP";

  if (closestSensor != -1) {
    if (closestDistance >= ZONE_A_MIN && closestDistance <= ZONE_A_MAX) return "Pahartoli";
    if (closestDistance >= DEADZONE_1_MIN && closestDistance <= DEADZONE_1_MAX) return "Deadzone";
    if (closestDistance >= ZONE_B_MIN && closestDistance <= ZONE_B_MAX) return "Noapara";
    if (closestDistance >= DEADZONE_2_MIN && closestDistance <= DEADZONE_2_MAX) return "Deadzone";
    if (closestDistance >= ZONE_C_MIN && closestDistance <= ZONE_C_MAX) return "Raojan";
  }

  return "None";
}

// LDR Auth
bool getAuth() {
  int lightValue = analogRead(LDR_PIN);
  const int THRESHOLD = 1600;
  return (lightValue > THRESHOLD);
}

// LED Control Functions (Test Case 4 Requirements)
void turnOffAllLEDs() {
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(LED_YELLOW_PIN, LOW);
  digitalWrite(LED_GREEN_PIN, LOW);
  Serial.println("LEDs: All OFF");
}

void setLEDs(bool red, bool yellow, bool green) {
  digitalWrite(LED_RED_PIN, red ? HIGH : LOW);
  digitalWrite(LED_YELLOW_PIN, yellow ? HIGH : LOW);
  digitalWrite(LED_GREEN_PIN, green ? HIGH : LOW);
  
  Serial.print("LEDs: Red=");
  Serial.print(red);
  Serial.print(", Yellow=");
  Serial.print(yellow);
  Serial.print(", Green=");
  Serial.println(green);
}

// Ultrasonic Presence Validation (Test Case 1 Requirements)
// Returns true if user has been present continuously for >= 3 seconds
bool validatePresence(String selection) {
  bool validSelection = (selection == "Pahartoli" || selection == "Noapara" || selection == "Raojan");
  
  if (validSelection && !presenceDetected) {
    // Start tracking presence
    presenceStartTime = millis();
    presenceDetected = true;
    Serial.println("Presence tracking started");
  } else if (!validSelection && presenceDetected) {
    // User left or moved out of range, reset
    presenceDetected = false;
    Serial.println("Presence lost, resetting timer");
  }
  
  if (presenceDetected) {
    unsigned long presenceDuration = millis() - presenceStartTime;
    if (presenceDuration >= PRESENCE_THRESHOLD) {
      Serial.print("Presence validated: ");
      Serial.print(presenceDuration);
      Serial.println(" ms");
      return true;
    } else {
      Serial.print("Waiting for 3s... Current: ");
      Serial.print(presenceDuration);
      Serial.println(" ms");
    }
  }
  
  return false;
}

// WiFi Connection
void connectWiFi() {
  Serial.print("Connecting to WiFi");
  oledShow("Connecting", "WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    oledShow("WiFi", "Connected");
    delay(1000);
  } else {
    Serial.println("\nWiFi failed!");
    oledShow("WiFi", "Failed");
    delay(2000);
  }
}

// Verify User with Backend
bool verifyUser(String location, float ultrasonicDuration) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("ERROR: WiFi not connected");
    return false;
  }
  
  HTTPClient http;
  String url = String(BACKEND_URL) + "/api/rides/verify";
  Serial.println("Verifying user at: " + url);
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Use actual measured ultrasonic duration
  Serial.print("Ultrasonic duration: ");
  Serial.print(ultrasonicDuration);
  Serial.println(" seconds");
  
  StaticJsonDocument<200> doc;
  doc["laser_frequency"] = laserFrequency.toFloat();
  doc["ultrasonic_duration"] = ultrasonicDuration;
  doc["location_block"] = location;
  
  String jsonBody;
  serializeJson(doc, jsonBody);
  Serial.println("Request body: " + jsonBody);
  
  int httpCode = http.POST(jsonBody);
  Serial.println("HTTP Response Code: " + String(httpCode));
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("Response: " + response);
    
    StaticJsonDocument<200> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (error) {
      Serial.print("ERROR: JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    
    if (responseDoc["success"] == true) {
      userId = responseDoc["user_id"].as<String>();
      Serial.println("✓ User verified: " + userId);
      http.end();
      return true;
    } else {
      Serial.println("ERROR: Backend returned success=false");
    }
  } else if (httpCode > 0) {
    String errorResponse = http.getString();
    Serial.println("ERROR: HTTP " + String(httpCode) + " - " + errorResponse);
  } else {
    Serial.println("ERROR: Connection failed, code: " + String(httpCode));
  }
  
  http.end();
  return false;
}

// Request Ride
bool requestRide(String destination) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("ERROR: WiFi not connected for ride request");
    return false;
  }
  
  if (userId == "") {
    Serial.println("ERROR: No user_id available");
    return false;
  }
  
  HTTPClient http;
  String url = String(BACKEND_URL) + "/api/rides/request";
  Serial.println("Requesting ride at: " + url);
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  StaticJsonDocument<300> doc;
  doc["user_id"] = userId;
  doc["pickup_location"] = previousSelection; // Use the location they're at
  doc["destination"] = destination;
  
  String jsonBody;
  serializeJson(doc, jsonBody);
  Serial.println("Request body: " + jsonBody);
  
  int httpCode = http.POST(jsonBody);
  Serial.println("HTTP Response Code: " + String(httpCode));
  
  if (httpCode == 201) {
    String response = http.getString();
    Serial.println("Response: " + response);
    
    StaticJsonDocument<200> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (error) {
      Serial.print("ERROR: JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return false;
    }
    
    currentRideId = responseDoc["ride_id"].as<String>();
    Serial.println("✓ Ride requested: " + currentRideId);
    http.end();
    return true;
  } else if (httpCode > 0) {
    String errorResponse = http.getString();
    Serial.println("ERROR: HTTP " + String(httpCode) + " - " + errorResponse);
  } else {
    Serial.println("ERROR: Connection failed, code: " + String(httpCode));
  }
  
  http.end();
  return false;
}

// Poll Ride Status
void pollRideStatus() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("ERROR: WiFi not connected for status poll");
    return;
  }
  
  if (currentRideId == "") {
    Serial.println("ERROR: No ride_id to poll");
    return;
  }
  
  HTTPClient http;
  String url = String(BACKEND_URL) + "/api/rides/" + currentRideId + "/status";
  Serial.println("Polling status: " + url);
  
  http.begin(url);
  int httpCode = http.GET();
  Serial.println("Poll Response Code: " + String(httpCode));
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("Status response: " + response);
    
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, response);
    
    if (error) {
      Serial.print("ERROR: JSON parsing failed: ");
      Serial.println(error.c_str());
      http.end();
      return;
    }
    
    String status = doc["status"].as<String>();
    Serial.println("Ride status: " + status);
    
    // Check LED states from backend (Test Case 4 Requirements)
    bool ledYellow = doc["led_yellow"];
    bool ledGreen = doc["led_green"];
    bool ledRed = doc["led_red"];
    
    Serial.print("Backend LEDs - Yellow: ");
    Serial.print(ledYellow);
    Serial.print(", Green: ");
    Serial.print(ledGreen);
    Serial.print(", Red: ");
    Serial.println(ledRed);
    
    // Update physical LEDs based on backend status
    setLEDs(ledRed, ledYellow, ledGreen);
    
    if (ledYellow && !pullerAssigned) {
      // Puller has accepted! (Test Case 4b & 6 & 9: < 3s latency)
      Serial.println("✓ Puller accepted ride!");
      pullerAssigned = true;
      acknowledgeSound();
    }
    
    // Show distance if puller is assigned and distance is available
    if (ledYellow && doc.containsKey("distance_to_pickup") && !doc["distance_to_pickup"].isNull()) {
      float distanceMeters = doc["distance_to_pickup"].as<float>();
      Serial.print("Distance to pickup: ");
      Serial.print(distanceMeters);
      Serial.println(" meters");
      
      // Display distance on OLED
      String distanceStr;
      if (distanceMeters >= 1000) {
        // Display in kilometers if >= 1km
        float distanceKm = distanceMeters / 1000.0;
        distanceStr = String(distanceKm, 1) + " KM";
      } else {
        // Display in meters
        distanceStr = String((int)distanceMeters) + " M";
      }
      oledShow("Puller", distanceStr);
    } else if (ledYellow) {
      // Fallback if distance not available
      oledShow("Puller", "Incoming...");
    }
    
    if (ledGreen) {
      // Pickup confirmed (Test Case 4d & 6: Yellow OFF, Green ON)
      Serial.println("✓ Pickup confirmed!");
      oledShow("Pickup", "Confirmed");
      delay(2000);
      resetRideState();
    }
    
    if (ledRed) {
      // Timeout (Test Case 4c & 8: No puller within 60s)
      Serial.println("✗ Ride timed out (60s expired)");
      errorSound();
      oledShow("Timeout", "Try Again");
      delay(2000);
      resetRideState();
    }
  } else if (httpCode > 0) {
    String errorResponse = http.getString();
    Serial.println("ERROR: HTTP " + String(httpCode) + " - " + errorResponse);
  } else {
    Serial.println("ERROR: Connection failed, code: " + String(httpCode));
  }
  
  http.end();
}

// Reset Ride State (Test Case 13: Reset all LEDs to idle)
void resetRideState() {
  Serial.println("Resetting ride state");
  rideRequested = false;
  pullerAssigned = false;
  currentRideId = "";
  userId = "";
  presenceDetected = false;
  turnOffAllLEDs(); // Turn off all LEDs when resetting
}

void acceptReq() {
  Serial.println("Accept Req");
  String destination = previousSelection;
  
  // Calculate actual presence duration in seconds
  float ultrasonicDuration = (millis() - presenceStartTime) / 1000.0;
  
  // Turn off all LEDs initially (Test Case 4a: All OFF after confirmation)
  turnOffAllLEDs();
  
  // First verify user with actual ultrasonic duration
  if (verifyUser(destination, ultrasonicDuration)) {
    // Then request ride
    if (requestRide(destination)) {
      rideRequested = true;
      pullerAssigned = false;
      acknowledgeSound();
      oledShow("Requesting", "Ride...");
    } else {
      errorSound();
      oledShow("Request", "Failed");
      delay(2000);
    }
  } else {
    errorSound();
    oledShow("Auth", "Failed");
    delay(2000);
  }
}

void rejectReq() {
  Serial.println("Reject Req");
  resetRideState();
  oledShow("Cancelled", "");
  delay(1000);
}

// Sounds
void acknowledgeSound() { buzzer.sound(800, 100); }
void errorSound() { buzzer.sound(400, 300); }

// SETUP
void setup() {
  // Button pins
  pinMode(11, INPUT_PULLDOWN); // Red (Reject)
  pinMode(12, INPUT_PULLDOWN); // Green (Accept)

  // LED pins (Test Case 4 Requirements)
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_YELLOW_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  turnOffAllLEDs(); // Start with all LEDs OFF

  Serial.begin(115200);
  delay(250);

  display.begin(i2c_Address, true);
  display.display();
  delay(2000);
  oledShow("Welcome", "");
  delay(1000);
  
  // Connect to WiFi
  connectWiFi();
}

// LOOP
void loop() {

  String selection = getSelection();
  bool authRaw = getAuth();  // raw LDR read

  // ---------------------------------------------------------
  // Persistent Authentication Logic + Ultrasonic Presence Tracking
  // ---------------------------------------------------------
  if (selection != "None") {
    // If user is present (even in deadzone) and lighting OK → store auth
    if (authRaw) {
      authState = true;
    }
    
    // Track presence for ultrasonic validation (Test Case 1: >=3 seconds)
    validatePresence(selection);
  } else {
    // Reset auth ONLY when user fully leaves
    authState = false;
    presenceDetected = false; // Reset presence tracking
    
    // Reset ride state when user leaves
    if (rideRequested) {
      resetRideState();
      display.clearDisplay();
      display.display();
    }
  }
  // ---------------------------------------------------------

  Serial.print("Selection: ");
  Serial.println(selection);
  Serial.print("AuthState: ");
  Serial.println(authState);
  Serial.print("RideRequested: ");
  Serial.println(rideRequested);
  
  // Log presence tracking status
  if (presenceDetected) {
    unsigned long duration = millis() - presenceStartTime;
    Serial.print("Presence Duration: ");
    Serial.print(duration);
    Serial.print(" ms (Need ");
    Serial.print(PRESENCE_THRESHOLD);
    Serial.println(" ms)");
  }

  // Poll ride status if ride is active
  if (rideRequested && (millis() - lastPollTime >= POLL_INTERVAL)) {
    pollRideStatus();
    lastPollTime = millis();
  }

  // If we're in an active ride state, skip normal location selection UI
  if (rideRequested && pullerAssigned) {
    // Keep showing "Puller" status
    // The pollRideStatus function handles display updates
    previousSelection = selection;
    delay(100);
    return;
  }

  if (selection == "None" && previousSelection != "None") {
    display.clearDisplay();
    display.display();
  }

  if (selection == "MP") {
    errorSound();
    if (previousSelection != "MP") {
      oledShow("Multiple", "Persons");
    }
    errorMode = true;
  }

  else {
    if (errorMode) errorMode = false;

    bool isValid =
      (selection == "Pahartoli" ||
       selection == "Noapara"  ||
       selection == "Raojan");

    // New VALID selection (only show if not in ride request mode)
    if (!rideRequested && (previousSelection == "None" || previousSelection == "Deadzone") && isValid) {
      acknowledgeSound();
      oledShow("Selected", selection);
    }

    // Moving between zones (only show if not in ride request mode)
    else if (!rideRequested && isValid &&
             previousSelection != selection &&
             (previousSelection == "Pahartoli" ||
              previousSelection == "Noapara" ||
              previousSelection == "Raojan")) {
      acknowledgeSound();
      oledShow("Selection", selection);
    }

    // Buttons allowed ONLY if:
    // 1. Valid selection
    // 2. Persistent auth (LDR) is TRUE
    // 3. Presence detected for >= 3 seconds (Test Case 1)
    // 4. Not already requesting a ride
    bool presenceValid = validatePresence(selection);
    
    if (isValid && authState && presenceValid && !rideRequested) {
      if (digitalRead(12) == HIGH) {
        acceptReq();
        delay(500); // Debounce
      }
      if (digitalRead(11) == HIGH) {
        rejectReq();
        delay(500); // Debounce
      }
    } else if (isValid && authState && !presenceValid && !rideRequested) {
      // Show user they need to wait for 3 seconds
      unsigned long remaining = PRESENCE_THRESHOLD - (millis() - presenceStartTime);
      if (remaining > 0 && remaining < PRESENCE_THRESHOLD) {
        // Only show this message once per second
        static unsigned long lastWarnTime = 0;
        if (millis() - lastWarnTime > 1000) {
          Serial.print("Wait for presence validation: ");
          Serial.print(remaining / 1000.0);
          Serial.println("s remaining");
          lastWarnTime = millis();
        }
      }
    }
  }

  previousSelection = selection;
  delay(100);
}
