import streamlit as st
import re

st.title("Tratador de Quebras de Linha (PDF)")

texto = st.text_area("Cole o texto aqui:", height=300)

def tratar_texto(t):
    # Remove quebras de linha que NÃO venham depois de um ponto
    t = re.sub(r'(?<!\.)\n', ' ', t)

    # Remover tempos do tipo 1m, 25m, 30m etc.
    t = re.sub(r'\b\d{1,2}m\b', '', t)

    # Remover o link (com possível número na frente)
    t = re.sub(r'www\.grancursosonline\.com\.br\s*\d*', '', t)

    # Remover mensagem de erro completa
    t = re.sub(r'Viu algum erro neste material\? Contate-nos em: degravacoes@grancursosonline\.com\.br', '', t, flags=re.IGNORECASE)

    # Remover múltiplos espaços gerados após substituições
    t = re.sub(r'\s{2,}', ' ', t)

    return t.strip()

if st.button("Tratar texto"):
    saida = tratar_texto(texto)
    st.text_area("Texto tratado:", saida, height=300)
    st.text("Agora basta selecionar e copiar o texto tratado!")

    