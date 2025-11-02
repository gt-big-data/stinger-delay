import torch
import torch.nn as nn


class BiLSTM(nn.Module):
    """Bidirectional LSTM for traffic prediction"""

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
        super(BiLSTM, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=True
        )

        # Output layer (hidden_size * 2 because bidirectional)
        self.fc = nn.Linear(hidden_size * 2, 1)

    def forward(self, x):
        # x shape: (batch_size, seq_length, input_size)

        # LSTM output
        lstm_out, _ = self.lstm(x)

        # Use the last output
        last_output = lstm_out[:, -1, :]

        # Prediction
        output = self.fc(last_output)

        return output
