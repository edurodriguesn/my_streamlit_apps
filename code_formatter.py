import re

_CSS = """
<style>
.code-block {
    background: #1e1e2e;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 12px 16px;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.6;
    overflow-x: auto;
    white-space: pre;
    margin: 8px 0;
    color: #cdd6f4;
}
</style>
"""


_NO_BREAK_AFTER = frozenset('"\')]};,&')

def _normalize_code(code: str) -> str:
    """
    - { seguido de char visível que não seja fechamento: insere \n
    - ; seguido de char visível (sem espaço intermediário): insere \n
    - } sempre fica sozinho: insere \n antes e depois se necessário
    """
    result = []
    i = 0
    n = len(code)
    while i < n:
        ch = code[i]

        if ch == '}':
            # Garante \n antes de } (sem duplicar)
            trailing = ''.join(result).rstrip(' ')
            if trailing and trailing[-1] != '\n':
                result.append('\n')
            result.append('}')
            # Garante \n depois de } (sem duplicar)
            rest_after = code[i+1:].lstrip(' ')
            if rest_after and rest_after[0] != '\n':
                result.append('\n')
            i += 1
            continue

        result.append(ch)

        if ch == '{':
            lookahead = code[i+1:i+3]
            next_visible = lookahead.lstrip(' ')
            if '\n' not in lookahead and (not next_visible or next_visible[0] not in _NO_BREAK_AFTER):
                result.append('\n')

        elif ch == ';':
            # Só quebra se o próximo char (sem espaço) for visível
            rest = code[i+1:]
            next_visible = rest.lstrip(' ')
            if next_visible and next_visible[0] != '\n' and next_visible[0] not in _NO_BREAK_AFTER:
                # Mas não quebra se houver espaço seguido de char visível (já está separado)
                after = code[i+1:i+2]
                if after != ' ':
                    result.append('\n')

        i += 1
    return ''.join(result)


def _indent_code(code: str) -> str:
    """Reindenta o código: aumenta após linha terminada em { ou :, reduz em }."""
    lines = code.split('\n')
    result = []
    indent = 0
    indent_size = 4

    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
            continue

        if stripped.startswith('}'):
            indent = max(0, indent - indent_size)

        result.append(' ' * indent + stripped)

        if stripped.endswith(('{', ':')):
            indent += indent_size
        elif stripped.endswith('}') and not stripped.startswith('}'):
            indent = max(0, indent - indent_size)

    return '\n'.join(result)


def _esc(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _collapse_blank_lines(code: str) -> str:
    """Remove linhas em branco duplicadas consecutivas."""
    return re.sub(r'\n{3,}', '\n\n', code)


def _is_numbered_list(code: str) -> bool:
    """Retorna True se a maioria das linhas não-vazias começa com número seguido de espaço."""
    lines = [l.strip() for l in code.strip().split('\n') if l.strip()]
    if len(lines) < 2:
        return False
    numbered = sum(1 for l in lines if re.match(r'^\d+\s', l))
    return numbered / len(lines) >= 0.5


def _unescape_block(code: str) -> str:
    """Converte \\n literais em quebras reais e entidades HTML comuns."""
    code = code.replace('\\n', '\n')
    code = code.replace('\\"', '"').replace('&quot;', '"')
    code = code.replace('\\&quot;', '"')
    return code


def _render_code_block(code: str) -> str:
    code = _unescape_block(code.strip('\n'))
    if _is_numbered_list(code):
        return f'<div class="code-block">{_esc(code)}</div>'
    code = _normalize_code(code)
    code = _collapse_blank_lines(code)
    code = _indent_code(code)
    return f'<div class="code-block">{_esc(code)}</div>'


def format_enunciado(text: str) -> tuple[str, bool]:
    """
    Substitui blocos >'''...'''< por HTML formatado como código.
    Retorna (resultado, tem_codigo).
    """
    pattern_escaped = r"&gt;'''(.*?)'''&lt;"
    pattern_literal = r">'''(.*?)'''<"

    has_code = bool(
        re.search(pattern_escaped, text, re.DOTALL) or
        re.search(pattern_literal, text, re.DOTALL)
    )

    if not has_code:
        return text, False

    def replace(m):
        return _render_code_block(m.group(1))

    result = re.sub(pattern_escaped, replace, text, flags=re.DOTALL)
    result = re.sub(pattern_literal, replace, result, flags=re.DOTALL)
    return result, True


def get_css() -> str:
    return _CSS
