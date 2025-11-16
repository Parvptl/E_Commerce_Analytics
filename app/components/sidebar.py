# app/components/sidebar.py
import streamlit as st

def show_sidebar():
    st.sidebar.image("app/assets/nexus_logo.png", width=180)
    st.sidebar.title("NEXUS Dashboard")
    st.sidebar.markdown("Load data and filters")
    uploaded_dom = st.sidebar.file_uploader("Domestic CSV", type=['csv'], key='dom')
    uploaded_int = st.sidebar.file_uploader("International CSV", type=['csv'], key='int')
    load = st.sidebar.button("Load/Reload Data")
    st.sidebar.markdown("---")
    st.sidebar.markdown("Built by Parv • Nexus Analytics")
    return uploaded_dom, uploaded_int, load
