import streamlit as st

def cached_loader(func):
    return st.cache_data(func)
