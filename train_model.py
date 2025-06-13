import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import joblib
import os
from datetime import datetime

class EnhancedLSTM(nn.Module):
    def __init__(self, input_size):
        super(EnhancedLSTM, self).__init__()
        self.input_size = input_size
        self.lstm = nn.LSTM(input_size, 128, 2, batch_first=True)
        
        # Multiple prediction heads
        self.pollution_head = nn.Linear(128, 1)  # General pollution
        self.explosion_head = nn.Linear(128, 1)  # Explosion risk
        self.gas_leak_head = nn.Linear(128, 1)  # Gas leak risk
        
        # Attention mechanism for parameter relationships
        self.attention = nn.MultiheadAttention(128, 4)
        
    def forward(self, x):
        # Reshape input for LSTM if necessary
        if len(x.shape) == 2:
            x = x.unsqueeze(1)
            
        lstm_out, _ = self.lstm(x)
        
        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Multiple risk predictions
        pollution_risk = torch.sigmoid(self.pollution_head(attn_out[:, -1]))
        explosion_risk = torch.sigmoid(self.explosion_head(attn_out[:, -1]))
        gas_leak_risk = torch.sigmoid(self.gas_leak_head(attn_out[:, -1]))
        
        return {
            'pollution_risk': pollution_risk,
            'explosion_risk': explosion_risk,
            'gas_leak_risk': gas_leak_risk
        }

class PollutionDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def load_and_preprocess_data():
    # Load the dataset
    df = pd.read_csv('dataset/pollution_dataset.csv')
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Create features for each pollutant
    pivot_df = df.pivot_table(
        index=['date', 'city', 'coordinateNumber'],
        columns='nameImpurity',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Fill missing values with 0
    pivot_df = pivot_df.fillna(0)
    
    # Add synthetic explosion-related features (for demonstration)
    pivot_df['Methane'] = np.random.uniform(2000, 6000, len(pivot_df))
    pivot_df['Hydrogen'] = np.random.uniform(2000, 5000, len(pivot_df))
    pivot_df['Temperature'] = np.random.uniform(20, 70, len(pivot_df))
    pivot_df['Pressure'] = np.random.uniform(1.0, 2.5, len(pivot_df))
    pivot_df['Oxygen_Level'] = np.random.uniform(19.5, 25.0, len(pivot_df))
    pivot_df['VOC'] = np.random.uniform(50, 150, len(pivot_df))
    
    # Create target variables
    pollutant_columns = pivot_df.columns[3:8]  # Original pollutants
    new_sensor_columns = ['Methane', 'Hydrogen', 'Temperature', 'Pressure', 'Oxygen_Level', 'VOC']
    
    # Calculate different risk levels
    pivot_df['pollution_level'] = pivot_df[pollutant_columns].mean(axis=1)
    pivot_df['explosion_risk'] = (
        (pivot_df['Methane'] > 5000).astype(float) * 0.4 +
        (pivot_df['Temperature'] > 60).astype(float) * 0.3 +
        (pivot_df['Pressure'] > 2.0).astype(float) * 0.3
    )
    pivot_df['gas_leak_risk'] = (
        (pivot_df['Methane'] > 4500).astype(float) * 0.5 +
        (pivot_df['VOC'] > 100).astype(float) * 0.5
    )
    
    # Create features
    pivot_df['month'] = pivot_df['date'].dt.month
    pivot_df['day'] = pivot_df['date'].dt.day
    pivot_df['day_of_week'] = pivot_df['date'].dt.dayofweek
    
    # Encode categorical variables
    le = LabelEncoder()
    pivot_df['city_encoded'] = le.fit_transform(pivot_df['city'])
    
    # Save label encoder
    os.makedirs('models', exist_ok=True)
    joblib.dump(le, 'models/city_encoder.pkl')
    
    # Select features for training
    feature_columns = list(pollutant_columns) + new_sensor_columns + ['month', 'day', 'day_of_week', 'city_encoded']
    X = pivot_df[feature_columns].values
    y = np.column_stack([
        pivot_df['pollution_level'].values,
        pivot_df['explosion_risk'].values,
        pivot_df['gas_leak_risk'].values
    ])
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale the features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save the scaler and feature columns for later use
    joblib.dump(scaler, 'models/scaler.pkl')
    joblib.dump(feature_columns, 'models/feature_columns.pkl')
    
    return X_train_scaled, X_test_scaled, y_train, y_test, feature_columns

def train_model():
    # Load and preprocess data
    X_train, X_test, y_train, y_test, feature_columns = load_and_preprocess_data()
    
    # Create datasets and dataloaders
    train_dataset = PollutionDataset(X_train, y_train)
    test_dataset = PollutionDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    
    # Initialize the model
    input_size = len(feature_columns)
    model = EnhancedLSTM(input_size)
    
    # Define loss function and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Training loop
    num_epochs = 50
    print("Starting training...")
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        for batch_X, batch_y in train_loader:
            # Forward pass
            outputs = model(batch_X)
            
            # Calculate loss for each prediction head
            loss_pollution = criterion(outputs['pollution_risk'], batch_y[:, 0].unsqueeze(1))
            loss_explosion = criterion(outputs['explosion_risk'], batch_y[:, 1].unsqueeze(1))
            loss_gas = criterion(outputs['gas_leak_risk'], batch_y[:, 2].unsqueeze(1))
            
            # Combined loss
            loss = loss_pollution + loss_explosion + loss_gas
            
            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        # Print training progress
        if (epoch + 1) % 5 == 0:
            print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss/len(train_loader):.4f}')
    
    # Evaluate the model
    model.eval()
    total_loss = 0
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            loss_pollution = criterion(outputs['pollution_risk'], batch_y[:, 0].unsqueeze(1))
            loss_explosion = criterion(outputs['explosion_risk'], batch_y[:, 1].unsqueeze(1))
            loss_gas = criterion(outputs['gas_leak_risk'], batch_y[:, 2].unsqueeze(1))
            total_loss += (loss_pollution + loss_explosion + loss_gas).item()
    
    mse = total_loss / len(test_loader)
    print(f'\nTest MSE: {mse:.4f}')
    print(f'Test RMSE: {np.sqrt(mse):.4f}')
    
    # Save the model
    torch.save(model.state_dict(), 'models/pollution_model.pth')
    
    return model

if __name__ == '__main__':
    train_model() 