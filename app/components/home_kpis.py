# app/components/home_kpis.py
import streamlit as st

def show_kpis(df):
    total_revenue = df['amount'].sum() if 'amount' in df.columns else 0
    total_orders = df['order_id'].nunique() if 'order_id' in df.columns else 0
    avg_aov = df['aov'].mean() if 'aov' in df.columns else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    col2.metric("Total Orders", f"{total_orders:,}")
    col3.metric("Avg Order Value", f"₹{avg_aov:.2f}")
