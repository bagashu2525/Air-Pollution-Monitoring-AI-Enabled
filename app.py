from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import numpy as np
import torch
from train_model import EnhancedLSTM
import joblib
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load the trained model and preprocessing objects
feature_columns = joblib.load('models/feature_columns.pkl')
model = EnhancedLSTM(input_size=len(feature_columns))
model.load_state_dict(torch.load('models/pollution_model.pth'))
model.eval()

scaler = joblib.load('models/scaler.pkl')
city_encoder = joblib.load('models/city_encoder.pkl')

# Define threshold values for different parameters
THRESHOLDS = {
    # Original pollutants
    'Suspended Particles': 0.15,    # mg/m³
    'Sulfur Dioxide': 0.05,        # mg/m³
    'Carbon Monoxide': 3.0,        # mg/m³
    'Nitrogen Dioxide': 0.085,     # mg/m³
    'Sulfates': 0.025,             # mg/m³
    
    # New explosion-related parameters
    'Methane': 5000,               # ppm
    'Hydrogen': 4000,              # ppm
    'Temperature': 60,             # °C
    'Pressure': 2.0,               # bar
    'Oxygen_Level': 23.5,          # %
    'VOC': 100                     # ppm
}

# Define risk levels
RISK_LEVELS = {
    'NORMAL': 0,
    'ATTENTION': 1,
    'WARNING': 2,
    'DANGER': 3,
    'IMMEDIATE_EVAC': 4
}

# Store the latest sensor data
latest_sensor_data = None

def get_recommended_actions(risk_level):
    actions = {
        RISK_LEVELS['NORMAL']: [
            "Continue normal monitoring",
            "Maintain regular safety checks"
        ],
        RISK_LEVELS['ATTENTION']: [
            "Increase monitoring frequency",
            "Check ventilation systems",
            "Notify shift supervisor"
        ],
        RISK_LEVELS['WARNING']: [
            "Activate additional ventilation",
            "Restrict non-essential personnel",
            "Prepare emergency response team",
            "Begin equipment safety checks"
        ],
        RISK_LEVELS['DANGER']: [
            "Initiate emergency protocols",
            "Evacuate non-essential personnel",
            "Contact emergency response team",
            "Shutdown non-critical operations"
        ],
        RISK_LEVELS['IMMEDIATE_EVAC']: [
            "IMMEDIATE EVACUATION REQUIRED",
            "Sound emergency alarms",
            "Contact emergency services",
            "Initiate emergency shutdown procedures"
        ]
    }
    return actions.get(risk_level, actions[RISK_LEVELS['NORMAL']])

def check_thresholds(data):
    alerts = []
    for key, value in data.items():
        if key in THRESHOLDS and value > THRESHOLDS[key]:
            alerts.append({
                'parameter': key,
                'value': value,
                'threshold': THRESHOLDS[key],
                'timestamp': datetime.now().isoformat()
            })
    return alerts

def analyze_explosion_risk(data):
    risks = []
    
    # Check for explosive gas mixtures
    if data.get('Methane', 0) > 0.1 * THRESHOLDS['Methane']:
        if data.get('Oxygen_Level', 21) > 19.5:  # Sufficient oxygen for combustion
            risks.append({
                'type': 'GAS_MIXTURE',
                'severity': 'HIGH',
                'description': 'Potentially explosive gas mixture detected'
            })
    
    # Check for temperature-pressure combination
    if data.get('Temperature', 0) > THRESHOLDS['Temperature'] * 0.8:
        if data.get('Pressure', 1.0) > THRESHOLDS['Pressure'] * 0.9:
            risks.append({
                'type': 'TEMP_PRESSURE',
                'severity': 'CRITICAL',
                'description': 'Dangerous temperature-pressure combination'
            })
    
    return risks

def prepare_model_input(data):
    # Create a feature vector matching the training data structure
    current_date = datetime.now()
    
    # Initialize feature vector with zeros
    features = {col: 0 for col in feature_columns}
    
    # Update pollutant values and explosion parameters
    for category in ['pollutants', 'explosion_parameters']:
        if category in data:
            for param, value in data[category].items():
                if param in features:
                    features[param] = value
    
    # Update temporal features
    features['month'] = current_date.month
    features['day'] = current_date.day
    features['day_of_week'] = current_date.weekday()
    
    # Update city encoding - handle unknown cities gracefully
    try:
        features['city_encoded'] = city_encoder.transform([data['city']])[0]
    except:
        # If city is unknown, use 0 as default encoding
        features['city_encoded'] = 0
    
    # Convert to array in the correct order
    feature_array = np.array([[features[col] for col in feature_columns]])
    return feature_array

