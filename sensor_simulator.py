import requests
import time
import random
from datetime import datetime
import numpy as np

# API endpoint
API_URL = "http://localhost:5000/api/sensor-data"

def generate_sensor_data():
    """Generate simulated sensor data"""
    # Use only cities that were in the training data
    cities = ['New York']  # For now, we'll use just one city to avoid encoding issues
    
    # Generate regular pollutant data
    pollutants = {
        'Suspended Particles': round(random.uniform(0.05, 0.25), 4),
        'Sulfur Dioxide': round(random.uniform(0.02, 0.08), 4),
        'Carbon Monoxide': round(random.uniform(1.0, 4.0), 4),
        'Nitrogen Dioxide': round(random.uniform(0.04, 0.12), 4),
        'Sulfates': round(random.uniform(0.01, 0.04), 4)
    }
    
    # Generate explosion-related parameters with occasional dangerous values
    explosion_parameters = {
        'Methane': round(random.uniform(2000, 6000), 2),
        'Hydrogen': round(random.uniform(2000, 5000), 2),
        'Temperature': round(random.uniform(20, 70), 2),
        'Pressure': round(random.uniform(1.0, 2.5), 2),
        'Oxygen_Level': round(random.uniform(19.5, 25.0), 2),
        'VOC': round(random.uniform(50, 150), 2)
    }
    
    # Occasionally generate dangerous conditions (10% chance)
    if random.random() < 0.1:
        # Simulate a potentially dangerous situation
        danger_type = random.choice(['gas', 'temperature', 'pressure'])
        if danger_type == 'gas':
            explosion_parameters['Methane'] = round(random.uniform(5500, 7000), 2)  # High methane
            explosion_parameters['Oxygen_Level'] = round(random.uniform(20.5, 23.0), 2)  # Sufficient oxygen
        elif danger_type == 'temperature':
            explosion_parameters['Temperature'] = round(random.uniform(75, 90), 2)  # High temperature
        else:
            explosion_parameters['Pressure'] = round(random.uniform(2.8, 3.5), 2)  # High pressure
    
    return {
        'city': random.choice(cities),
        'pollutants': pollutants,
        'explosion_parameters': explosion_parameters,
        'timestamp': datetime.now().isoformat()
    }

def simulate_sensor():
    """Simulate sensor readings and send to API"""
    print("Starting sensor simulation...")
    print("Press Ctrl+C to stop the simulation.")
    print("\nMonitoring both pollution and explosion risks...")
    
    while True:
        try:
            # Generate sensor data
            data = generate_sensor_data()
            
            # Send data to API
            response = requests.post(API_URL, json=data)
            
            # Print response
            if response.status_code == 200:
                result = response.json()
                print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                print("\nPollutant Levels:")
                for pollutant, value in data['pollutants'].items():
                    print(f"- {pollutant}: {value:.4f} mg/m³")
                
                print("\nExplosion Parameters:")
                for param, value in data['explosion_parameters'].items():
                    unit = {
                        'Methane': 'ppm',
                        'Hydrogen': 'ppm',
                        'Temperature': '°C',
                        'Pressure': 'bar',
                        'Oxygen_Level': '%',
                        'VOC': 'ppm'
                    }.get(param, '')
                    print(f"- {param}: {value:.2f} {unit}")
                
                print("\nRisk Assessment:")
                print(f"Risk Level: {result['risk_status']}")
                print(f"Pollution Risk: {result['predictions']['pollution_risk']:.4f}")
                print(f"Explosion Risk: {result['predictions']['explosion_risk']:.4f}")
                print(f"Gas Leak Risk: {result['predictions']['gas_leak_risk']:.4f}")
                
                if result['alerts']:
                    print("\n⚠️ Parameter Alerts:")
                    for alert in result['alerts']:
                        print(f"- {alert['parameter']}: {alert['value']:.4f} (Threshold: {alert['threshold']})")
                
                if result['explosion_risks']:
                    print("\n🔥 Explosion Risks:")
                    for risk in result['explosion_risks']:
                        print(f"- {risk['type']}: {risk['severity']} - {risk['description']}")
                
                if result['recommended_actions']:
                    print("\n📋 Recommended Actions:")
                    for action in result['recommended_actions']:
                        print(f"- {action}")
                
                print("\n" + "="*50)
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        # Wait for 5 seconds before next reading
        time.sleep(5)

if __name__ == "__main__":
    simulate_sensor() 