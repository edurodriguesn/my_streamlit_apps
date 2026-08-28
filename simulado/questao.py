import streamlit as st
import re
import os
import random
import html as html_lib
from code_formatter import format_enunciado


def highlight_texto(text):
    highlighted = re.sub(r'\*\*\*(.+?)\*\*\*', r'<span style="background:white;color:black;padding:0 2px">\1</span>', text)
    if highlighted == text:
        return text, False
    return highlighted.replace('\n', '<br>'), True


def escape_markdown(text):
    text = text.replace('\n', '  \n')
    text = text.replace('R$', 'R\x00')
    pattern = r'(?<!\\)(\$.*?(?<!\\)\$)|\$'
    def replace_match(match):
        if match.group(1):
            return match.group(1)
        return r'\$'
    text = re.sub(pattern, replace_match, text)
    return text.replace('R\x00', r'R\$')


def render_alternativa_com_imagens(prefixo, alt, arquivo_local_selecionado, css=None):
    partes = re.split(r'\{image\((\d+)\)\}', alt)
    tem_imagem = len(partes) > 1
    texto_inicial = partes[0].strip()
    label = f"{prefixo} {texto_inicial}" if texto_inicial else prefixo
    if css:
        st.markdown(f'<div class="{css}">{html_lib.escape(label)}</div>', unsafe_allow_html=True)
    else:
        st.markdown(escape_markdown(label))
    for i, parte in enumerate(partes[1:], 1):
        if i % 2 == 1:
            if arquivo_local_selecionado:
                pasta_json = os.path.basename(os.path.dirname(arquivo_local_selecionado))
                nome_json = os.path.splitext(os.path.basename(arquivo_local_selecionado))[0]
                img_path = os.path.join("images", pasta_json, f"{nome_json}-{parte}")
                for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    if os.path.exists(img_path + ext):
                        st.image(img_path + ext)
                        break
                else:
                    st.warning(f"Imagem não encontrada: {img_path}")
        else:
            texto = parte.strip()
            if texto:
                if css:
                    st.markdown(f'<div class="{css}">{html_lib.escape(texto)}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(escape_markdown(texto))


def render_enunciado_com_imagens(enunciado, arquivo_local_selecionado):
    partes = re.split(r'\{image\((\d+)\)\}', enunciado)
    for i, parte in enumerate(partes):
        if i % 2 == 0:
            enunciado_html, tem_codigo = format_enunciado(parte)
            if tem_codigo:
                st.markdown(enunciado_html, unsafe_allow_html=True)
            elif parte.strip():
                highlighted, tem_highlight = highlight_texto(parte)
                if tem_highlight:
                    st.markdown(highlighted, unsafe_allow_html=True)
                else:
                    st.markdown(escape_markdown(parte))
        else:
            if arquivo_local_selecionado:
                pasta_json = os.path.basename(os.path.dirname(arquivo_local_selecionado))
                nome_json = os.path.splitext(os.path.basename(arquivo_local_selecionado))[0]
                img_path = os.path.join("images", pasta_json, f"{nome_json}-{parte}")
                for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    if os.path.exists(img_path + ext):
                        st.image(img_path + ext)
                        break
                else:
                    st.warning(f"Imagem não encontrada: {img_path}")


def secao_questao(questoes, arquivo_local_selecionado):
    total = len(questoes)
    idx = st.session_state.idx
    q = questoes[idx]
    qid = q["id"]
    letras = "ABCDE"

    col_titulo, col_ir = st.columns([3, 1])
    with col_titulo:
        st.subheader(f"Questão {q['id']} de {total}")
    with col_ir:
        ir_para = st.number_input("Ir para:", min_value=1, max_value=total, value=idx + 1,
                                  key=f"ir_questao_{idx}", label_visibility="collapsed")
        if ir_para != idx + 1:
            st.session_state.idx = ir_para - 1
            st.rerun()

    if q.get("assunto") or q.get("banca"):
        partes = []
        if q.get("assunto"): partes.append(f"📚 {q['assunto']}")
        if q.get("banca"): partes.append(f"🏛️ {q['banca']}")
        st.caption(" | ".join(partes))

    render_enunciado_com_imagens(q["enunciado"], arquivo_local_selecionado)

    ja_respondida = qid in st.session_state.respondidas
    mostrar_gab = st.session_state.mostrar_gabarito.get(qid, False)
    escolha = st.session_state.respostas.get(qid)

    if not ja_respondida and not mostrar_gab:
        elim = st.session_state.eliminadas.get(qid, set())
        alts_visiveis = [(letras[i], alt) for i, alt in enumerate(q["alternativas"]) if letras[i] not in elim]
        if not alts_visiveis:
            st.warning("Todas as alternativas foram eliminadas.")
            selecao = None
        else:
            opcoes_filtradas = [f"{letra}) {escape_markdown(re.sub(r'{image(.*?)}', '', alt)).strip()}" for letra, alt in alts_visiveis]
            selecao = st.radio("Alternativas:", opcoes_filtradas, index=None,
                               key=f"radio_{qid}", label_visibility="collapsed")
            for letra, alt in alts_visiveis:
                if re.search(r'\{image\(\d+\)\}', alt):
                    render_alternativa_com_imagens(f"{letra})", alt, arquivo_local_selecionado)

        opcoes_pills = [f"✂️{letras[i]}" for i in range(len(q["alternativas"])) if letras[i] not in elim]
        if elim:
            opcoes_pills.append("↩ Restaurar")
        eliminada_pill = st.pills("Eliminar letra:", opcoes_pills, key=f"pills_{qid}", label_visibility="collapsed")
        if eliminada_pill and eliminada_pill != "↩ Restaurar" and eliminada_pill[-1] not in elim:
            st.session_state.eliminadas.setdefault(qid, set()).add(eliminada_pill[-1])
            st.rerun()
        elif eliminada_pill == "↩ Restaurar":
            st.session_state.eliminadas[qid] = set()
            st.rerun()

        col_resp, col_gab = st.columns(2)
        with col_resp:
            if st.button("✔️ Responder", key=f"resp_{qid}", use_container_width=True):
                if selecao:
                    st.session_state.respostas[qid] = selecao[0]
                    st.session_state.respondidas[qid] = True
                    st.rerun()
                else:
                    st.warning("Selecione uma alternativa.")
        with col_gab:
            if st.button("👁️ Mostrar Gabarito", key=f"gab_{qid}", use_container_width=True):
                st.session_state.mostrar_gabarito[qid] = True
                st.rerun()
    else:
        letra_gabarito = next(
            (letras[i] for i, alt in enumerate(q["alternativas"]) if alt == q["gabarito"]), None
        )
        acertou = (escolha == letra_gabarito) if ja_respondida else None
        mostrar_correta = mostrar_gab or (ja_respondida and acertou)

        for i, alt in enumerate(q["alternativas"]):
            letra = letras[i]
            if ja_respondida:
                if mostrar_correta and letra == letra_gabarito:
                    css = "alt-box correta"
                elif letra == escolha and not acertou:
                    css = "alt-box errada"
                else:
                    css = "alt-box"
            elif mostrar_gab:
                css = "alt-box gabarito" if letra == letra_gabarito else "alt-box"
            else:
                css = "alt-box"
            render_alternativa_com_imagens(f"{letra})", alt, arquivo_local_selecionado, css=css)

        if ja_respondida and not acertou and not mostrar_gab:
            if st.button("👁️ Mostrar Resposta", key=f"mostrar_{qid}", use_container_width=True):
                st.session_state.mostrar_gabarito[qid] = True
                st.rerun()

    st.markdown('<hr style="margin:4px 0">', unsafe_allow_html=True)

    col_prev, col_next, col_rand, col_fim = st.columns(4)
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

    letra_gab = next(
        (letras[i] for i, alt in enumerate(q["alternativas"]) if alt == q["gabarito"]), None
    )
    texto_copiar = q["enunciado"] + "\n\n" + "\n".join(
        f"({letras[i]}) {alt}" for i, alt in enumerate(q["alternativas"])
    ) + (f"\n\nGabarito: {letra_gab}" if letra_gab else "")
    st.components.v1.html(f"""
        <textarea id="t" style="position:absolute;left:-9999px">{texto_copiar}</textarea>
        <button onclick="var t=document.getElementById('t');t.select();document.execCommand('copy');this.innerText='✅ Copiado! Quem cola prejudica a si mesmo!';setTimeout(()=>this.innerText='📋',2000)"
            style="cursor:pointer">
            📋
        </button>
    """, height=40)
