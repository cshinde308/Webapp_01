import streamlit as st
from gui_canvas import run_gui

st.set_page_config(
    page_title="Black Canvas App",
    layout="wide",
    initial_sidebar_state="collapsed"
)

run_gui()