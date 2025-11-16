"""
network_visualization.py - FIXED VERSION
Builds interactive network graphs from association rules using PyVis
All emoji encoding fixed, optimized for Streamlit display
"""

import pandas as pd
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CORE FUNCTION: Generate Association Rules from DataFrame
# =============================================================================
def generate_association_rules(df, min_support=0.05, min_lift=1.2, min_conf=0.3):
    """
    Generate association rules from transaction data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'order_id' and 'category' columns
    min_support : float
        Minimum support threshold (default: 0.05)
    min_lift : float
        Minimum lift threshold (default: 1.2)
    min_conf : float
        Minimum confidence threshold (default: 0.3)
    
    Returns:
    --------
    pd.DataFrame or None
        DataFrame containing association rules with columns:
        - antecedents (string)
        - consequents (string)
        - antecedents_raw (list)
        - consequents_raw (list)
        - support, confidence, lift
    """
    
    if df is None or df.empty:
        logger.warning("Empty dataframe provided")
        return None

    if 'order_id' not in df.columns or 'category' not in df.columns:
        logger.error("Required columns 'order_id' or 'category' not found")
        return None

    try:
        # Build transactions
        transactions = (
            df.groupby('order_id')['category']
            .apply(lambda s: list(s.dropna().astype(str)))
            .tolist()
        )
        
        # Remove duplicates within transactions
        transactions = [list(dict.fromkeys(t)) for t in transactions]
        
        # Filter out empty transactions
        transactions = [t for t in transactions if len(t) > 1]  # Need at least 2 items
        
        if len(transactions) == 0:
            logger.warning("No valid transactions found (need at least 2 items per transaction)")
            return None

        # One-hot encode transactions
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        basket = pd.DataFrame(te_ary, columns=te.columns_)
        
        # Generate frequent itemsets
        freqs = apriori(basket, min_support=min_support, use_colnames=True)
        
        if freqs.empty:
            logger.warning(f"No frequent itemsets found with min_support={min_support}")
            return None

        # Generate association rules
        rules = association_rules(freqs, metric='lift', min_threshold=min_lift)
        
        if rules.empty:
            logger.warning(f"No rules found with min_lift={min_lift}")
            return None

        # Filter by confidence
        rules = rules[rules['confidence'] >= min_conf]
        
        if rules.empty:
            logger.warning(f"No rules found with min_confidence={min_conf}")
            return None

        # Store RAW frozensets for network graph (IMPORTANT!)
        rules["antecedents_raw"] = rules["antecedents"].apply(lambda x: list(x))
        rules["consequents_raw"] = rules["consequents"].apply(lambda x: list(x))

        # Convert to human-readable strings for display
        rules['antecedents'] = rules['antecedents'].apply(
            lambda x: ', '.join(sorted(list(x)))
        )
        rules['consequents'] = rules['consequents'].apply(
            lambda x: ', '.join(sorted(list(x)))
        )

        # Sort by lift (most interesting rules first)
        rules = rules.sort_values('lift', ascending=False).reset_index(drop=True)
        
        logger.info(f"Generated {len(rules)} association rules")
        return rules
    
    except Exception as e:
        logger.error(f"Error generating association rules: {e}")
        return None


# =============================================================================
# NETWORK GRAPH BUILDER
# =============================================================================
def build_network_graph(rules_df, max_rules=30):
    """
    Build PyVis network graph from association rules.
    
    Parameters:
    -----------
    rules_df : pd.DataFrame
        Association rules with 'antecedents_raw' and 'consequents_raw' columns
    max_rules : int
        Maximum number of rules to visualize (default: 30)
    
    Returns:
    --------
    pyvis.network.Network or None
    """
    
    if rules_df is None or rules_df.empty:
        logger.warning("Empty rules dataframe")
        return None

    try:
        # Limit rules for performance
        if len(rules_df) > max_rules:
            rules_df = rules_df.head(max_rules)
            logger.info(f"Limited to top {max_rules} rules for visualization")

        # Initialize network
        net = Network(
            height="640px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#000000",
            notebook=False,
            directed=True
        )
        
        # Configure physics for better layout
        net.barnes_hut(
            gravity=-8000,
            central_gravity=0.3,
            spring_length=100,
            spring_strength=0.001,
            damping=0.09
        )

        # Track added nodes to avoid duplicates
        added_nodes = set()

        # Build network from rules
        for idx, row in rules_df.iterrows():
            raw_a = row['antecedents_raw']
            raw_c = row['consequents_raw']
            lift = float(row['lift'])
            conf = float(row['confidence'])
            supp = float(row['support'])

            # Add nodes and edges
            for a_item in raw_a:
                # Add antecedent node if not exists
                if a_item not in added_nodes:
                    net.add_node(
                        a_item,
                        label=a_item,
                        title=f"Category: {a_item}",
                        color="#667eea",
                        size=20
                    )
                    added_nodes.add(a_item)

                for c_item in raw_c:
                    # Add consequent node if not exists
                    if c_item not in added_nodes:
                        net.add_node(
                            c_item,
                            label=c_item,
                            title=f"Category: {c_item}",
                            color="#764ba2",
                            size=20
                        )
                        added_nodes.add(c_item)

                    # Add edge with rule metrics
                    edge_title = (
                        f"<b>Rule {idx + 1}</b><br>"
                        f"Lift: <b>{lift:.3f}</b><br>"
                        f"Confidence: <b>{conf:.3f}</b><br>"
                        f"Support: <b>{supp:.3f}</b><br>"
                        f"<i>{a_item} → {c_item}</i>"
                    )
                    
                    # Edge width based on lift
                    edge_width = min(10, max(1, int(lift * 2)))
                    
                    net.add_edge(
                        a_item,
                        c_item,
                        value=lift,
                        title=edge_title,
                        width=edge_width,
                        color={'color': '#999999', 'highlight': '#ff0000'}
                    )

        logger.info(f"Built network with {len(added_nodes)} nodes")
        return net
    
    except Exception as e:
        logger.error(f"Error building network graph: {e}")
        return None


