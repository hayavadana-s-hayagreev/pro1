"""Basic tests for the Crop Yield Estimator."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path


def test_data_file_exists():
    """Test that the dataset file exists."""
    assert Path("data/raw/yield_df.csv").exists(), "Dataset not found!"


def test_data_loads():
    """Test that the dataset loads properly."""
    df = pd.read_csv("data/raw/yield_df.csv")
    assert not df.empty, "Dataset is empty!"
    assert len(df.columns) > 5, "Dataset has too few columns"


def test_required_columns():
    """Test that required columns are present."""
    df = pd.read_csv("data/raw/yield_df.csv")
    required = ["Area", "Item", "Year", "average_rain_fall_mm_per_year",
                "pesticides_tonnes", "avg_temp", "hg/ha_yield"]
    for col in required:
        assert col in df.columns, f"Missing column: {col}"
def test_yield_is_numeric():
    """Test that yield column is numeric."""
    df = pd.read_csv("data/raw/yield_df.csv")
    assert df["hg/ha_yield"].dtype in [np.float64, np.int64], "Yield is not numeric"


def test_no_negative_yield():
    """Test that there are no negative yield values."""
    df = pd.read_csv("data/raw/yield_df.csv")
    assert (df["hg/ha_yield"] >= 0).all(), "Found negative yield values!"


def test_model_file_exists_after_training():
    """Test that model file exists (only if training was done)."""
    if Path("models/best_model.joblib").exists():
        import joblib
        model = joblib.load("models/best_model.joblib")
        assert hasattr(model, "predict"), "Model has no predict method!"