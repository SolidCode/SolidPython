literals = [
            ".", ",", ";",
            "=",
            "!",
            ">", "<",
            "+", "-", "*", "/", "^",
            "?", ":",
            "[", "]", "{", "}", "(", ")",
            "%", "#"
]

reserved = {
                'use'    : 'USE',
                'include': 'INCLUDE',
                'module' : 'MODULE',
                'function' : 'FUNCTION',
                'if'     : 'IF',
                'else'   : 'ELSE',
                'let'    : 'LET',
                'assert' : 'ASSERT',
                'for'    : 'FOR',
                'each'   : 'EACH',
                'true'   : 'TRUE',
                'false'  : 'FALSE',
                'echo'   : 'ECHO',
}

tokens = [
    "ID",
    "NUMBER",
    "STRING",
    "EQUAL",
    "GREATER_OR_EQUAL",
    "LESS_OR_EQUAL",
    "NOT_EQUAL",
    "AND", "OR",
    "FILENAME",
    ] + list(reserved.values())

#copy & paste from https://github.com/eliben/pycparser/blob/master/pycparser/c_lexer.py
#LICENSE: BSD
simple_escape = r"""([a-wyzA-Z._~!=&\^\-\\?'"]|x(?![0-9a-fA-F]))"""
decimal_escape = r"""(\d+)(?!\d)"""
hex_escape = r"""(x[0-9a-fA-F]+)(?![0-9a-fA-F])"""
bad_escape = r"""([\\][^a-zA-Z._~^!=&\^\-\\?'"x0-9])"""
escape_sequence = r"""(\\("""+simple_escape+'|'+decimal_escape+'|'+hex_escape+'))'
escape_sequence_start_in_string = r"""(\\[0-9a-zA-Z._~!=&\^\-\\?'"])"""
string_char = r"""([^"\\\n]|"""+escape_sequence_start_in_string+')'
t_STRING = '"'+string_char+'*"' + " | " + "'" +string_char+ "*'"

t_EQUAL = "=="
t_GREATER_OR_EQUAL = ">="
t_LESS_OR_EQUAL = "<="
t_NOT_EQUAL = "!="
t_AND = "\&\&"
t_OR = "\|\|"

t_FILENAME = r'<[a-zA-Z_0-9/\\\.-]*>'

def t_eat_escaped_quotes(t):
    r"\\\""
    pass

def t_comments1(t):
    r'(/\*(.|\n)*?\*/)'
    t.lexer.lineno += t.value.count("\n")
    pass

def t_comments2(t):
    r'//.*[\n\']?'
    t.lexer.lineno += 1
    pass

def t_whitespace(t):
    r'\s'
    t.lexer.lineno += t.value.count("\n")

def t_ID(t):
    r'[\$]?[0-9]*[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value,'ID')
    return t

def t_NUMBER(t):
    r'[0-9]*\.?\d+([eE][-\+]\d+)?'
    t.value = float(t.value)
    return t

def t_error(t):
    print(f'py_scadparser: Illegal character: {t.lexer.filename}({t.lexer.lineno}) "{t.value[0]}"')
    t.lexer.skip(1)

if __name__ == "__main__":
    import sys
    from ply import lex
    from pathlib import Path

    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <scad-file>")

    p = Path(sys.argv[1])
    f = p.open()
    lexer = lex.lex()
    lexer.filename = p.as_posix()
    lexer.input(''.join(f.readlines()))
    for tok in iter(lexer.token, None):
        if tok.type == "MODULE":
            print("")
        print(repr(tok.type), repr(tok.value), end='')

