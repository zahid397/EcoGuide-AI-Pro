import streamlit as st
from utils.cards import render_card

def render(data):
    for item in data.get('activities', []):
        st.markdown(render_card(item), unsafe_allow_html=True)
        
