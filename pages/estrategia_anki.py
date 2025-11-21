import streamlit as st
import re
import io

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

    # 5. CORTE APÓS GABARITO (Crucial)
    # Encontra onde está o Gabarito curto e descarta tudo depois dele.
    match_gabarito = re.search(r'(Gabarito:\s*[\w]+(?:\s+[\w\.]+)?).*', texto_unido, re.IGNORECASE)
    
    if match_gabarito:
        # Pega a string original APENAS até o fim do "Gabarito: XX"
        # O grupo 1 do regex pega o padrão do gabarito. Usamos o span dele.
        # Mas para ser mais seguro, vamos usar o match específico do gabarito dentro da string limpa
        padrao_gabarito = r'Gabarito:\s*[\w]+(?:\s+[\w\.]+)?'
        match_exato = re.search(padrao_gabarito, texto_unido, re.IGNORECASE)
        if match_exato:
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
    # 1. Limpeza inicial
    texto_sem_rodape = limpar_rodape_estrategia(texto_bruto)

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

    partes = re.split(f'({padrao_inicio})', texto_sem_rodape, flags=re.MULTILINE)
    
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

# --- Interface Streamlit ---

st.set_page_config(page_title="Extrator de Questões (Limpo)", layout="wide")

st.title("✂️ Extrator de Questões - TXT Limpo")
st.markdown("""
**Regras aplicadas:**
1. Remove rodapés do Estratégia.
2. Remove numeração inicial (ex: `14.`).
3. Separa Pergunta e Resposta por `|`.
4. **Corte Rígido:** A linha termina imediatamente após o Gabarito (ex: `Gabarito: Letra B`).
""")

texto_input = st.text_area("Cole o texto do PDF:", height=300)

if st.button("Processar Texto"):
    if not texto_input:
        st.warning("Cole o texto primeiro.")
    else:
        try:
            resultado = processar_texto(texto_input)
            
            if not resultado.strip():
                qtd = 0
            else:
                qtd = len(resultado.splitlines())
            
            if qtd == 0:
                st.error("Nenhuma questão válida encontrada.")
            else:
                st.success(f"{qtd} questões formatadas.")
                
                st.subheader("Exemplo (Primeira linha):")
                preview = resultado.split("\n")[0]
                st.code(preview, language="text")

                buffer = io.BytesIO()
                buffer.write(resultado.encode('utf-8'))
                buffer.seek(0)

                st.download_button(
                    label="📥 Baixar TXT",
                    data=buffer,
                    file_name="anki_estrategia.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"Erro: {e}")