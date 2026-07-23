import streamlit as st
from code_formatter import get_css

def aplicar_estilos():
    st.markdown(get_css(), unsafe_allow_html=True)
    st.markdown("""
<style>
.alt-box {
    border: 2px solid transparent;
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 1.1rem;
}
.alt-box p { margin: 0; }
.correta { background-color: #d4edda; border-color: #28a745; }
.errada  { background-color: #f8d7da; border-color: #dc3545; }
.gabarito{ background-color: #d4edda; border-color: #28a745; }
.stRadio label { font-size: 3rem !important; }
[data-testid="stMarkdownContainer"] p { text-align: justify; }
</style>
""", unsafe_allow_html=True)
