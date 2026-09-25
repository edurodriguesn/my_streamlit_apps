import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import tempfile
import streamlit as st
from extrator import processar_pdf
from anki_generator_json import generate_apkg_from_questoes, deck_name_from_pdf

st.title("PDF → Anki")

uploaded = st.file_uploader("Selecione o PDF", type="pdf")

if st.button("Gerar .apkg", disabled=not uploaded):
    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, uploaded.name)
        with open(pdf_path, "wb") as f:
            f.write(uploaded.read())

        nome_base = os.path.splitext(uploaded.name)[0]
        deck_name = deck_name_from_pdf(nome_base)

        with st.spinner("Processando PDF..."):
            questoes = processar_pdf(pdf_path, nome_arquivo=nome_base)

        if not questoes:
            st.error("Nenhuma questão encontrada no PDF.")
        else:
            st.info(f"Baralho: **{deck_name}**")
            apkg_path = os.path.join(tmpdir, nome_base + ".apkg")
            generate_apkg_from_questoes(deck_name, questoes, apkg_path)

            with open(apkg_path, "rb") as f:
                st.download_button(
                    label=f"Baixar baralho gerado(.apkg)",
                    data=f,
                    file_name=nome_base + ".apkg",
                    mime="application/octet-stream",
                )
