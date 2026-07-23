import streamlit as st
from code_formatter import get_css

def aplicar_estilos():
    st.markdown(get_css(), unsafe_allow_html=True)
    st.markdown("""
<style>
.correta { 
    background-color: #d4edda; 
    color: #000000 !important; 
    border: 2px solid #28a745; 
    border-radius: 8px; 
    padding: 8px; 
    margin: 4px 0; 
    font-size: 1.1rem; 
}
.errada { 
    background-color: #f8d7da; 
    color: #000000 !important; 
    border: 2px solid #dc3545; 
    border-radius: 8px; 
    padding: 8px; 
    margin: 4px 0; 
    font-size: 1.1rem; 
}
.gabarito { 
    background-color: #d4edda; 
    color: #000000 !important; 
    border: 2px solid #28a745; 
    border-radius: 8px; 
    padding: 8px; 
    margin: 4px 0; 
    font-size: 1.1rem; 
}
.stRadio label { font-size: 3rem !important; }
[data-testid="stMarkdownContainer"] p { text-align: justify; }
</style>
""", unsafe_allow_html=True)
