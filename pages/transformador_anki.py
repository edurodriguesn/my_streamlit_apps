import streamlit as st
import re


def tratar_texto(texto, cebraspe_option=False):
    # Limpezas iniciais
    texto = re.sub(r'(.*?)Assuntos\)', '', texto, flags=re.DOTALL)
    texto = re.sub(r'^www\..*\n?', '', texto, flags=re.MULTILINE)

    # Padroniza gabarito
    texto = texto.replace('Gabarito:', '|Gabarito')

    if not cebraspe_option:
        linhas = texto.splitlines()
        novas_linhas = []

        for i, linha in enumerate(linhas):
            match_gab = re.search(r'\|Gabarito\s*([A-E])', linha)
            if match_gab:
                letra = match_gab.group(1).lower()

                alternativa = None
                # procura a alternativa acima
                for j in range(i - 1, -1, -1):
                    m_alt = re.match(rf'{letra}\)\s*(.*)', linhas[j], re.IGNORECASE)
                    if m_alt:
                        alternativa = m_alt.group(1).strip()
                        break

                if alternativa:
                    novas_linhas.append(f"| {alternativa}")
                else:
                    novas_linhas.append(linha)
            else:
                novas_linhas.append(linha)

        texto = "\n".join(novas_linhas)

    texto = texto.replace('\n', '<br>')

    # Outras limpezas já existentes
    texto = re.sub(r'<br>[0-9]{1,4}\)', '\n', texto)
    texto = texto.replace('<br>\n <br>', '\n')
    texto = texto.replace('\n <br>', '\n')
    texto = texto.replace('<br><br>', '<br>')
    texto = re.sub(r'<br>.<br>', '<br>', texto)
    texto = texto.replace('<br><br>', '<br>')
    texto = texto.replace('<br>| ', '|')
    texto = re.sub(r'^\n', '', texto)
    texto = re.sub(r'.*Caderno de Questões.*\n', '', texto)

    return texto


# ➕ CEBRASPE (INALTERADO)
def tratar_cebraspe(texto):
    cards = re.split(r'(?=\n)', texto)

    novos_cards = []
    for card in cards:
        c = card.strip()
        if not c:
            continue

        match = re.search(r'\.<br>', c)
        if match:
            c = c[match.end():].lstrip()

        c = re.sub(r'Certo<br>Errado<br>', '', c)
        c = re.sub(r'Certo<br>Errado', '', c)
        c = re.sub(r'Certo Errado', '', c)
        c = re.sub(r'<br>\|', '|', c)
        c = re.sub(r'^<br>', '', c)
        c = re.sub(r'Gabarito ', '', c)

        novos_cards.append(c)

    return "\n".join(novos_cards)


def main():
    st.set_page_config(
        page_title="Transformador de Texto para Anki",
        page_icon="📝",
        layout="wide"
    )

    st.title("📝 Transformador de Texto para Anki")
    st.markdown("---")

    with st.sidebar:
        st.header("ℹ️ Como usar")
        st.markdown("""
        1. Cole o texto que deseja transformar
        2. Marque opções extras se desejar
        3. Clique em 'Processar Texto'
        4. Copie ou baixe o resultado
        """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Texto de entrada")
        texto_entrada = st.text_area("Cole seu texto aqui:", height=400)
        cebraspe_option = st.checkbox(
            "Marque aqui se todas as questões são da banca Cebraspe",
            value=False
        )

        if st.button("🔄 Processar Texto", type="primary", use_container_width=True):
            if texto_entrada.strip():
                texto_processado = tratar_texto(texto_entrada, cebraspe_option)

                if cebraspe_option:
                    texto_processado = tratar_cebraspe(texto_processado)

                st.session_state['texto_processado'] = texto_processado
                st.session_state['processado'] = True
            else:
                st.warning("⚠️ Por favor, insira algum texto.")

    with col2:
        st.subheader("📤 Resultado processado")

        if st.session_state.get('processado'):
            st.text_area(
                "Texto processado:",
                value=st.session_state['texto_processado'],
                height=400
            )

            st.download_button(
                "📥 Baixar como cards.txt",
                st.session_state['texto_processado'],
                "cards.txt",
                "text/plain",
                use_container_width=True
            )
        else:
            st.info("👆 Processe um texto para ver o resultado aqui.")


if __name__ == "__main__":
    st.session_state.setdefault('processado', False)
    st.session_state.setdefault('texto_processado', "")
    main()
