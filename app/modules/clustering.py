"""
Clustering Module - Customer & Product Segmentation
K-Means, Hierarchical, DBSCAN clustering with PCA visualization
FIXED: Handles small datasets properly
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
import matplotlib.pyplot as plt
import seaborn as sns

def show_clustering_dashboard(df):
    """Main clustering dashboard"""
    
    st.markdown("## 🎯 Clustering & Segmentation Engine")
    
    clustering_options = [
        "K-Means Clustering",
        "Hierarchical Clustering",
        "DBSCAN Clustering",
        "PCA Analysis"
    ]
    
    selected_method = st.selectbox("Select Clustering Method", clustering_options)
    
    st.markdown("---")
    
    if selected_method == "K-Means Clustering":
        show_kmeans_clustering(df)
    elif selected_method == "Hierarchical Clustering":
        show_hierarchical_clustering(df)
    elif selected_method == "DBSCAN Clustering":
        show_dbscan_clustering(df)
    elif selected_method == "PCA Analysis":
        show_pca_analysis(df)

def prepare_clustering_data(df, feature_type='category'):
    """Prepare and aggregate data for clustering"""
    
    try:
        if feature_type == 'category' and 'category' in df.columns:
            # Category-level aggregation
            agg_df = df.groupby('category').agg({
                'amount': ['sum', 'mean', 'count'],
                'quantity': 'sum'
            }).reset_index()
            
            agg_df.columns = ['category', 'total_revenue', 'avg_order_value', 'order_count', 'total_quantity']
            agg_df['revenue_per_unit'] = agg_df['total_revenue'] / agg_df['total_quantity'].replace(0, 1)
            
            features = ['total_revenue', 'avg_order_value', 'order_count', 'revenue_per_unit']
            X = agg_df[features].values
            labels = agg_df['category'].values
            
        elif feature_type == 'state' and 'shipping_state' in df.columns:
            # State-level aggregation
            agg_df = df.groupby('shipping_state').agg({
                'amount': ['sum', 'mean', 'count'],
                'quantity': 'sum'
            }).reset_index()
            
            agg_df.columns = ['state', 'total_revenue', 'avg_order_value', 'order_count', 'total_quantity']
            
            features = ['total_revenue', 'avg_order_value', 'order_count', 'total_quantity']
            X = agg_df[features].values
            labels = agg_df['state'].values
            
        else:
            # Transaction-level (sample for performance)
            sample_size = min(5000, len(df))
            sample_df = df.sample(sample_size, random_state=42)
            
            numeric_cols = ['amount', 'quantity']
            if 'aov' in sample_df.columns:
                numeric_cols.append('aov')
            
            X = sample_df[numeric_cols].values
            labels = sample_df.index.values
            agg_df = None
        
        # Check minimum data requirements
        n_samples = len(X)
        if n_samples < 2:
            st.error(f"❌ Insufficient data: Only {n_samples} sample(s) found. Need at least 2.")
            return None, None, None
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, labels, agg_df if 'agg_df' in locals() else None
        
    except Exception as e:
        st.error(f"Error preparing data: {str(e)}")
        return None, None, None

def show_kmeans_clustering(df):
    """K-Means clustering analysis"""
    
    st.markdown("### 🔵 K-Means Clustering")
    
    # Clustering level selection
    clustering_level = st.radio(
        "Clustering Level",
        ["Category Level", "State Level", "Transaction Level"],
        horizontal=True
    )
    
    # Map selection to feature type
    feature_map = {
        "Category Level": "category",
        "State Level": "state",
        "Transaction Level": "transaction"
    }
    
    feature_type = feature_map[clustering_level]
    
    # Prepare data
    with st.spinner("Preparing data..."):
        X_scaled, labels, agg_df = prepare_clustering_data(df, feature_type)
    
    if X_scaled is None:
        st.error("Could not prepare clustering data")
        return
    
    # Check data size
    n_samples = len(X_scaled)
    max_clusters = min(10, n_samples - 1)  # Can't have more clusters than samples
    
    if n_samples < 2:
        st.error(f"❌ Not enough data points. Found {n_samples}, need at least 2.")
        return
    
    # Display data info
    st.info(f"📊 Dataset: {n_samples} samples available for clustering")
    
    # Parameters
    col1, col2 = st.columns(2)
    
    with col1:
        # Adjust slider max based on available data
        n_clusters = st.slider(
            "Number of Clusters (k)", 
            min_value=2, 
            max_value=max_clusters, 
            value=min(4, max_clusters),
            help=f"Maximum clusters limited to {max_clusters} based on dataset size"
        )
    
    with col2:
        # Allow elbow method for any dataset size >= 3
        show_elbow = st.checkbox(
            "Show Elbow Method", 
            value=True,
            help="Works with 3+ samples. More reliable with 10+ samples."
        )
    
    # Elbow method - works with 3+ samples
    if show_elbow:
        # Minimum requirement: need at least 3 samples
        min_samples_for_elbow = 3
        
        if n_samples >= min_samples_for_elbow:
            st.markdown("#### 📈 Elbow Method for Optimal k")
            
            # Show informational message for small datasets
            if n_samples < 10:
                st.info(f"ℹ️ Dataset has {n_samples} samples. Elbow method works but is more reliable with 10+ samples. Consider using 'Transaction Level' for better results.")
            
            with st.spinner("Computing WCSS..."):
                wcss = []
                # k_range must be at least 2 and less than n_samples
                k_max = min(n_samples - 1, 10)
                k_range = range(2, k_max + 1)
                
                for k in k_range:
                    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                    kmeans.fit(X_scaled)
                    wcss.append(kmeans.inertia_)
            
            # Plot elbow curve
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=list(k_range),
                y=wcss,
                mode='lines+markers',
                marker=dict(size=10, color='#667eea'),
                line=dict(color='#667eea', width=2)
            ))
            
            fig.update_layout(
                title=f"Elbow Method: WCSS vs Number of Clusters (n={n_samples} samples)",
                xaxis_title="Number of Clusters (k)",
                yaxis_title="Within-Cluster Sum of Squares (WCSS)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Add interpretation guide for small datasets
            if n_samples < 10:
                with st.expander("📖 How to Interpret This Elbow Plot"):
                    st.markdown(f"""
                    **Your Dataset:** {n_samples} samples
                    
                    **Looking for the "Elbow":**
                    - Find where the curve bends sharply (the elbow point)
                    - Before the elbow: WCSS drops quickly
                    - After the elbow: WCSS drops slowly
                    - The elbow point suggests the optimal k
                    
                    **With Small Datasets ({n_samples} samples):**
                    - Elbow may not be clearly visible
                    - Recommended k: 2-4 clusters
                    - Consider business interpretation over statistical measures
                    - Focus on cluster profiles and actionable insights
                    
                    **💡 For Better Results:**
                    - Switch to "Transaction Level" (thousands of samples)
                    - This gives more reliable elbow detection
                    - Enables finer customer segmentation
                    """)
        else:
            st.warning(f"⚠️ Elbow method requires at least {min_samples_for_elbow} samples. You have {n_samples}.")
            st.info("💡 **Solution:** Switch to 'Transaction Level' clustering for thousands of samples.")
    
    # Perform K-Means
    st.markdown(f"#### 🎯 K-Means Clustering (k={n_clusters})")
    
    with st.spinner("Running K-Means..."):
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
    
    st.success(f"✅ Clustering complete: {n_clusters} clusters identified")
    
    # Cluster distribution
    col1, col2 = st.columns(2)
    
    with col1:
        cluster_counts = pd.Series(cluster_labels).value_counts().sort_index()
        
        fig = px.bar(
            x=cluster_counts.index,
            y=cluster_counts.values,
            labels={'x': 'Cluster', 'y': 'Count'},
            title="Cluster Size Distribution"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(
            values=cluster_counts.values,
            names=[f'Cluster {i}' for i in cluster_counts.index],
            title="Cluster Proportion"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # PCA visualization
    st.markdown("#### 📊 Cluster Visualization (PCA)")
    
    # Check if we need PCA
    n_features = X_scaled.shape[1]
    if n_features >= 2:
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        pca_df = pd.DataFrame({
            'PC1': X_pca[:, 0],
            'PC2': X_pca[:, 1],
            'Cluster': [f'Cluster {i}' for i in cluster_labels],
            'Label': labels
        })
        
        fig = px.scatter(
            pca_df,
            x='PC1',
            y='PC2',
            color='Cluster',
            hover_data=['Label'],
            title=f"K-Means Clusters in PCA Space (Variance Explained: {pca.explained_variance_ratio_.sum():.2%})",
            labels={'PC1': f'PC1 ({pca.explained_variance_ratio_[0]:.2%})',
                    'PC2': f'PC2 ({pca.explained_variance_ratio_[1]:.2%})'}
        )
        
        fig.update_traces(marker=dict(size=10, opacity=0.7))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Only 1 feature available. PCA visualization not applicable.")
    
    # Cluster profiles
    if agg_df is not None:
        st.markdown("#### 📋 Cluster Profiles")
        
        agg_df['cluster'] = cluster_labels
        
        cluster_profiles = agg_df.groupby('cluster').agg({
            'total_revenue': 'mean',
            'avg_order_value': 'mean',
            'order_count': 'mean'
        }).round(2)
        
        cluster_profiles.columns = ['Avg Total Revenue', 'Avg Order Value', 'Avg Order Count']
        
        st.dataframe(cluster_profiles, use_container_width=True)
        
        # Show members of each cluster
        with st.expander("🔍 View Cluster Members"):
            for cluster_id in sorted(agg_df['cluster'].unique()):
                st.markdown(f"**Cluster {cluster_id}:**")
                col_name = 'category' if feature_type == 'category' else 'state'
                if col_name in agg_df.columns:
                    members = agg_df[agg_df['cluster'] == cluster_id][[col_name, 'total_revenue', 'order_count']].sort_values('total_revenue', ascending=False)
                    st.dataframe(members.head(10), use_container_width=True)

def show_hierarchical_clustering(df):
    """Hierarchical clustering with dendrogram"""
    
    st.markdown("### 🌳 Hierarchical Clustering")
    
    # Clustering level
    clustering_level = st.radio(
        "Clustering Level",
        ["Category Level", "State Level"],
        horizontal=True
    )
    
    feature_type = "category" if clustering_level == "Category Level" else "state"
    
    # Prepare data
    with st.spinner("Preparing data..."):
        X_scaled, labels, agg_df = prepare_clustering_data(df, feature_type)
    
    if X_scaled is None or len(X_scaled) == 0:
        st.error("Could not prepare clustering data")
        return
    
    n_samples = len(X_scaled)
    
    if n_samples < 2:
        st.error(f"❌ Not enough data points. Found {n_samples}, need at least 2.")
        return
    
    # Limit for visualization
    if n_samples > 50:
        st.warning(f"⚠️ Limiting to top 50 items for visualization (total: {n_samples})")
        top_indices = np.argsort(X_scaled[:, 0])[-50:]  # Top 50 by first feature
        X_scaled = X_scaled[top_indices]
        labels = labels[top_indices]
        n_samples = 50
    
    st.info(f"📊 Analyzing {n_samples} samples")
    
    # Linkage method
    linkage_method = st.selectbox(
        "Linkage Method",
        ["ward", "complete", "average", "single"]
    )
    
    # Compute linkage
    with st.spinner("Computing hierarchical clustering..."):
        linkage_matrix = linkage(X_scaled, method=linkage_method)
    
    # Dendrogram
    st.markdown("#### 🌳 Dendrogram")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    dendrogram(
        linkage_matrix,
        labels=labels,
        ax=ax,
        leaf_font_size=10,
        orientation='right'
    )
    
    ax.set_title(f"Hierarchical Clustering Dendrogram ({linkage_method.capitalize()} Linkage)")
    ax.set_xlabel("Distance")
    plt.tight_layout()
    
    st.pyplot(fig)
    
    # Cut tree to form clusters
    st.markdown("#### ✂️ Cut Dendrogram to Form Clusters")
    
    max_clusters = min(10, n_samples - 1)
    n_clusters = st.slider(
        "Number of Clusters", 
        min_value=2, 
        max_value=max_clusters, 
        value=min(4, max_clusters)
    )
    
    hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage_method)
    cluster_labels = hierarchical.fit_predict(X_scaled)
    
    # Cluster distribution
    cluster_counts = pd.Series(cluster_labels).value_counts().sort_index()
    
    fig = px.bar(
        x=cluster_counts.index,
        y=cluster_counts.values,
        labels={'x': 'Cluster', 'y': 'Count'},
        title=f"Hierarchical Cluster Distribution (k={n_clusters})"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # PCA visualization
    if X_scaled.shape[1] >= 2:
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        pca_df = pd.DataFrame({
            'PC1': X_pca[:, 0],
            'PC2': X_pca[:, 1],
            'Cluster': [f'Cluster {i}' for i in cluster_labels],
            'Label': labels
        })
        
        fig = px.scatter(
            pca_df,
            x='PC1',
            y='PC2',
            color='Cluster',
            hover_data=['Label'],
            title="Hierarchical Clusters in PCA Space"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_dbscan_clustering(df):
    """DBSCAN density-based clustering"""
    
    st.markdown("### 🔴 DBSCAN Clustering")
    
    st.info("""
    **DBSCAN** (Density-Based Spatial Clustering) identifies clusters based on density 
    and can detect outliers (noise points).
    """)
    
    # Clustering level
    clustering_level = st.radio(
        "Clustering Level",
        ["Category Level", "State Level"],
        horizontal=True
    )
    
    feature_type = "category" if clustering_level == "Category Level" else "state"
    
    # Parameters
    col1, col2 = st.columns(2)
    
    with col1:
        eps = st.slider("Epsilon (ε) - Neighborhood Radius", 0.1, 3.0, 0.5, 0.1)
    
    with col2:
        # Prepare data first to get n_samples
        with st.spinner("Preparing data..."):
            X_scaled, labels, agg_df = prepare_clustering_data(df, feature_type)
        
        if X_scaled is None:
            st.error("Could not prepare clustering data")
            return
        
        n_samples = len(X_scaled)
        max_min_samples = max(2, min(10, n_samples - 1))
        
        min_samples = st.slider(
            "Min Samples - Min Points to Form Cluster", 
            min_value=2, 
            max_value=max_min_samples, 
            value=min(3, max_min_samples)
        )
    
    if n_samples < 2:
        st.error(f"❌ Not enough data points. Found {n_samples}, need at least 2.")
        return
    
    st.info(f"📊 Analyzing {n_samples} samples")
    
    # Perform DBSCAN
    with st.spinner("Running DBSCAN..."):
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        cluster_labels = dbscan.fit_predict(X_scaled)
    
    # Analyze results
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)
    
    st.success(f"✅ DBSCAN complete: {n_clusters} clusters + {n_noise} noise points")
    
    # Cluster distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Number of Clusters", n_clusters)
        st.metric("Noise Points (Outliers)", n_noise)
    
    with col2:
        cluster_counts = pd.Series(cluster_labels).value_counts().sort_index()
        
        fig = px.bar(
            x=cluster_counts.index,
            y=cluster_counts.values,
            labels={'x': 'Cluster (-1 = Noise)', 'y': 'Count'},
            title="Cluster Distribution"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # PCA visualization
    if X_scaled.shape[1] >= 2:
        st.markdown("#### 📊 DBSCAN Clusters Visualization")
        
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)
        
        pca_df = pd.DataFrame({
            'PC1': X_pca[:, 0],
            'PC2': X_pca[:, 1],
            'Cluster': ['Noise' if i == -1 else f'Cluster {i}' for i in cluster_labels],
            'Label': labels
        })
        
        fig = px.scatter(
            pca_df,
            x='PC1',
            y='PC2',
            color='Cluster',
            hover_data=['Label'],
            title="DBSCAN Clusters (Noise points marked separately)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Outlier analysis
    if n_noise > 0:
        st.markdown("#### ⚠️ Outlier Analysis")
        
        outlier_indices = np.where(cluster_labels == -1)[0]
        outlier_labels = labels[outlier_indices]
        
        st.write(f"**Outliers detected:** {', '.join(map(str, outlier_labels[:20]))}")
        
        if len(outlier_labels) > 20:
            st.write(f"... and {len(outlier_labels) - 20} more")

def show_pca_analysis(df):
    """Principal Component Analysis"""
    
    st.markdown("### 📉 Principal Component Analysis (PCA)")
    
    st.info("""
    **PCA** reduces dimensionality while preserving maximum variance, 
    enabling visualization of high-dimensional data.
    """)
    
    # Clustering level
    clustering_level = st.radio(
        "Analysis Level",
        ["Category Level", "State Level"],
        horizontal=True
    )
    
    feature_type = "category" if clustering_level == "Category Level" else "state"
    
    # Prepare data
    with st.spinner("Preparing data..."):
        X_scaled, labels, agg_df = prepare_clustering_data(df, feature_type)
    
    if X_scaled is None:
        st.error("Could not prepare clustering data")
        return
    
    n_samples, n_features = X_scaled.shape
    
    if n_samples < 2:
        st.error(f"❌ Not enough data points. Found {n_samples}, need at least 2.")
        return
    
    st.info(f"📊 Dataset: {n_samples} samples × {n_features} features")
    
    # Perform PCA
    n_components = min(n_features, n_samples, 10)
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)
    
    # Explained variance
    st.markdown("#### 📊 Explained Variance")
    
    variance_df = pd.DataFrame({
        'Component': [f'PC{i+1}' for i in range(n_components)],
        'Variance Explained': pca.explained_variance_ratio_,
        'Cumulative Variance': np.cumsum(pca.explained_variance_ratio_)
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            variance_df,
            x='Component',
            y='Variance Explained',
            title="Variance Explained by Each Component"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(
            variance_df,
            x='Component',
            y='Cumulative Variance',
            title="Cumulative Variance Explained",
            markers=True
        )
        
        fig.add_hline(y=0.95, line_dash="dash", line_color="red",
                     annotation_text="95% threshold")
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 2D Visualization
    if n_components >= 2:
        st.markdown("#### 🎨 2D PCA Projection")
        
        pca_df = pd.DataFrame({
            'PC1': X_pca[:, 0],
            'PC2': X_pca[:, 1],
            'Label': labels
        })
        
        fig = px.scatter(
            pca_df,
            x='PC1',
            y='PC2',
            hover_data=['Label'],
            title=f"First Two Principal Components (Variance: {pca.explained_variance_ratio_[:2].sum():.2%})",
            labels={'PC1': f'PC1 ({pca.explained_variance_ratio_[0]:.2%})',
                    'PC2': f'PC2 ({pca.explained_variance_ratio_[1]:.2%})'}
        )
        
        fig.update_traces(marker=dict(size=10, opacity=0.7))
        st.plotly_chart(fig, use_container_width=True)
    
    # Feature loadings
    if agg_df is not None and n_components >= 2:
        st.markdown("#### 🔍 Feature Loadings")
        
        feature_names = ['total_revenue', 'avg_order_value', 'order_count', 'revenue_per_unit'][:n_features]
        
        loadings = pd.DataFrame(
            pca.components_[:2].T,
            columns=['PC1', 'PC2'],
            index=feature_names
        )
        
        st.dataframe(loadings, use_container_width=True)