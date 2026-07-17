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
.ck { color: #cba6f7; }  /* keywords */
.cs { color: #a6e3a1; }  /* strings */
.cn { color: #fab387; }  /* numbers */
.cc { color: #6c7086; font-style: italic; }  /* comments */
.cb { color: #89b4fa; }  /* builtins / types */
.co { color: #89dceb; }  /* operators */
</style>
"""

_KEYWORDS = {
    "if", "else", "elif", "for", "while", "return", "def", "class", "import",
    "from", "as", "in", "not", "and", "or", "is", "None", "True", "False",
    "try", "except", "finally", "with", "pass", "break", "continue", "lambda",
    "yield", "raise", "del", "global", "nonlocal", "assert", "async", "await",
    # Java/C/JS comuns
    "public", "private", "protected", "static", "void", "new", "this", "super",
    "interface", "extends", "implements", "throws", "throw", "final", "abstract",
    "var", "let", "const", "function", "=>", "null", "undefined",
}

_BUILTINS = {
    "int", "str", "float", "bool", "list", "dict", "set", "tuple", "len",
    "print", "range", "type", "isinstance", "self", "String", "List", "Map",
    "System", "console", "Math",
}


def _highlight_line(line: str) -> str:
    """Aplica syntax highlighting em uma linha de código."""
    result = []
    i = 0
    n = len(line)

    while i < n:
        # Comentário de linha
        if line[i] == '#' or line[i:i+2] in ('//', '--'):
            span = 2 if line[i] != '#' else 1
            result.append(f'<span class="cc">{_esc(line[i:])}</span>')
            break

        # String com aspas duplas ou simples
        if line[i] in ('"', "'"):
            q = line[i]
            j = i + 1
            while j < n and line[j] != q:
                if line[j] == '\\':
                    j += 1
                j += 1
            token = line[i:j+1]
            result.append(f'<span class="cs">{_esc(token)}</span>')
            i = j + 1
            continue

        # Número
        if line[i].isdigit() or (line[i] == '-' and i + 1 < n and line[i+1].isdigit()):
            j = i + (1 if line[i] == '-' else 0)
            while j < n and (line[j].isdigit() or line[j] in '.xXabcdefABCDEF_'):
                j += 1
            result.append(f'<span class="cn">{_esc(line[i:j])}</span>')
            i = j
            continue

        # Palavra (keyword, builtin ou identificador)
        if line[i].isalpha() or line[i] == '_':
            j = i
            while j < n and (line[j].isalnum() or line[j] == '_'):
                j += 1
            word = line[i:j]
            if word in _KEYWORDS:
                result.append(f'<span class="ck">{_esc(word)}</span>')
            elif word in _BUILTINS:
                result.append(f'<span class="cb">{_esc(word)}</span>')
            else:
                result.append(_esc(word))
            i = j
            continue

        # Operadores
        if line[i] in '=<>!+-*/%&|^~':
            result.append(f'<span class="co">{_esc(line[i])}</span>')
            i += 1
            continue

        result.append(_esc(line[i]))
        i += 1

    return ''.join(result)


def _esc(text: str) -> str:
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _indent_code(code: str) -> str:
    """Aplica indentação automática após { ou : no final de linha."""
    lines = code.split('\n')
    result = []
    indent = 0
    indent_size = 4

    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
            continue

        # Reduz indentação para linhas que fecham bloco
        if stripped.startswith(('}', ']', ')')):
            indent = max(0, indent - indent_size)

        result.append(' ' * indent + stripped)

        # Aumenta indentação após { ou : no final
        if stripped.endswith(('{', ':')):
            indent += indent_size
        elif stripped.endswith('}'):
            indent = max(0, indent - indent_size)

    return '\n'.join(result)


def _render_code_block(code: str) -> str:
    indented = _indent_code(code.strip('\n'))
    highlighted = '\n'.join(_highlight_line(line) for line in indented.split('\n'))
    return f'<div class="code-block">{highlighted}</div>'


def format_enunciado(text: str) -> tuple[str, bool]:
    """
    Processa o texto substituindo blocos >'''...'''< por HTML formatado.
    Retorna (html_ou_texto, tem_codigo: bool).
    """
    pattern = r"&gt;'''(.*?)'''&lt;"
    # Tenta também a versão literal (sem escape HTML)
    pattern_literal = r">'''(.*?)'''<"

    has_code = bool(re.search(pattern, text, re.DOTALL) or re.search(pattern_literal, text, re.DOTALL))

    if not has_code:
        return text, False

    def replace(m):
        return _render_code_block(m.group(1))

    result = re.sub(pattern, replace, text, flags=re.DOTALL)
    result = re.sub(pattern_literal, replace, result, flags=re.DOTALL)
    return result, True


def get_css() -> str:
    return _CSS
