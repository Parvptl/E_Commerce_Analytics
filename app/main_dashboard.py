# """
# NEXUS Dashboard - Main Application
# Fixed version with proper error handling and emoji encoding
# """

# import sys
# from pathlib import Path
# import streamlit as st
# import pandas as pd
# import logging

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # =====================================================
# # PATH SETUP
# # =====================================================
# ROOT_DIR = Path(__file__).resolve().parent.parent
# if str(ROOT_DIR) not in sys.path:
#     sys.path.insert(0, str(ROOT_DIR))

# # =====================================================
# # IMPORTS
# # =====================================================
# try:
#     from app.components.sidebar import show_sidebar
#     from app.modules import (
#         data_processing,
#         visualization,
#         statistical_inference,
#         association_rules,
#         clustering,
#         network_visualization
#     )
# except ImportError as e:
#     logger.error(f"Import error: {e}")
#     st.error(f"Module import failed: {e}")
#     st.stop()

# # =====================================================
# # PAGE CONFIG
# # =====================================================
# st.set_page_config(
#     page_title="NEXUS Dashboard",
#     page_icon="📈",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # =====================================================
# # CUSTOM CSS
# # =====================================================
# def load_custom_styles():
#     """Load custom CSS styles"""
#     st.markdown("""
#         <style>
#         /* Main container */
#         .main-header {
#             font-size: 2.5rem;
#             font-weight: bold;
#             background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
#             -webkit-background-clip: text;
#             -webkit-text-fill-color: transparent;
#             text-align: center;
#             padding: 1rem 0;
#         }
        
#         /* Metric cards */
#         .stMetric {
#             background-color: #f8f9fa;
#             padding: 1rem;
#             border-radius: 0.5rem;
#             box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#         }
        
#         /* Buttons */
#         .stButton>button {
#             border-radius: 0.5rem;
#             font-weight: 600;
#         }
        
#         /* Tabs */
#         .stTabs [data-baseweb="tab-list"] {
#             gap: 1rem;
#         }
        
#         .stTabs [data-baseweb="tab"] {
#             height: 50px;
#             padding: 0 1.5rem;
#             font-weight: 600;
#         }
        
#         /* DataFrames */
#         .dataframe {
#             font-size: 0.9rem;
#         }
#         </style>
#     """, unsafe_allow_html=True)

# load_custom_styles()

# # =====================================================
# # UTILITY FUNCTIONS
# # =====================================================
# def load_csv_safe(file):
#     """Safely load CSV file with error handling"""
#     if file is None:
#         return None
#     try:
#         df = pd.read_csv(file)
#         logger.info(f"Successfully loaded CSV: {file.name if hasattr(file, 'name') else 'file'}")
#         return df
#     except Exception as e:
#         logger.error(f"Error loading CSV: {e}")
#         st.error(f"❌ Error loading CSV file: {e}")
#         return None

# def try_load_local_data():
#     """Attempt to load data from local directory"""
#     dom_path = ROOT_DIR / "data" / "Amazon Sale Report.csv"
#     int_path = ROOT_DIR / "data" / "International sale Report.csv"
    
#     dom_df = None
#     int_df = None
    
#     if dom_path.exists():
#         try:
#             dom_df = pd.read_csv(dom_path)
#             logger.info(f"Loaded local domestic data: {len(dom_df)} rows")
#         except Exception as e:
#             logger.error(f"Error loading local domestic data: {e}")
    
#     if int_path.exists():
#         try:
#             int_df = pd.read_csv(int_path)
#             logger.info(f"Loaded local international data: {len(int_df)} rows")
#         except Exception as e:
#             logger.error(f"Error loading local international data: {e}")
    
#     return dom_df, int_df

# @st.cache_data(show_spinner=False)
# def process_data_cached(dom_df, int_df):
#     """Cache data processing for performance"""
#     return data_processing.process_data(dom_df, int_df)

# # =====================================================
# # MAIN APPLICATION
# # =====================================================
# def main():
#     """Main application entry point"""
    
