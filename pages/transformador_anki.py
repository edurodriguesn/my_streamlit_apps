import streamlit as st
import re

def tratar_texto(texto):
    texto = re.sub(r'(.*?)Assuntos\)', '', texto, flags=re.DOTALL)
    texto = re.sub(r'^www\..*\n?', '', texto, flags=re.MULTILINE)
    texto = texto.replace('\n', '<br>')
    texto = texto.replace('Gabarito:', '|Gabarito')
    texto = re.sub(r'<br>[0-9][0-9]\)', '<br>\n', texto)
    texto = re.sub(r'<br>[0-9]\)', '\n', texto)
    texto = texto.replace('<br>\n <br>', '\n')
    texto = texto.replace('\n <br>', '\n')
    texto = texto.replace('<br><br>', '<br>')
    texto = re.sub(r'<br>.<br>', '<br>', texto)
    texto = texto.replace('<br><br>', '<br>')
    texto = re.sub(r'.*Caderno de Questões.*\n', '', texto)
    return texto

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
        1. Cole o texto que deseja transformar no campo abaixo
        2. Clique em 'Processar Texto'
        3. O resultado aparecerá na área de resultado
        4. Você pode copiar ou baixar o texto processado
        """)
        
        st.header("🔧 Transformações aplicadas")
        st.markdown("""
        - Remove linhas que começam com www.*
        - Substitui quebras de linha por `<br>`
        - Substitui 'Gabarito:' por '|Gabarito'
        - Formata números de questões
        - Remove formatação desnecessária
        """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📥 Texto de entrada")
        texto_entrada = st.text_area(
            "Cole seu texto aqui:",
            height=400,
            placeholder="Cole o texto que deseja transformar aqui...",
            help="Cole o texto que você quer processar para criar flashcards do Anki"
        )
        
        if st.button("🔄 Processar Texto", type="primary", use_container_width=True):
            if texto_entrada.strip():
                with st.spinner("Processando texto..."):
                    texto_processado = tratar_texto(texto_entrada)
                    st.session_state['texto_processado'] = texto_processado
                    st.session_state['processado'] = True
            else:
                st.warning("⚠️ Por favor, insira algum texto para processar.")
    
    with col2:
        st.subheader("📤 Resultado processado")
        
        if st.session_state.get('processado', False) and 'texto_processado' in st.session_state:
            st.text_area(
                "Texto processado:",
                value=st.session_state['texto_processado'],
                height=400,
                help="Texto transformado, pronto para usar no Anki"
            )

            # 🔥 Botão de download como TXT
            st.download_button(
                label="📥 Baixar como cards.txt",
                data=st.session_state['texto_processado'],
                file_name="cards.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("👆 Processe um texto para ver o resultado aqui.")
    
    st.markdown("---")
    st.markdown("💡 **Dica:** Após processar o texto, você pode copiar ou baixar o resultado para usar no Anki!")

if __name__ == "__main__":
    if 'processado' not in st.session_state:
        st.session_state['processado'] = False
    if 'texto_processado' not in st.session_state:
        st.session_state['texto_processado'] = ""
    
    main()
