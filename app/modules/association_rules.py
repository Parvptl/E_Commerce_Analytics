"""
association_rules.py - FIXED VERSION
Market Basket Analysis with Apriori algorithm
Integrates with network_visualization module
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import logging

# Import from network_visualization module
from app.modules.network_visualization import (
    generate_association_rules,
    display_network_graph
)

logger = logging.getLogger(__name__)


# =============================================================================
# MAIN DASHBOARD
# =============================================================================
def show_association_dashboard(df: pd.DataFrame):
    """
    Main Market Basket Analysis dashboard.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Transaction data with 'order_id' and 'category' columns
    """
    
    st.markdown("## 🛒 Market Basket Analysis")
    st.markdown("Discover product associations and cross-selling opportunities using the Apriori algorithm")
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please load data first.")
        return

    if "order_id" not in df.columns or "category" not in df.columns:
        st.error("❌ Dataset must include 'order_id' and 'category' columns.")
        return
    
    st.markdown("---")
    
    # =========================================================================
    # PARAMETER CONTROLS
    # =========================================================================
    st.markdown("### ⚙️ Algorithm Parameters")
    
    with st.expander("📖 Understanding Association Rule Metrics"):
        st.markdown("""
        **Support**: Frequency of itemset in transactions
        - Example: Support = 0.05 means itemset appears in 5% of transactions
        - Higher support = more common pattern
        
        **Confidence**: Probability of consequent given antecedent
        - Example: Confidence = 0.80 means 80% of customers who buy A also buy B
        - Higher confidence = stronger association
        
        **Lift**: Strength of association vs. random chance
        - Lift > 1: Items appear together more than random
        - Lift = 1: No association (random)
        - Lift < 1: Items avoid each other
        - Example: Lift = 2.5 means 2.5x more likely than random
        """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_support = st.slider(
            "Minimum Support",
            min_value=0.01,
            max_value=0.50,
            value=0.05,
            step=0.01,
            help="Lower values find more rules but slower"
        )
    
    with col2:
        min_conf = st.slider(
            "Minimum Confidence",
            min_value=0.10,
            max_value=0.99,
            value=0.30,
            step=0.01,
            help="Minimum prediction accuracy"
        )
    
    with col3:
        min_lift = st.slider(
            "Minimum Lift",
            min_value=0.50,
            max_value=10.00,
            value=1.20,
            step=0.10,
            help="Minimum association strength"
        )
    
    st.markdown("---")
    
    # =========================================================================
    # GENERATE RULES
    # =========================================================================
    if st.button("🔍 Generate Association Rules", type="primary", use_container_width=True):
        
        with st.spinner("⏳ Mining frequent itemsets and generating rules..."):
            rules = generate_association_rules(
                df,
                min_support=min_support,
                min_lift=min_lift,
                min_conf=min_conf
            )
        
        if rules is None or rules.empty:
            st.warning("""
            ⚠️ No association rules found with current parameters.
            
            **Suggestions:**
            - Try lowering minimum support (e.g., 0.03)
            - Try lowering minimum confidence (e.g., 0.20)
            - Try lowering minimum lift (e.g., 1.0)
            - Ensure your data has multi-item transactions
            """)
            return
        
        # Store in session state for persistence
        st.session_state['rules'] = rules
        
        st.success(f"✅ Generated {len(rules)} association rules!")
        
        # =====================================================================
        # DISPLAY RESULTS
        # =====================================================================
        show_rules_analysis(rules)
    
    else:
        # Check if rules already generated
        if 'rules' in st.session_state and st.session_state['rules'] is not None:
            st.info("📊 Showing previously generated rules. Click button above to regenerate with new parameters.")
            show_rules_analysis(st.session_state['rules'])
        else:
            st.info("👆 Click the button above to generate association rules")


# =============================================================================
# RULES ANALYSIS DISPLAY
# =============================================================================
def show_rules_analysis(rules):
    """
    Display comprehensive analysis of association rules.
    
    Parameters:
    -----------
    rules : pd.DataFrame
        Association rules dataframe
    """
    
    # =========================================================================
    # 1. RULES TABLE
    # =========================================================================
    st.markdown("---")
    st.markdown("### 📋 Top Association Rules")
    
    # Display top rules
    display_rules = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].copy()
    display_rules = display_rules.round(4)
    
    st.dataframe(
        display_rules.head(20),
        use_container_width=True,
        height=400
    )
    
    # Download button
    csv = display_rules.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download All Rules (CSV)",
        data=csv,
        file_name="association_rules.csv",
        mime="text/csv"
    )
    
    # =========================================================================
    # 2. VISUALIZATIONS
    # =========================================================================
    st.markdown("---")
    st.markdown("### 📊 Rule Visualizations")
    
    # Tab layout for different visualizations
    tab1, tab2, tab3 = st.tabs(["📈 Scatter Plot", "📊 Top Rules", "📉 Distributions"])
    
    with tab1:
        show_scatter_plot(rules)
    
    with tab2:
        show_top_rules_chart(rules)
    
    with tab3:
        show_metric_distributions(rules)
    
    # =========================================================================
    # 3. BUSINESS RECOMMENDATIONS
    # =========================================================================
    st.markdown("---")
    st.markdown("### 💡 Business Recommendations")
    
    show_business_recommendations(rules)
    
    # =========================================================================
    # 4. NETWORK GRAPH (OPTIONAL)
    # =========================================================================
    st.markdown("---")
    st.markdown("### 🌐 Network Visualization")
    
    if st.checkbox("Show Interactive Network Graph", value=False):
        max_rules = st.slider(
            "Maximum rules to visualize",
            min_value=10,
            max_value=50,
            value=20,
            help="Limit for better performance"
        )
        display_network_graph(rules, max_rules=max_rules)


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================
def show_scatter_plot(rules):
    """Support vs Confidence scatter plot"""
    
    st.markdown("#### 📈 Support vs Confidence (Bubble Size = Lift)")
    
    fig = px.scatter(
        rules,
        x='support',
        y='confidence',
        size='lift',
        color='lift',
        hover_data=['antecedents', 'consequents', 'lift'],
        title="Association Rules: Support vs Confidence",
        labels={
            'support': 'Support (Frequency)',
            'confidence': 'Confidence (Probability)',
            'lift': 'Lift (Association Strength)'
        },
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("""
    **How to read:** 
    - **Right side**: Higher frequency patterns
    - **Top**: More reliable predictions
    - **Larger bubbles**: Stronger associations
    """)


def show_top_rules_chart(rules):
    """Top rules by lift bar chart"""
    
    st.markdown("#### 📊 Top 10 Rules by Lift")
    
    top_rules = rules.nlargest(10, 'lift').copy()
    top_rules['rule'] = top_rules.apply(
        lambda x: f"{x['antecedents']} → {x['consequents']}",
        axis=1
    )
    
    fig = px.bar(
        top_rules,
        x='lift',
        y='rule',
        orientation='h',
        title="Strongest Association Rules",
        labels={'lift': 'Lift Value', 'rule': 'Rule'},
        color='lift',
        color_continuous_scale='Blues',
        text='lift'
    )
    
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def show_metric_distributions(rules):
    """Distribution histograms for metrics"""
    
    st.markdown("#### 📉 Metric Distributions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = px.histogram(
            rules,
            x='support',
            nbins=30,
            title="Support Distribution",
            labels={'support': 'Support', 'count': 'Frequency'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.histogram(
            rules,
            x='confidence',
            nbins=30,
            title="Confidence Distribution",
            labels={'confidence': 'Confidence', 'count': 'Frequency'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = px.histogram(
            rules,
            x='lift',
            nbins=30,
            title="Lift Distribution",
            labels={'lift': 'Lift', 'count': 'Frequency'}
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)


def show_business_recommendations(rules):
    """Generate business recommendations from top rules"""
    
    st.markdown("#### 🎯 Actionable Insights")
    
    # Get top 5 rules by lift
    top_5 = rules.nlargest(5, 'lift')
    
    for idx, row in top_5.iterrows():
        with st.expander(f"**Rule {idx + 1}**: {row['antecedents']} → {row['consequents']}"):
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.metric("Support", f"{row['support']:.3f}")
                st.metric("Confidence", f"{row['confidence']:.3f}")
                st.metric("Lift", f"{row['lift']:.3f}")
            
            with col2:
                st.markdown("**Business Actions:**")
                
                # Generate recommendations based on metrics
                if row['confidence'] > 0.7:
                    st.success("✅ **Strong Association** - High confidence rule")
                    st.markdown(f"""
                    - **Cross-Sell Strategy**: When customers buy **{row['antecedents']}**, 
                      actively recommend **{row['consequents']}** (70%+ success rate)
                    - **Product Bundling**: Create discounted bundle with both items
                    - **Email Marketing**: Send targeted recommendations to past buyers
                    """)
                
                if row['lift'] > 3.0:
                    st.info("💪 **Very Strong Association** - High lift value")
                    st.markdown(f"""
                    - **Website Layout**: Place these products near each other
                    - **Inventory Management**: Stock together in warehouse
                    - **Promotions**: "Frequently Bought Together" campaigns
                    """)
                
                if row['support'] > 0.1:
                    st.warning("🔥 **Popular Pattern** - High frequency")
                    st.markdown(f"""
                    - **High Priority**: Focus marketing efforts here
                    - **Scalable Impact**: Large customer base affected
                    - **A/B Testing**: Test bundle pricing for maximum revenue
                    """)
                
                # Calculate potential revenue impact
                st.markdown("**Estimated Impact:**")
                adoption_rate = min(row['confidence'], 0.5)  # Conservative estimate
                st.markdown(f"""
                - **Adoption Rate**: ~{adoption_rate*100:.0f}% (based on confidence)
                - **Recommendation**: Implement as automatic suggestion at checkout
                - **Priority**: {'🔴 High' if row['lift'] > 2.5 else '🟡 Medium' if row['lift'] > 1.5 else '🟢 Low'}
                """)
    
    # Summary recommendations
    st.markdown("---")
    st.markdown("#### 📌 Summary Recommendations")
    
    avg_lift = rules['lift'].mean()
    high_conf_rules = len(rules[rules['confidence'] > 0.5])
    
    st.info(f"""
    **Overall Insights:**
    - **Total Rules Found**: {len(rules)}
    - **High-Confidence Rules**: {high_conf_rules} (confidence > 50%)
    - **Average Lift**: {avg_lift:.2f}x above random chance
    
    **Next Steps:**
    1. Implement top 10 rules as automatic cross-sell recommendations
    2. Create product bundles for high-lift pairs
    3. Update website layout to co-locate associated products
    4. Train sales team on common product associations
    5. Monitor conversion rates and adjust thresholds monthly
    """)


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================
def prepare_basket_data(df, order_col='order_id', item_col='category'):
    """
    DEPRECATED: This function is no longer needed.
    Rule generation now handled in network_visualization module.
    Kept for backward compatibility.
    """
    logger.warning("prepare_basket_data() is deprecated. Use generate_association_rules() instead.")
    return None
