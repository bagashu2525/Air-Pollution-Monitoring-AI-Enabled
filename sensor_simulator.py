import random
import time
import requests
import json
from datetime import datetime

# Flask server URL
FLASK_SERVER = "http://localhost:5000"

# Base values and variation ranges for each parameter
SENSOR_RANGES = {
    "pollutants": {
        "Suspended Particles": {"base": 0.15, "variation": 0.05},  # mg/m³
        "Sulfur Dioxide": {"base": 0.05, "variation": 0.02},      # mg/m³
        "Carbon Monoxide": {"base": 3.0, "variation": 0.5},       # mg/m³
        "Nitrogen Dioxide": {"base": 0.085, "variation": 0.02},   # mg/m³
        "Sulfates": {"base": 0.025, "variation": 0.01}            # mg/m³
    },
    "explosion_parameters": {
        "Methane": {"base": 4500, "variation": 500},     # ppm
        "Hydrogen": {"base": 3500, "variation": 400},    # ppm
        "Temperature": {"base": 25, "variation": 5},     # °C
        "Pressure": {"base": 1.5, "variation": 0.2},     # bar
        "Oxygen_Level": {"base": 21.0, "variation": 0.5}, # %
        "VOC": {"base": 100, "variation": 20}            # ppm
    }
}

def generate_varying_value(base, variation):
    """Generate a value that varies around a base value"""
    return round(base + random.uniform(-variation, variation), 3)

def generate_sensor_data():
    """Generate simulated sensor data with realistic variations"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "pollutants": {},
        "explosion_parameters": {},
        "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])
    }
    
    # Generate pollutant values
    for pollutant, range_info in SENSOR_RANGES["pollutants"].items():
        data["pollutants"][pollutant] = generate_varying_value(
            range_info["base"], 
            range_info["variation"]
        )
    
    # Generate explosion parameter values
    for param, range_info in SENSOR_RANGES["explosion_parameters"].items():
        data["explosion_parameters"][param] = generate_varying_value(
            range_info["base"], 
            range_info["variation"]
        )
    
    # Occasionally generate a spike in values (10% chance)
    if random.random() < 0.1:
        spike_param = random.choice(list(data["pollutants"].keys()))
        data["pollutants"][spike_param] *= 2  # Double the value
    
    return data

def send_data_to_server(data):
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
    print("Starting sensor data simulation...")
    print(f"Sending data to: {FLASK_SERVER}")
    
    try:
        while True:
            # Generate new sensor data
            sensor_data = generate_sensor_data()
            
            # Print the data being sent
            print("\nGenerated Sensor Data:")
            print(json.dumps(sensor_data, indent=2))
            
            # Send data to server
            send_data_to_server(sensor_data)
            
            # Wait for 2 seconds before next reading
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 