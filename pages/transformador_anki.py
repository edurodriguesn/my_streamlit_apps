import streamlit as st
import re

def tratar_texto(texto):
    """
    Aplica as mesmas transformações do script original:
    1. Remove linhas que começam com www.*
    2. Substitui quebras de linha por '<br>'
    3. Substitui 'Gabarito:' por '|Gabarito'
    4. Substitui números de questões por quebras de linha
    5. Limpa formatação desnecessária
    """
    # 1. Remover linhas que começam com www.*
    texto = re.sub(r'^www\..*\n?', '', texto, flags=re.MULTILINE)

    # 2. Substituir todas as quebras de linha por '<br>'
    texto = texto.replace('\n', '<br>')

    # 3. Substituir 'Gabarito:' por '|Gabarito'
    texto = texto.replace('Gabarito:', '|Gabarito')
    
    # 4. Substituir o número da questão por quebra de linha
    texto = re.sub(r'<br>[0-9][0-9]\)', '<br>\n', texto)    
    texto = re.sub(r'<br>[0-9]\)', '\n', texto)
    
    # 5. Limpar <br> no começo e fim de quebra de linhas e remover linhas não úteis
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
    
    # Sidebar com instruções
    with st.sidebar:
        st.header("ℹ️ Como usar")
        st.markdown("""
        1. Cole o texto que deseja transformar no campo abaixo
        2. Clique em 'Processar Texto'
        3. O resultado aparecerá na área de resultado
        4. Você pode copiar o texto processado
        """)
        
        st.header("🔧 Transformações aplicadas")
        st.markdown("""
        - Remove linhas que começam com www.*
        - Substitui quebras de linha por `<br>`
        - Substitui 'Gabarito:' por '|Gabarito'
        - Formata números de questões
        - Remove formatação desnecessária
        """)
    
    # Área principal
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📥 Texto de entrada")
        texto_entrada = st.text_area(
            "Cole seu texto aqui:",
            height=400,
            placeholder="Cole o texto que deseja transformar aqui...",
            help="Cole o texto que você quer processar para criar flashcards do Anki"
        )
        
        # Botão para processar
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
            # Exibir o resultado
            st.text_area(
                "Texto processado:",
                value=st.session_state['texto_processado'],
                height=400,
                help="Este é o texto transformado, pronto para usar no Anki"
            )
            
        else:
            st.info("👆 Processe um texto para ver o resultado aqui.")
    
    # Rodapé
    st.markdown("---")
    st.markdown("💡 **Dica:** Após processar o texto, você pode copiá-lo e colá-lo diretamente no Anki para criar seus flashcards!")

if __name__ == "__main__":
    # Inicializar variáveis de sessão
    if 'processado' not in st.session_state:
        st.session_state['processado'] = False
    if 'texto_processado' not in st.session_state:
        st.session_state['texto_processado'] = ""
    
    main()
