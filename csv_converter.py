import csv
import os
import random
import re
from pathlib import Path

_LABELS_RE = re.compile(
    r"^.*(?:Alternativas:|Opções:|Escolhas:).*$", re.IGNORECASE | re.MULTILINE
)

def _fix_alternativas(celula):
    # Remove a linha e ajusta quebras de linha duplicadas residuais
    celula = _LABELS_RE.sub("", celula)
    celula = celula.replace('\n\n','\n')
    lines = [l for l in celula.split('\n') if l.strip()]
    if len(lines) < 4:
        return celula
    body, alts = lines[:-4], lines[-4:]
    fixed = [f"{chr(65+i)}) {re.sub(r'^\s*([A-Da-d][).]|\d[).\-]|-)\s*', '', line).strip()}" for i, line in enumerate(alts)]
    return '\n'.join(body + fixed)

def _embaralhar_alternativas(celula):
    lines = celula.split('\n')
    
    # Identifica as últimas 4 linhas não vazias
    indices_alts = []
    matches = []
    alt_regex = re.compile(r'^\s*([A-D])\)\s*(.*)$')
    
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip():
            m = alt_regex.match(lines[i])
            if m:
                indices_alts.append(i)
                matches.append(m)
            else:
                break
        if len(indices_alts) == 4:
            break
            
    # Se encontrou exatamente 4 alternativas no final
    if len(indices_alts) == 4:
        indices_alts.reverse()
        matches.reverse()
        
        # Extrai os textos correspondentes
        textos = [m.group(2) for m in matches]
        
        # Embaralha os textos
        random.shuffle(textos)
        
        # Reatribui mantendo a ordem das letras A), B), C), D)
        letras = ['A', 'B', 'C', 'D']
        for idx, line_idx in enumerate(indices_alts):
            lines[line_idx] = f"{letras[idx]}) {textos[idx]}"
            
        return '\n'.join(lines)
        
    return celula

def converter_csv(csv_path):
    arquivo_entrada = Path(csv_path)

    if not arquivo_entrada.is_file():
        print(f"Arquivo não encontrado: {csv_path}")
        return
    
    # Nova regex para remover $\text{...}$ externo
    padrao_remove_text_wrapper = r"\$\\text\{((?:\\\}|[^}])+)\}\$"
    
    padrao = r"\$(?=\S)((?:\\.|[^$])+?)(?<=\S)\$"
    substituicao = r"\\(\\ce{$\1$}\\)"

    try:
        arquivo_temp = arquivo_entrada.with_suffix(".tmp")

        with open(arquivo_entrada, mode="r", encoding="utf-8", newline="") as f_in, \
             open(arquivo_temp, mode="w", encoding="utf-8", newline="") as f_out:

            leitor = csv.reader(f_in)
            escritor = csv.writer(f_out)

            for linha in leitor:
                nova_linha = []
                for celula in linha:
                    # ETAPA 1: Remove $\text{conteudo}$ -> conteudo
                    celula_modificada = re.sub(padrao_remove_text_wrapper, r"\1", celula)
                    
                    # ETAPAS SEGUINTES: Outras transformações já existentes
                    celula_modificada = celula_modificada.replace('; ou', ';')
                    celula_modificada = re.sub(r'\?$', '', celula_modificada)
                    if re.search(r'\([A-Da-d]\)\s.+;\s*\([A-Da-d]\)', celula_modificada):
                        celula_modificada = re.sub(r'\s*;\s*(?=\([A-Da-d]\))', '\n', celula_modificada)
                        celula_modificada = re.sub(r'\(([A-Da-d])\)\s*', lambda m: f'\n{m.group(1).upper()}) ', celula_modificada)
                    celula_modificada = re.sub(r'(?<![\S\d])([ABCDabcd][).]|[1-4][).])', r'\n\1', celula_modificada)
                    if celula_modificada.count('-') >= 4 and not re.search(r'(?:^|\n)-', celula_modificada):
                        celula_modificada = re.sub(r'(?<!\n)-(?=\s)', r'\n-', celula_modificada)
                    celula_modificada = _fix_alternativas(celula_modificada)
                    celula_modificada = re.sub(padrao, substituicao, celula_modificada)
                    
                    # ETAPA FINAL: Embaralhar o conteúdo das alternativas
                    celula_modificada = _embaralhar_alternativas(celula_modificada)
                    
                    nova_linha.append(celula_modificada)
                escritor.writerow(nova_linha)

        os.replace(arquivo_temp, arquivo_entrada)
        print(f"Arquivo processado e substituído: {arquivo_entrada.name}")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        converter_csv(sys.argv[1])
    else:
        print("Uso: python csv_converter.py <caminho_do_csv>")