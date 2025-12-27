import streamlit as st
import re
import io
import fitz

def limpar_rodape_estrategia(texto_completo):
    """
    Remove linhas contendo 'www.estrategiaconcursos.com.br',
    bem como 3 linhas acima e 3 linhas abaixo.
    """
    linhas = texto_completo.splitlines()
    indices_para_remover = set()

    for i, linha in enumerate(linhas):
        if "www.estrategiaconcursos.com.br" in linha:
            inicio = max(0, i - 3)
            fim = min(len(linhas), i + 4)
            for k in range(inicio, fim):
                indices_para_remover.add(k)
    
    linhas_limpas = [linha for i, linha in enumerate(linhas) if i not in indices_para_remover]
    return "\n".join(linhas_limpas)

def normalizar_tracos(txt):
    txt = (
        txt.replace("–", "-")
           .replace("—", "-")
           .replace("-", "-")
           .replace("‒", "-")
           .replace("−", "-")
    )
    txt = re.sub(r'\s\s', ' ', txt)
    txt = re.sub(r'[0-9]{1,4}\.', '.', txt)
    txt = re.sub(r'\b\d{1,2}\s\d{1,2}\b', '', txt)
    return txt

def validar_bloco_questao(texto):
    """
    Verifica se o bloco é válido.
    Exige apenas:
    1. Presença de 'Comentários'.
    2. Conteúdo de pergunta antes do comentário (> 30 chars).
    """
    match_comentario = re.search(r'Comentários?:', texto, re.IGNORECASE)
    
    if match_comentario:
        conteudo_antes = texto[:match_comentario.start()].strip()
        # Exige pelo menos 30 caracteres para considerar uma pergunta válida
        tem_pergunta = len(conteudo_antes) > 30
        return tem_pergunta
    
    return False

def formatar_questao_final(texto_bloco):
    """
    Aplica formatações e insere o PIPE.
    """
    # 1. REMOVER NUMERAÇÃO INICIAL (Ex: "14. ", "05. ", "1. ")
    texto_bloco = re.sub(r'^\s*\d{1,3}\.\s+', '', texto_bloco.strip())

    # 2. Inserir <br> antes de alternativas (a), b), c)...)
    texto_bloco = re.sub(r'\n([a-eA-E]\))', r'<br> \1', texto_bloco)

    # 3. Tratamento de quebras de linha
    texto_unido = re.sub(r'(?<!\.)\n', ' ', texto_bloco)
    texto_unido = re.sub(r'\n', ' <br> ', texto_unido)
    texto_unido = re.sub(r'^<br>', '', texto_unido)
    texto_unido = re.sub(r'\s+', ' ', texto_unido).strip()
    texto_unido = re.sub(r'^\.+\s+', '', texto_unido)
    texto_unido = re.sub(r'([a-z])([A-Z])', r'\1 \2', texto_unido)
    texto_unido = re.sub(r'([azA-Z][A-Z])([a-z])', r'\1 \2', texto_unido)
    

    # 4. CORTE COSMÉTICO (Gabarito final)
    # Tenta cortar se achar "Gabarito: Letra X" ou "Questão Correta" no final da string
    padrao_corte = (
        r'\bGabarito\b(?!\s+da)'
        r'(?=(?:\s*(?:é|:)\s*(?:a\s+)?)?(?:\s*(?:letra|item)?\s*[A-E]\b\.?))'
        r'(?:\s*(?:é|:)\s*(?:a\s+)?)?(?:\s*(?:letra|item)?\s*[A-E]\b\.?)'
        r'|Questão\s+(?:correta|certa|incorreta|errada)\.?'
    )

    match_corte = re.search(padrao_corte, texto_unido, re.IGNORECASE)
    if match_corte:
        texto_unido = texto_unido[:match_corte.end()]

    # 5. Inserir o PIPE (|)
    # Divisor: palavra "Comentários"
    match_sep = re.search(r'(Comentários?:)', texto_unido, re.IGNORECASE)
    
    if match_sep:
        idx = match_sep.start()
        parte_pergunta = texto_unido[:idx].strip()
        parte_resposta = texto_unido[idx:].strip()
        
        if parte_pergunta:
            final = f"{parte_pergunta}|{parte_resposta}"
        else:
            final = texto_unido
    else:
        final = texto_unido

    return final

