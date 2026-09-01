import streamlit as st
from bs4 import BeautifulSoup

def parse_html_tree(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Encontrar a ul principal (raiz)
    root_ul = soup.find('ul', class_='arvore')
    if not root_ul:
        return "Nenhuma estrutura de árvore encontrada. Verifique se o HTML contém a tag <ul class='arvore'>."

    results = []

    def traverse(ul_element, prefix=""):
        # Buscar apenas os <li> que são filhos diretos desta <ul>
        items = ul_element.find_all('li', class_='arvore-item', recursive=False)
        
        count = 1
        for li in items:
            # Extrair o nome do item
            nome_span = li.find('span', class_='arvore-item-nome')
            if not nome_span:
                continue
            
            nome = nome_span.get_text(strip=True)
            
            # Otimização: pular os nós redundantes de seleção em massa
            if nome.startswith('Todo o conteúdo de'):
                continue
            
            # Formatar o número hierárquico (ex: 1., 1.1., 1.1.1.)
            current_prefix = f"{prefix}{count}." if prefix else f"{count}."
            results.append(f"{current_prefix} {nome}")
            
            # Verificar se há subníveis (<ul class="arvore"> dentro deste <li>)
            child_ul = li.find('ul', class_='arvore', recursive=False)
            if child_ul:
                traverse(child_ul, current_prefix)
            
            count += 1

    traverse(root_ul)
    return "\n".join(results)

st.set_page_config(page_title="Extrator de Árvore", layout="centered")
st.title("🌳 Extrator de Hierarquia HTML")
st.markdown("Cole o trecho HTML da árvore de assuntos abaixo para extrair os nomes com numeração hierárquica.")

html_input = st.text_area("Trecho HTML:", height=300)

if st.button("Extrair Nomes"):
    if html_input.strip():
        resultado = parse_html_tree(html_input)
        st.success("Extração concluída!")
        st.text_area("Resultado Hierárquico:", resultado, height=400)
    else:
        st.warning("Por favor, cole um trecho HTML primeiro.")
