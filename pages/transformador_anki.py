import streamlit as st
import re

def tratar_texto(texto):
    texto = re.sub(r'(.*?)Assuntos\)', '', texto, flags=re.DOTALL)
    texto = re.sub(r'^www\..*\n?', '', texto, flags=re.MULTILINE)
    texto = texto.replace('\n', '<br>')
    texto = texto.replace('Gabarito:', '|Gabarito')
    
    # Trata questões com 1 a 4 dígitos antes do ')'
    texto = re.sub(r'<br>[0-9]{1,4}\)', '\n', texto)

    texto = texto.replace('<br>\n <br>', '\n')
    texto = texto.replace('\n <br>', '\n')
    texto = texto.replace('<br><br>', '<br>')
    texto = re.sub(r'<br>.<br>', '<br>', texto)
    texto = texto.replace('<br><br>', '<br>')
    texto = re.sub(r'.*Caderno de Questões.*\n', '', texto)
    
    return texto


# ➕ ADIÇÃO CEBRASPE: função pós-processamento
def tratar_cebraspe(texto):
    # quebra o texto em cartões pelo marcador de gabarito
    cards = re.split(r'(?=\n)', texto)

    novos_cards = []
    for card in cards:
        c = card.strip()

        if not c:
            continue

        # --- Remover prefixo antes do primeiro ponto ---
        # encontra o primeiro "." depois de algum texto
        match = re.search(r'\.<br>', c)
        if match:
            idx = match.end()
            c = c[idx:].lstrip()  # remove espaço ou <br> no começo

        # --- Remover bloco Certo Errado ---
        c = re.sub(r'Certo<br>Errado<br>', '', c)
        c = re.sub(r'Certo<br>Errado', '', c)
        c = re.sub(r'Certo Errado', '', c)
        c = re.sub(r'<br>\|', '|', c)   # remove <br>| e deixa só |
        c = re.sub(r'^<br>', '', c)     # remove <br> apenas no início
        c = re.sub(r'Gabarito ', '', c)

        novos_cards.append(c)

    # junta novamente com quebra dupla entre cartões
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

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📥 Texto de entrada")
        texto_entrada = st.text_area(
            "Cole seu texto aqui:",
            height=400
        )
        cebraspe_option = st.checkbox("Marque aqui se todas as questões são da banca Cebraspe", value=False)
        
        if st.button("🔄 Processar Texto", type="primary", use_container_width=True):
            if texto_entrada.strip():
                with st.spinner("Processando texto..."):
                    texto_processado = tratar_texto(texto_entrada)
                      
                    # ➕ ADIÇÃO CEBRASPE: aplicar depois do processamento normal
                    if cebraspe_option:
                        texto_processado = tratar_cebraspe(texto_processado)

                    st.session_state['texto_processado'] = texto_processado
                    st.session_state['processado'] = True
            else:
                st.warning("⚠️ Por favor, insira algum texto.")
    
    with col2:
        st.subheader("📤 Resultado processado")
        
        if st.session_state.get('processado', False):
            st.text_area(
                "Texto processado:",
                value=st.session_state['texto_processado'],
                height=400
            )

            st.download_button(
                label="📥 Baixar como cards.txt",
                data=st.session_state['texto_processado'],
                file_name="cards.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("👆 Processe um texto para ver o resultado aqui.")

if __name__ == "__main__":
    if 'processado' not in st.session_state:
        st.session_state['processado'] = False
    if 'texto_processado' not in st.session_state:
        st.session_state['texto_processado'] = ""
    
    main()