#     # Header
#     st.markdown('<h1 class="main-header">🎯 NEXUS DASHBOARD</h1>', unsafe_allow_html=True)
#     st.markdown(
#         '<p style="text-align: center; color: #666; font-size: 1.1rem;">E-Commerce Analytics Platform: Domestic vs International Channels</p>',
#         unsafe_allow_html=True
#     )
#     st.markdown("---")
    
#     # Sidebar
#     uploaded_dom, uploaded_int, do_load = show_sidebar()
    
#     # =====================================================
#     # DATA LOADING LOGIC
#     # =====================================================
#     if do_load:
#         # Load from uploaded files
#         dom_df = load_csv_safe(uploaded_dom) if uploaded_dom else None
#         int_df = load_csv_safe(uploaded_int) if uploaded_int else None
        
#         if dom_df is None and int_df is None:
#             st.warning("⚠️ Please upload at least one CSV file to begin analysis.")
#             return
        
#         # Process data
#         with st.spinner("🔄 Processing data... Please wait."):
#             try:
#                 master = process_data_cached(dom_df, int_df)
                
#                 if master is None or master.empty:
#                     st.error("❌ Data processing failed. Please check your CSV files.")
#                     return
                
#                 st.session_state["master_df"] = master
#                 st.success(f"✅ Data loaded successfully! {len(master):,} records processed.")
#                 logger.info(f"Data processing complete: {len(master)} rows")
                
#             except Exception as e:
#                 logger.error(f"Data processing error: {e}")
#                 st.error(f"❌ Error processing data: {e}")
#                 return
    
#     else:
#         # Check if data already loaded
#         master = st.session_state.get("master_df", None)
        
#         # If not, try loading from local directory
#         if master is None:
#             with st.spinner("🔍 Looking for local data files..."):
#                 dom_df, int_df = try_load_local_data()
                
#                 if dom_df is None and int_df is None:
#                     st.info("📤 Please upload data files using the sidebar to begin analysis.")
                    
#                     # Show welcome message
#                     col1, col2, col3 = st.columns([1, 2, 1])
#                     with col2:
#                         st.markdown("""
#                         ### 👋 Welcome to NEXUS Dashboard
                        
#                         **Get Started:**
#                         1. Upload CSV files in the sidebar
#                         2. Click "Load Data" button
#                         3. Explore analytics across 6 modules
                        
#                         **Required Files:**
#                         - Amazon Sale Report.csv (Domestic)
#                         - International sale Report.csv (International)
                        
#                         **Features:**
#                         - 📊 ETL & Data Processing
#                         - 📈 Visual Analytics
#                         - 🔬 Statistical Testing
#                         - 🛒 Market Basket Analysis
#                         - 🎯 Clustering & Segmentation
#                         - 🌐 Network Visualization
#                         """)
#                     return
                
#                 # Process local data
#                 try:
#                     master = process_data_cached(dom_df, int_df)
#                     st.session_state["master_df"] = master
#                     st.success(f"📂 Loaded local dataset: {len(master):,} records")
#                     logger.info(f"Local data loaded: {len(master)} rows")
#                 except Exception as e:
#                     logger.error(f"Local data processing error: {e}")
#                     st.error(f"❌ Error processing local data: {e}")
#                     return
    
#     # Verify data is loaded
#     master = st.session_state.get("master_df", None)
#     if master is None or master.empty:
#         st.warning("⚠️ No processed data available. Please upload valid CSV files.")
#         return
    
#     # =====================================================
#     # NAVIGATION
#     # =====================================================
#     st.markdown("---")
    
#     pages = [
#         "🏠 Home",
#         "📊 ETL & Processing",
#         "📈 Visual Analytics",
#         "🔬 Statistical Tests",
#         "🛒 Market Basket",
#         "🎯 Clustering",
#         "🌐 Network Graph"
#     ]
    
#     selected_page = st.selectbox("📍 Navigate to Module", pages, label_visibility="collapsed")
    
#     st.markdown("---")
    
#     # =====================================================
#     # PAGE ROUTING
#     # =====================================================
#     try:
#         if selected_page == "🏠 Home":
#             show_home_page(master)
        
