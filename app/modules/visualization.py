"""visualization.py - Improved visualizations with safer checks and deterministic sampling"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

SAMPLE_SEED = 42

def show_visualization_dashboard(df: pd.DataFrame):
    st.markdown("## 📈 Visual Analytics (Improved)")
    if df is None or df.empty:
        st.warning("No data to visualize")
        return
    viz_options = ["Revenue Trends","Category Analysis","Geographic Analysis","Distribution Analysis","Correlation Analysis","Advanced Visualizations"]
    choice = st.selectbox("Choose view", viz_options)
    if choice == "Revenue Trends":
        show_revenue_trends(df)
    elif choice == "Category Analysis":
        show_category_analysis(df)
    elif choice == "Geographic Analysis":
        show_geographic_analysis(df)
    elif choice == "Distribution Analysis":
        show_distribution_analysis(df)
    elif choice == "Correlation Analysis":
        show_correlation_analysis(df)
    else:
        show_advanced_visualizations(df)

def safe_sample(df, n):
    return df.sample(n=min(len(df), n), random_state=SAMPLE_SEED) if len(df)>n else df.copy()

def show_revenue_trends(df):
    if 'order_date' not in df.columns:
        st.warning("order_date missing")
        return
    agg_level = st.radio("Aggregation Level", ["Daily","Weekly","Monthly"], horizontal=True)
    df2 = df.copy()
    if agg_level == "Daily":
        df2['period'] = df2['order_date'].dt.date
    elif agg_level == "Weekly":
        df2['period'] = df2['order_date'].dt.to_period('W').astype(str)
    else:
        df2['period'] = df2['order_date'].dt.to_period('M').astype(str)
    trend = df2.groupby(['period','sales_channel'])['amount'].sum().reset_index()
    fig = px.line(trend, x='period', y='amount', color='sales_channel', labels={'amount':'Revenue'}, title=f"{agg_level} Revenue by Channel")
    fig.update_layout(height=480, xaxis={'tickangle':-45})
    st.plotly_chart(fig, use_container_width=True)

def show_category_analysis(df):
    if 'category' not in df.columns:
        st.warning("category missing")
        return
    topk = st.slider("Top K categories", 5, 50, 10)
    cat_rev = df.groupby('category')['amount'].sum().sort_values(ascending=False).head(topk)
    fig = px.bar(cat_rev, x=cat_rev.values, y=cat_rev.index, orientation='h', labels={'x':'Revenue','y':'Category'}, title="Top Categories by Revenue")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.groupby('category').agg({'amount':['sum','mean','count'], 'quantity':'sum'}).round(2))

def show_geographic_analysis(df):
    if 'shipping_state' not in df.columns:
        st.warning("shipping_state missing")
        return
    topk=st.slider("Top states",5,50,15)
    state_rev = df.groupby('shipping_state')['amount'].sum().sort_values(ascending=False).head(topk)
    fig = px.bar(x=state_rev.values,y=state_rev.index,orientation='h',title="Top States by Revenue")
    st.plotly_chart(fig, use_container_width=True)

def show_distribution_analysis(df):
    if 'amount' not in df.columns:
        st.warning("amount missing")
        return
    sampled = safe_sample(df, 5000)
    fig = px.histogram(sampled, x='amount', nbins=50, title="Amount distribution", marginal='box')
    st.plotly_chart(fig, use_container_width=True)

def show_correlation_analysis(df):
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric = [c for c in numeric if c!='order_id']
    if len(numeric)<2:
        st.warning("Not enough numeric columns")
        return
    corr = df[numeric].corr()
    fig = px.imshow(corr, text_auto='.2f', title="Correlation matrix")
    st.plotly_chart(fig, use_container_width=True)
    pairs=[]
    cols=corr.columns
    for i in range(len(cols)):
        for j in range(i+1,len(cols)):
            pairs.append((cols[i],cols[j],corr.iloc[i,j]))
    pairs = sorted(pairs, key=lambda x: abs(x[2]), reverse=True)[:10]
    st.table(pd.DataFrame(pairs, columns=['var1','var2','corr']).round(3))

def show_advanced_visualizations(df):
    choice = st.selectbox("Advanced", ["Sunburst","Treemap","Violin"])
    if choice=="Sunburst":
        if all(c in df.columns for c in ['sales_channel','category']):
            sb = df.groupby(['sales_channel','category'])['amount'].sum().reset_index()
            fig = px.sunburst(sb, path=['sales_channel','category'], values='amount', title="Revenue sunburst")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Required columns missing")
    elif choice=="Treemap":
        if 'category' in df.columns:
            tm = df.groupby(['sales_channel','category'])['amount'].sum().reset_index()
            fig = px.treemap(tm, path=['sales_channel','category'], values='amount')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("category missing")
    else:
        if all(c in df.columns for c in ['sales_channel','amount']):
            fig = px.violin(df, x='sales_channel', y='amount', box=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Required columns missing")
