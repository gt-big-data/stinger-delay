import argparse
import torch
import numpy as np
import matplotlib.pyplot as plt
from models.bilstm import BiLSTM
from models.gru import GRU
from utils.data_loader import load_traffic_data
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import os


def evaluate_model(args):
    """Evaluate trained model on test set"""
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

    # Load checkpoint
    checkpoint_path = f'checkpoints/{args.model}_sensor{args.sensor_id}_best.pth'
    if not os.path.exists(checkpoint_path):
        print(f"Error: Checkpoint not found at {checkpoint_path}")
        print("Please train the model first using train.py")
        return

    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    scaler = checkpoint['scaler']
    print(f'Loaded checkpoint from epoch {checkpoint["epoch"]} with val loss {checkpoint["val_loss"]:.6f}')

    # Evaluate
    model.eval()
    predictions = []
    actuals = []

    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(device)
            outputs = model(batch_x)
            predictions.append(outputs.cpu().numpy())
            actuals.append(batch_y.numpy())

    # Concatenate all batches
    predictions = np.concatenate(predictions, axis=0)
    actuals = np.concatenate(actuals, axis=0)

    # Inverse transform to get original scale
    predictions = scaler.inverse_transform(predictions)
    actuals = scaler.inverse_transform(actuals)

    # Calculate metrics
    mse = mean_squared_error(actuals, predictions)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(actuals, predictions)
    r2 = r2_score(actuals, predictions)

    print('\n--- Test Set Metrics ---')
    print(f'MSE:  {mse:.6f}')
    print(f'RMSE: {rmse:.6f}')
    print(f'MAE:  {mae:.6f}')
    print(f'R2:   {r2:.6f}')

    # Plot predictions vs actuals
    plt.figure(figsize=(15, 6))

    # Plot 1: Time series comparison
    plt.subplot(1, 2, 1)
    n_samples = min(500, len(predictions))
    plt.plot(actuals[:n_samples], label='Actual', alpha=0.7)
    plt.plot(predictions[:n_samples], label='Predicted', alpha=0.7)
    plt.xlabel('Time Steps')
    plt.ylabel('Traffic Occupancy')
    plt.title(f'{args.model.upper()} - Predictions vs Actuals (First {n_samples} samples)')
    plt.legend()
    plt.grid(True)

    # Plot 2: Scatter plot
    plt.subplot(1, 2, 2)
    plt.scatter(actuals, predictions, alpha=0.5, s=10)
    min_val = min(actuals.min(), predictions.min())
    max_val = max(actuals.max(), predictions.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    plt.xlabel('Actual')
    plt.ylabel('Predicted')
    plt.title(f'{args.model.upper()} - Scatter Plot (R2={r2:.4f})')
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    os.makedirs('results', exist_ok=True)
    plt.savefig(f'results/{args.model}_sensor{args.sensor_id}_evaluation.png')
    print(f'\nEvaluation plot saved to results/{args.model}_sensor{args.sensor_id}_evaluation.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate traffic prediction model')
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

    args = parser.parse_args()
    evaluate_model(args)
