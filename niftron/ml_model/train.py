# niftron/ml_model/train.py (FINAL CORRECTED VERSION)

from dotenv import load_dotenv
load_dotenv()

import os
import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from niftron.ml_model.data_prep import load_and_prepare_data

def train_lem_model():
    """
    Main function to train and save the Learned Ensemble Model (LEM).
    """
    full_dataset = load_and_prepare_data()

    feature_columns = ['trend_signal', 'momentum_score', 'macd_score']
    target_column = 'target'
    X = full_dataset[feature_columns]
    y = full_dataset[target_column]

    train_end_date = pd.to_datetime('2022-12-31')
    X_train = X[X.index <= train_end_date]
    y_train = y[y.index <= train_end_date]

    print("\nData Splitting Complete:")
    print(f"Training set size: {len(X_train)} samples (from {X_train.index.min().date()} to {X_train.index.max().date()})")

    model = GradientBoostingClassifier(random_state=42)
    param_grid = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.01, 0.1, 0.2],
        'max_depth': [3, 5, 7],
        'subsample': [0.7, 0.8, 1.0]
    }

    tscv = TimeSeriesSplit(n_splits=5)

    print("\nStarting Hyperparameter Tuning with GridSearchCV...")
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=tscv,
        scoring='f1',
        n_jobs=-1,
        verbose=2
    )
    grid_search.fit(X_train, y_train)

    print("\nHyperparameter Tuning Complete.")
    print(f"Best F1-score found: {grid_search.best_score_:.4f}")
    print(f"Best parameters found: {grid_search.best_params_}")

    print("\nTraining the final model on the entire training dataset...")
    final_model = GradientBoostingClassifier(**grid_search.best_params_, random_state=42)
    final_model.fit(X_train, y_train)
    print("Final model training complete.")

    # --- CORRECTED SAVE PATH (NO 'src' FOLDER) ---
    # This builds the correct path relative to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    model_dir = os.path.join(project_root, 'niftron', 'ml_model')
    os.makedirs(model_dir, exist_ok=True)
    save_path = os.path.join(model_dir, 'lem_model.joblib')
    
    joblib.dump(final_model, save_path)
    print(f"\nSaving the final model to: {save_path}")
    print("Model saved successfully.")


if __name__ == '__main__':
    train_lem_model()