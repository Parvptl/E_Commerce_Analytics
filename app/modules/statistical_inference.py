"""
statistical_inference.py - Improved hypothesis testing with robust error handling
"""
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import chi2_contingency, f_oneway, ttest_ind
import warnings
warnings.filterwarnings('ignore')

def show_statistical_dashboard(df):
    st.markdown("## 🔬 Statistical Inference & Hypothesis Testing")
    
    if df is None or df.empty:
        st.warning("⚠️ No data available for statistical analysis")
        return
    
    st.info("""
    **Statistical tests help answer business questions:**
    - Are there significant differences between sales channels?
    - Do product categories perform differently?
    - Are certain states more profitable than others?
    """)
    
    options = [
        "Correlation Analysis",
        "Independent t-Test",
        "Chi-Square Test",
        "ANOVA Test",
        "Summary Statistics"
    ]
    
    choice = st.selectbox("Choose Statistical Test", options)
    
    st.markdown("---")
    
    if choice == "Correlation Analysis":
        show_correlation_test(df)
    elif choice == "Independent t-Test":
        show_ttest(df)
    elif choice == "Chi-Square Test":
        show_chi_square(df)
    elif choice == "ANOVA Test":
        show_anova(df)
    else:
        show_summary_report(df)

def show_correlation_test(df):
    """Pearson correlation analysis"""
    st.markdown("### 📊 Correlation Analysis")
    
    st.info("""
    **Correlation measures linear relationships between numerical variables:**
    - **r = +1**: Perfect positive correlation
    - **r = 0**: No correlation
    - **r = -1**: Perfect negative correlation
    - **|r| > 0.7**: Strong correlation
    - **|r| > 0.4**: Moderate correlation
    - **|r| < 0.3**: Weak correlation
    """)
    
    # Get numeric columns
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric = [c for c in numeric if c not in ['order_id', 'year', 'month', 'day_of_week']]
    
    if len(numeric) < 2:
        st.warning("⚠️ Not enough numeric columns for correlation analysis")
        st.info("💡 Your dataset needs at least 2 numerical variables")
        return
    
    st.success(f"✅ Found {len(numeric)} numerical variables: {', '.join(numeric)}")
    
    # Calculate correlation
    corr = df[numeric].corr()
    
    # Correlation heatmap
    st.markdown("#### 🎨 Correlation Heatmap")
    
    fig = px.imshow(
        corr,
        text_auto='.2f',
        title="Pearson Correlation Matrix",
        labels=dict(color="Correlation"),
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1
    )
    
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Top correlations
    st.markdown("#### 🔝 Top 10 Strongest Correlations")
    
    # Extract correlation pairs
    pairs = []
    cols = corr.columns
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            pairs.append({
                'Variable 1': cols[i],
                'Variable 2': cols[j],
                'Correlation': corr.iloc[i, j],
                'Strength': abs(corr.iloc[i, j])
            })
    
    pairs_df = pd.DataFrame(pairs).sort_values('Strength', ascending=False).head(10)
    pairs_df = pairs_df[['Variable 1', 'Variable 2', 'Correlation']]
    
    st.dataframe(pairs_df.style.format({'Correlation': '{:.4f}'}), use_container_width=True)
    
    # Interpretation
    with st.expander("📖 How to Interpret"):
        st.markdown("""
        **Positive Correlation (+):**
        - Variables increase together
        - Example: Higher quantity → Higher total amount
        
        **Negative Correlation (-):**
        - One increases as other decreases
        - Example: Higher discounts → Lower profit margins
        
        **Practical Use:**
        - Identify which factors drive revenue
        - Spot redundant metrics
        - Guide pricing and inventory decisions
        """)