# =============================================================================
# STREAMLIT COMPONENT: Display Network Graph
# =============================================================================
def display_network_graph(rules_df, max_rules=30):
    """
    Display interactive network graph in Streamlit.
    
    Parameters:
    -----------
    rules_df : pd.DataFrame
        Association rules dataframe
    max_rules : int
        Maximum rules to visualize
    """
    
    st.subheader("🔗 Association Rule Network Graph")
    
    if rules_df is None or rules_df.empty:
        st.warning("⚠️ No rules available to visualize.")
        return

    # Build network
    with st.spinner("Building interactive network graph..."):
        net = build_network_graph(rules_df, max_rules=max_rules)
    
    if net is None:
        st.error("❌ Could not build network graph.")
        return

    try:
        # Save to temporary file
        tmp_dir = tempfile.mkdtemp()
        html_path = os.path.join(tmp_dir, "network.html")
        net.save_graph(html_path)

        # Read HTML content
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Display in Streamlit
        st.success(f"✅ Network graph generated with {len(rules_df)} rules")
        
        # Show legend
        with st.expander("📖 How to Use the Network Graph"):
            st.markdown("""
            **Interaction:**
            - 🖱️ **Click & Drag** nodes to rearrange
            - 🔍 **Zoom** with mouse wheel
            - 👆 **Hover** over edges to see rule metrics
            - 📌 **Click** nodes to highlight connections
            
            **Color Legend:**
            - 🟦 **Blue nodes**: Antecedents (left side of rule)
            - 🟪 **Purple nodes**: Consequents (right side of rule)
            - ➡️ **Edge thickness**: Proportional to lift value
            
            **Metrics:**
            - **Lift**: How much more likely items appear together vs. random
            - **Confidence**: Probability of consequent given antecedent
            - **Support**: Frequency of itemset in transactions
            """)
        
        # Render graph
        components.html(html_content, height=700, scrolling=True)
        
        # Cleanup
        os.remove(html_path)
        os.rmdir(tmp_dir)
    
    except Exception as e:
        logger.error(f"Error displaying network: {e}")
        st.error(f"❌ Error displaying network: {e}")


# =============================================================================
# STREAMLIT PAGE: Standalone Network Dashboard
# =============================================================================
def show_network_dashboard(df):
    """
    Full network visualization dashboard page.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Transaction data with 'order_id' and 'category'
    """
    
    st.markdown("## 🌐 Network Graph Analysis")
    st.markdown("Interactive visualization of product association patterns")
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please load data first.")
        return
    
    # Check required columns
    if 'order_id' not in df.columns or 'category' not in df.columns:
        st.error("❌ Required columns 'order_id' and 'category' not found in data.")
        return
    
    st.markdown("---")
    
    # Parameter controls
    st.markdown("### ⚙️ Algorithm Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_support = st.slider(
            "Minimum Support",
            min_value=0.01,
            max_value=0.30,
            value=0.05,
            step=0.01,
            help="Minimum frequency of itemset (lower = more rules, slower)"
        )
    
    with col2:
        min_confidence = st.slider(
            "Minimum Confidence",
            min_value=0.10,
            max_value=0.90,
            value=0.30,
            step=0.05,
            help="Minimum probability of consequent given antecedent"
        )
    
    with col3:
        min_lift = st.slider(
            "Minimum Lift",
            min_value=0.5,
            max_value=5.0,
            value=1.2,
            step=0.1,
            help="Minimum association strength (>1 = positive association)"
        )
    
    max_rules = st.slider(
        "Maximum Rules to Visualize",
        min_value=10,
        max_value=100,
        value=30,
        step=5,
        help="Limit rules for better performance"
    )
    
    st.markdown("---")
    
    # Generate rules
    if st.button("🔄 Generate Network Graph", type="primary", use_container_width=True):
        with st.spinner("🔍 Mining association rules..."):
            rules = generate_association_rules(
                df,
                min_support=min_support,
                min_lift=min_lift,
                min_conf=min_confidence
            )
        
        if rules is None or rules.empty:
            st.warning("""
            ⚠️ No association rules found with current parameters.
            
            **Try:**
            - Lower minimum support (e.g., 0.03)
            - Lower minimum confidence (e.g., 0.20)
            - Lower minimum lift (e.g., 1.0)
            """)
            return
        
        # Display rules table
        st.markdown("### 📋 Association Rules Table")
        st.dataframe(
            rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head(50),
            use_container_width=True
        )
        
        # Download option
        csv = rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].to_csv(index=False)
        st.download_button(
            label="📥 Download Rules (CSV)",
            data=csv.encode('utf-8'),
            file_name="association_rules.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        
        # Display network graph
        display_network_graph(rules, max_rules=max_rules)
    
    else:
        st.info("👆 Click the button above to generate and visualize association rules")


# =============================================================================
# BACKWARD COMPATIBILITY: Keep old function name
# =============================================================================
def _rules_from_df(df, min_support=0.05, min_lift=1.2, min_conf=0.3):
    """
    Backward compatibility wrapper for generate_association_rules().
    DEPRECATED: Use generate_association_rules() instead.
    """
    return generate_association_rules(df, min_support, min_lift, min_conf)


def show_network_from_rules(rules_df):
    """
    Backward compatibility wrapper for display_network_graph().
    DEPRECATED: Use display_network_graph() instead.
    """
    display_network_graph(rules_df)
