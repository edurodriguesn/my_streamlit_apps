import streamlit as st
import re

def tratar_texto(texto):
    """
    Pré-tratamento:
    - remove cabeçalho até 'Assuntos)'
    - remove linhas que começam com www.
    - marca questões antes de transformar quebras de linha em <br>
    - converte 'Gabarito:' em '|Gabarito'
    - limpezas diversas
    """
    # Remove cabeçalho até "Assuntos)"
    texto = re.sub(r'(.*?)Assuntos\)', '', texto, flags=re.DOTALL)

    # Remove linhas que começam com www.*
    texto = re.sub(r'^www\..*\n?', '', texto, flags=re.MULTILINE)

    # Marcar início de questões (antes de substituir \n por <br>) para não perder separação
    texto = re.sub(r'\n\s*(\d+)\)', r'\n@@Q@@\1)', texto)

    # Marcar "Certo" e "Errado" que aparecem sozinhos em linhas para preservá-los
    texto = re.sub(r'\n(Certo)\s*\n', r'\n@@CE@@\1@@CE@@\n', texto)
    texto = re.sub(r'\n(Errado)\s*\n', r'\n@@CE@@\1@@CE@@\n', texto)
    
    # Substitui quebras de linha por <br>
    texto = texto.replace('\n', '<br>')

    # Restaura marcador como quebras reais (cada questão começará em linha nova)
    texto = texto.replace('@@Q@@', '\n')
    
    # Restaura marcadores de Certo/Errado como quebras reais
    texto = texto.replace('@@CE@@', '\n')

    # Substituir 'Gabarito:' por '|Gabarito'
    texto = texto.replace('Gabarito:', '|Gabarito')

    # Limpezas
    texto = texto.replace('<br>\n <br>', '\n')
    texto = texto.replace('\n <br>', '\n')
    texto = texto.replace('<br><br>', '<br>')
    texto = re.sub(r'<br>.<br>', '<br>', texto)
    texto = texto.replace('<br><br>', '<br>')
    texto = re.sub(r'.*Caderno de Questões.*\n', '', texto)

    return texto

def gerar_cards(texto_tratado):
    """
    Processa o texto tratado e gera linhas no formato:
    Frente[TAB]Verso
    - Para questões com alternativas (a-e): gera 1 card por alternativa.
    - Para questões do tipo "Certo / Errado" (sem alternativas letra): gera 1 card com frente=enunciado e verso=gabarito.
    """

    # Cada bloco separado por linha (marcada antes com \n)
    blocos = [b.strip() for b in texto_tratado.split('\n') if b.strip()]
    cards = []

    for bloco in blocos:
        # localizar gabarito (pode ser letra A-E ou palavra Certo/Errado)
        gabarito_match = re.search(r'\|Gabarito\s*([A-Za-zÀ-ÿ0-9]+)', bloco, flags=re.IGNORECASE)
        if not gabarito_match:
            # tenta também caso "Gabarito:" tenha sido escrito de outro jeito ou esteja em linha separada
            gabarito_match = re.search(r'Gabarito[:\s]*([A-Za-zÀ-ÿ0-9]+)', bloco, flags=re.IGNORECASE)
            if not gabarito_match:
                continue
        gabarito_raw = gabarito_match.group(1).strip()
        gabarito_up = gabarito_raw.upper()

        # remover trecho do gabarito do bloco para não atrapalhar extração de enunciado/alternativas
        # Remove tanto "|Gabarito" quanto "Gabarito:" seguido de letra/palavra (em qualquer posição)
        bloco_sem_gab = re.sub(r'\|?Gabarito[:\s]*[A-Za-zÀ-ÿ0-9]+', '', bloco, flags=re.IGNORECASE).strip()

        # remover marcador inicial tipo "1)" caso exista
        bloco_sem_gab = re.sub(r'^\s*\d+\)\s*', '', bloco_sem_gab)

        # Extrair enunciado completo: tudo até a primeira alternativa "a)" ou até "Certo/Errado"
        enunciado = ""
        
        # Tentar encontrar onde começa a primeira alternativa ou Certo/Errado
        match_primeira_alt = re.search(r'<br>\s*a\)', bloco_sem_gab, flags=re.IGNORECASE)
        match_certo_errado = re.search(r'<br>\s*(?:Certo|Errado)\s*(?:<br>|$)', bloco_sem_gab, flags=re.IGNORECASE)
        
        # Determinar onde o enunciado termina
        if match_primeira_alt:
            enunciado = bloco_sem_gab[:match_primeira_alt.start()].strip()
        elif match_certo_errado:
            enunciado = bloco_sem_gab[:match_certo_errado.start()].strip()
        else:
            # Se não encontrou nada, pega tudo
            enunciado = bloco_sem_gab.strip()
        
        # Remover <br> extras no início e fim do enunciado
        enunciado = enunciado.strip('<br>').strip()

        # Preparar versão em texto "limpo" (substituir <br> por \n) para detectar linhas do tipo "Certo" / "Errado"
        plain = bloco_sem_gab.replace('<br>', '\n')
        linhas = [l.strip() for l in plain.splitlines() if l.strip()]

        # Detectar se há alternativas com letras (a) b) c) ...)
        tem_alternativas_com_letra = bool(re.search(r'<br>\s*[a-e]\)', bloco_sem_gab, flags=re.IGNORECASE) or
                                     any(re.match(r'^[a-e]\)', l, flags=re.IGNORECASE) for l in linhas))

        # Detectar se é questão do tipo "Certo/Errado"
        linhas_sem_gab = [l for l in linhas if not re.match(r'^\|?Gabarito', l, flags=re.IGNORECASE)]
        somente_ce = False

        if not tem_alternativas_com_letra:
            ce_items = [l.lower() for l in linhas_sem_gab if l.lower() in ('certo', 'errado')]
            if ce_items:
                somente_ce = True

        # Se for questão tipo Certo/Errado -> extrair enunciado completo corretamente
        if somente_ce:
            # extrair tudo até a primeira ocorrência de "Certo" ou "Errado"
            partes_ce = re.split(r'<br>\s*(?:Certo|Errado)\s*', bloco_sem_gab, maxsplit=1, flags=re.IGNORECASE)
            enunciado_ce = partes_ce[0].strip()
            
            # Limpar tags <br> no início e fim, mas manter <br> internos
            enunciado_ce = enunciado_ce.strip('<br>').strip()

            frente = enunciado_ce

            # determinar verso pelo gabarito
            if gabarito_up.startswith('C'):
                verso = "Certo"
            elif gabarito_up.startswith('E'):
                verso = "Errado"
            else:
                verso = gabarito_raw

            cards.append(f"{frente}\t{verso}")
            continue

        # Caso padrão: tem alternativas com letras -> criar 1 card por alternativa
        # Expressão robusta para capturar alternativas preceded by <br>a) ... until next <br>[b-e]) or end
        padrao_alt = re.compile(r'<br>\s*([a-e])\)\s*(.*?)(?=(?:<br>\s*[a-e]\)|$))', flags=re.IGNORECASE | re.DOTALL)
        alternativas_matches = padrao_alt.findall(bloco_sem_gab)

        # fallback: tentar sem <br> (apenas em caso de variação do formato)
        if not alternativas_matches:
            padrao_alt2 = re.compile(r'([a-e])\)\s*(.*?)(?=(?:[a-e]\)|$))', flags=re.IGNORECASE | re.DOTALL)
            alternativas_matches = padrao_alt2.findall(bloco_sem_gab)

        if not alternativas_matches:
            # se ainda não encontrou alternativas, pular (ou poderia criar card único)
            continue

        # gerar cards por alternativa
        for letra, texto_alt in alternativas_matches:
            letra = letra.upper()
            # Manter <br> no texto da alternativa, apenas limpar início/fim
            texto_alt = texto_alt.strip()
            # Remover qualquer resíduo de gabarito que possa ter ficado
            texto_alt = re.sub(r'\|?Gabarito[:\s]*[A-Za-zÀ-ÿ0-9]+', '', texto_alt, flags=re.IGNORECASE).strip()
            frente = f"{enunciado} {texto_alt}".strip()
            verso = "Certo" if letra == gabarito_up else "Errado"
            cards.append(f"{frente}\t{verso}")

    return "\n".join(cards)


