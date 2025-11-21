import streamlit as st
import re
import io
from pypdf import PdfReader

# --- FUNÇÕES DE LÓGICA ---

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

def validar_bloco_questao(texto):
    """
    Verifica se o bloco é válido:
    1. Tem Comentário.
    2. Tem Gabarito curto (até 2 palavras).
    """
    tem_comentario = re.search(r'Comentários?:', texto, re.IGNORECASE)
    tem_gabarito = re.search(r'Gabarito:\s*[\w]+(?:\s+[\w\.]+)?', texto, re.IGNORECASE)
    return bool(tem_comentario and tem_gabarito)

def formatar_questao_final(texto_bloco):
    """
    Aplica formatações, remove números iniciais e corta após o gabarito.
    """
    
    # 1. REMOVER NUMERAÇÃO INICIAL
    # Remove: 1 ou 2 digitos, ponto, espaço (ex: "14. ", "05. ", "1. ") no inicio da string
    texto_bloco = re.sub(r'^\s*\d{1,2}\.\s+', '', texto_bloco)
    
    # 2. Tratamento de quebras de linha (unir parágrafos quebrados)
    texto_unido = re.sub(r'(?<!\.)\n', ' ', texto_bloco)
    
    # 3. Substitui os \n restantes (após ponto) por <br>
    texto_unido = re.sub(r'\n', ' <br> ', texto_unido)
    
    # 4. Limpeza de espaços duplos
    texto_unido = re.sub(r'\s+', ' ', texto_unido).strip()

    # 5. CORTE APÓS GABARITO (Corte Interno da Questão)
    padrao_gabarito = r'Gabarito:\s*[\w]+(?:\s+[\w\.]+)?'
    match_exato = re.search(padrao_gabarito, texto_unido, re.IGNORECASE)
    
    if match_exato:
        # Corta a string exatamente onde termina o gabarito curto encontrado
        texto_unido = texto_unido[:match_exato.end()]

    # 6. Inserir o PIPE (|)
    match_sep = re.search(r'(Comentários?:|Gabarito:)', texto_unido, re.IGNORECASE)
    
    if match_sep:
        idx = match_sep.start()
        parte_pergunta = texto_unido[:idx].strip()
        parte_resposta = texto_unido[idx:].strip()
        final = f"{parte_pergunta}|{parte_resposta}"
    else:
        final = texto_unido

    return final