#         elif selected_page == "📊 ETL & Processing":
#             data_processing.show_etl_dashboard(master, master)
        
#         elif selected_page == "📈 Visual Analytics":
#             visualization.show_visualization_dashboard(master)
        
#         elif selected_page == "🔬 Statistical Tests":
#             statistical_inference.show_statistical_dashboard(master)
        
#         elif selected_page == "🛒 Market Basket":
#             association_rules.show_association_dashboard(master)
        
#         elif selected_page == "🎯 Clustering":
#             clustering.show_clustering_dashboard(master)
        
#         elif selected_page == "🌐 Network Graph":
#             network_visualization.show_network_dashboard(master)
    
#     except Exception as e:
#         logger.error(f"Page rendering error: {e}")
#         st.error(f"❌ Error displaying page: {e}")
#         st.info("Please try refreshing the page or contact support.")

# # =====================================================
# # HOME PAGE
# # =====================================================
# def show_home_page(df):
#     """Display executive summary home page"""
    
#     st.markdown("## 📊 Executive Summary")
    
#     # Calculate KPIs
#     total_revenue = df["amount"].sum()
#     total_orders = df["order_id"].nunique()
#     avg_aov = df["aov"].mean() if "aov" in df.columns else df["amount"].mean()
#     median_value = df["amount"].median()
    