def determine_risk_level(predictions, alerts, explosion_risks):
    risk_level = RISK_LEVELS['NORMAL']
    
    # Check predictions
    if predictions['explosion_risk'] > 0.7 or predictions['gas_leak_risk'] > 0.7:
        risk_level = max(risk_level, RISK_LEVELS['DANGER'])
    elif predictions['explosion_risk'] > 0.4 or predictions['gas_leak_risk'] > 0.4:
        risk_level = max(risk_level, RISK_LEVELS['WARNING'])
    
    # Check alerts
    if len(alerts) > 2:
        risk_level = max(risk_level, RISK_LEVELS['WARNING'])
    elif len(alerts) > 0:
        risk_level = max(risk_level, RISK_LEVELS['ATTENTION'])
    
    # Check explosion risks
    for risk in explosion_risks:
        if risk['severity'] == 'CRITICAL':
            risk_level = RISK_LEVELS['IMMEDIATE_EVAC']
        elif risk['severity'] == 'HIGH':
            risk_level = max(risk_level, RISK_LEVELS['DANGER'])
    
    return risk_level

@app.route('/api/sensor-data', methods=['GET', 'POST'])
def receive_sensor_data():
    global latest_sensor_data
    
    if request.method == 'POST':
        data = request.json
        
        # Prepare data for prediction
        input_data = prepare_model_input(data)
        input_scaled = scaler.transform(input_data)
        input_tensor = torch.FloatTensor(input_scaled)
        
        # Make predictions
        with torch.no_grad():
            predictions = model(input_tensor)
            predictions = {k: v.item() for k, v in predictions.items()}
        
        # Check for threshold violations and risks
        alerts = check_thresholds(data.get('pollutants', {}))
        explosion_risks = analyze_explosion_risk(data.get('explosion_parameters', {}))
        
        # Determine overall risk level
        risk_level = determine_risk_level(predictions, alerts, explosion_risks)
        
        # Prepare response
        response = {
            'timestamp': datetime.now().isoformat(),
            'pollutants': data.get('pollutants', {}),
            'explosion_parameters': data.get('explosion_parameters', {}),
            'predictions': predictions,
            'alerts': alerts,
            'explosion_risks': explosion_risks,
            'risk_level': risk_level,
            'risk_status': list(RISK_LEVELS.keys())[list(RISK_LEVELS.values()).index(risk_level)],
            'recommended_actions': get_recommended_actions(risk_level)
        }
        
        # Store the latest data
        latest_sensor_data = response
        
        # Emit real-time update to connected clients
        socketio.emit('sensor_update', response)
        
        return jsonify(response)
    else:  # GET request
        if latest_sensor_data is None:
            return jsonify({'error': 'No sensor data available yet'}), 404
        return jsonify(latest_sensor_data)

@app.route('/api/thresholds', methods=['GET'])
def get_thresholds():
    return jsonify(THRESHOLDS)

# Keep the first function as is
@app.route('/api/thresholds', methods=['POST'])
def update_thresholds():
    new_thresholds = request.json
    THRESHOLDS.update(new_thresholds)
    return jsonify(THRESHOLDS)

# Rename the second function
@app.route('/api/admin/thresholds', methods=['POST'])
def update_admin_thresholds():  # Changed function name here
    # In a real app, you would save these to a database
    thresholds = request.json
    # Save thresholds to your database here
    return jsonify({'success': True})

@app.route('/api/admin/settings', methods=['GET'])
def get_admin_settings():
    # Return current thresholds and actions
    return jsonify({
        'thresholds': {
            'CO': 9.0,
            'NO2': 0.1,
            'PM2.5': 35.0,
            'PM10': 150.0,
            'O3': 0.07,
            'SO2': 0.075,
            'Temperature': 35.0,
            'Humidity': 80.0,
            'Pressure': 1030.0,
        },
        'recommended_actions': [
            {
                'title': 'Evacuate Area',
                'description': 'Clear all personnel from the affected zone immediately',
                'priority': 'HIGH'
            },
            {
                'title': 'Increase Ventilation',
                'description': 'Activate emergency ventilation systems',
                'priority': 'MEDIUM'
            },
            {
                'title': 'Monitor Levels',
                'description': 'Continue monitoring pollutant levels at 5-minute intervals',
                'priority': 'LOW'
            }
        ]
    })

@app.route('/api/admin/actions', methods=['POST'])
def update_actions():
    data = request.json
    action = data.get('action')
    index = data.get('index')
    # Save action to your database here
    return jsonify({'success': True})

@app.route('/api/admin/actions/<int:index>', methods=['DELETE'])
def delete_action(index):
    # Delete action from your database here
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)