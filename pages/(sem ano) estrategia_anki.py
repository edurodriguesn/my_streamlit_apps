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
    txt = re.sub(r'[\u00A0\u2000-\u200B\u202F\u205F\u3000]', ' ', txt)
    txt = re.sub(r'\s\s', ' ', txt)
    txt = re.sub(r'[0-9]{1,4}\.', '.', txt)
    txt = re.sub(r'\b\d{1,2}\s\d{1,2}\b', '', txt)
    txt = re.sub(r"==.{6}==", "", txt)
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
    # 1. Remover a numeração puramente numérica do início para o Anki (opcional)
    # Mantém apenas o (BANCA - ÓRGÃO - ANO)
    texto_bloco = re.sub(r'^\d+\.\s+', '', texto_bloco.strip())

    # 2. Inserir <br> antes de alternativas
    texto_bloco = re.sub(r'\n([a-eA-E]\))', r'<br> \1', texto_bloco)

    # 3. Limpeza de quebras de linha excessivas
    # Transforma quebras simples em espaços, mas mantém o que já é <br>
    texto_unido = re.sub(r'\s+', ' ', texto_bloco).strip()

    # 4. CAPTURA DO GABARITO E CORTE
    # Procuramos "Gabarito" seguido de qualquer caractere até o ponto final
    padrao_gabarito_final = r'(Gabarito\s*[:\-]?\s*[A-E]\b\.?)'
    match_gabarito = re.search(padrao_gabarito_final, texto_unido, re.IGNORECASE)
    
    if match_gabarito:
        # Corta tudo que vier depois do ponto do Gabarito
        texto_unido = texto_unido[:match_gabarito.end()]

    # 5. Inserir o PIPE (|) no divisor "Comentários"
    match_sep = re.search(r'(Comentários?:)', texto_unido, re.IGNORECASE)
    
    if match_sep:
        idx = match_sep.start()
        parte_pergunta = texto_unido[:idx].strip()
        parte_resposta = texto_unido[idx:].strip()
        return f"{parte_pergunta}|{parte_resposta}"
    
    return texto_unido

def processar_texto(texto_bruto):
    # 1. Normalização e Limpeza
    texto_limpo = limpar_rodape_estrategia(texto_bruto)
    texto_limpo = normalizar_tracos(texto_limpo)

    # 2. DIVISÃO PELO PADRÃO: 1. (FGV - ... - 202X)
    # Explicação do Regex:
    # \d+\.\s+ -> Número seguido de ponto e espaço
    # \([A-Z]{3,}\s+-\s+ -> Abre parênteses, 3+ letras (banca), hífen
    # .*? -> Qualquer conteúdo (órgão)
    # -\s+202\d\) -> Hífen, ano 202x e fecha parênteses
    padrao_inicio_questao = r'(\d+\.\s+\([A-Z]{3,}\s+-\s+.*?-\s+202\d\))'
    
    # Usamos o split mantendo o delimitador para não perder o cabeçalho da questão
    partes = re.split(padrao_inicio_questao, texto_limpo)
    
    questoes_finais = []
    
    # Como o split com grupo de captura retorna [vazio, delimitador, conteúdo, delimitador, conteúdo...]
    # Vamos iterar de 2 em 2 para remontar Cabeçalho + Corpo
    for i in range(1, len(partes), 2):
        cabecalho = partes[i]
        corpo = partes[i+1] if (i+1) < len(partes) else ""
        bloco_completo = cabecalho + corpo
        
        if validar_bloco_questao(bloco_completo):
            questao_formatada = formatar_questao_final(bloco_completo)
            questoes_finais.append(questao_formatada)
    
    return "\n".join(questoes_finais)

def pos_processar_texto(texto):
    texto = (
        texto.replace("..",".")
        .replace("alternativa. <br>", "alternativa")
    )
    texto = re.sub(r'(?<=[.:;])\s([a-e]\))', r'<br>\1', texto)

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

st.title("📄🦉🟣❓ Extrator de Questões para Anki (Sem ano)")
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
