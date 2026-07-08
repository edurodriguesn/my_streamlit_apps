import streamlit as st
import tempfile
import os
import sys
import random
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extrator_questoes import processar_pdf

st.set_page_config(page_title="Simulado de Questões", layout="centered")

# CSS para colorir alternativas
st.markdown("""
<style>
.correta { background-color: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 8px; margin: 4px 0; font-size: 1.1rem; }
.errada { background-color: #f8d7da; border: 2px solid #dc3545; border-radius: 8px; padding: 8px; margin: 4px 0; font-size: 1.1rem; }
.gabarito { background-color: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 8px; margin: 4px 0; font-size: 1.1rem; }
.stRadio label { font-size: 3rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("📝 Simulado de Questões")

# Upload do PDF ou JSON
uploaded_file = st.file_uploader("Envie o PDF ou JSON com as questões", type=["pdf", "json"])

if uploaded_file:
    if "questoes" not in st.session_state or st.session_state.get("arquivo_nome") != uploaded_file.name:
        try:
            if uploaded_file.name.endswith(".json"):
                questoes = json.loads(uploaded_file.read().decode("utf-8"))
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                try:
                    with st.spinner("Gerando seu simulado, por favor aguarde alguns segundos..."):
                        questoes = processar_pdf(tmp_path)
                finally:
                    os.unlink(tmp_path)
            st.session_state.questoes = questoes
            st.session_state.arquivo_nome = uploaded_file.name
            st.session_state.idx = 0
            st.session_state.respostas = {}
            st.session_state.respondidas = {}
            st.session_state.mostrar_gabarito = {}
            st.session_state.finalizado = False
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")
            st.stop()

if "questoes" not in st.session_state:
    st.info("Envie um PDF para começar.")
    st.stop()

questoes = st.session_state.questoes
total = len(questoes)

if total == 0:
    st.warning("Nenhuma questão encontrada no PDF.")
    st.stop()

# Garantir que idx está dentro dos limites
if st.session_state.idx >= total:
    st.session_state.idx = total - 1

# Tela de resultado final
if st.session_state.finalizado:
    respondidas = len(st.session_state.respostas)
    acertos = sum(1 for qid, resp in st.session_state.respostas.items()
                  if any(q["alternativas"][ord(resp) - ord('A')] == q["gabarito"] for q in questoes if q["id"] == qid))
    porcentagem = (acertos / respondidas * 100) if respondidas > 0 else 0

    st.markdown("---")
    st.subheader("🏁 Resultado Final")
    st.metric("Acertos", f"{acertos}/{respondidas}")
    st.metric("Porcentagem", f"{porcentagem:.1f}%")
    st.metric("Erros", f"{respondidas - acertos}/{respondidas}")

    if st.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.idx = 0
        st.session_state.respostas = {}
        st.session_state.respondidas = {}
        st.session_state.mostrar_gabarito = {}
        st.session_state.finalizado = False
        st.rerun()
    st.stop()

# Contador de acertos/erros visível
acertos = sum(1 for qid, resp in st.session_state.respostas.items()
              if any(q["alternativas"][ord(resp) - ord('A')] == q["gabarito"] for q in questoes if q["id"] == qid))
erros = len(st.session_state.respostas) - acertos

col_ac, col_er, col_tot = st.columns(3)
col_ac.metric("✅ Acertos", acertos)
col_er.metric("❌ Erros", erros)
col_tot.metric("📊 Respondidas", f"{len(st.session_state.respostas)}/{total}")

st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)

# Questão atual
idx = st.session_state.idx
q = questoes[idx]
qid = q["id"]
letras = "ABCDE"

st.subheader(f"Questão {q['id']} de {total}")
st.markdown(q["enunciado"])

ja_respondida = qid in st.session_state.respondidas
mostrar_gab = st.session_state.mostrar_gabarito.get(qid, False)

# Mostrar alternativas
escolha = st.session_state.respostas.get(qid)

if not ja_respondida and not mostrar_gab:
    opcoes = [f"{letras[i]}) {alt}" for i, alt in enumerate(q["alternativas"])]
    selecao = st.radio("Alternativas:", opcoes, index=None, key=f"radio_{qid}")

    col_resp, col_gab = st.columns(2)
    with col_resp:
        if st.button("✔️ Responder", key=f"resp_{qid}", use_container_width=True):
            if selecao:
                letra = selecao[0]
                st.session_state.respostas[qid] = letra
                st.session_state.respondidas[qid] = True
                st.rerun()
            else:
                st.warning("Selecione uma alternativa.")
    with col_gab:
        if st.button("👁️ Mostrar Gabarito", key=f"gab_{qid}", use_container_width=True):
            st.session_state.mostrar_gabarito[qid] = True
            st.rerun()
else:
    gabarito_texto = q["gabarito"]
    # Encontrar a letra correta baseado no texto do gabarito
    letra_gabarito = None
    for i, alt in enumerate(q["alternativas"]):
        if alt == gabarito_texto:
            letra_gabarito = letras[i]
            break
    acertou = (escolha == letra_gabarito) if ja_respondida else None
    mostrar_correta = mostrar_gab or (ja_respondida and acertou)

    for i, alt in enumerate(q["alternativas"]):
        letra = letras[i]
        texto_alt = f"{letra}) {alt}"

        if ja_respondida:
            if mostrar_correta and letra == letra_gabarito:
                st.markdown(f'<div class="correta">{texto_alt}</div>', unsafe_allow_html=True)
            elif letra == escolha and not acertou:
                st.markdown(f'<div class="errada">{texto_alt}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"&nbsp;&nbsp;{texto_alt}")
        elif mostrar_gab:
            if letra == letra_gabarito:
                st.markdown(f'<div class="gabarito">{texto_alt}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"&nbsp;&nbsp;{texto_alt}")

    if ja_respondida and not acertou and not mostrar_gab:
        if st.button("👁️ Mostrar Resposta", key=f"mostrar_{qid}", use_container_width=True):
            st.session_state.mostrar_gabarito[qid] = True
            st.rerun()

st.markdown("---")

# Navegação
col_prev, col_next, col_rand, col_fim = st.columns([1, 1, 1, 1])
with col_prev:
    if st.button("⬅️ Anterior", disabled=(idx == 0), use_container_width=True):
        st.session_state.idx -= 1
        st.rerun()
with col_next:
    if st.button("➡️ Próxima", disabled=(idx == total - 1), use_container_width=True):
        st.session_state.idx += 1
        st.rerun()
with col_rand:
    if st.button("🎲 Aleatória", use_container_width=True):
        st.session_state.idx = random.randint(0, total - 1)
        st.rerun()
with col_fim:
    if st.button("🏁 Terminar", use_container_width=True):
        st.session_state.finalizado = True
        st.rerun()
