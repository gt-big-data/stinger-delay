import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# ========================================================================
# DATA GENERATION FUNCTIONS
# ========================================================================

def generate_synthetic_bus_data(n_samples=10000):
    """
    Generate synthetic bus delay prediction dataset.

    Parameters:
    -----------
    n_samples : int
        Number of samples to generate

    Returns:
    --------
    pd.DataFrame
        Synthetic dataset with features and target
    """
    np.random.seed(42)
    data = []

    for _ in range(n_samples):
        # Route and stop information
        route_id_idx = np.random.randint(0, 21)  # 0-20
        target_stop_idx = np.random.randint(0, 101)  # 0-100

        # Distance to target stop (0-5000 meters)
        distance_to_target_stop_m = np.random.uniform(100, 5000)

        # Time features
        time_of_day_min = np.random.randint(0, 1440)  # 0-1439 minutes
        day_of_week = np.random.randint(0, 7)  # 0=Mon, 6=Sun

        # Weather
        is_raining = np.random.choice([0, 1], p=[0.7, 0.3])  # 30% chance of rain

        # Current speed (meters/second)
        base_speed = np.random.uniform(5, 15)

        # Rush hour effects (6-9am, 4-7pm)
        hour = time_of_day_min // 60
        if (6 <= hour < 9) or (16 <= hour < 19):
            base_speed *= 0.7  # Slower during rush hour

        # Weather effects
        if is_raining:
            base_speed *= 0.85  # Slower in rain

        # Weekend effects
        if day_of_week >= 5:
            base_speed *= 1.1  # Slightly faster on weekends

        current_speed_mps = np.clip(base_speed, 0, 20)

        # Current delay (seconds)
        base_delay = np.random.normal(0, 300)

        if (6 <= hour < 9) or (16 <= hour < 19):
            base_delay += np.random.normal(300, 200)

        if is_raining:
            base_delay += np.random.normal(180, 120)

        current_delay_sec = np.clip(base_delay, -900, 1800)

        # Headway to previous bus (seconds)
        if (6 <= hour < 9) or (16 <= hour < 19):
            headway_to_prev_bus_sec = np.random.uniform(300, 900)  # 5-15 min
        else:
            headway_to_prev_bus_sec = np.random.uniform(600, 1800)  # 10-30 min

        # Calculate time to arrival (TARGET)
        base_tta = distance_to_target_stop_m / (current_speed_mps + 0.1)

        # Add realistic variation factors
        delay_propagation = current_delay_sec * 0.5
        num_stops = int(distance_to_target_stop_m / 500)
        stop_time = num_stops * np.random.uniform(20, 40)
        traffic_delays = np.random.uniform(0, 60) * (distance_to_target_stop_m / 1000)
        weather_delay = 0
        if is_raining:
            weather_delay = np.random.uniform(30, 90)
        bunching_delay = 0
        if headway_to_prev_bus_sec < 300:
            bunching_delay = np.random.uniform(30, 120)

        # Total time to arrival
        tta_sec = base_tta + delay_propagation + stop_time + traffic_delays + weather_delay + bunching_delay
        tta_sec += np.random.normal(0, 30)
        tta_sec = np.clip(tta_sec, 10, 3600)

        data.append({
            'route_id_idx': route_id_idx,
            'target_stop_idx': target_stop_idx,
            'distance_to_target_stop_m': round(distance_to_target_stop_m, 2),
            'current_speed_mps': round(current_speed_mps, 2),
            'time_of_day_min': time_of_day_min,
            'day_of_week': day_of_week,
            'current_delay_sec': round(current_delay_sec, 2),
            'is_raining': is_raining,
            'headway_to_prev_bus_sec': round(headway_to_prev_bus_sec, 2),
            'tta_sec': round(tta_sec, 2)
        })

    df = pd.DataFrame(data)
    return df


# ========================================================================
# FEATURE ENGINEERING FUNCTIONS
# ========================================================================

def create_time_features(df):
    """
    Decompose time_of_day_min into cyclical features.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with time_of_day_min column

    Returns:
    --------
    pd.DataFrame
        DataFrame with added time features
    """
    df = df.copy()

    # Extract hour and minute
    df['hour'] = df['time_of_day_min'] // 60
    df['minute'] = df['time_of_day_min'] % 60

    # Create cyclical features for time of day (0-1439 minutes)
    df['time_sin'] = np.sin(2 * np.pi * df['time_of_day_min'] / 1440)
    df['time_cos'] = np.cos(2 * np.pi * df['time_of_day_min'] / 1440)

    # Create cyclical features for hour
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    # Rush hour indicator
    df['is_rush_hour'] = ((df['hour'] >= 6) & (df['hour'] < 9) |
                          (df['hour'] >= 16) & (df['hour'] < 19)).astype(int)

    return df


def create_day_features(df):
    """
    Create features from day_of_week.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with day_of_week column

    Returns:
    --------
    pd.DataFrame
        DataFrame with added day features
    """
    df = df.copy()

    # Cyclical encoding for day of week
    df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

    # Weekend indicator
    df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

    return df


def create_interaction_features(df):
    """
    Create interaction features between variables.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with base features

    Returns:
    --------
    pd.DataFrame
        DataFrame with added interaction features
    """
    df = df.copy()

    # Speed and distance interaction
    df['speed_distance_ratio'] = df['current_speed_mps'] / (df['distance_to_target_stop_m'] / 1000 + 0.1)

    # Delay and distance interaction
    df['delay_per_km'] = df['current_delay_sec'] / (df['distance_to_target_stop_m'] / 1000 + 0.1)

    # Weather and speed interaction
    df['rain_speed_interaction'] = df['is_raining'] * df['current_speed_mps']

    # Rush hour and delay interaction
    if 'is_rush_hour' in df.columns:
        df['rush_delay_interaction'] = df['is_rush_hour'] * df['current_delay_sec']

    return df