def show_ttest(df):
    """Independent samples t-test"""
    st.markdown("### 📊 Independent t-Test (Two Sample Comparison)")
    
    st.info("""
    **Purpose:** Compare means between two groups
    - Example: Domestic vs International sales
    - **Null Hypothesis (H₀):** No difference between groups
    - **Alternative (H₁):** Significant difference exists
    - **Significance Level:** α = 0.05 (95% confidence)
    """)
    
    # Check required columns
    if 'sales_channel' not in df.columns:
        st.error("❌ Required column 'sales_channel' not found in dataset")
        return
    
    if 'amount' not in df.columns:
        st.error("❌ Required column 'amount' not found in dataset")
        return
    
    # Get unique channels
    channels = df['sales_channel'].unique()
    
    if len(channels) < 2:
        st.warning(f"⚠️ Need at least 2 groups for comparison. Found: {len(channels)}")
        st.info("💡 Your dataset should have both Domestic and International channels")
        return
    
    st.success(f"✅ Found {len(channels)} sales channels: {', '.join(channels)}")
    
    # Select comparison variable
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in ['order_id', 'year', 'month']]
    
    comparison_var = st.selectbox(
        "Select variable to compare",
        options=numeric_cols,
        index=numeric_cols.index('amount') if 'amount' in numeric_cols else 0
    )
    
    # Prepare groups
    # Group and ensure each group is a Series, not a float
    grouped = {
        name: g[comparison_var].dropna()
        for name, g in df.groupby('sales_channel')
    }

    # Filter out empty groups
    grouped = {k: v for k, v in grouped.items() if len(v) >= 1}

    if len(grouped) < 2:
        st.error("❌ Not enough valid groups for t-test.")
        return

    group_names = list(grouped.keys())
    group_a = grouped[group_names[0]]
    group_b = grouped[group_names[1]]

    
    # Check minimum sample size
    if len(group_a) < 2 or len(group_b) < 2:
        st.error(f"❌ Insufficient data: {group_names[0]} has {len(group_a)} samples, {group_names[1]} has {len(group_b)} samples")
        st.info("💡 Each group needs at least 2 samples for t-test")
        return
    
    st.info(f"📊 Comparing **{group_names[0]}** (n={len(group_a)}) vs **{group_names[1]}** (n={len(group_b)})")
    
    # Descriptive statistics
    st.markdown("#### 📋 Descriptive Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{group_names[0]}**")
        st.metric("Mean", f"₹{group_a.mean():,.2f}")
        st.metric("Median", f"₹{group_a.median():,.2f}")
        st.metric("Std Dev", f"₹{group_a.std():,.2f}")
        st.metric("Sample Size", f"{len(group_a):,}")
    
    with col2:
        st.markdown(f"**{group_names[1]}**")
        st.metric("Mean", f"₹{group_b.mean():,.2f}")
        st.metric("Median", f"₹{group_b.median():,.2f}")
        st.metric("Std Dev", f"₹{group_b.std():,.2f}")
        st.metric("Sample Size", f"{len(group_b):,}")
    
    # Visualization
    st.markdown("#### 📊 Distribution Comparison")
    
    # Combine data for plotting
    plot_df = pd.DataFrame({
        comparison_var: pd.concat([group_a, group_b]),
        'Group': [group_names[0]]*len(group_a) + [group_names[1]]*len(group_b)
    })
    
    tab1, tab2 = st.tabs(["Box Plot", "Histogram"])
    
    with tab1:
        fig = px.box(
            plot_df,
            x='Group',
            y=comparison_var,
            title=f"{comparison_var.title()} Distribution by Group",
            color='Group'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        fig = px.histogram(
            plot_df,
            x=comparison_var,
            color='Group',
            barmode='overlay',
            title=f"{comparison_var.title()} Histogram",
            opacity=0.7
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Perform t-test
    st.markdown("#### 🧪 t-Test Results")
    
    try:
        # Welch's t-test (doesn't assume equal variances)
        tstat, pvalue = ttest_ind(group_a, group_b, equal_var=False)
        
        # Check for valid results
        if np.isnan(tstat) or np.isnan(pvalue) or np.isinf(tstat):
            st.error("❌ t-test could not be computed. Possible reasons:")
            st.write("- One or both groups have zero variance (all values are identical)")
            st.write("- Insufficient data points")
            st.write("- Extreme outliers in the data")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("t-statistic", f"{tstat:.4f}")
        
        with col2:
            st.metric("p-value", f"{pvalue:.4f}")
        
        with col3:
            # Effect size (Cohen's d)
            pooled_std = np.sqrt((group_a.std()**2 + group_b.std()**2) / 2)
            if pooled_std > 0:
                cohens_d = abs((group_a.mean() - group_b.mean()) / pooled_std)
                st.metric("Cohen's d", f"{cohens_d:.4f}")
            else:
                st.metric("Cohen's d", "N/A")
        
        # Interpretation
        st.markdown("#### 💡 Interpretation")
        
        alpha = 0.05
        
        if pvalue < alpha:
            st.success(f"""
            ✅ **Statistically Significant Difference** (p = {pvalue:.4f} < 0.05)
            
            **Conclusion:** There is strong evidence that {group_names[0]} and {group_names[1]} 
            have different average {comparison_var} values.
            
            **Mean Difference:** ₹{abs(group_a.mean() - group_b.mean()):,.2f}
            
            **Business Implication:** The difference is unlikely due to chance. Consider this when 
            making strategic decisions about channel allocation and pricing.
            """)
        else:
            st.info(f"""
            ℹ️ **No Statistically Significant Difference** (p = {pvalue:.4f} ≥ 0.05)
            
            **Conclusion:** We don't have enough evidence to say {group_names[0]} and {group_names[1]} 
            have different average {comparison_var} values.
            
            **Business Implication:** The observed difference might be due to random chance. 
            Both channels perform similarly on this metric.
            """)
        
        # Effect size interpretation
        if pooled_std > 0:
            cohens_d = abs((group_a.mean() - group_b.mean()) / pooled_std)
            
            st.markdown("**Effect Size (Cohen's d):**")
            if cohens_d < 0.2:
                st.write("- 📏 **Small effect** (d < 0.2): Minimal practical difference")
            elif cohens_d < 0.5:
                st.write("- 📏 **Small to medium effect** (0.2 ≤ d < 0.5): Noticeable difference")
            elif cohens_d < 0.8:
                st.write("- 📏 **Medium to large effect** (0.5 ≤ d < 0.8): Substantial difference")
            else:
                st.write("- 📏 **Large effect** (d ≥ 0.8): Very substantial difference")
        
    except Exception as e:
        st.error(f"❌ Error performing t-test: {str(e)}")
        st.info("This might be due to insufficient data or data quality issues")

def show_chi_square(df):
    """Chi-square test of independence"""
    st.markdown("### 🔲 Chi-Square Test of Independence")
    
    st.info("""
    **Purpose:** Test if two categorical variables are related
    - Example: Is product category associated with shipping state?
    - **Null Hypothesis (H₀):** Variables are independent
    - **Alternative (H₁):** Variables are associated
    """)
    
    if 'category' not in df.columns or 'shipping_state' not in df.columns:
        st.error("❌ Required columns 'category' and/or 'shipping_state' not found")
        return
    
    # Limit to top categories and states for cleaner analysis
    top_n = st.slider("Number of top categories/states to analyze", 5, 15, 8)
    
    top_cats = df['category'].value_counts().head(top_n).index
    top_states = df['shipping_state'].value_counts().head(top_n).index
    
    df_subset = df[df['category'].isin(top_cats) & df['shipping_state'].isin(top_states)]
    
    if len(df_subset) < 10:
        st.error("❌ Insufficient data after filtering")
        return
    
    # Create contingency table
    table = pd.crosstab(df_subset['shipping_state'], df_subset['category'])
    
    st.markdown("#### 📊 Contingency Table")
    st.dataframe(table, use_container_width=True)
    
    # Visualize
    st.markdown("#### 🎨 Heatmap")
    
    fig = px.imshow(
        table,
        labels=dict(x="Category", y="State", color="Count"),
        title="Distribution of Categories across States",
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Perform chi-square test
    st.markdown("#### 🧪 Chi-Square Test Results")
    
    try:
        chi2, pvalue, dof, expected = chi2_contingency(table)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("χ² statistic", f"{chi2:.4f}")
        
        with col2:
            st.metric("p-value", f"{pvalue:.4f}")
        
        with col3:
            st.metric("Degrees of Freedom", f"{dof}")
        
        # Interpretation
        st.markdown("#### 💡 Interpretation")
        
        if pvalue < 0.05:
            st.success(f"""
            ✅ **Significant Association Found** (p = {pvalue:.4f} < 0.05)
            
            **Conclusion:** Product categories and shipping states are statistically associated.
            Certain categories are more popular in specific states.
            
            **Business Implication:** Customize inventory and marketing strategies by region.
            """)
        else:
            st.info(f"""
            ℹ️ **No Significant Association** (p = {pvalue:.4f} ≥ 0.05)
            
            **Conclusion:** No strong evidence that categories and states are related.
            
            **Business Implication:** Product preferences are similar across regions.
            """)
    
    except Exception as e:
        st.error(f"❌ Error performing chi-square test: {str(e)}")

def show_anova(df):
    """One-way ANOVA test"""
    st.markdown("### 📊 One-Way ANOVA Test")
    
    st.info("""
    **Purpose:** Compare means across 3+ groups
    - Example: Do different product categories have different revenues?
    - **Null Hypothesis (H₀):** All group means are equal
    - **Alternative (H₁):** At least one group differs
    """)
    
    if 'category' not in df.columns or 'amount' not in df.columns:
        st.error("❌ Required columns not found")
        return
    
    # Select top categories
    top_n = st.slider("Number of categories to compare", 3, 10, 6)
    
    top_cats = df['category'].value_counts().head(top_n).index
    df_subset = df[df['category'].isin(top_cats)]
    
    # Prepare groups
    groups = [df_subset[df_subset['category'] == cat]['amount'].dropna() for cat in top_cats]
    groups = [g for g in groups if len(g) > 2]
    
    if len(groups) < 3:
        st.error("❌ Need at least 3 groups with sufficient data")
        return
    
    st.success(f"✅ Comparing {len(groups)} categories")
    
    # Descriptive statistics
    st.markdown("#### 📋 Descriptive Statistics by Category")
    
    desc_stats = df_subset.groupby('category')['amount'].agg(['mean', 'median', 'std', 'count']).round(2)
    desc_stats.columns = ['Mean', 'Median', 'Std Dev', 'Count']
    st.dataframe(desc_stats, use_container_width=True)
    
    # Visualization
    st.markdown("#### 📊 Distribution Comparison")
    
    fig = px.box(
        df_subset,
        x='category',
        y='amount',
        title="Amount Distribution by Category",
        color='category'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Perform ANOVA
    st.markdown("#### 🧪 ANOVA Test Results")
    
    try:
        f_stat, pvalue = f_oneway(*groups)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("F-statistic", f"{f_stat:.4f}")
        
        with col2:
            st.metric("p-value", f"{pvalue:.4f}")
        
        # Interpretation
        st.markdown("#### 💡 Interpretation")
        
        if pvalue < 0.05:
            st.success(f"""
            ✅ **Significant Difference Found** (p = {pvalue:.4f} < 0.05)
            
            **Conclusion:** At least one category has a significantly different average amount.
            
            **Business Implication:** Categories have distinct revenue patterns. 
            Consider category-specific strategies.
            
            **Next Step:** Perform post-hoc tests (e.g., Tukey HSD) to identify which specific 
            categories differ from each other.
            """)
        else:
            st.info(f"""
            ℹ️ **No Significant Difference** (p = {pvalue:.4f} ≥ 0.05)
            
            **Conclusion:** All categories have similar average amounts.
            
            **Business Implication:** Categories perform similarly. 
            General strategies can work across all categories.
            """)
    
    except Exception as e:
        st.error(f"❌ Error performing ANOVA: {str(e)}")

def show_summary_report(df):
    """Comprehensive summary statistics"""
    st.markdown("### 📊 Summary Statistics Report")
    
    # Overall summary
    st.markdown("#### 📋 Descriptive Statistics (All Numerical Variables)")
    
    summary = df.describe(include='all').T
    st.dataframe(summary, use_container_width=True)
    
    # By channel
    if 'sales_channel' in df.columns:
        st.markdown("#### 🔄 Statistics by Sales Channel")
        
        channel_summary = df.groupby('sales_channel').agg({
            'amount': ['count', 'mean', 'median', 'std', 'min', 'max'],
            'quantity': ['sum', 'mean']
        }).round(2)
        
        st.dataframe(channel_summary, use_container_width=True)
    
    # By category
    if 'category' in df.columns:
        st.markdown("#### 📦 Top 10 Categories by Revenue")
        
        cat_summary = df.groupby('category')['amount'].agg(['sum', 'mean', 'count']).round(2)
        cat_summary.columns = ['Total Revenue', 'Avg Amount', 'Order Count']
        cat_summary = cat_summary.sort_values('Total Revenue', ascending=False).head(10)
        
        st.dataframe(cat_summary, use_container_width=True)