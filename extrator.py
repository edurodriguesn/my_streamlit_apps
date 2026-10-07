import re
import os
import json
import shutil

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


def _extrair_imagens_fitz(caminho_pdf, pasta_imagens, nome_base):
    """
    Extrai imagens do PDF usando fitz, retornando lista de
    (pagina_idx, y_topo, caminho_imagem, n) ordenada por posição.
    """
    if not fitz:
        return []
    os.makedirs(pasta_imagens, exist_ok=True)
    resultado = []
    n = 1
    primeira = True
    pdf = fitz.open(caminho_pdf)
    for p_idx, pagina in enumerate(pdf):
        for img in pagina.get_images(full=True):
            if primeira:
                primeira = False
                continue
            xref = img[0]
            rects = pagina.get_image_rects(xref)
            y_topo = rects[0].y0 if rects else 0
            pix = fitz.Pixmap(pdf, xref)
            if pix.colorspace and pix.colorspace.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            caminho_img = os.path.join(pasta_imagens, f"{nome_base}-{n}.png")
            pix.save(caminho_img)
            resultado.append((p_idx, y_topo, caminho_img, n))
            n += 1
    pdf.close()
    return resultado


def _injetar_marcadores_imagens(caminho_pdf, pasta_imagens, nome_base):
    """
    Extrai texto página a página com posições dos blocos e injeta
    {image(n)} no ponto correto do texto, baseado na posição Y da imagem.
    Retorna (texto_com_marcadores, lista_imagens_extraidas).
    """
    if not fitz:
        return None, []

    imagens = _extrair_imagens_fitz(caminho_pdf, pasta_imagens, nome_base)
    if not imagens:
        return None, []

    # Monta mapa: pagina -> lista de (y_topo, marcador)
    marcadores_por_pagina = {}
    for p_idx, y_topo, _, n in imagens:
        marcadores_por_pagina.setdefault(p_idx, []).append((y_topo, n))

    pdf = fitz.open(caminho_pdf)
    paginas_texto = []
    for p_idx, pagina in enumerate(pdf):
        blocos = pagina.get_text("blocks")  # (x0,y0,x1,y1,texto,block_no,block_type)
        # filtra só blocos de texto (type==0)
        blocos_texto = [(b[1], b[4]) for b in blocos if b[6] == 0]
        marcadores = sorted(marcadores_por_pagina.get(p_idx, []), key=lambda x: x[0])

        # intercala marcadores entre blocos de texto por posição Y
        itens = [(y, 'texto', t) for y, t in blocos_texto]
        for y_img, n in marcadores:
            itens.append((y_img, 'imagem', n))
        itens.sort(key=lambda x: x[0])

        partes = []
        for _, tipo, val in itens:
            if tipo == 'texto':
                partes.append(val.strip())
            else:
                partes.append(f"\n{{image({val})}}\n")
        paginas_texto.append("\n".join(partes))
    pdf.close()

    texto = "\n".join(paginas_texto)
    caminhos = [c for _, _, c, _ in imagens]
    return texto, caminhos


