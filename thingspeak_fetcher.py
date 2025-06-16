import requests
import time
import json
from datetime import datetime

# ThingSpeak settings
THINGSPEAK_API_KEY = "2YU9I0E8CK6OE0CG"
THINGSPEAK_CHANNEL_ID = "2990480"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json"

# Flask server settings
FLASK_SERVER = "http://localhost:5000"

# Field mappings for your ThingSpeak channel
FIELD_MAPPINGS = {
    "field1": "Temperature",      # DHT22
    "field2": "Humidity",         # DHT22
    "field3": "MQ135",           # Air Quality
    "field4": "MQ6",             # LNG
    "field5": "MQ2",             # LPG
    "field6": "MQ4",             # Methane
    "field7": "MQ7"              # CO
}

# Conversion factors for raw sensor values
CONVERSION_FACTORS = {
    "Temperature": 1.0,          # Already in °C
    "Humidity": 1.0,             # Already in %
    "MQ135": 0.001,            # Convert to mg/m³
    "MQ6": 0.0001,              # Convert to mg/m³
    "MQ2": 0.001,              # Convert to mg/m³
    "MQ4": 0.01,              # Convert to mg/m³
    "MQ7": 0.01               # Convert to mg/m³
}

def convert_sensor_value(raw_value, sensor_type):
    """Convert raw sensor value to appropriate unit"""
    if raw_value is None or raw_value == "":
        return 0.0
    return float(raw_value) * CONVERSION_FACTORS.get(sensor_type, 1.0)

def fetch_thingspeak_data():
    """Fetch latest data from ThingSpeak"""
    try:
        params = {
            "api_key": THINGSPEAK_API_KEY,
            "results": 1  # Get only the latest reading
        }
        
        response = requests.get(THINGSPEAK_URL, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data["feeds"]:
                feed = data["feeds"][0]
                
                # Print raw data for debugging
                print("\nRaw ThingSpeak Data:")
                for field, value in feed.items():
                    if field.startswith("field"):
                        print(f"{FIELD_MAPPINGS.get(field, field)}: {value}")
                
                # Convert and structure the data
                return {
                    "timestamp": feed["created_at"],
                    "pollutants": {
                        "Suspended Particles": convert_sensor_value(feed["field3"], "MQ135"),  # MQ135
                        "Sulfur Dioxide": convert_sensor_value(feed["field4"], "MQ6"),        # MQ6
                        "Carbon Monoxide": convert_sensor_value(feed["field7"], "MQ7"),       # MQ7
                        "Nitrogen Dioxide": convert_sensor_value(feed["field5"], "MQ2"),      # MQ2
                        "Sulfates": convert_sensor_value(feed["field6"], "MQ4")               # MQ4
                    },
                    "explosion_parameters": {
                        "Methane": convert_sensor_value(feed["field4"], "MQ6"),     # MQ6
                        "Hydrogen": convert_sensor_value(feed["field3"], "MQ135"),  # MQ135
                        "Temperature": float(feed["field1"] or 0),                 # DHT22
                        "Pressure": 1.0,                                           # Default
                        "Oxygen_Level": 21.0,                                      # Default
                        "VOC": convert_sensor_value(feed["field5"], "MQ2")         # MQ2
                    },
                    "city": "New York"  # Default city
                }
        return None
    except Exception as e:
        print(f"Error fetching ThingSpeak data: {e}")
        return None

def send_to_flask(data):
    """Send data to Flask server"""
    try:
        response = requests.post(
            f"{FLASK_SERVER}/api/sensor-data",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("Data sent successfully!")
            print("Server response:", response.json())
        else:
            print(f"Error sending data. Status code: {response.status_code}")
            print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")

def main():
    print("Starting ThingSpeak data fetcher...")
    print(f"Fetching data from ThingSpeak channel: {THINGSPEAK_CHANNEL_ID}")
    print(f"Sending data to: {FLASK_SERVER}")
    
    try:
        while True:
            # Fetch data from ThingSpeak
            thingspeak_data = fetch_thingspeak_data()
            
            if thingspeak_data:
                # Print the converted data being sent
                print("\nConverted Data for Flask:")
                print(json.dumps(thingspeak_data, indent=2))
                
                # Send data to Flask server
                send_to_flask(thingspeak_data)
            else:
                print("No data available from ThingSpeak")
            
            # Wait for 15 seconds before next fetch
            time.sleep(15)
            
    except KeyboardInterrupt:
        print("\nFetcher stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 