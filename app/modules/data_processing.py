"""
data_processing.py - FIXED VERSION
Improved ETL with all bug fixes
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def _to_numeric(series):
    """Safely convert series to numeric"""
    return pd.to_numeric(
        series.astype(str).str.replace(',', '').str.replace('₹', '').str.replace('$', ''),
        errors='coerce'
    )

def _safe_rename(df, mapping):
    """Safely rename columns that exist"""
    cols = [c for c in mapping.keys() if c in df.columns]
    return df.rename(columns={k: mapping[k] for k in cols})

# =====================================================
# CLEANING FUNCTIONS
# =====================================================
def clean_domestic_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean domestic sales data with fixes"""
    df = df.copy()
    
    # Remove noise columns
    noise_cols = [c for c in df.columns if 'Unnamed' in c or c.strip() == '']
    df = df.drop(columns=noise_cols, errors='ignore')
    
    # Strip whitespace from column names
    df.columns = [c.strip() for c in df.columns]
    
    # Column mapping
    mapping = {
        'Order ID': 'order_id', 'OrderID': 'order_id', 'Order_Id': 'order_id',
        'Date': 'date', 'Status': 'status',
        'Fulfilment': 'fulfillment', 'Fulfillment': 'fulfillment',
        'Sales Channel': 'sales_channel_raw',
        'Category': 'category', 'Size': 'size',
        'Qty': 'quantity', 'Quantity': 'quantity',
        'Amount': 'amount',
        'ship-state': 'shipping_state', 'Shipping State': 'shipping_state',
        'Courier Status': 'courier_status',
        'ASIN': 'asin'
    }
    
    df = _safe_rename(df, mapping)
    
    # Date parsing
    if 'date' in df.columns:
        df['order_date'] = pd.to_datetime(df['date'], errors='coerce')
    else:
        for c in ['Order Date', 'order_date', 'DATE']:
            if c in df.columns:
                df['order_date'] = pd.to_datetime(df[c], errors='coerce')
                break
    
    # Numeric conversions
    if 'amount' in df.columns:
        df['amount'] = _to_numeric(df['amount'])
    
    if 'quantity' in df.columns:
        df['quantity'] = _to_numeric(df['quantity']).fillna(1).astype(int)
    
    # Fill missing categorical values
    fill_values = {
        'category': 'Unknown',
        'shipping_state': 'Unspecified',
        'courier_status': 'Not Available',
        'size': 'Standard'
    }
    
    for col, val in fill_values.items():
        if col in df.columns:
            df[col] = df[col].fillna(val).astype(str)
    
    # Generate order_id if missing
    if 'order_id' not in df.columns or df['order_id'].isnull().all():
        df['order_id'] = 'DOM_' + pd.Series(range(len(df))).astype(str)
    
    # FIXED: Set sales_channel directly (not using .get())
    df['sales_channel'] = 'Domestic'
    
    # Ensure status exists
    if 'status' not in df.columns:
        df['status'] = 'Shipped'
    
    # Select final columns
    final_cols = [
        'order_id', 'order_date', 'status', 'fulfillment',
        'sales_channel', 'category', 'size', 'quantity',
        'amount', 'shipping_state', 'courier_status'
    ]
    
    return df[[c for c in final_cols if c in df.columns]]

def clean_international_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean international sales data"""
    df = df.copy()
    
    # Strip column names
    df.columns = [c.strip() for c in df.columns]
    
    # Convert numeric columns
    for col in ['PCS', 'RATE', 'GROSS AMT', 'GROSS_AMT']:
        if col in df.columns:
            df[col] = _to_numeric(df[col])
    
    # Parse dates
    for col in ['Date', 'DATE', 'date', 'Order Date']:
        if col in df.columns:
            df['order_date'] = pd.to_datetime(df[col], errors='coerce')
            break
    
    # Find order column
    order_col = None
    for c in ['Order number', 'Order Number', 'OrderNo', 'Order']:
        if c in df.columns:
            order_col = c
            break
    
    # Generate order_id
    if order_col:
        df['order_id'] = 'INT_' + df[order_col].astype(str)
    else:
        df['order_id'] = 'INT_' + pd.Series(range(len(df))).astype(str)
    
    # Column mapping
    mapping = {
        'PCS': 'quantity',
        'GROSS AMT': 'amount',
        'Category': 'category',
        'CATEGORY': 'category'
    }
    
    df = _safe_rename(df, mapping)
    
    # Set defaults
    df['sales_channel'] = 'International'
    df['status'] = df.get('status', 'Shipped') if 'status' in df.columns else 'Shipped'
    df['fulfillment'] = df.get('fulfillment', 'Direct') if 'fulfillment' in df.columns else 'Direct'
    df['size'] = df.get('size', 'Standard') if 'size' in df.columns else 'Standard'
    df['shipping_state'] = df.get('shipping_state', 'International') if 'shipping_state' in df.columns else 'International'
    df['courier_status'] = df.get('courier_status', 'Delivered') if 'courier_status' in df.columns else 'Delivered'
    
    # Select final columns
    final_cols = [
        'order_id', 'order_date', 'status', 'fulfillment',
        'sales_channel', 'category', 'size', 'quantity',
        'amount', 'shipping_state', 'courier_status'
    ]
    
    return df[[c for c in final_cols if c in df.columns]]

# =====================================================
# FEATURE ENGINEERING
# =====================================================
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features"""
    df = df.copy()
    
    # Temporal features
    if 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        df = df.dropna(subset=['order_date'])
        
        df['year'] = df['order_date'].dt.year
        df['month'] = df['order_date'].dt.month
        df['month_name'] = df['order_date'].dt.month_name()
        df['day_of_week'] = df['order_date'].dt.dayofweek
        df['weekday_name'] = df['order_date'].dt.day_name()
        df['quarter'] = df['order_date'].dt.quarter
        df['week_of_year'] = df['order_date'].dt.isocalendar().week
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    
    # Amount features
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Winsorization
        upper = df['amount'].quantile(0.99)
        df['amount_winsorized'] = df['amount'].clip(upper=upper)
        
        # Log transform
        df['amount_log'] = np.log1p(df['amount'].fillna(0))
    
    # Quantity
    if 'quantity' in df.columns:
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(1)
    
    # AOV calculation
    if 'amount' in df.columns and 'quantity' in df.columns:
        df['aov'] = df['amount'] / df['quantity'].replace(0, 1)
    
    return df

