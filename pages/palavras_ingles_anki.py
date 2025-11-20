import streamlit as st
from deep_translator import GoogleTranslator

st.title("Tradutor de Palavras - EN ➜ PT")

# Campo de texto com altura maior
entrada = st.text_area(
    "Cole suas palavras em inglês (separadas por vírgula ou linha):",
    height=200
)

if st.button("Traduzir"):
    if entrada.strip():
        palavras = [p.strip() for p in entrada.replace(",", "\n").split("\n") if p.strip()]

        # Placeholder para mostrar mensagem temporária
        status = st.empty()
        status.write("⏳ Traduzindo...")

        resultado = ""

        for palavra in palavras:
            traducao = GoogleTranslator(source="en", target="pt").translate(palavra)
            resultado += f"{palavra} | {traducao}\n"

        # Remove a mensagem de processamento e mostra o resultado final
        status.empty()

        st.write("### Resultado:")
        st.text_area("Pronto! Agora copie o resultado:", resultado, height=200)

    else:
        st.warning("Por favor, insira pelo menos uma palavra.")
