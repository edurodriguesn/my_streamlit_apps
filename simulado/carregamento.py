import streamlit as st
import tempfile
import os
import json
from extrator_questoes import processar_pdf

PASTA_RAIZ = "questoes_filtradas"


def _botao_atalho(label, caminho_pasta):
    if os.path.exists(caminho_pasta) and os.path.isdir(caminho_pasta):
        if st.button(label, use_container_width=True):
            jsons = [f for f in os.listdir(caminho_pasta) if f.endswith(".json")]
            if jsons:
                st.session_state.arquivo_simulado_ativo = os.path.join(caminho_pasta, jsons[0])
                st.success(f"Carregado: `{jsons[0]}`")
            else:
                st.error("Nenhum arquivo `.json` encontrado.")


def secao_carregamento():
    uploaded_file = st.file_uploader("Envie o PDF ou JSON com as questões", type=["pdf", "json"])
    st.markdown("### 📂 Ou escolha um arquivo do servidor")

    arquivo_local_selecionado = None

    if not os.path.exists(PASTA_RAIZ):
        st.info(f"A pasta `{PASTA_RAIZ}` ainda não existe no diretório raiz.")
        return uploaded_file, arquivo_local_selecionado

    _botao_atalho("📝 Exercício de Inglês", os.path.join(PASTA_RAIZ, "Inglês Texto"))
    _botao_atalho("📝 Fazer simulado da Semana", os.path.join(PASTA_RAIZ, "Simulado"))
    _botao_atalho("📝 Fazer simulado da Semana (Danilo)", os.path.join(PASTA_RAIZ, "Simulado_Danilo"))

    todos_arquivos = []
    for raiz, _, nomes in os.walk(PASTA_RAIZ):
        for nome in nomes:
            if nome.endswith((".pdf", ".json")):
                caminho_completo = os.path.join(raiz, nome)
                todos_arquivos.append((os.path.relpath(caminho_completo, PASTA_RAIZ), caminho_completo))

    aba_pastas, aba_busca = st.tabs(["📁 Navegar por pastas", "🔍 Pesquisar"])

    with aba_pastas:
        subpastas = [f for f in os.listdir(PASTA_RAIZ) if os.path.isdir(os.path.join(PASTA_RAIZ, f))]
        if not subpastas:
            st.warning(f"Nenhuma subpasta encontrada dentro de `{PASTA_RAIZ}`.")
        else:
            subpasta_sel = st.selectbox("Selecione a disciplina/pasta:", ["Selecione..."] + subpastas)
            if subpasta_sel != "Selecione...":
                if "arquivo_simulado_ativo" in st.session_state:
                    del st.session_state.arquivo_simulado_ativo
                caminho_subpasta = os.path.join(PASTA_RAIZ, subpasta_sel)
                arquivos = [f for f in os.listdir(caminho_subpasta) if f.endswith((".pdf", ".json"))]
                if not arquivos:
                    st.warning("Nenhum arquivo PDF ou JSON encontrado nesta pasta.")
                else:
                    arquivo_sel = st.selectbox("Selecione o arquivo de questões:", ["Selecione..."] + arquivos)
                    if arquivo_sel != "Selecione...":
                        arquivo_local_selecionado = os.path.join(caminho_subpasta, arquivo_sel)

    with aba_busca:
        st.caption("Digite no campo abaixo para filtrar — o seletor já tem busca nativa.")
        opcoes = ["Selecione..."] + [label for label, _ in todos_arquivos]
        sel_label = st.selectbox("Simulados disponíveis:", opcoes)
        if sel_label != "Selecione...":
            if "arquivo_simulado_ativo" in st.session_state:
                del st.session_state.arquivo_simulado_ativo
            arquivo_local_selecionado = next(p for l, p in todos_arquivos if l == sel_label)

    if "arquivo_simulado_ativo" in st.session_state:
        arquivo_local_selecionado = st.session_state.arquivo_simulado_ativo

    return uploaded_file, arquivo_local_selecionado


def processar_arquivo(uploaded_file, arquivo_local_selecionado):
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

    if not arquivo_para_processar:
        return

    if "questoes" in st.session_state and st.session_state.get("arquivo_nome") == nome_do_arquivo:
        return

    try:
        if nome_do_arquivo.endswith(".json"):
            if origem_local:
                with open(arquivo_para_processar, "r", encoding="utf-8") as f:
                    questoes = json.load(f)
            else:
                questoes = json.loads(arquivo_para_processar.read().decode("utf-8"))
        else:
            if origem_local:
                with st.spinner("Gerando seu simulado do servidor, aguarde..."):
                    questoes = processar_pdf(arquivo_para_processar)
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
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
        st.session_state.eliminadas = {}
        st.session_state.finalizado = False
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")
        st.stop()
