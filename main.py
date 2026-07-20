import streamlit as st

st.set_page_config(page_title="App Modular", layout="wide")

st.title("Bem-vindo ao App Modular!")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.subheader("Escolha uma das funcionalidades:")

    if st.button("📕📄 Tratar Texto de PDF", use_container_width=True):
        st.switch_page("pages/tratar_texto.py")

    if st.button("📘✨ Transformador TEC → Anki", use_container_width=True):
        st.switch_page("pages/transformador_anki.py")

    if st.button("🇺🇸🌐 Tradutor de Palavras EN → PT", use_container_width=True):
        st.switch_page("pages/palavras_ingles_anki.py")

    if st.button("📚📋 Organizador de Conteúdos de Edital", use_container_width=True):
        st.switch_page("pages/organizar_conteudo_edital.py")

    if st.button("📝 Gerador de Cards Alternativa por Alternativa", use_container_width=True):
        st.switch_page("pages/transformado_tec_anki_cespe.py")

    if st.button("🟣🦉 Extrator de Questões de PDF do Estratégia", use_container_width=True):
        st.switch_page("pages/estrategia_anki.py")

    if st.button("⚙️Gerador de Simulados TEC", use_container_width=True):
        st.switch_page("pages/simulado_questoes.py")

    if st.button("❓ (Questões sem ano) Extrator de Questões de PDF do Estratégia", use_container_width=True):
        st.switch_page("pages/(sem ano) estrategia_anki.py")