def extrair_questoes_pdf(caminho_pdf, pasta_imagens=None, nome_base=None):
    texto_completo = None
    imagens_extraidas = []

    if pasta_imagens and nome_base and fitz:
        texto_completo, imagens_extraidas = _injetar_marcadores_imagens(caminho_pdf, pasta_imagens, nome_base)

    if not texto_completo:
        if pdfplumber:
            try:
                texto_completo = _extrair_texto_pdfplumber(caminho_pdf)
            except Exception:
                texto_completo = None
        if not texto_completo and fitz:
            texto_completo = _extrair_texto_fitz(caminho_pdf)
    if not texto_completo:
        raise RuntimeError("Não foi possível extrair texto do PDF.")

    texto_completo = re.sub(r'\s{2,}', ' ', texto_completo)
    texto_completo = '\n'.join(texto_completo.split('\n')[3:])
    # Remove linhas com URL do tecconcursos e a linha imediatamente abaixo
    texto_completo = re.sub(r'[^\n]*https://www\.tecconcursos\.com\.br/questoes/cadernos/[^\n]*(?:\n[^\n]*){1,3}','',texto_completo)
    texto_completo = re.sub(r'[^\n]*https://www.tecconcursos.com.br/s/[^\n]*\n?[^\n]*\n?', '', texto_completo)
    linhas = texto_completo.split('\n')
    linhas_filtradas = []
    i = 0
    num_questao_re = re.compile(r'(?<!\()\d{1,3}\)\s*')
    while i < len(linhas):
        if linhas[i].startswith('www'):
            i += 1
            linhas_entre = []
            while i < len(linhas) and not num_questao_re.match(linhas[i]):
                linhas_entre.append(linhas[i])
                i += 1
            # Junta linhas da banca até que a linha termine com um ano (20XX)
            if linhas_entre:
                banca_juntada = linhas_entre[0]
                j = 1
                while not re.search(r'20\d{2}$', banca_juntada) and j < len(linhas_entre):
                    banca_juntada += ' ' + linhas_entre[j]
                    j += 1
                linhas_entre = [banca_juntada] + linhas_entre[j:]
            # 0 linhas: sem banca nem assunto
            # 1 linha: só banca
            # 2+ linhas: banca e assunto
            if len(linhas_entre) == 1:
                linhas_filtradas.append('Banca: ' + linhas_entre[0])
            elif len(linhas_entre) >= 2:
                linhas_filtradas.append('Banca: ' + linhas_entre[0])
                linhas_filtradas.append(linhas_entre[1])
        else:
            linhas_filtradas.append(linhas[i])
            i += 1
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

    linhas = texto_completo.split('\n')
    novas_linhas = []
    for linha in linhas:
        if num_questao_re.match(linha):
            if novas_linhas:
                idx_assunto = next(
                    (k for k in range(len(novas_linhas)-1, -1, -1)
                     if not novas_linhas[k].startswith('Banca: ')),
                    None
                )
                if idx_assunto is not None and not novas_linhas[idx_assunto].startswith('Assunto: ') and not re.match(r'^[a-e]\)', novas_linhas[idx_assunto].strip()) and not novas_linhas[idx_assunto].strip().startswith('Gabarito:') and not novas_linhas[idx_assunto].strip().startswith('Enunciado: '):
                    prev = novas_linhas[idx_assunto].rstrip('.')
                    novas_linhas[idx_assunto] = 'Assunto: ' + prev + '.'
            linha_sem_num = num_questao_re.sub('', linha, count=1)
            novas_linhas.append('Enunciado: ' + linha_sem_num)
        else:
            novas_linhas.append(linha)
    texto_completo = '\n'.join(novas_linhas)

    texto_completo = re.sub(r'(Gabarito:\s[A-E])', r'\1.', texto_completo, flags=re.MULTILINE)
    texto_completo = re.sub(r'(?<![.\:;])\n(?![\(A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]|[IVX]+[\s\-.]|[1-5][\s\-.]|Assunto: |Enunciado: |Banca: |Gabarito:)', ' ', texto_completo)
    texto_completo = re.sub(r'(?<!\n)\s+([a-e]\))', r'\n\1', texto_completo)
    texto_completo = re.sub(r'(?<!\n)(Gabarito:\s[A-E]\.)', r'\n\1', texto_completo)
    texto_completo = re.sub(r'^([a-e]\).*)(?<![.;])$', r'\1.', texto_completo, flags=re.MULTILINE)
    texto_completo = texto_completo.replace(' .', '.')
    texto_completo = re.sub(r'(\{image\(\d+\)\})\.', r'\1', texto_completo)
    texto_completo = texto_completo.replace('Enunciado:','')

    return texto_completo, imagens_extraidas


def armazenar_questoes(texto):
    questoes = []
    gabarito_pattern = re.compile(r'^Gabarito:\s*([A-E])\s*\.?$', re.MULTILINE | re.IGNORECASE)
    matches = list(gabarito_pattern.finditer(texto))

    if not matches:
        return questoes

    inicio = 0
    qid = 0
    for match in matches:
        fim = match.end()
        bloco = texto[inicio:fim].strip()
        inicio = fim

        try:
            gabarito = match.group(1).upper()
            linhas = bloco.splitlines()

            banca = ""
            assunto = ""

            for j, linha in enumerate(linhas):
                if linha.strip().startswith('Banca: '):
                    raw = linha.strip()[len('Banca: '):]
                    banca = raw.split('-')[0].strip()
                    linhas = linhas[:j] + linhas[j+1:]
                    break

            for j, linha in enumerate(linhas):
                if linha.strip().startswith('Assunto: '):
                    assunto = linha.strip().replace('Assunto: ', '', 1).rstrip('.')
                    linhas = linhas[:j] + linhas[j+1:]
                    break

            for j, linha in enumerate(linhas):
                if linha.strip().startswith('Enunciado: '):
                    linhas[j] = linha.replace('Enunciado: ', '', 1)
                    break

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

            idx_gabarito = ord(gabarito.lower()) - ord('a')
            texto_gabarito = alternativas[idx_gabarito] if idx_gabarito < len(alternativas) else gabarito

            qid += 1
            questao = {
                "id": qid,
                "enunciado": enunciado,
                "alternativas": alternativas,
                "gabarito": texto_gabarito
            }
            if banca:
                questao["banca"] = banca
            if assunto:
                questao["assunto"] = assunto
            questoes.append(questao)
        except Exception:
            continue

    return questoes


def processar_pdf(pdf_path, nome_arquivo=""):
    nome_base = nome_arquivo.strip() if nome_arquivo.strip() else "questoes_processadas"
    pasta_imagens = os.path.join(os.path.dirname(pdf_path), "images", nome_base)

    texto, _ = extrair_questoes_pdf(pdf_path, pasta_imagens=pasta_imagens, nome_base=nome_base)
    questoes = armazenar_questoes(texto)
    return questoes
