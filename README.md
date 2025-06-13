# Industrial Pollution Monitoring and Prediction System

This project implements an IoT-based industrial pollution monitoring system with real-time alerts and AI-powered prediction capabilities.

## Features

- Real-time monitoring of multiple pollution parameters
- AI-powered prediction of pollution levels and potential hazards
- Automatic alerts when thresholds are exceeded
- RESTful API for data collection and monitoring
- Real-time updates using WebSocket
- Simulated IoT sensor data for testing

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Train the AI model:
```bash
python train_model.py
```

3. Start the Flask server:
```bash
python app.py
```

4. In a separate terminal, run the sensor simulator:
```bash
python sensor_simulator.py
```

## System Architecture

- `train_model.py`: Trains the LSTM-based neural network for pollution prediction
- `app.py`: Flask application providing the REST API and WebSocket server
- `sensor_simulator.py`: Simulates IoT sensor data for testing

## API Endpoints

- `POST /api/sensor-data`: Submit new sensor readings
- `GET /api/thresholds`: Get current threshold values
- `POST /api/thresholds`: Update threshold values

## Monitored Parameters

- CO2 (ppm)
- CO (ppm)
- NO2 (ppb)
- PM2.5 (µg/m³)
- Temperature (°C)
- Humidity (%)
- Pressure (hPa)

## Default Threshold Values

- CO2: 5000 ppm
- CO: 50 ppm
- NO2: 100 ppb
- PM2.5: 35 µg/m³
- Temperature: 40°C

## Real-time Alerts

The system will generate alerts when:
1. Any parameter exceeds its threshold value
2. The AI model predicts a high probability of hazardous conditions

## WebSocket Events

- `sensor_update`: Real-time updates of sensor data and predictions

## Future Improvements

1. Add more sensor parameters
2. Implement data visualization dashboard
3. Add user authentication
4. Implement mobile app notifications
5. Add historical data analysis 