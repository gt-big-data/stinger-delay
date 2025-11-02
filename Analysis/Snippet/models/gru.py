import torch
import torch.nn as nn


class GRU(nn.Module):
    """GRU model for traffic prediction"""

    def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
        super(GRU, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # GRU layers
        self.gru = nn.GRU(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )

        # Output layer
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x shape: (batch_size, seq_length, input_size)

        # GRU output
        gru_out, _ = self.gru(x)

        # Use the last output
        last_output = gru_out[:, -1, :]

        # Prediction
        output = self.fc(last_output)

        return output
