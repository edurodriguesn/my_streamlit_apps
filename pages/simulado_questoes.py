import streamlit as st
import tempfile
import os
import sys
import random
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extrator_questoes import processar_pdf

st.set_page_config(page_title="Simulado de Questões", layout="centered")

# CSS para colorir alternativas
# CSS para colorir alternativas e garantir texto preto no destaque
st.markdown("""
<style>
.correta { 
    background-color: #d4edda; 
    color: #000000 !important; 
    border: 2px solid #28a745; 
    border-radius: 8px; 
    padding: 8px; 
    margin: 4px 0; 
    font-size: 1.1rem; 
}
.errada { 
    background-color: #f8d7da; 
    color: #000000 !important; 
    border: 2px solid #dc3545; 
    border-radius: 8px; 
    padding: 8px; 
    margin: 4px 0; 
    font-size: 1.1rem; 
}
.gabarito { 
    background-color: #d4edda; 
    color: #000000 !important; 
    border: 2px solid #28a745; 
    border-radius: 8px; 
    padding: 8px; 
    margin: 4px 0; 
    font-size: 1.1rem; 
}
.stRadio label { font-size: 3rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("📝 Simulado de Questões")

# --- SEÇÃO DE CARREGAMENTO DE ARQUIVOS ---
PASTA_RAIZ = "questoes_filtradas"
arquivo_local_selecionado = None

# 1. Upload manual por arquivo
uploaded_file = st.file_uploader("Envie o PDF ou JSON com as questões", type=["pdf", "json"])

st.markdown("### 📂 Ou escolha um arquivo do servidor")

# 1. Inicializa a variável para que ela exista no escopo do código
arquivo_local_selecionado = None

if not os.path.exists(PASTA_RAIZ):
    st.info(f"A pasta `{PASTA_RAIZ}` ainda não existe no diretório raiz. Crie-a para navegar pelos arquivos.")
else:
    # --- NOVO: Botão "Fazer simulado da Semana" ---
    caminho_simulado = os.path.join(PASTA_RAIZ, "Simulado")
    caminho_simulado_danilo = os.path.join(PASTA_RAIZ, "Simulado_Danilo")
    # O botão só aparece se a pasta "Simulado" de fato existir
    if os.path.exists(caminho_simulado) and os.path.isdir(caminho_simulado):
        if st.button("📝 Fazer simulado da Semana", use_container_width=True):
            # Busca o primeiro arquivo .json dentro da pasta Simulado
            jsons_simulado = [f for f in os.listdir(caminho_simulado) if f.endswith(".json")]
            if jsons_simulado:
                st.session_state.arquivo_simulado_ativo = os.path.join(caminho_simulado, jsons_simulado[0])
                st.success(f"Simulado carregado: `{jsons_simulado[0]}`")
            else:
                st.error("Nenhum arquivo `.json` encontrado dentro da pasta Simulado.")

    # O botão só aparece se a pasta "Simulado" de fato existir
    if os.path.exists(caminho_simulado_danilo) and os.path.isdir(caminho_simulado_danilo):
        if st.button("📝 Fazer simulado da Semana (Danilo)", use_container_width=True):
            # Busca o primeiro arquivo .json dentro da pasta Simulado
            jsons_simulado = [f for f in os.listdir(caminho_simulado_danilo) if f.endswith(".json")]
            if jsons_simulado:
                st.session_state.arquivo_simulado_ativo = os.path.join(caminho_simulado_danilo, jsons_simulado[0])
                st.success(f"Simulado carregado: `{jsons_simulado[0]}`")
            else:
                st.error("Nenhum arquivo `.json` encontrado dentro da pasta Simulado.")

    # --- Código Original Mantido ---
    subpastas = [f for f in os.listdir(PASTA_RAIZ) if os.path.isdir(os.path.join(PASTA_RAIZ, f))]
    
    if not subpastas:
        st.warning(f"Nenhuma subpasta encontrada dentro de `{PASTA_RAIZ}`.")
    else:
        subpasta_sel = st.selectbox("Selecione a disciplina/pasta:", ["Selecione..."] + subpastas)
        
        if subpasta_sel != "Selecione...":
            # Se o usuário mexer no selectbox, limpamos o estado do botão para priorizar a nova escolha
            if "arquivo_simulado_ativo" in st.session_state:
                del st.session_state.arquivo_simulado_ativo
                
            caminho_subpasta = os.path.join(PASTA_RAIZ, subpasta_sel)
            # Listar PDFs e JSONs
            arquivos = [f for f in os.listdir(caminho_subpasta) if f.endswith((".pdf", ".json"))]
            
            if not arquivos:
                st.warning("Nenhum arquivo PDF ou JSON encontrado nesta pasta.")
            else:
                arquivo_sel = st.selectbox("Selecione o arquivo de questões:", ["Selecione..."] + arquivos)
                if arquivo_sel != "Selecione...":
                    arquivo_local_selecionado = os.path.join(caminho_subpasta, arquivo_sel)

    # --- 2. Definição final da variável arquivo_local_selecionado ---
    # Se o botão do simulado foi clicado, ele assume o valor da variável principal
    if "arquivo_simulado_ativo" in st.session_state:
        arquivo_local_selecionado = st.session_state.arquivo_simulado_ativo

# --- LÓGICA DE PROCESSAMENTO (Upload OU Local) ---
# Define qual arquivo e nome usar na lógica do programa
arquivo_para_processar = None
nome_do_arquivo = None
origem_local = False

if uploaded_file:
    arquivo_para_processar = uploaded_file
    nome_do_arquivo = uploaded_file.name
elif arquivo_local_selecionado:
    arquivo_para_processar = arquivo_local_selecionado
    nome_do_arquivo = os.path.basename(arquivo_local_selecionado)
    origem_local = True

# Processamento do arquivo unificado
if arquivo_para_processar:
    if "questoes" not in st.session_state or st.session_state.get("arquivo_nome") != nome_do_arquivo:
        try:
            if nome_do_arquivo.endswith(".json"):
                if origem_local:
                    with open(arquivo_para_processar, "r", encoding="utf-8") as f:
                        questoes = json.load(f)
                else:
                    questoes = json.loads(arquivo_para_processar.read().decode("utf-8"))
            else:
                # Se for PDF
                if origem_local:
                    caminho_pdf = arquivo_para_processar
                    with st.spinner("Gerando seu simulado do servidor, aguarde..."):
                        questoes = processar_pdf(caminho_pdf)
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(arquivo_para_processar.read())
                        tmp_path = tmp.name
                    try:
                        with st.spinner("Gerando seu simulado, por favor aguarde alguns segundos..."):
                            questoes = processar_pdf(tmp_path)
                    finally:
                        os.unlink(tmp_path)
                        
            st.session_state.questoes = questoes
            st.session_state.arquivo_nome = nome_do_arquivo
            st.session_state.idx = 0
            st.session_state.respostas = {}
            st.session_state.respondidas = {}
            st.session_state.mostrar_gabarito = {}
            st.session_state.finalizado = False
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")
            st.stop()

if "questoes" not in st.session_state:
    st.info("Envie um PDF ou selecione um arquivo do servidor para começar.")
    st.stop()

questoes = st.session_state.questoes
total = len(questoes)

if total == 0:
    st.warning("Nenhuma questão encontrada no arquivo.")
    st.stop()

# Garantir que idx está dentro dos limites
if st.session_state.idx >= total:
    st.session_state.idx = total - 1

# Tela de resultado final
if st.session_state.finalizado:
    respondidas = len(st.session_state.respostas)
    acertos = sum(1 for qid, resp in st.session_state.respostas.items()
                  if any(q["alternativas"][ord(resp) - ord('A')] == q["gabarito"] for q in questoes if q["id"] == qid))
    porcentagem = (acertos / respondidas * 100) if respondidas > 0 else 0

    st.markdown("---")
    st.subheader("🏁 Resultado Final")
    st.metric("Acertos", f"{acertos}/{respondidas}")
    st.metric("Porcentagem", f"{porcentagem:.1f}%")
    st.metric("Erros", f"{respondidas - acertos}/{respondidas}")

    if st.button("🔄 Reiniciar", use_container_width=True):
        st.session_state.idx = 0
        st.session_state.respostas = {}
        st.session_state.respondidas = {}
        st.session_state.mostrar_gabarito = {}
        st.session_state.finalizado = False
        st.rerun()
    st.stop()

# Contador de acertos/erros visível
acertos = sum(1 for qid, resp in st.session_state.respostas.items()
              if any(q["alternativas"][ord(resp) - ord('A')] == q["gabarito"] for q in questoes if q["id"] == qid))
erros = len(st.session_state.respostas) - acertos

col_ac, col_er, col_tot = st.columns(3)
col_ac.metric("✅ Acertos", acertos)
col_er.metric("❌ Erros", erros)
col_tot.metric("📊 Respondidas", f"{len(st.session_state.respostas)}/{total}")

st.markdown("<hr style='margin: 0.5rem 0'>", unsafe_allow_html=True)

# Questão atual
idx = st.session_state.idx
q = questoes[idx]
qid = q["id"]
letras = "ABCDE"

import re
def escape_markdown(text):
    # Converte \n em quebra de linha para markdown (dois espaços + newline)
    text = text.replace('\n', '  \n')
    pattern = r'(?<!\\)(\$.*?(?<!\\)\$)|\$'
    
    def replace_match(match):
        if match.group(1):
            return match.group(1)
        return r'\$'
    
    return re.sub(pattern, replace_match, text)

col_titulo, col_ir = st.columns([3, 1])
with col_titulo:
    st.subheader(f"Questão {q['id']} de {total}")
with col_ir:
    ir_para = st.number_input("Ir para:", min_value=1, max_value=total, value=idx + 1, key=f"ir_questao_{idx}", label_visibility="collapsed")
    if ir_para != idx + 1:
        st.session_state.idx = ir_para - 1
        st.rerun()
if q.get("assunto"):
    st.caption(f"📚 Assunto: {q['assunto']}")
st.markdown(escape_markdown(q["enunciado"]))

ja_respondida = qid in st.session_state.respondidas
mostrar_gab = st.session_state.mostrar_gabarito.get(qid, False)

# Mostrar alternativas
escolha = st.session_state.respostas.get(qid)

if not ja_respondida and not mostrar_gab:
    opcoes = [f"{letras[i]}) {escape_markdown(alt)}" for i, alt in enumerate(q["alternativas"])]
    selecao = st.radio("Alternativas:", opcoes, index=None, key=f"radio_{qid}")

    col_resp, col_gab = st.columns(2)
    with col_resp:
        if st.button("✔️ Responder", key=f"resp_{qid}", use_container_width=True):
            if selecao:
                letra = selecao[0]
                st.session_state.respostas[qid] = letra
                st.session_state.respondidas[qid] = True
                st.rerun()
            else:
                st.warning("Selecione uma alternativa.")
    with col_gab:
        if st.button("👁️ Mostrar Gabarito", key=f"gab_{qid}", use_container_width=True):
            st.session_state.mostrar_gabarito[qid] = True
            st.rerun()
else:
    gabarito_texto = q["gabarito"]
    # Encontrar a letra correta baseado no texto do gabarito
    letra_gabarito = None
    for i, alt in enumerate(q["alternativas"]):
        if alt == gabarito_texto:
            letra_gabarito = letras[i]
            break
    acertou = (escolha == letra_gabarito) if ja_respondida else None
    mostrar_correta = mostrar_gab or (ja_respondida and acertou)

    for i, alt in enumerate(q["alternativas"]):
        letra = letras[i]
        texto_alt = f"{letra}) {escape_markdown(alt)}"

        if ja_respondida:
            if mostrar_correta and letra == letra_gabarito:
                st.markdown(f'<div class="correta">{texto_alt}</div>', unsafe_allow_html=True)
            elif letra == escolha and not acertou:
                st.markdown(f'<div class="errada">{texto_alt}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"&nbsp;&nbsp;{texto_alt}")
        elif mostrar_gab:
            if letra == letra_gabarito:
                st.markdown(f'<div class="gabarito">{texto_alt}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"&nbsp;&nbsp;{texto_alt}")

    if ja_respondida and not acertou and not mostrar_gab:
        if st.button("👁️ Mostrar Resposta", key=f"mostrar_{qid}", use_container_width=True):
            st.session_state.mostrar_gabarito[qid] = True
            st.rerun()

st.markdown("---")

# Navegação
col_prev, col_next, col_rand, col_fim = st.columns([1, 1, 1, 1])
with col_prev:
    if st.button("⬅️ Anterior", disabled=(idx == 0), use_container_width=True):
        st.session_state.idx -= 1
        st.rerun()
with col_next:
    if st.button("➡️ Próxima", disabled=(idx == total - 1), use_container_width=True):
        st.session_state.idx += 1
        st.rerun()
with col_rand:
    if st.button("🎲 Aleatória", use_container_width=True):
        st.session_state.idx = random.randint(0, total - 1)
        st.rerun()
with col_fim:
    if st.button("🏁 Terminar", use_container_width=True):
        st.session_state.finalizado = True
        st.rerun()