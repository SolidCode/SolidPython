from ply import lex, yacc

#workaround relative imports.... make this module runable as script
if __name__ == "__main__":
    from scad_ast import *
    from scad_tokens import *
else:
    from .scad_ast import *
    from .scad_tokens import *

precedence = (
        ('nonassoc', 'NO_ELSE'),
        ('nonassoc', 'ELSE'),
        )

def p_input(p):
    """input :"""
    p[0] = []

def p_input_use(p):
    """input : input USE FILENAME
            | input INCLUDE FILENAME"""
    p[0] = p[1]

def p_input_statement(p):
    """input : input statement"""
    p[0] = p[1]
    if p[2] != None:
        p[0].append(p[2])

def p_statement(p):
    """statement : ';'
        | '{' inner_input '}'
        | module_instantiation
        """
    p[0] = None

def p_statement_assigment(p):
    """statement : assignment"""
    p[0] = p[1]

def p_statement_function(p):
    """statement : MODULE ID '(' parameters optional_commas ')' statement
                 | FUNCTION ID '(' parameters optional_commas ')' '=' expr ';'
    """
    if p[1] == 'module':
        p[0] = ScadModule(p[2], p[4])
    elif p[1] == 'function':
        p[0] = ScadFunction(p[2], p[4])
    else:
        assert(False)

def p_inner_input(p):
    """inner_input :
        | inner_input statement
    """

def p_assignment(p):
    """assignment : ID '=' expr ';'"""
    p[0] = ScadGlobalVar(p[1])

def p_module_instantiation(p):
    """module_instantiation : '!' module_instantiation
        | '#' module_instantiation
        | '%' module_instantiation
        | '*' module_instantiation
        | single_module_instantiation child_statement
        | ifelse_statement
    """

def p_ifelse_statement(p):
    """ifelse_statement : if_statement %prec NO_ELSE
        | if_statement ELSE child_statement
    """

def p_if_statement(p):
    """if_statement : IF '(' expr ')' child_statement
    """

def p_child_statements(p):
    """child_statements :
        | child_statements child_statement
        | child_statements assignment
    """

def p_child_statement(p):
    """child_statement : ';'
        | '{' child_statements '}'
        | module_instantiation
    """

def p_module_id(p):
    """module_id : ID
        | FOR
        | LET
        | ASSERT
        | ECHO
        | EACH
    """

def p_single_module_instantiation(p):
    """single_module_instantiation : module_id '(' arguments ')'
    """

def p_expr(p):
    """expr : logic_or
        | FUNCTION '(' parameters optional_commas ')' expr %prec NO_ELSE
        | logic_or '?' expr ':' expr
        | LET '(' arguments ')' expr
        | ASSERT '(' arguments ')' expr_or_empty
        | ECHO '(' arguments ')' expr_or_empty
    """

def p_logic_or(p):
    """logic_or : logic_and
        | logic_or OR logic_and
    """

def p_logic_and(p):
    """logic_and : equality
        | logic_and AND equality
    """

def p_equality(p):
    """equality : comparison
        | equality EQUAL comparison
        | equality NOT_EQUAL comparison
    """

def p_comparison(p):
    """comparison : addition
        | comparison '>' addition
        | comparison GREATER_OR_EQUAL addition
        | comparison '<' addition
        | comparison LESS_OR_EQUAL addition
    """

def p_addition(p):
    """addition : multiplication
        | addition '+' multiplication
        | addition '-' multiplication
    """

def p_multiplication(p):
    """multiplication : unary
        | multiplication '*' unary
        | multiplication '/' unary
        | multiplication '%' unary
    """

def p_unary(p):
    """unary : exponent
        | '+' unary
        | '-' unary
        | '!' unary
    """

def p_exponent(p):
    """exponent : call
        | call '^' unary
    """

def p_call(p):
    """call : primary
        | call '(' arguments ')'
        | call '[' expr ']'
        | call '.' ID
    """

def p_primary(p):
    """primary : TRUE
        | FALSE
        | UNDEF
        | NUMBER
        | STRING
        | ID
        | '(' expr ')'
        | '[' expr ':' expr ']'
        | '[' expr ':' expr ':' expr ']'
        | '[' optional_commas ']'
        | '[' vector_expr optional_commas ']'
    """

def p_expr_or_empty(p):
    """expr_or_empty :
          | expr
    """

def p_list_comprehension_elements(p):
    """list_comprehension_elements : LET '(' arguments ')' list_comprehension_elements_p
        | EACH list_comprehension_elements_or_expr
        | FOR '(' arguments ')' list_comprehension_elements_or_expr
        | FOR '(' arguments ';' expr ';' arguments ')' list_comprehension_elements_or_expr
        | IF '(' expr ')' list_comprehension_elements_or_expr %prec NO_ELSE
        | IF '(' expr ')' list_comprehension_elements_or_expr ELSE list_comprehension_elements_or_expr
    """

def p_list_comprehension_elements_p(p):
    """list_comprehension_elements_p : list_comprehension_elements
        | '(' list_comprehension_elements ')'
    """

def p_list_comprehension_elements_or_expr(p):
    """list_comprehension_elements_or_expr : list_comprehension_elements_p
        | expr
    """

def p_optional_commas(p):
    """optional_commas :
          | ',' optional_commas
    """

def p_vector_expr(p):
    """vector_expr : expr
        | list_comprehension_elements
        | vector_expr ',' optional_commas list_comprehension_elements_or_expr
    """

def p_parameters(p):
    """parameters :
        | parameter
        | parameters ',' optional_commas parameter
    """
    if len(p) == 1:
        p[0] = []
    elif len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[4]]

def p_parameter(p):
    """parameter : ID
        | ID '=' expr
    """
    p[0] = ScadParameter(p[1], len(p) == 4)

def p_arguments(p):
    """arguments :
        | argument
        | arguments ',' optional_commas argument
    """

def p_argument(p):
    """argument : expr
        | ID '=' expr
    """

def p_error(p):
    print(f'py_scadparser: Syntax error: {p.lexer.filename}({p.lineno}) {p.type} - {p.value}')

def parseFile(scadFile):

    lexer = lex.lex()
    lexer.filename = scadFile
    parser = yacc.yacc(debug=False, write_tables=False)

    modules = []
    functions = []
    globalVars = []

    appendObject = { ScadTypes.MODULE : lambda x: modules.append(x),
                     ScadTypes.FUNCTION: lambda x: functions.append(x),
                     ScadTypes.GLOBAL_VAR: lambda x: globalVars.append(x),
    }

    from pathlib import Path
    with Path(scadFile).open() as f:
        for i in  parser.parse(f.read(), lexer=lexer):
            appendObject[i.getType()](i)

    return modules, functions, globalVars

def parseFileAndPrintGlobals(scadFile):

    print(f'======{scadFile}======')
    modules, functions, globalVars = parseFile(scadFile)

    print("Modules:")
    for m in modules:
        print(f'    {m}')

    print("Functions:")
    for m in functions:
        print(f'    {m}')

    print("Global Variables:")
    for m in globalVars:
        print(f'    {m.name}')

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} [-q] <scad-file> [<scad-file> ...]\n   -q : quiete")

    quiete = sys.argv[1] == "-q"
    files = sys.argv[2:] if quiete else sys.argv[1:]

    for i in files:
        if quiete:
            parseFile(i)
        else:
            parseFileAndPrintGlobals(i)

