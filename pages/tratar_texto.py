import streamlit as st
import re
import streamlit.components.v1 as components

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

if "saida" not in st.session_state:
    st.session_state.saida = ""

col1, col2 = st.columns(2)

with col1:
    if st.button("Tratar texto"):
        st.session_state.saida = tratar_texto(texto)

with col2:
    if st.button("Tratar questão"):
        st.session_state.saida = re.sub(r'([A-E])\n', r'(\1)', texto)

if st.session_state.saida:
    st.text_area("Texto tratado:", st.session_state.saida, height=300)
    escaped = st.session_state.saida.replace('`', '\\`').replace('$', '\\$')
    components.html(f"""
        <button onclick="navigator.clipboard.writeText(`{escaped}`).then(() => this.innerText='✅ Copiado!').catch(() => this.innerText='❌ Erro')"
            style="padding:6px 16px;cursor:pointer;font-size:14px">📋 Copiar</button>
    """, height=45)

    