# --------------------------
# Data Handling
# --------------------------


#def preprocess_data(df, feature_cols, target_col):
    # normalizing/ numeritizing categorical data


#def split_data(X, y, test_size=0.2, val_size=0.1):
    # splitting data into test, train, and val

"""
    Splits your sequence data into train, validation, and test sets.

    Inputs:
    - X, y: arrays from make_lstm_sequences()
    - train_ratio: % of data to use for training (default 70%)
    - val_ratio: % of data to use for validation (default 15%)
                 → the rest (15%) automatically becomes test data.

    Outputs:
    - X_train, y_train
    - X_val, y_val
    - X_test, y_test

"""
    
def split_lstm_data(X, y, train_ratio=0.7, val_ratio=0.15):


    n = len(X)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    X_train, y_train = X[:train_end], y[:train_end]
    X_val, y_val = X[train_end:val_end], y[train_end:val_end]
    X_test, y_test = X[val_end:], y[val_end:]

    return X_train, y_train, X_val, y_val, X_test, y_test





#def create_sequences(X, y, seq_length):
    #time based sequences (not for dummy data)
"""
Turns your DataFrame into LSTM-ready sequences.

Inputs:
- df: your pandas DataFrame.
      ⚠️ The last column should be the target you want to predict.
      All other columns are treated as input features.
      Make sure df is sorted by time (oldest → newest).
- steps: how many past rows (time steps) to include in each sequence.
         e.g., steps = 24 uses the last 24 hours/days/etc. to predict the next.

Outputs:
- X: NumPy array of shape (num_samples, steps, num_features)
     → the rolling windows of input features.
- y: NumPy array of shape (num_samples,)
     → the corresponding target values.
"""


def create_sequences(df, steps):
    X, y = [], []
    values = df.values  # convert DataFrame to NumPy array

    for i in range(len(values) - steps):
        # Take the past `steps` rows of all columns except the last (features)
        X.append(values[i:i+steps, :-1])

        # Take the target value at the next time step (last column)
        y.append(values[i+steps, -1])

    return np.array(X), np.array(y)




#def make_lstm_model(seq_length, n_features):


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense

def make_lstm_model(seq_length, n_features):
    """
    Very simple LSTM model builder.
    seq_length  = number of time steps
    n_features  = number of input features per step
    """
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(seq_length, n_features)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25, activation='relu'),
        Dense(1)
    ])

    model.compile(optimizer='adam', loss='mse')
    return model



#def train_lstm_model(model, x_train, y_train, x_test, y_test, epochs=60, batch_size=32,verbose=1):

"""
Train an LSTM model and evaluate on validation data.

Parameters
----------
model : keras.Model
    LSTM model from make_lstm_model().
X_train, y_train : np.ndarray
    Training data and labels.
X_val, y_val : np.ndarray
    Validation / test data and labels.
epochs : int
    Number of training epochs.
batch_size : int
    Batch size for training.
verbose : int
    Keras verbosity level (0, 1, or 2).

Returns
-------
history : keras.callbacks.History
    Training history object.
y_pred : np.ndarray
    Predictions on X_val.
rmse : float
    RMSE on validation labels (y_val).
"""


def train_lstm_model(model,
                     X_train, y_train,
                     X_val, y_val,
                     epochs=60,
                     batch_size=32,
                     verbose=1):


    # Train the model
    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_val, y_val),
        verbose=verbose
    )

    # Predict and compute RMSE
    y_pred = model.predict(X_val)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    print("Validation RMSE:", rmse)

    return history, y_pred, rmse





# --------------------------
# Visualization Helpers
# --------------------------

#def visualizing (train_losses, val_losses=None):
    #plotting data