# =====================================================
# MAIN PROCESSING
# =====================================================
def process_data(domestic_df: pd.DataFrame, international_df: pd.DataFrame) -> pd.DataFrame:
    """Main ETL pipeline"""
    
    try:
        # Clean datasets
        d = clean_domestic_data(domestic_df.copy()) if domestic_df is not None else pd.DataFrame()
        i = clean_international_data(international_df.copy()) if international_df is not None else pd.DataFrame()
        
        # Check if we have any data
        if d.empty and i.empty:
            logger.warning("Both datasets are empty after cleaning")
            return pd.DataFrame()
        
        # Merge
        master = pd.concat([d, i], ignore_index=True, sort=False)
        
        # Feature engineering
        master = engineer_features(master)
        
        # Final cleanup
        master = master[master['amount'].notna() & master['sales_channel'].notna()]
        
        logger.info(f"Processing complete: {len(master)} rows")
        return master
    
    except Exception as e:
        logger.error(f"Error in process_data: {e}")
        raise

# =====================================================
# DASHBOARD
# =====================================================
def show_etl_dashboard(full_df: pd.DataFrame, filtered_df: pd.DataFrame = None):
    """Display ETL & Data Quality dashboard"""
    
    st.markdown("## 📊 ETL & Data Quality Report")
    
    if full_df is None or len(full_df) == 0:
        st.warning("⚠️ No data available")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rows", f"{len(full_df):,}")
    
    with col2:
        completeness = (1 - full_df.isnull().sum().sum() / (full_df.shape[0] * full_df.shape[1])) * 100
        st.metric("Data Completeness", f"{completeness:.1f}%")
    
    with col3:
        if 'sales_channel' in full_df.columns:
            channels = full_df['sales_channel'].nunique()
            st.metric("Sales Channels", channels)
    
    with col4:
        if 'category' in full_df.columns:
            categories = full_df['category'].nunique()
            st.metric("Categories", categories)
    
    st.markdown("---")
    
    # Missing values
    st.markdown("### 🔍 Missing Values Analysis")
    
    missing = full_df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    
    if not missing.empty:
        miss_df = pd.DataFrame({
            'Column': missing.index,
            'Missing Count': missing.values,
            'Missing %': (missing.values / len(full_df) * 100).round(2)
        })
        
        fig = px.bar(
            miss_df,
            x='Column',
            y='Missing %',
            title="Missing Values by Column",
            color='Missing %',
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(miss_df, use_container_width=True)
    else:
        st.success("✅ No missing values detected!")
    
    st.markdown("---")
    
    # Channel distribution
    if 'sales_channel' in full_df.columns:
        st.markdown("### 🔄 Channel Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            channel_counts = full_df['sales_channel'].value_counts()
            fig = px.pie(
                values=channel_counts.values,
                names=channel_counts.index,
                title="Order Distribution by Channel",
                color_discrete_sequence=['#667eea', '#764ba2']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            channel_revenue = full_df.groupby('sales_channel')['amount'].sum()
            fig = px.bar(
                x=channel_revenue.index,
                y=channel_revenue.values,
                title="Revenue by Channel",
                labels={'x': 'Channel', 'y': 'Revenue (₹)'},
                color=channel_revenue.index,
                color_discrete_sequence=['#667eea', '#764ba2']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Summary statistics
    st.markdown("### 📊 Summary Statistics")
    
    numeric_cols = full_df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        summary = full_df[numeric_cols].describe().T
        st.dataframe(summary, use_container_width=True)
    
    st.markdown("---")
    
    # Export
    st.markdown("### 💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv = full_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Processed Data (CSV)",
            data=csv,
            file_name="nexus_processed_data.csv",
            mime="text/csv"
        )
    
    with col2:
        if filtered_df is not None and not filtered_df.equals(full_df):
            csv_filtered = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=csv_filtered,
                file_name="nexus_filtered_data.csv",
                mime="text/csv"
            )