#     # Display KPIs
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric(
#             "Total Revenue",
#             f"₹{total_revenue:,.0f}",
#             help="Sum of all transaction amounts"
#         )
    
#     with col2:
#         st.metric(
#             "Total Orders",
#             f"{total_orders:,}",
#             help="Count of unique orders"
#         )
    
#     with col3:
#         st.metric(
#             "Avg Order Value",
#             f"₹{avg_aov:.2f}",
#             help="Mean transaction value"
#         )
    
#     with col4:
#         st.metric(
#             "Median Value",
#             f"₹{median_value:.2f}",
#             help="50th percentile transaction value"
#         )
    
#     st.markdown("---")
    
#     # Channel comparison
#     if "sales_channel" in df.columns:
#         st.markdown("### 🔄 Channel Performance")
        
#         channel_metrics = df.groupby("sales_channel").agg({
#             "amount": ["sum", "mean", "count", "median"]
#         }).round(2)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown("#### 🏠 Domestic Channel")
#             if "Domestic" in channel_metrics.index:
#                 dom_data = channel_metrics.loc["Domestic"]
#                 st.metric("Revenue", f"₹{dom_data['amount']['sum']:,.0f}")
#                 st.metric("AOV", f"₹{dom_data['amount']['mean']:,.2f}")
#                 st.metric("Orders", f"{int(dom_data['amount']['count']):,}")
#                 st.metric("Median", f"₹{dom_data['amount']['median']:,.2f}")
        
#         with col2:
#             st.markdown("#### 🌍 International Channel")
#             if "International" in channel_metrics.index:
#                 int_data = channel_metrics.loc["International"]
#                 st.metric("Revenue", f"₹{int_data['amount']['sum']:,.0f}")
#                 st.metric("AOV", f"₹{int_data['amount']['mean']:,.2f}")
#                 st.metric("Orders", f"{int(int_data['amount']['count']):,}")
#                 st.metric("Median", f"₹{int_data['amount']['median']:,.2f}")
    
#     st.markdown("---")
    
#     # Quick insights
#     st.markdown("### 💡 Quick Insights")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if "category" in df.columns:
#             top_category = df.groupby("category")["amount"].sum().idxmax()
#             top_cat_revenue = df.groupby("category")["amount"].sum().max()
#             st.info(f"**Top Category:** {top_category}  \n**Revenue:** ₹{top_cat_revenue:,.0f}")
    
#     with col2:
#         if "shipping_state" in df.columns:
#             top_state = df.groupby("shipping_state")["amount"].sum().idxmax()
#             top_state_revenue = df.groupby("shipping_state")["amount"].sum().max()
#             st.info(f"**Top Market:** {top_state}  \n**Revenue:** ₹{top_state_revenue:,.0f}")
    
#     st.markdown("---")
    
#     # Navigation prompt
#     st.success("✨ Use the navigation menu above to explore detailed analytics across all modules!")

# # =====================================================
# # RUN APPLICATION
# # =====================================================
# if __name__ == "__main__":
#     main()


# Save this as main_dashboard.py with UTF-8 encoding
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.components.sidebar import show_sidebar
from app.modules import (
    data_processing, visualization, statistical_inference,
    association_rules, clustering, network_visualization
)

st.set_page_config(
    page_title="NEXUS Dashboard",
    page_icon="📈",
    layout="wide"
)

def load_csv_safe(file):
    if file is None:
        return None
    try:
        return pd.read_csv(file)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def try_load_local_data():
    dom_path = ROOT_DIR / "data" / "Amazon Sale Report.csv"
    int_path = ROOT_DIR / "data" / "International sale Report.csv"
    dom_df = pd.read_csv(dom_path) if dom_path.exists() else None
    int_df = pd.read_csv(int_path) if int_path.exists() else None
    return dom_df, int_df

@st.cache_data(show_spinner=False)
def process_data_cached(dom_df, int_df):
    return data_processing.process_data(dom_df, int_df)

def main():
    st.title("🎯 NEXUS DASHBOARD")
    st.markdown("E-Commerce Analytics Platform")
    st.markdown("---")
    
    uploaded_dom, uploaded_int, do_load = show_sidebar()
    
    if do_load:
        dom_df = load_csv_safe(uploaded_dom) if uploaded_dom else None
        int_df = load_csv_safe(uploaded_int) if uploaded_int else None
        
        if dom_df is None and int_df is None:
            st.warning("⚠️ Please upload at least one CSV file")
            return
        
        with st.spinner("Processing..."):
            master = process_data_cached(dom_df, int_df)
            if master is None or master.empty:
                st.error("❌ Processing failed")
                return
            st.session_state["master_df"] = master
            st.success(f"✅ Loaded {len(master):,} records")
    else:
        master = st.session_state.get("master_df", None)
        if master is None:
            dom_df, int_df = try_load_local_data()
            if dom_df is None and int_df is None:
                st.info("📤 Upload data files to begin")
                return
            master = process_data_cached(dom_df, int_df)
            st.session_state["master_df"] = master
    
    if master is None or master.empty:
        st.warning("⚠️ No data available")
        return
    
    st.markdown("---")
    
    pages = [
        "🏠 Home",
        "📊 ETL & Processing", 
        "📈 Visual Analytics",
        "🔬 Statistical Tests",
        "🛒 Market Basket",
        "🎯 Clustering",
        "🌐 Network Graph"
    ]
    
    selected = st.selectbox("Navigate", pages, label_visibility="collapsed")
    st.markdown("---")
    
    try:
        if selected == "🏠 Home":
            show_home(master)
        elif selected == "📊 ETL & Processing":
            data_processing.show_etl_dashboard(master, master)
        elif selected == "📈 Visual Analytics":
            visualization.show_visualization_dashboard(master)
        elif selected == "🔬 Statistical Tests":
            statistical_inference.show_statistical_dashboard(master)
        elif selected == "🛒 Market Basket":
            association_rules.show_association_dashboard(master)
        elif selected == "🎯 Clustering":
            clustering.show_clustering_dashboard(master)
        elif selected == "🌐 Network Graph":
            network_visualization.show_network_dashboard(master)
    except Exception as e:
        st.error(f"❌ Error: {e}")

def show_home(df):
    st.markdown("## 📊 Executive Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    total_revenue = df["amount"].sum()
    total_orders = df["order_id"].nunique()
    avg_aov = df["aov"].mean() if "aov" in df.columns else df["amount"].mean()
    median_value = df["amount"].median()
    
    col1.metric("Total Revenue", f"₹{total_revenue:,.0f}")
    col2.metric("Total Orders", f"{total_orders:,}")
    col3.metric("Avg Order Value", f"₹{avg_aov:.2f}")
    col4.metric("Median Value", f"₹{median_value:.2f}")
    
    st.markdown("---")
    st.success("✨ Use navigation above to explore modules!")

if __name__ == "__main__":
    main()