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


def extrair_questoes_pdf(caminho_pdf, com_assunto=False):
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
    # 3 - remover as linhas que começam com www (e a linha seguinte se com_assunto)
    linhas = texto_completo.split('\n')
    linhas_filtradas = []
    pular_proxima = False
    for linha in linhas:
        if pular_proxima:
            pular_proxima = False
            continue
        if linha.startswith('www'):
            if com_assunto:
                pular_proxima = True
            continue
        linhas_filtradas.append(linha)
    texto_completo = '\n'.join(linhas_filtradas)

    texto_completo = re.sub(
        r'Certo\s+Errado\s+Gabarito:\s*Certo',
        'a) Certo\nb) Errado\nGabarito: A',
        texto_completo
    )
    texto_completo = re.sub(
        r'Certo\s+Errado\s+Gabarito:\s*Errado',
        'a) Certo\nb) Errado\nGabarito: B',
        texto_completo
    )

    # 3.5 - se com_assunto, marcar linha acima da numeração como assunto
    if com_assunto:
        linhas = texto_completo.split('\n')
        novas_linhas = []
        for i, linha in enumerate(linhas):
            if re.match(r'(?<!\()\d+\)\s*', linha):
                if novas_linhas:
                    prev = novas_linhas[-1].rstrip('.')
                    novas_linhas[-1] = 'Assunto: ' + prev + '.'
                linha_sem_num = re.sub(r'(?<!\()\d+\)\s*', '', linha)
                novas_linhas.append('Enunciado: ' + linha_sem_num)
            else:
                novas_linhas.append(linha)
        texto_completo = '\n'.join(novas_linhas)
    else:
        # 4 - remover numeração tipo "1) ", "23) "
        texto_completo = re.sub(r'(?<!\()\d+\)\s*', '', texto_completo)

    # 5 - adicionar ponto final após "Gabarito: X"
    texto_completo = re.sub(r'(Gabarito:\s[A-E])', r'\1.', texto_completo, flags=re.MULTILINE)
    # 6 - remover quebras de linha não terminadas com ponto
    texto_completo = re.sub(r'(?<!\.|\:|\;)\n', ' ', texto_completo)
    # 7 - adiciona quebra de linha em casos a-e)
    texto_completo = re.sub(r'(?<!\n)\s+([a-e]\))', r'\n\1', texto_completo)
    # 8 - adicionar quebra de linha quando houver "Gabarito: A-E" no meio do texto
    texto_completo = re.sub(r'(?<!\n)(Gabarito:\s[A-E]\.)', r'\n\1', texto_completo)
    # 9 - adicionar ponto no final de texto que começa com a-e) e não termina com ponto ou ponto e vírgula
    texto_completo = re.sub(r'^([a-e]\).*)(?<![.;])$', r'\1.', texto_completo, flags=re.MULTILINE)
    texto_completo = texto_completo.replace(' .', '.')

    return texto_completo


def armazenar_questoes(texto, com_assunto=False):
    questoes = []

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

            # Extrair assunto se com_assunto
            assunto = ""
            if com_assunto:
                for j, linha in enumerate(linhas):
                    if linha.strip().startswith('Assunto: '):
                        assunto = linha.strip().replace('Assunto: ', '', 1).rstrip('.')
                        linhas = linhas[:j] + linhas[j+1:]
                        break
                for j, linha in enumerate(linhas):
                    if linha.strip().startswith('Enunciado: '):
                        linhas[j] = linha.replace('Enunciado: ', '', 1)
                        break

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

            # Resolver gabarito: texto da alternativa correspondente à letra
            idx_gabarito = ord(gabarito.lower()) - ord('a')
            texto_gabarito = alternativas[idx_gabarito] if idx_gabarito < len(alternativas) else gabarito

            qid += 1
            questao = {
                "id": qid,
                "enunciado": enunciado,
                "alternativas": alternativas,
                "gabarito": texto_gabarito
            }
            if com_assunto:
                questao["assunto"] = assunto
            questoes.append(questao)
        except Exception:
            continue

    return questoes


def processar_pdf(pdf_path, com_assunto=False):
    texto = extrair_questoes_pdf(pdf_path, com_assunto=com_assunto)
    questoes = armazenar_questoes(texto, com_assunto=com_assunto)
    return questoes
