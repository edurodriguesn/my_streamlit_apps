import streamlit as st


def tela_resultado(questoes):
    respondidas = len(st.session_state.respostas)
    acertos = sum(
        1 for qid, resp in st.session_state.respostas.items()
        if any(q["alternativas"][ord(resp) - ord('A')] == q["gabarito"] for q in questoes if q["id"] == qid)
    )
    porcentagem = (acertos / respondidas * 100) if respondidas > 0 else 0

    st.markdown("---")
    st.subheader("🏁 Resultado Final")
    st.metric("Acertos", f"{acertos}/{respondidas}")
    st.metric("Porcentagem", f"{porcentagem:.1f}%")
    st.metric("Erros", f"{respondidas - acertos}/{respondidas}")

    blocos_html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin:16px 0">'
    for i, q in enumerate(questoes):
        qid = q["id"]
        resp = st.session_state.respostas.get(qid)
        if resp is not None:
            cor = "#28a745" if q["alternativas"][ord(resp) - ord('A')] == q["gabarito"] else "#dc3545"
        else:
            cor = "#aaaaaa"
        blocos_html += (
            f'<div style="width:44px;height:44px;background:{cor};border-radius:6px;'
            f'display:flex;align-items:center;justify-content:center;'
            f'color:#fff;font-weight:bold;font-size:0.75rem">{i+1}</div>'
        )
        if (i + 1) % 10 == 0:
            blocos_html += '<div style="width:100%;height:0"></div>'
    blocos_html += '</div>'
    st.markdown(blocos_html, unsafe_allow_html=True)

    if st.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.idx = 0
        st.session_state.respostas = {}
        st.session_state.respondidas = {}
        st.session_state.mostrar_gabarito = {}
        st.session_state.eliminadas = {}
        st.session_state.finalizado = False
        st.rerun()
    st.stop()