def processar_texto(texto_bruto):
    # 1. Normalização e Limpeza de Rodapé
    texto_limpo = limpar_rodape_estrategia(texto_bruto)
    texto_limpo = normalizar_tracos(texto_limpo)

    # 2. Pré-tratamento do "Gabarito:"
    # Padrão: captura "Gabarito:" seguido de até 3 palavras OU até encontrar \n
    # Grupo 1: "Gabarito:"
    # Grupo 2: conteúdo até 3 palavras ou quebra de linha
    padrao_gabarito = r'(Gabarito:\s*)([^\n]*?)(?=\n|(?:\s+\S+){3}\s+)'
    
    def adicionar_ponto_gabarito(match):
        prefixo = match.group(1)  # "Gabarito: "
        conteudo = match.group(2).strip()  # conteúdo capturado
        
        # Pega até 3 palavras do conteúdo
        palavras = conteudo.split()
        ate_tres_palavras = ' '.join(palavras[:3])
        resto = ' '.join(palavras[3:]) if len(palavras) > 3 else ''
        
        # Monta o resultado com ponto e quebra de linha
        resultado = f"{prefixo}{ate_tres_palavras}.\n"
        if resto:
            resultado += resto
        
        return resultado
    
    texto_limpo = re.sub(padrao_gabarito, adicionar_ponto_gabarito, texto_limpo)

    # 3. Aplicação do padrão agressivo
    texto_marcado = re.sub(
        r'(?<![^\s.] )\(([^.]*?)\)',
        r'\n;;;(\1)',
        texto_limpo
    )



    # Verifica se o marcador foi inserido (debugging visual)
    if ";;;" not in texto_marcado:
        st.error("ERRO CRÍTICO: O padrão não foi encontrado no texto. O PDF pode estar com formatação muito irregular.")
        return ""

    # 4. DIVISÃO
    blocos = texto_marcado.split(';;;')
    
    questoes_finais = []
    
    for bloco in blocos:
        if not bloco.strip():
            continue
            
        # 4. VALIDAÇÃO (Requer apenas Comentários + Pergunta)
        if validar_bloco_questao(bloco):
            questao_formatada = formatar_questao_final(bloco)
            questoes_finais.append(questao_formatada)
    
    return "\n".join(questoes_finais)

def pos_processar_texto(texto):
    texto = (
        texto.replace("..",".")
        .replace("alternativa. <br>", "alternativa")
    )
    texto = re.sub(r'(?<=[.;])\s([a-e]\))', r'<br>\1', texto)

    return texto

def extrair_texto_pdf(arquivo_pdf, pagina_inicial=None, pagina_final=None):
    # LER O ARQUIVO ENVIADO PELO STREAMLIT
    pdf_bytes = arquivo_pdf.read()

    # ABRIR O PDF A PARTIR DO STREAM
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Se for para pegar tudo
    if pagina_inicial is None or pagina_final is None:
        pagina_inicial = 1
        pagina_final = len(doc)

    texto_completo = ""
    total_paginas = pagina_final - pagina_inicial + 1
    barra_progresso = st.progress(0)

    for i, pagina in enumerate(range(pagina_inicial - 1, pagina_final)):
        texto_pagina = doc[pagina].get_text("text")
        if texto_pagina:
            texto_completo += texto_pagina + "\n"
        
        barra_progresso.progress((i + 1) / total_paginas)

    barra_progresso.empty()
    return texto_completo


# --- Interface Streamlit ---

st.set_page_config(page_title="Extrator PDF → Flashcards Anki", layout="wide")

st.title("📄🦉🟣 Extrator de Questões para Anki")
st.markdown("""
Este aplicativo converte PDFs de questões comentadas do Estratégia Concursos em um formato compatível com flashcards do Anki.
""")

uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

# Campos para intervalo
pagina_inicial = st.number_input("Página inicial", min_value=1, value=1)
pagina_final = st.number_input("Página final", min_value=1, value=1)

# ➕ Botão "Tudo"
processar_tudo = st.button("Processar TUDO (Documento inteiro)")

if uploaded_file is not None:

    if st.button("Processar Páginas"):
        with st.spinner('Processando somente o intervalo selecionado...'):
            try:
                texto_extraido = extrair_texto_pdf(uploaded_file, pagina_inicial, pagina_final)
                resultado = processar_texto(texto_extraido)
                resultado = pos_processar_texto(resultado)
                # --- restante do código permanece igual ---
                if not resultado.strip():
                    qtd = 0
                else:
                    qtd = len(resultado.splitlines())

                if qtd <= 1:
                    st.warning(f"Atenção: Apenas {qtd} questão foi identificada. Verifique se o PDF contém texto selecionável.")
                    if qtd == 1:
                        st.text("Preview do conteúdo processado:")
                        st.text(resultado[:500] + "...")
                else:
                    st.success(f"✅ {qtd} questões extraídas com sucesso!")
                    st.text_area(
                        "Texto:",
                        value=resultado,
                        height=400
                    )

                    buffer = io.BytesIO()
                    buffer.write(resultado.encode('utf-8'))
                    buffer.seek(0)

                    st.download_button(
                        label="📥 Baixar Arquivo para Anki",
                        data=buffer,
                        file_name="questoes_anki.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")

    # --- Botão Processar TUDO ---
    if processar_tudo:
        with st.spinner('Processando DOCUMENTO INTEIRO...'):
            try:
                texto_extraido = extrair_texto_pdf(uploaded_file)  # sem intervalos
                resultado = processar_texto(texto_extraido)
                resultado = pos_processar_texto(resultado)
                # --- restante igual ---
                if not resultado.strip():
                    qtd = 0
                else:
                    qtd = len(resultado.splitlines())

                if qtd <= 1:
                    st.warning(f"Atenção: Apenas {qtd} questão foi identificada.")
                else:
                    st.success(f"✅ {qtd} questões extraídas com sucesso!")
                    st.subheader("Preview da Primeira Questão:")
                    st.code(resultado.split("\n")[0], language="text")

                    buffer = io.BytesIO()
                    buffer.write(resultado.encode('utf-8'))
                    buffer.seek(0)

                    st.download_button(
                        label="📥 Baixar Arquivo para Anki",
                        data=buffer,
                        file_name="questoes_anki.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
