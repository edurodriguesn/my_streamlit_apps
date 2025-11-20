import streamlit as st
import re

st.title("Organizador de Conteúdos de Edital")
entrada = st.text_area("Cole o texto do edital:", height=340)

def organizar_texto(texto):
    texto = re.sub(r'\n[0-9][0-9]\n', ' ', texto)  # Remove quebras de linha entre números de páginas
    texto = re.sub(r' \(EXCETO.*\n.*\)', '', texto) # Remove exceções entre parênteses
    # Remove quebras de linha que NÃO venham depois de um ponto
    texto = re.sub(r'(?<!\.)\n', ' ', texto)
    # Remove múltiplos espaços
    texto = re.sub(r'\s{2,}', ' ', texto)
    texto = texto.strip()
    
    linhas_formatadas = []
    
    # Encontra todos os títulos (texto em maiúsculas seguido de ':')
    # e divide o texto mantendo os títulos
    titulo_pattern = r'([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s,:-]+):\s*'
    matches = list(re.finditer(titulo_pattern, texto))
    
    if not matches:
        # Se não encontrou títulos, processa o texto inteiro
        conteudo = texto
        processar_conteudo(conteudo, linhas_formatadas)
    else:
        # Processa cada seção (título + conteúdo)
        for i, match in enumerate(matches):
            titulo = match.group(1).strip()
            # Adiciona linha em branco antes do título (exceto no primeiro)
            if i > 0:
                linhas_formatadas.append("")
            linhas_formatadas.append(f"{titulo}:")
            
            # Pega o conteúdo entre este título e o próximo (ou fim)
            start_conteudo = match.end()
            if i + 1 < len(matches):
                end_conteudo = matches[i + 1].start()
            else:
                end_conteudo = len(texto)
            
            conteudo = texto[start_conteudo:end_conteudo].strip()
            processar_conteudo(conteudo, linhas_formatadas)
    
    return "\n".join(linhas_formatadas)

def processar_conteudo(conteudo, linhas_formatadas):
    """Processa o conteúdo identificando e formatando itens numerados"""
    if not conteudo:
        return
    
    # Padrão para encontrar itens numerados (ex: "1 ", "4.1 ", "5.3.2 ")
    # Garante que não capture números que fazem parte de códigos com /
    # Usa lookbehind negativo para ignorar números após /
    pattern = r'(?<![/\d])(\d+(?:\.\d+)*)\s+(?=[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ])'
    matches = list(re.finditer(pattern, conteudo))
    
    if not matches:
        # Se não há números, adiciona o conteúdo como está
        linhas_formatadas.append(conteudo)
        return
    
    # Processa cada item numerado
    for i, match in enumerate(matches):
        numero = match.group(1)
        start_pos = match.end()
        
        # Define onde termina este item (começo do próximo ou fim do texto)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(conteudo)
        
        # Extrai o texto do item
        texto_item = conteudo[start_pos:end_pos].strip()
        
        # Remove espaços extras
        texto_item = re.sub(r'\s+', ' ', texto_item)
        
        # Calcula a profundidade (quantidade de pontos no número)
        profundidade = numero.count(".")
        tab = "\t" * profundidade
        
        # Adiciona o item formatado
        linhas_formatadas.append(f"{tab}{numero} {texto_item}")

if st.button("Organizar"):
    if entrada.strip():
        saida = organizar_texto(entrada)
        st.write("### Resultado Organizado:")
        st.text_area("Texto organizado:", saida, height=420)
    else:
        st.warning("Insira um texto para organizar.")