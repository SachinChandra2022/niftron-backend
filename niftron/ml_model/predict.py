# src/niftron/ml_model/predict.py (FINAL VERSION)

import os
import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

# This line constructs a path that is RELATIVE to the current file (predict.py).
# This is the most reliable method.
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lem_model.joblib')

# Initialize model variable in the global scope
model: GradientBoostingClassifier = None

def load_model():
    """Loads the model from disk into the global 'model' variable."""
    global model
    if model is not None:
        return

    # Add a check to see if the file actually exists before trying to load
    if not os.path.exists(MODEL_PATH):
        print(f"FATAL Error: Model file does not exist at the expected path: {MODEL_PATH}")
        print("Please run the training script (`python -m src.niftron.ml_model.train`) to create the model file.")
        model = None
        return

    try:
        model = joblib.load(MODEL_PATH)
        print(f"LEM model loaded successfully from {MODEL_PATH}")
    except Exception as e:
        print(f"Error loading model from {MODEL_PATH}: {e}")
        model = None

def generate_lem_score(model: GradientBoostingClassifier, features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates prediction scores using the provided LEM model.

    Args:
        model (GradientBoostingClassifier): The pre-trained model object.
        features_df (pd.DataFrame): DataFrame containing the input features
                                    ('trend_signal', 'momentum_score', 'macd_score').

    Returns:
        pd.DataFrame: A DataFrame with a single 'lem_score' column.
                      The score is the probability of the positive class (target=1),
                      scaled to 0-100.
    """
    if model is None:
        raise ValueError("A valid model object must be provided.")

    feature_columns = ['trend_signal', 'momentum_score', 'macd_score']
    X = features_df[feature_columns]

    probabilities = model.predict_proba(X)[:, 1]
    lem_scores = probabilities * 100
    
    return pd.DataFrame({'lem_score': lem_scores}, index=features_df.index)

# Load the model automatically when the module is first imported
load_model()