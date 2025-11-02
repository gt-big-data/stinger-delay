import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler


class TrafficDataset(Dataset):
    """Dataset for traffic sensor data"""

    def __init__(self, data, seq_length):
        self.data = torch.FloatTensor(data)
        self.seq_length = seq_length

    def __len__(self):
        return len(self.data) - self.seq_length

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_length]
        y = self.data[idx + self.seq_length]
        return x, y


def load_traffic_data(csv_path, sensor_id=0, seq_length=12, train_ratio=0.7, val_ratio=0.15, batch_size=32):
    """
    Load and preprocess traffic data

    Args:
        csv_path: Path to traffic.csv
        sensor_id: Which sensor to predict (0-861)
        seq_length: Number of timesteps to use for prediction
        train_ratio: Ratio of training data
        val_ratio: Ratio of validation data
        batch_size: Batch size for training

    Returns:
        train_loader, val_loader, test_loader, scaler
    """
    # Load data
    df = pd.read_csv(csv_path)

    # Extract sensor data (skip date column)
    sensor_data = df.iloc[:, sensor_id + 1].values.reshape(-1, 1)

    # Split data
    n = len(sensor_data)
    train_size = int(n * train_ratio)
    val_size = int(n * val_ratio)

    train_data = sensor_data[:train_size]
    val_data = sensor_data[train_size:train_size + val_size]
    test_data = sensor_data[train_size + val_size:]

    # Normalize using training data statistics
    scaler = StandardScaler()
    train_data = scaler.fit_transform(train_data)
    val_data = scaler.transform(val_data)
    test_data = scaler.transform(test_data)

    # Create datasets
    train_dataset = TrafficDataset(train_data, seq_length)
    val_dataset = TrafficDataset(val_data, seq_length)
    test_dataset = TrafficDataset(test_data, seq_length)

    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader, test_loader, scaler
