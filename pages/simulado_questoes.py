import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulado.ui import aplicar_estilos
from simulado.carregamento import secao_carregamento, processar_arquivo
from simulado.resultado import tela_resultado
from simulado.questao import secao_questao

st.set_page_config(page_title="Simulado de Questões", layout="centered")
aplicar_estilos()
st.title("📝 Simulado de Questões")

# Inicialização do estado para sequência atual de acertos
if "streak" not in st.session_state:
    st.session_state.streak = 0

uploaded_file, arquivo_local_selecionado = secao_carregamento()
processar_arquivo(uploaded_file, arquivo_local_selecionado)

if "arquivo_local_pdf" in st.session_state:
    arquivo_local_selecionado = st.session_state.arquivo_local_pdf

if "questoes" not in st.session_state:
    st.info("Envie um PDF ou selecione um arquivo do servidor para começar.")
    st.stop()

questoes = st.session_state.questoes
total = len(questoes)

if total == 0:
    st.warning("Nenhuma questão encontrada no arquivo.")
    st.stop()

if st.session_state.idx >= total:
    st.session_state.idx = total - 1

if st.session_state.finalizado:
    tela_resultado(questoes)

acertos = sum(
    1 for qid, resp in st.session_state.respostas.items()
    if any(q["alternativas"][ord(resp) - ord('A')] == q["gabarito"] for q in questoes if q["id"] == qid)
)
erros = len(st.session_state.respostas) - acertos

# Exibição das métricas apenas com a sequência atual
col_ac, col_er, col_str, col_tot = st.columns(4)
col_ac.metric("✅ Acertos", acertos)
col_er.metric("❌ Erros", erros)
col_str.metric("🔥 Sequência", st.session_state.streak)
col_tot.metric("📊 Respondidas", f"{len(st.session_state.respostas)}/{total}")
st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)

secao_questao(questoes, arquivo_local_selecionado)

st.components.v1.html(
    "<script>setInterval(()=>fetch(window.location.href,{method:'HEAD'}),60000)</script>",
    height=0
)