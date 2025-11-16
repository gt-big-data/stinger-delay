# XGBoost Bus Delay Prediction

This folder contains the XGBoost-based model for predicting bus arrival times (Time To Arrival - TTA) at target stops.

## Project Structure

```
XGBoost/
├── Stinger_XGboost.ipynb          # Main Jupyter notebook
├── utils.py                        # Utility functions for data generation, preprocessing, and evaluation
├── generate_synthetic_data.py     # Standalone script for data generation (optional)
├── dummy_data/
│   └── synthetic_bus_data.csv     # Generated synthetic dataset
└── README.md                       # This file
```

## Dataset Description

### Target Variable
- **tta_sec** (float): Time to arrival at the target stop in seconds
  - Formula: `tta_sec = t_arrival(target_stop) - snapshot_time`

### Features

#### Route and Stop Information
- **route_id_idx** (int): Numeric ID of the route (0-20)
- **target_stop_idx** (int): Numeric ID of the target stop (0-100)

#### Spatial Features
- **distance_to_target_stop_m** (float): Distance from bus to target stop along the route in meters (100-5000m)

#### Temporal Features
- **time_of_day_min** (int): Minutes since midnight at snapshot time (0-1439)
- **day_of_week** (int): Day of week (0=Monday, 6=Sunday)

#### Operational Features
- **current_speed_mps** (float): Current bus speed in meters/second (0-20)
- **current_delay_sec** (float): How late/early the bus is up to the current point (-900 to +1800 seconds)
  - Formula: `actual_elapsed_time - scheduled_elapsed_time`
- **headway_to_prev_bus_sec** (float): Time gap since the previous bus on the same route passed this point (0-3600 seconds)

#### Environmental Features
- **is_raining** (int): Simple weather flag (0=no rain, 1=rain)

### Engineered Features

The preprocessing pipeline creates additional features:

#### Time-based Features
- **hour**: Hour of day (0-23)
- **minute**: Minute within hour (0-59)
- **time_sin**: Cyclical encoding of time (sine component)
- **time_cos**: Cyclical encoding of time (cosine component)
- **hour_sin**: Cyclical encoding of hour (sine component)
- **hour_cos**: Cyclical encoding of hour (cosine component)
- **is_rush_hour**: Binary indicator for rush hour periods (6-9am, 4-7pm)

#### Day-based Features
- **day_sin**: Cyclical encoding of day of week (sine component)
- **day_cos**: Cyclical encoding of day of week (cosine component)
- **is_weekend**: Binary indicator for weekend (Saturday/Sunday)

#### Interaction Features
- **speed_distance_ratio**: Ratio of speed to distance
- **delay_per_km**: Current delay normalized by distance
- **rain_speed_interaction**: Interaction between rain and speed
- **rush_delay_interaction**: Interaction between rush hour and delay

## Workflow

### 1. Data Generation
The synthetic data is generated with realistic patterns:
- Rush hour effects (slower speeds, higher delays)
- Weather effects (rain causes slower speeds and delays)
- Weekend effects (slightly faster speeds)
- Bus bunching (short headways cause additional delays)
- Traffic signals and stop time (based on distance)

### 2. Feature Engineering
The raw features are decomposed and enriched:
- Cyclical encoding for temporal features (prevents discontinuity at midnight/week boundaries)
- Binary indicators for important time periods (rush hour, weekend)
- Interaction features to capture complex relationships

### 3. Model Training
XGBoost Regressor with optimized hyperparameters:
- **n_estimators**: 200 boosting rounds
- **max_depth**: 6 (tree depth)
- **learning_rate**: 0.1
- **subsample**: 0.8 (row sampling)
- **colsample_bytree**: 0.8 (column sampling)
- **L1/L2 regularization**: Prevents overfitting

### 4. Evaluation
Model performance is assessed using:
- **RMSE** (Root Mean Squared Error): Average prediction error in seconds
- **MAE** (Mean Absolute Error): Average absolute prediction error in seconds
- **R² Score**: Proportion of variance explained by the model

### 5. Visualization
- Scatter plots: True vs predicted values
- Residual plots: Error distribution
- Feature importance plots: Which features contribute most to predictions

## Functions in utils.py

### Data Generation
- `generate_synthetic_bus_data(n_samples)`: Generate synthetic dataset

### Feature Engineering
- `create_time_features(df)`: Decompose time into cyclical features
- `create_day_features(df)`: Create day-based features
- `create_interaction_features(df)`: Create interaction features
- `engineer_features(df)`: Apply all feature engineering steps

### Data Pipeline
- `prepare_data_for_xgboost(df, target_col, test_size, random_state)`: Split data into train/test
- `scale_features(X_train, X_test, feature_cols)`: Standardize features (optional)

### Evaluation
- `evaluate_model(y_true, y_pred, model_name)`: Calculate and print metrics
- `plot_predictions(y_true, y_pred, model_name, sample_size)`: Visualize predictions
- `plot_feature_importance(model, feature_names, top_n)`: Plot feature importance

## How to Run

1. Open the Jupyter notebook: `Stinger_XGboost.ipynb`
2. Run all cells in order:
   - Cell 1: Import libraries
   - Cell 2: Generate and load synthetic data
   - Cell 3: Apply feature engineering
   - Cell 4: Train XGBoost model
   - Cell 5: Evaluate and visualize results

The notebook will:
- Generate 10,000 synthetic samples
- Create engineered features
- Train the XGBoost model
- Display performance metrics
- Show visualizations

## Data Characteristics

The synthetic data includes realistic patterns:
- **Rush hour slowdown**: Buses are 30% slower during 6-9am and 4-7pm
- **Weather impact**: Rain reduces speed by 15% and adds 3 minutes average delay
- **Weekend speedup**: 10% faster on weekends (less traffic)
- **Bus bunching**: Short headways (<5 min) add 30-120 seconds delay
- **Stop delays**: ~30 seconds per stop (1 stop per 500m)
- **Traffic signals**: Random delays proportional to distance

## Expected Performance

With the synthetic dataset, expect:
- **R² Score**: 0.85-0.95 (high explanatory power)
- **RMSE**: 30-60 seconds (0.5-1 minute average error)
- **MAE**: 20-40 seconds

Top important features typically include:
1. distance_to_target_stop_m
2. current_speed_mps
3. current_delay_sec
4. speed_distance_ratio
5. time-based features (hour, is_rush_hour)

## Next Steps

To use this model with real data:
1. Replace the data generation step with loading real bus data
2. Ensure the same features are available or can be calculated
3. Adjust hyperparameters based on real data characteristics
4. Consider cross-validation for more robust evaluation
5. Add additional features from real-world data (e.g., real weather API, traffic conditions)