def processar_texto(texto_bruto):
    # 1. Limpeza inicial (Rodapés)
    texto_trabalho = limpar_rodape_estrategia(texto_bruto)

    # ============================================================
    # NOVO: CORTE GLOBAL "LISTA DE QUESTÕES"
    # Se encontrar "LISTA DE QUESTÕES", descarta tudo dali para baixo.
    # ============================================================
    match_fim = re.search(r'LISTA DE QUESTÕES', texto_trabalho, re.IGNORECASE)
    if match_fim:
        # Pega o texto apenas do início até onde começa a frase "LISTA DE QUESTÕES"
        texto_trabalho = texto_trabalho[:match_fim.start()]

    # 2. Lista de bancas
    bancas = [
        "FGV","CESGRANRIO","CEBRASPE","CESPE","VUNESP","FCC",
        "IDECAN","IBFC","QUADRIX","CONSULPLAN","AOCP","SELECON",
        "FUNDATEC","INSTITUTO MAIS","FEPESE",

        "IADES","FADESP","COPESE","COPEL","FAPEC","FUNRIO",
        "NUCEPE","CETREDE","COPEVE","FAEPE","FMP CONCURSOS",
        "OBJETIVA CONCURSOS","LEGALLE","CONSULPAM","INAZ DO PARÁ",
        "IBAM","MS CONCURSOS","GUALIMP","ADVISE","ÁGUIA CONSULTORIA",
        "RBO CONCURSOS","HC CONSULTORIA","SUSTENTE CONCURSOS",
        "OMNI CONCURSOS","KLC CONCURSOS","ALPHA CONCURSOS",
        "ECH CONSULTORIA","FAPAM","FUNIVERSA","FUMARC","IBADE",
        "FADURPE","FAFIPA CONCURSOS","FAUEL CONCURSOS","FAPETEC",
        "FUNDEP","CESPLAN","COVEST","CEPS","FUNDESPE","FGAF",
        "PROCERGS CONCURSOS",

        "INSTITUTO ÁGATA","INSTITUTO ACCESS","INSTITUTO SELETA",
        "INSTITUTO CONSULPAM","INSTITUTO UNIVERSAL",
        "INSTITUTO EXCELÊNCIA","INSTITUTO IDEAP","INSTITUTO RENNOVE",
        "INSTITUTO AVALIA","INSTITUTO IBRASP","INSTITUTO AVANÇAR",
        "INSTITUTO FATEC","INSTITUTO NOSSA SENHORA AUXILIADORA (INSA)",
        "INSTITUTO OBJETIVO","INSTITUTO LEGATUS","INSTITUTO MADRE JULIANA",
        "INSTITUTO VICENTINA","INSTITUTO IGPBR","INSTITUTO OCP",
        "INSTITUTO AOCP",
        "INSTITUTO UNIÃO","INSTITUTO CONSULWEST","INSTITUTO CONSULMO",
        "INSTITUTO PROMUN" 
    ]
    bancas_regex = "|".join(bancas)
    
    # Regex de Cabeçalho
    padrao_inicio = rf'(?:^\d+\s*[\.\-\)]\s*)?\(?\b(?:{bancas_regex})\b.*?20\d{{2}}.*?'

    partes = re.split(f'({padrao_inicio})', texto_trabalho, flags=re.MULTILINE)
    
    questoes_finais = []
    buffer_atual = ""
    
    for parte in partes:
        if not parte: continue

        if re.search(padrao_inicio, parte, re.MULTILINE):
            if buffer_atual:
                if validar_bloco_questao(buffer_atual):
                    questoes_finais.append(formatar_questao_final(buffer_atual))
            buffer_atual = parte
        else:
            buffer_atual += parte

    if buffer_atual and validar_bloco_questao(buffer_atual):
        questoes_finais.append(formatar_questao_final(buffer_atual))
    
    return "\n".join(questoes_finais)

def extrair_texto_pdf(arquivo_pdf):
    """Lê o arquivo PDF carregado e retorna todo o texto como string."""
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

st.set_page_config(page_title="Extrator PDF -> TXT", layout="wide")

st.title("📄 Extrator de Questões (PDF)")
st.markdown("""
**Filtros Ativos:**
1. **Ignora tudo** após encontrar a frase "LISTA DE QUESTÕES".
2. **Remove rodapés** e numeração inicial.
3. **Valida:** Somente blocos com Comentário e Gabarito curto.
4. **Formata:** `Pergunta | Resposta` (com `<br>`).
""")

uploaded_file = st.file_uploader("Escolha o arquivo PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Processar Arquivo"):
        with st.spinner('Lendo e processando PDF...'):
            try:
                texto_extraido = extrair_texto_pdf(uploaded_file)
                
                resultado = processar_texto(texto_extraido)
                
                if not resultado.strip():
                    qtd = 0
                else:
                    qtd = len(resultado.splitlines())
                
                if qtd == 0:
                    st.error("Nenhuma questão válida encontrada.")
                else:
                    st.success(f"Sucesso! {qtd} questões extraídas.")
                    
                    st.subheader("Exemplo (Primeira linha):")
                    preview = resultado.split("\n")[0]
                    st.code(preview, language="text")

                    buffer = io.BytesIO()
                    buffer.write(resultado.encode('utf-8'))
                    buffer.seek(0)

                    st.download_button(
                        label="📥 Baixar TXT Formatado",
                        data=buffer,
                        file_name="estrategia_anki.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"Erro: {e}")