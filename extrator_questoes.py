import pdfplumber
import re
import json

def extrair_questoes_pdf(caminho_pdf):
    texto_completo = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto_completo += (pagina.extract_text() or "") + "\n"
    # 1 - remover espaços extras
    texto_completo = re.sub(r'\s{2,}', ' ', texto_completo)
    # 2 - remover as 3 primeiras linhas
    texto_completo = '\n'.join(texto_completo.split('\n')[3:])
    # 3 - remover as linhas que comçam com www
    texto_completo = '\n'.join([linha for linha in texto_completo.split('\n') if not linha.startswith('www')])
    # 4 - adicionar ponto final no fim da linha que começa com "Gabarito"
    texto_completo = re.sub(r'^(Gabarito.*)(?<!\.)$', r'\1.', texto_completo, flags=re.MULTILINE)
    # 5 - remover quebras de linha não terminadas com ponto
    texto_completo = re.sub(r'(?<!\.|\:|\;)\n', ' ', texto_completo)
    # 6 - adiciona quebra de linha em casos a-e) que não estão na posição incial da linha
    texto_completo = re.sub(r'(?<!\n)\s+([a-e]\))', r'\n\1', texto_completo)
    # 7 - adicionar quebra de linha quando houver "Gabarito: A-E" no meio do texto
    texto_completo = re.sub(r'(?<!\n)(Gabarito:\s[A-E]\.)', r'\n\1', texto_completo)
    # 8 - adicionar ponto no final de texto que começa com a-e) e não termina com ponto
    texto_completo = re.sub(r'^([a-e]\).*)(?<!\.)$', r'\1.', texto_completo, flags=re.MULTILINE)
    

    return texto_completo

import re

def armazenar_questoes(texto):
    questoes = []

    # início de questão: qualquer número seguido de )
    inicio_pattern = re.compile(r'^\d+\)\s*(.*)$', re.MULTILINE)

    matches = list(inicio_pattern.finditer(texto))

    for i, match in enumerate(matches):
        inicio = match.start()
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)

        bloco = texto[inicio:fim].strip()
        qid = i + 1

        linhas = bloco.splitlines()

        # remove o marcador numérico "N)"
        linhas[0] = re.sub(r'^\d+\)\s*', '', linhas[0])

        # encontra alternativas
        idx_alt = None
        for j, linha in enumerate(linhas):
            if re.match(r'^\$?[aA]\)', linha.strip()):
                idx_alt = j
                break

        if idx_alt is None:
            raise ValueError(f"Questão {qid}: alternativa a) não encontrada")

        enunciado = "\n".join(linhas[:idx_alt]).strip()

        alternativas = []
        esperada = ord('a')

        while idx_alt < len(linhas):
            linha = linhas[idx_alt].strip()

            if re.match(r'^Gabarito:\s*[A-E]\s*\.?$', linha, re.IGNORECASE):
                break

            m = re.match(r'^\$?([a-e])\)\s*(.*)$', linha, re.IGNORECASE)

            if not m:
                raise ValueError(
                    f"Questão {qid}: linha inválida: {linha}"
                )

            letra = m.group(1).lower()

            if ord(letra) != esperada:
                raise ValueError(
                    f"Questão {qid}: esperada alternativa {chr(esperada)})"
                )

            alternativas.append(m.group(2).strip())
            esperada += 1
            idx_alt += 1

        # procura gabarito
        gabarito = None
        for linha in linhas[idx_alt:]:
            m = re.match(
                r'^Gabarito:\s*([A-E])\s*\.?$',
                linha.strip(),
                re.IGNORECASE
            )
            if m:
                gabarito = m.group(1).upper()
                break

        if gabarito is None:
            raise ValueError(f"Questão {qid}: gabarito não encontrado")

        questoes.append({
            "id": qid,
            "enunciado": enunciado,
            "alternativas": alternativas,
            "gabarito": gabarito
        })

    return questoes

def processar_pdf(pdf_path):
    texto = extrair_questoes_pdf(pdf_path)
    questoes = armazenar_questoes(texto)
    return questoes