def engineer_features(df):
    """
    Apply all feature engineering steps.

    Parameters:
    -----------
    df : pd.DataFrame
        Raw DataFrame

    Returns:
    --------
    pd.DataFrame
        DataFrame with all engineered features
    """
    df = create_time_features(df)
    df = create_day_features(df)
    df = create_interaction_features(df)

    return df


# ========================================================================
# DATA PIPELINE FUNCTIONS
# ========================================================================

def prepare_data_for_xgboost(df, target_col='tta_sec', test_size=0.2, random_state=42):
    """
    Prepare data for XGBoost model training.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with all features
    target_col : str
        Name of target column
    test_size : float
        Fraction of data to use for testing
    random_state : int
        Random seed for reproducibility

    Returns:
    --------
    tuple
        (X_train, X_test, y_train, y_test, feature_names)
    """
    from sklearn.model_selection import train_test_split

    # Separate features and target
    if target_col in df.columns:
        y = df[target_col]
        X = df.drop(columns=[target_col])
    else:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame")

    # Get feature names
    feature_names = X.columns.tolist()

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    return X_train, X_test, y_train, y_test, feature_names


def scale_features(X_train, X_test, feature_cols=None):
    """
    Scale numerical features using StandardScaler.

    Parameters:
    -----------
    X_train : pd.DataFrame
        Training features
    X_test : pd.DataFrame
        Test features
    feature_cols : list, optional
        List of columns to scale. If None, scales all columns.

    Returns:
    --------
    tuple
        (X_train_scaled, X_test_scaled, scaler)
    """
    scaler = StandardScaler()

    if feature_cols is None:
        feature_cols = X_train.columns.tolist()

    X_train_scaled = X_train.copy()
    X_test_scaled = X_test.copy()

    X_train_scaled[feature_cols] = scaler.fit_transform(X_train[feature_cols])
    X_test_scaled[feature_cols] = scaler.transform(X_test[feature_cols])

    return X_train_scaled, X_test_scaled, scaler


# ========================================================================
# EVALUATION FUNCTIONS
# ========================================================================

def evaluate_model(y_true, y_pred, model_name="Model"):
    """
    Calculate and print evaluation metrics.

    Parameters:
    -----------
    y_true : array-like
        True values
    y_pred : array-like
        Predicted values
    model_name : str
        Name of the model for display

    Returns:
    --------
    dict
        Dictionary of metrics
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    print(f"\n{model_name} Performance Metrics:")
    print("=" * 50)
    print(f"RMSE (Root Mean Squared Error): {rmse:.2f} seconds")
    print(f"MAE (Mean Absolute Error):      {mae:.2f} seconds")
    print(f"R² Score:                        {r2:.4f}")
    print("=" * 50)

    return {
        'rmse': rmse,
        'mae': mae,
        'r2': r2
    }


def plot_predictions(y_true, y_pred, model_name="Model", sample_size=500):
    """
    Plot true vs predicted values.

    Parameters:
    -----------
    y_true : array-like
        True values
    y_pred : array-like
        Predicted values
    model_name : str
        Name of the model for display
    sample_size : int
        Number of samples to plot (for visualization clarity)
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Sample for visualization if dataset is large
    if len(y_true) > sample_size:
        indices = np.random.choice(len(y_true), sample_size, replace=False)
        y_true_sample = y_true.iloc[indices] if hasattr(y_true, 'iloc') else y_true[indices]
        y_pred_sample = y_pred[indices]
    else:
        y_true_sample = y_true
        y_pred_sample = y_pred

    # Scatter plot
    axes[0].scatter(y_true_sample, y_pred_sample, alpha=0.5, s=20)
    axes[0].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()],
                 'r--', lw=2, label='Perfect Prediction')
    axes[0].set_xlabel('True TTA (seconds)', fontsize=12)
    axes[0].set_ylabel('Predicted TTA (seconds)', fontsize=12)
    axes[0].set_title(f'{model_name}: True vs Predicted', fontsize=14)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Residual plot
    residuals = y_true_sample - y_pred_sample if hasattr(y_true_sample, '__sub__') else y_true_sample - y_pred_sample
    axes[1].scatter(y_pred_sample, residuals, alpha=0.5, s=20)
    axes[1].axhline(y=0, color='r', linestyle='--', lw=2)
    axes[1].set_xlabel('Predicted TTA (seconds)', fontsize=12)
    axes[1].set_ylabel('Residuals (seconds)', fontsize=12)
    axes[1].set_title(f'{model_name}: Residual Plot', fontsize=14)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def plot_feature_importance(model, feature_names, top_n=20):
    """
    Plot feature importance from XGBoost model.

    Parameters:
    -----------
    model : XGBoost model
        Trained XGBoost model
    feature_names : list
        List of feature names
    top_n : int
        Number of top features to display
    """
    importance = model.feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False).head(top_n)

    plt.figure(figsize=(10, 8))
    plt.barh(range(len(feature_importance_df)), feature_importance_df['importance'])
    plt.yticks(range(len(feature_importance_df)), feature_importance_df['feature'])
    plt.xlabel('Importance', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.title(f'Top {top_n} Feature Importances', fontsize=14)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()
