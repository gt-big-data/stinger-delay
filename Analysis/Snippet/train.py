import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from models.bilstm import BiLSTM
from models.gru import GRU
from utils.data_loader import load_traffic_data
import numpy as np
import matplotlib.pyplot as plt
import os


class MASELoss(nn.Module):
    """Mean Absolute Scaled Error Loss"""
    def __init__(self, train_data=None, epsilon=1e-8):
        super(MASELoss, self).__init__()
        self.epsilon = epsilon
        self.scale = None
        if train_data is not None:
            self.compute_scale(train_data)

    def compute_scale(self, train_data):
        """Compute the scaling factor from training data (naive forecast MAE)"""
        # train_data shape: (n_samples, seq_length, features)
        if isinstance(train_data, torch.Tensor):
            train_data = train_data.cpu().numpy()

        # Calculate MAE of naive forecast (using previous value as prediction)
        naive_errors = np.abs(np.diff(train_data.flatten()))
        self.scale = np.mean(naive_errors) + self.epsilon

    def forward(self, predictions, targets):
        """Calculate MASE"""
        mae = torch.mean(torch.abs(predictions - targets))

        if self.scale is None:
            # If scale not computed, use MAE of naive forecast on current batch
            if targets.shape[1] > 1:
                naive_errors = torch.abs(targets[:, 1:] - targets[:, :-1])
                scale = torch.mean(naive_errors) + self.epsilon
            else:
                # Fallback to MAE if only single timestep
                return mae
        else:
            scale = self.scale

        mase = mae / scale
        return mase


def train_epoch(model, train_loader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0

    for batch_x, batch_y in train_loader:
        batch_x = batch_x.to(device)
        batch_y = batch_y.to(device)

        # Forward pass
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(train_loader)


def validate(model, val_loader, criterion, device):
    """Validate the model"""
    model.eval()
    total_loss = 0

    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)

            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            total_loss += loss.item()

    return total_loss / len(val_loader)


def train_model(args):
    """Main training function"""
    # Set device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    # Load data
    print(f'Loading data for sensor {args.sensor_id}...')
    train_loader, val_loader, test_loader, scaler = load_traffic_data(
        csv_path=args.data_path,
        sensor_id=args.sensor_id,
        seq_length=args.seq_length,
        train_ratio=0.7,
        val_ratio=0.15,
        batch_size=args.batch_size
    )
    print(f'Data loaded. Train batches: {len(train_loader)}, Val batches: {len(val_loader)}, Test batches: {len(test_loader)}')

    # Initialize model
    if args.model == 'bilstm':
        model = BiLSTM(
            input_size=1,
            hidden_size=args.hidden_size,
            num_layers=args.num_layers,
            dropout=args.dropout
        ).to(device)
    elif args.model == 'gru':
        model = GRU(
            input_size=1,
            hidden_size=args.hidden_size,
            num_layers=args.num_layers,
            dropout=args.dropout
        ).to(device)
    else:
        raise ValueError(f"Unknown model: {args.model}")

    print(f'Model: {args.model}')
    print(f'Parameters: {sum(p.numel() for p in model.parameters())}')

    # Compute scaling factor for MASE from training data
    train_data = []
    for batch_x, _ in train_loader:
        train_data.append(batch_x.numpy())
    train_data = np.concatenate(train_data, axis=0)

    # Loss and optimizer
    criterion = MASELoss(train_data=train_data)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    # Training loop
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')

    print('Starting training...')
    for epoch in range(args.epochs):
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss = validate(model, val_loader, criterion, device)

        train_losses.append(train_loss)
        val_losses.append(val_loss)

        print(f'Epoch [{epoch + 1}/{args.epochs}], Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}')

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            os.makedirs('checkpoints', exist_ok=True)
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': val_loss,
                'scaler': scaler
            }, f'checkpoints/{args.model}_sensor{args.sensor_id}_best.pth')

    # Plot training history
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title(f'{args.model.upper()} Training History - Sensor {args.sensor_id}')
    plt.legend()
    plt.grid(True)
    os.makedirs('results', exist_ok=True)
    plt.savefig(f'results/{args.model}_sensor{args.sensor_id}_training.png')
    print(f'Training plot saved to results/{args.model}_sensor{args.sensor_id}_training.png')

    print(f'Training completed. Best validation loss: {best_val_loss:.6f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train traffic prediction model')
    parser.add_argument('--model', type=str, default='bilstm', choices=['bilstm', 'gru'],
                        help='Model type: bilstm or gru')
    parser.add_argument('--data_path', type=str, default='traffic.csv',
                        help='Path to traffic.csv')
    parser.add_argument('--sensor_id', type=int, default=0,
                        help='Sensor ID to predict (0-861)')
    parser.add_argument('--seq_length', type=int, default=12,
                        help='Sequence length for prediction')
    parser.add_argument('--hidden_size', type=int, default=64,
                        help='Hidden size of LSTM/GRU')
    parser.add_argument('--num_layers', type=int, default=2,
                        help='Number of LSTM/GRU layers')
    parser.add_argument('--dropout', type=float, default=0.2,
                        help='Dropout rate')
    parser.add_argument('--batch_size', type=int, default=32,
                        help='Batch size')
    parser.add_argument('--epochs', type=int, default=50,
                        help='Number of epochs')
    parser.add_argument('--lr', type=float, default=0.001,
                        help='Learning rate')

    args = parser.parse_args()
    train_model(args)
