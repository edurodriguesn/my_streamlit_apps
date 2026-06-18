import re

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import fitz
except ImportError:
    fitz = None


def _extrair_texto_pdfplumber(caminho_pdf):
    texto = ""
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto += (pagina.extract_text() or "") + "\n"
    return texto


def _extrair_texto_fitz(caminho_pdf):
    texto = ""
    pdf = fitz.open(caminho_pdf)
    for pagina in pdf:
        texto += pagina.get_text() + "\n"
    pdf.close()
    return texto


def extrair_questoes_pdf(caminho_pdf):
    # Tenta pdfplumber primeiro, se falhar usa fitz
    texto_completo = None
    if pdfplumber:
        try:
            texto_completo = _extrair_texto_pdfplumber(caminho_pdf)
        except Exception:
            texto_completo = None
    if not texto_completo and fitz:
        texto_completo = _extrair_texto_fitz(caminho_pdf)
    if not texto_completo:
        raise RuntimeError("Não foi possível extrair texto do PDF.")

    # 1 - remover espaços extras
    texto_completo = re.sub(r'\s{2,}', ' ', texto_completo)
    # 2 - remover as 3 primeiras linhas
    texto_completo = '\n'.join(texto_completo.split('\n')[3:])
    # 3 - remover as linhas que começam com www
    texto_completo = '\n'.join([linha for linha in texto_completo.split('\n') if not linha.startswith('www')])
    # 4 - remover numeração tipo "1) ", "23) " (sem abre parênteses antes)
    texto_completo = re.sub(r'(?<!\()\d+\)\s*', '', texto_completo)
    # 5 - adicionar ponto final após "Gabarito: X" (apenas a letra)
    texto_completo = re.sub(r'(Gabarito:\s[A-E])', r'\1.', texto_completo, flags=re.MULTILINE)
    # 6 - remover quebras de linha não terminadas com ponto
    texto_completo = re.sub(r'(?<!\.|\:|\;)\n', ' ', texto_completo)
    # 7 - adiciona quebra de linha em casos a-e) que não estão na posição inicial da linha
    texto_completo = re.sub(r'(?<!\n)\s+([a-e]\))', r'\n\1', texto_completo)
    # 8 - adicionar quebra de linha quando houver "Gabarito: A-E" no meio do texto
    texto_completo = re.sub(r'(?<!\n)(Gabarito:\s[A-E]\.)', r'\n\1', texto_completo)
    # 9 - adicionar ponto no final de texto que começa com a-e) e não termina com ponto
    texto_completo = re.sub(r'^([a-e]\).*)(?<!\.)$', r'\1.', texto_completo, flags=re.MULTILINE)

    return texto_completo


def armazenar_questoes(texto):
    questoes = []

    # Divide usando "Gabarito: X." como delimitador de fim de questão
    gabarito_pattern = re.compile(r'^Gabarito:\s*([A-E])\s*\.?$', re.MULTILINE | re.IGNORECASE)
    matches = list(gabarito_pattern.finditer(texto))

    if not matches:
        return questoes

    inicio = 0
    qid = 0
    for i, match in enumerate(matches):
        fim = match.end()
        bloco = texto[inicio:fim].strip()
        inicio = fim

        try:
            gabarito = match.group(1).upper()
            linhas = bloco.splitlines()

            # encontra alternativas (primeira linha que começa com a))
            idx_alt = None
            for j, linha in enumerate(linhas):
                if re.match(r'^\$?[aA]\)', linha.strip()):
                    idx_alt = j
                    break

            if idx_alt is None:
                continue

            enunciado = "\n".join(linhas[:idx_alt]).strip()

            alternativas = []
            esperada = ord('a')
            valida = True

            for linha in linhas[idx_alt:]:
                linha = linha.strip()
                if re.match(r'^Gabarito:', linha, re.IGNORECASE):
                    break
                m = re.match(r'^\$?([a-e])\)\s*(.*)$', linha, re.IGNORECASE)
                if m:
                    letra = m.group(1).lower()
                    if ord(letra) != esperada:
                        valida = False
                        break
                    alternativas.append(m.group(2).strip())
                    esperada += 1
                elif alternativas:
                    alternativas[-1] += ' ' + linha

            if not valida or not alternativas:
                continue

            qid += 1
            questoes.append({
                "id": qid,
                "enunciado": enunciado,
                "alternativas": alternativas,
                "gabarito": gabarito
            })
        except Exception:
            continue

    return questoes


def processar_pdf(pdf_path):
    texto = extrair_questoes_pdf(pdf_path)
    questoes = armazenar_questoes(texto)
    return questoes
