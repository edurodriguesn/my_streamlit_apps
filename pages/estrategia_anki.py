import streamlit as st
import re
import io
from pypdf import PdfReader

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
           .replace("  ", " ")
    )
    txt = re.sub(r'[0-9]{1,4}\.', '.', txt)
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
    texto_unido = re.sub(r'\s+', ' ', texto_unido).strip()
    texto_unido = re.sub(r'^\.+\s+', '', texto_unido)
    

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
    
    padrao_agressivo = r'(\.[^.]*?[A-Za-z]\s?[-/]\s?20[12][0-9])'
    texto_marcado = re.sub(padrao_agressivo, r'\n;;;\1', texto_limpo, flags=re.MULTILINE)
    # Verifica se o marcador foi inserido (debugging visual)
    if ";;;" not in texto_marcado:
        st.error("ERRO CRÍTICO: O padrão de data (ex: '- 2023' ou '/ 2023') não foi encontrado no texto. O PDF pode estar com formatação muito irregular.")
        return ""

    # 3. DIVISÃO
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

def extrair_texto_pdf(arquivo_pdf):
    leitor = PdfReader(arquivo_pdf)
    texto_completo = ""
    barra_progresso = st.progress(0)
    total_paginas = len(leitor.pages)
    
    for i, pagina in enumerate(leitor.pages):
        texto_pagina = pagina.extract_text()
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

**Como funciona:**
- Faz upload do PDF de questões comentadas
- O sistema identifica e separa cada questão automaticamente
- Gera um arquivo TXT formatado pronto para importação no Anki
""")

uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Processar Arquivo"):
        with st.spinner('Processando PDF...'):
            try:
                texto_extraido = extrair_texto_pdf(uploaded_file)
                
                resultado = processar_texto(texto_extraido)
                
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