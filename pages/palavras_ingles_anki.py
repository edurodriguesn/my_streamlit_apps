import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
from deep_translator import GoogleTranslator
from anki_generator import generate_apkg_from_pairs

st.title("Tradutor de Palavras - EN ➜ PT")

entrada = st.text_area(
    "Cole suas palavras em inglês (separadas por vírgula ou linha):",
    height=200
)

if st.button("Traduzir"):
    if entrada.strip():
        palavras = [p.strip() for p in entrada.replace(",", "\n").split("\n") if p.strip()]

        status = st.empty()
        status.write("⏳ Traduzindo...")

        pares = []
        resultado = ""
        for palavra in palavras:
            traducao = GoogleTranslator(source="en", target="pt").translate(palavra)
            pares.append((palavra, traducao))
            resultado += f"{palavra} | {traducao}\n"

        status.empty()
        st.session_state["pares"] = pares

        st.write("### Resultado:")
        st.text_area("Pronto! Agora copie o resultado:", resultado, height=200)

    else:
        st.warning("Por favor, insira pelo menos uma palavra.")

if st.session_state.get("pares"):
    apkg_bytes = generate_apkg_from_pairs("Inglês::Words", st.session_state["pares"])
    st.download_button(
        label="📥 Baixar baralho",
        data=apkg_bytes,
        file_name="Words.apkg",
        mime="application/octet-stream",
    )
