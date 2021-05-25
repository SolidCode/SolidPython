from ply import lex, yacc

#workaround relative imports.... make this module runable as script
if __name__ == "__main__":
    from scad_ast import *
    from scad_tokens import *
else:
    from .scad_ast import *
    from .scad_tokens import *

precedence = (
    ('nonassoc', 'ASSERT'),
    ('nonassoc', 'ECHO'),
    ('nonassoc', "THEN"),
    ('nonassoc', "ELSE"),
    ('nonassoc', "?"),
    ('nonassoc', ":"),
    ('nonassoc', "(", ")", "{", "}"),

    ('nonassoc', '='),
    ('left', "AND", "OR"),
    ('left', "EQUAL", "NOT_EQUAL", "GREATER_OR_EQUAL", "LESS_OR_EQUAL", ">", "<"),
    ('left', '+', '-'),
    ('left', "%"),
    ('left', '*', '/'),
    ('right', '^'),
    ('right', 'NEG', 'POS', 'BACKGROUND', 'NOT'),
    ('left', "ACCESS"),
 )

def p_statements(p):
    '''statements : statements statement'''
    p[0] = p[1]
    if p[2] != None:
        p[0].append(p[2])

def p_statements_empty(p):
    '''statements : empty'''
    p[0] = []

def p_empty(p):
    'empty : '

def p_statement(p):
    ''' statement : IF "(" expression ")" statement %prec THEN
                |   IF "(" expression ")" statement ELSE statement
                |   for_loop statement
                |   LET "(" assignment_list ")" statement %prec THEN
                |   ASSERT "(" opt_call_parameter_list ")" statement
                |   ECHO "(" opt_call_parameter_list ")" statement
                |   "{" statements "}"
                |   "%" statement %prec BACKGROUND
                |   "*" statement %prec BACKGROUND
                |   "!" statement %prec BACKGROUND
                |   "#" statement %prec BACKGROUND
                |   call statement
                |   USE FILENAME
                |   INCLUDE FILENAME
                |   ";"
                '''
def p_for_loop(p):
    '''for_loop : FOR "(" parameter_list ")"
                | FOR "(" parameter_list ";" expression ";" parameter_list ")"'''

def p_statement_function(p):
    'statement : function'
    p[0] = p[1]

def p_statement_module(p):
    'statement : module'
    p[0] = p[1]

def p_statement_assignment(p):
    'statement : ID "=" expression ";"'
    p[0] = ScadGlobalVar(p[1])

def p_logic_expr(p):
    '''logic_expr :  "-" expression %prec NEG
                |   "+" expression %prec POS
                |   "!" expression %prec NOT
                |   expression "?" expression ":" expression
                |   expression "%" expression
                |   expression "+" expression
                |   expression "-" expression
                |   expression "/" expression
                |   expression "*" expression
                |   expression "^" expression
                |   expression "<" expression
                |   expression ">" expression
                |   expression EQUAL expression
                |   expression NOT_EQUAL expression
                |   expression GREATER_OR_EQUAL expression
                |   expression LESS_OR_EQUAL expression
                |   expression AND expression
                |   expression OR expression
       '''

def p_access_expr(p):
    '''access_expr : ID %prec ACCESS
                |   expression "." ID %prec ACCESS
                |   expression "(" call_parameter_list ")" %prec ACCESS
                |   expression "(" ")" %prec ACCESS
                |   expression "[" expression "]" %prec ACCESS
        '''

def p_list_stuff(p):
    '''list_stuff : FUNCTION "(" opt_parameter_list ")" expression
                |   LET "(" assignment_list ")" expression %prec THEN
                |   EACH expression %prec THEN
                |   "[" expression ":" expression "]"
                |   "[" expression ":" expression ":" expression "]"
                |   "[" for_loop expression "]"
                |   tuple
        '''

def p_assert_or_echo(p):
    '''assert_or_echo : ASSERT "(" opt_call_parameter_list ")"
                    |   ECHO "(" opt_call_parameter_list ")"
       '''
def p_constants(p):
    '''constants : STRING
                |  TRUE
                |  FALSE
                |  NUMBER'''

def p_opt_else(p):
    '''opt_else :
                | ELSE expression %prec THEN
       '''
       #this causes some shift/reduce conflicts, but I don't know how to solve it
def p_for_or_if(p):
    '''for_or_if :  for_loop expression %prec THEN
                |   IF "(" expression ")" expression opt_else
       '''

def p_expression(p):
    '''expression : access_expr
                |   logic_expr
                |   list_stuff
                |   assert_or_echo
                |   assert_or_echo expression %prec ASSERT
                |   constants
                |   for_or_if
                |   "(" expression ")"
       '''
       #the assert_or_echo stuff causes some shift/reduce conflicts, but I don't know how to solve it

def p_assignment_list(p):
    '''assignment_list : ID "=" expression
                    |   assignment_list "," ID "=" expression
       '''

def p_call(p):
    ''' call : ID "(" call_parameter_list ")"
            |  ID "(" ")"'''

def p_tuple(p):
    ''' tuple : "[" opt_expression_list "]"
        '''

def p_commas(p):
    '''commas : commas ","
              | ","
       '''

def p_opt_expression_list(p):
    '''opt_expression_list : expression_list
                        |    expression_list commas
                        |    empty'''
def p_expression_list(p):
    ''' expression_list : expression_list commas expression
                    |     expression
        '''

def p_opt_call_parameter_list(p):
    '''opt_call_parameter_list :
                               | call_parameter_list
       '''
def p_call_parameter_list(p):
    '''call_parameter_list : call_parameter_list commas call_parameter
                        |    call_parameter'''

def p_call_parameter(p):
    '''call_parameter : expression
                    |   ID "=" expression'''

def p_opt_parameter_list(p):
    '''opt_parameter_list : parameter_list
                        |   parameter_list commas
                        |   empty
       '''
    if p[1] != None:
        p[0] = p[1]
    else:
       p[0] = []

def p_parameter_list(p):
    '''parameter_list :     parameter_list commas parameter
                        |   parameter'''
    if len(p) > 2:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_parameter(p):
    '''parameter : ID
                |  ID "=" expression'''
    p[0] = ScadParameter(p[1], len(p) == 4)

def p_function(p):
    '''function : FUNCTION ID "(" opt_parameter_list ")" "=" expression
       '''
    params = None
    if p[4] != ")":
        params = p[4]

    p[0] = ScadFunction(p[2], params)

def p_module(p):
    '''module : MODULE ID "(" opt_parameter_list ")" statement
       '''
    params = None
    if p[4] != ")":
        params = p[4]

    p[0] = ScadModule(p[2], params)


def p_error(p):
    print(f'py_scadparser: Syntax error: {p.lexer.filename}({p.lineno}) {p.type} - {p.value}')

def parseFile(scadFile):

    lexer = lex.lex(debug=False)
    lexer.filename = scadFile
    parser = yacc.yacc(debug=False)

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
            print(i)
            parseFile(i)
        else:
            parseFileAndPrintGlobals(i)

