"""
Cyber Raksha AI - Preprocessing and Pipeline Management
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from ai_engine.utils.config import FEATURE_NAMES, RANDOM_STATE


class URLPreprocessor:
    """
    Standardizes feature vectors and manages preprocessing transformations.
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = FEATURE_NAMES
        self.is_fitted = False

    def transform_single(self, features_dict: Dict[str, Any]) -> pd.DataFrame:
        """Converts a single URL features dictionary into an ordered DataFrame."""
        ordered_data = {feat: [features_dict.get(feat, 0)] for feat in self.feature_names}
        df = pd.DataFrame(ordered_data)
        return df

    def fit(self, X: pd.DataFrame):
        """Fits the scaler on training feature DataFrame."""
        self.scaler.fit(X[self.feature_names])
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Scales numerical feature columns."""
        if not self.is_fitted:
            # Fallback for unscaled inference if raw tree model handles unscaled features directly
            return X[self.feature_names].values
        return self.scaler.transform(X[self.feature_names])

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """Fits and transforms feature DataFrame."""
        return self.fit(X).transform(X)