def main():
    st.set_page_config(
        page_title="Transformador de Questões em Cards (1 alternativa = 1 card)",
        page_icon="📝",
        layout="wide"
    )

    st.title("📝 Transformador de Questões em Cards (1 alternativa = 1 card)")
    st.markdown("---")

    with st.sidebar:
        st.header("Como usar")
        st.markdown("""
        1. Cole o texto com várias questões (igual ao exemplo).
        2. O script identifica dois tipos:
           - Alternativas a)–e) → 1 card por alternativa.
           - Questão estilo "Certo / Errado" (sem letras) → 1 card (frente=enunciado, verso=gabarito).
        3. Clique em **Processar Texto** e copie o resultado (Frente[TAB]Verso) para importar no Anki.
        """)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Texto de entrada")
        texto_entrada = st.text_area(
            "Cole seu texto aqui:",
            height=520,
            placeholder="Cole o texto bruto com várias questões (e gabaritos) ..."
        )

        if st.button("🔄 Processar Texto", type="primary", use_container_width=True):
            if texto_entrada.strip():
                with st.spinner("Processando..."):
                    tratado = tratar_texto(texto_entrada)
                    resultado = gerar_cards(tratado)
                    st.session_state['resultado'] = resultado
                    st.session_state['processado'] = True
            else:
                st.warning("Insira algum texto para processar.")

    with col2:
        st.subheader("Cards gerados")
        if st.session_state.get('processado', False) and 'resultado' in st.session_state:
            st.text_area("Resultado (cada linha = Frente[TAB]Verso):", value=st.session_state['resultado'], height=520)
            st.markdown("**Dica:** copie tudo e cole no Anki (campo 1 = frente, campo 2 = verso).")
            
            # Botão de download
            st.download_button(
                label="📥 Baixar arquivo TXT",
                data=st.session_state['resultado'],
                file_name="cards_anki.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.info("Cole o texto à esquerda e clique em 'Processar Texto'.")

    st.markdown("---")
    st.markdown("Se quiser, posso adicionar exportação CSV, destacar a alternativa correta na frente, ou gerar .apkg para download.")

if __name__ == "__main__":
    if 'processado' not in st.session_state:
        st.session_state['processado'] = False
    if 'resultado' not in st.session_state:
        st.session_state['resultado'] = ""
    main()