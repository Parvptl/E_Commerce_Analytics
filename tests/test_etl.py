"""
Unit tests for ETL pipeline
Run with: pytest tests/test_etl.py
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add app to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.modules import data_processing

# =====================================================
# FIXTURES
# =====================================================
@pytest.fixture
def sample_domestic_df():
    """Create sample domestic dataframe"""
    return pd.DataFrame({
        'Order ID': ['DOM001', 'DOM002', 'DOM003'],
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Status': ['Shipped', 'Shipped', 'Cancelled'],
        'Amount': ['1000', '2000', '1500'],
        'Quantity': ['1', '2', '1'],
        'Category': ['Electronics', 'Fashion', 'Electronics'],
        'ship-state': ['Maharashtra', 'Delhi', 'Karnataka']
    })

@pytest.fixture
def sample_international_df():
    """Create sample international dataframe"""
    return pd.DataFrame({
        'Order number': ['INT001', 'INT002'],
        'Date': ['2024-01-01', '2024-01-02'],
        'PCS': ['2', '3'],
        'GROSS AMT': ['3000', '4500'],
        'Category': ['Electronics', 'Home']
    })

# =====================================================
# TEST DOMESTIC CLEANING
# =====================================================
def test_clean_domestic_data(sample_domestic_df):
    """Test domestic data cleaning"""
    result = data_processing.clean_domestic_data(sample_domestic_df)
    
    # Check required columns exist
    assert 'order_id' in result.columns
    assert 'order_date' in result.columns
    assert 'amount' in result.columns
    assert 'sales_channel' in result.columns
    
    # Check sales channel is set
    assert (result['sales_channel'] == 'Domestic').all()
    
    # Check data types
    assert result['amount'].dtype in [np.float64, np.float32]
    assert pd.api.types.is_datetime64_any_dtype(result['order_date'])

def test_clean_domestic_handles_missing_values(sample_domestic_df):
    """Test handling of missing values"""
    # Add missing values
    sample_domestic_df.loc[0, 'Category'] = None
    
    result = data_processing.clean_domestic_data(sample_domestic_df)
    
    # Check missing category is filled
    assert result.loc[0, 'category'] == 'Unknown'

# =====================================================
# TEST INTERNATIONAL CLEANING
# =====================================================
def test_clean_international_data(sample_international_df):
    """Test international data cleaning"""
    result = data_processing.clean_international_data(sample_international_df)
    
    # Check required columns
    assert 'order_id' in result.columns
    assert 'amount' in result.columns
    assert 'quantity' in result.columns
    assert 'sales_channel' in result.columns
    
    # Check sales channel
    assert (result['sales_channel'] == 'International').all()
    
    # Check order_id generation
    assert result['order_id'].str.startswith('INT_').all()

# =====================================================
# TEST FEATURE ENGINEERING
# =====================================================
def test_engineer_features():
    """Test feature engineering"""
    df = pd.DataFrame({
        'order_date': pd.to_datetime(['2024-01-01', '2024-01-02']),
        'amount': [1000, 2000],
        'quantity': [1, 2]
    })
    
    result = data_processing.engineer_features(df)
    
    # Check temporal features
    assert 'year' in result.columns
    assert 'month' in result.columns
    assert 'weekday_name' in result.columns
    
    # Check business metrics
    assert 'aov' in result.columns
    assert 'amount_log' in result.columns
    
    # Verify calculations
    assert result.loc[0, 'aov'] == 1000
    assert result.loc[1, 'aov'] == 1000

# =====================================================
# TEST FULL PIPELINE
# =====================================================
def test_process_data(sample_domestic_df, sample_international_df):
    """Test complete ETL pipeline"""
    result = data_processing.process_data(sample_domestic_df, sample_international_df)
    
    # Check data merged
    assert len(result) == 5  # 3 domestic + 2 international
    
    # Check both channels present
    assert 'Domestic' in result['sales_channel'].values
    assert 'International' in result['sales_channel'].values
    
    # Check all required columns
    required_cols = ['order_id', 'amount', 'sales_channel', 'order_date']
    for col in required_cols:
        assert col in result.columns
    
    # Check no nulls in critical columns
    assert result['amount'].notna().all()
    assert result['sales_channel'].notna().all()

def test_process_data_empty_inputs():
    """Test pipeline with empty inputs"""
    result = data_processing.process_data(None, None)
    
    assert result.empty

def test_process_data_single_source(sample_domestic_df):
    """Test pipeline with only one data source"""
    result = data_processing.process_data(sample_domestic_df, None)
    
    assert not result.empty
    assert len(result) == 3
    assert (result['sales_channel'] == 'Domestic').all()

# =====================================================
# TEST EDGE CASES
# =====================================================
def test_handle_corrupted_amounts():
    """Test handling of non-numeric amounts"""
    df = pd.DataFrame({
        'Order ID': ['A1'],
        'Date': ['2024-01-01'],
        'Amount': ['invalid'],
        'Quantity': ['1'],
        'Category': ['Test']
    })
    
    result = data_processing.clean_domestic_data(df)
    
    # Should convert to NaN
    assert pd.isna(result.loc[0, 'amount'])

def test_handle_missing_dates():
    """Test handling of missing dates"""
    df = pd.DataFrame({
        'Order ID': ['A1', 'A2'],
        'Date': [None, '2024-01-01'],
        'Amount': ['1000', '2000'],
        'Quantity': ['1', '2']
    })
    
    result = data_processing.clean_domestic_data(df)
    
    # First row should have NaT date
    assert pd.isna(result.loc[0, 'order_date'])
    # Second row should be valid
    assert pd.notna(result.loc[1, 'order_date'])

# =====================================================
# RUN TESTS
# =====================================================
if __name__ == "__main__":
    pytest.main([__file__, '-v'])
