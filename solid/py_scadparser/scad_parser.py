from enum import Enum

from ply import lex, yacc

#workaround relative imports.... make this module runable as script
if __name__ == "__main__":
    from scad_tokens import *
else:
    from .scad_tokens import *

class ScadTypes(Enum):
    GLOBAL_VAR = 0
    MODULE = 1
    FUNCTION = 2
    USE = 3
    INCLUDE = 4
    PARAMETER = 5

class ScadObject:
    def __init__(self, scadType):
        self.scadType = scadType

    def getType(self):
        return self.scadType

class ScadUse(ScadObject):
    def __init__(self, filename):
        super().__init__(ScadTypes.USE)
        self.filename = filename

class ScadInclude(ScadObject):
    def __init__(self, filename):
        super().__init__(ScadTypes.INCLUDE)
        self.filename = filename

class ScadGlobalVar(ScadObject):
    def __init__(self, name):
        super().__init__(ScadTypes.GLOBAL_VAR)
        self.name = name

class ScadCallable(ScadObject):
    def __init__(self, name, parameters, scadType):
        super().__init__(scadType)
        self.name = name
        self.parameters = parameters

    def __repr__(self):
        return f'{self.name} ({self.parameters})'

class ScadModule(ScadCallable):
    def __init__(self, name, parameters):
        super().__init__(name, parameters, ScadTypes.MODULE)

class ScadFunction(ScadCallable):
    def __init__(self, name, parameters):
        super().__init__(name, parameters, ScadTypes.FUNCTION)

class ScadParameter(ScadObject):
    def __init__(self, name, optional=False):
        super().__init__(ScadTypes.PARAMETER)
        self.name = name
        self.optional = optional

    def __repr__(self):
        return self.name + "=..." if self.optional else  self.name

precedence = (
    ('nonassoc', "THEN"),
    ('nonassoc', "ELSE"),
    ('nonassoc', "?"),
    ('nonassoc', ":"),
    ('nonassoc', "[", "]", "(", ")", "{", "}"),

    ('nonassoc', '='),
    ('left', "AND", "OR"),
    ('nonassoc', "EQUAL", "NOT_EQUAL", "GREATER_OR_EQUAL", "LESS_OR_EQUAL", ">", "<"),
    ('left', "%"),
    ('left', '+', '-'),
    ('left', '*', '/'),
    ('right', 'NEG', 'POS', 'BACKGROUND', 'NOT'),
    ('right', '^'),
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
                |   "{" statements "}"
                |   "%" statement %prec BACKGROUND
                |   "*" statement %prec BACKGROUND
                |   "!" statement %prec BACKGROUND
                |   call statement
                |   ";"
                '''

def p_for_loop(p):
    '''for_loop : FOR "(" parameter_list ")"'''

def p_statement_use(p):
    'statement : USE FILENAME'
    p[0] = ScadUse(p[2][1:len(p[2])-1])

def p_statement_include(p):
    'statement : INCLUDE FILENAME'
    p[0] = ScadInclude(p[2][1:len(p[2])-1])

def p_statement_function(p):
    'statement : function'
    p[0] = p[1]

def p_statement_module(p):
    'statement : module'
    p[0] = p[1]

def p_statement_assignment(p):
    'statement : ID "=" expression ";"'
    p[0] = ScadGlobalVar(p[1])

def p_expression(p):
    '''expression : ID
                |   expression "." ID
                |   "-" expression %prec NEG
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
                |   LET "(" assignment_list ")" expression %prec THEN
                |   EACH expression %prec THEN
                |   "[" expression ":" expression "]"
                |   "[" expression ":" expression ":" expression "]"
                |   "[" for_loop expression "]"
                |   for_loop expression %prec THEN
                |   IF "(" expression ")" expression %prec THEN
                |   IF "(" expression ")" expression ELSE expression
                |   "(" expression ")"
                |   call
                |   expression "[" expression "]"
                |   tuple
                |   STRING
                |   NUMBER'''

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

def p_opt_expression_list(p):
    '''opt_expression_list : expression_list
                        |    expression_list ","
                        |    empty'''
def p_expression_list(p):
    ''' expression_list : expression_list "," expression
                    |     expression
        '''

def p_call_parameter_list(p):
    '''call_parameter_list : call_parameter_list "," call_parameter
                        |    call_parameter'''

def p_call_parameter(p):
    '''call_parameter : expression
                    |   ID "=" expression'''

def p_opt_parameter_list(p):
    '''opt_parameter_list : parameter_list
                        |   parameter_list ","
                        |   empty
       '''
    if p[1] != None:
        p[0] = p[1]
    else:
       p[0] = []

def p_parameter_list(p):
    '''parameter_list :     parameter_list "," parameter
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

    lexer = lex.lex()
    lexer.filename = scadFile
    parser = yacc.yacc()

    uses = []
    includes = []
    modules = []
    functions = []
    globalVars = []

    appendObject = { ScadTypes.MODULE : lambda x: modules.append(x),
                     ScadTypes.FUNCTION: lambda x: functions.append(x),
                     ScadTypes.GLOBAL_VAR: lambda x: globalVars.append(x),
                     ScadTypes.USE: lambda x: uses.append(x),
                     ScadTypes.INCLUDE: lambda x: includes.append(x),
    }

    from pathlib import Path
    with Path(scadFile).open() as f:
        for i in  parser.parse(f.read(), lexer=lexer):
            appendObject[i.getType()](i)

    return uses, includes, modules, functions, globalVars

def parseFileAndPrintGlobals(scadFile):

    print(f'======{scadFile}======')
    uses, includes, modules, functions, globalVars = parseFile(scadFile)

    print("Uses:")
    for u in uses:
        print(f'    {u.filename}')

    print("Includes:")
    for i in includes:
        print(f'    {i.filename}')

    print("Modules:")
    for m in modules:
        print(f'    {m}')

    print("Functions:")
    for m in functions:
        print(f'    {m}')

    print("Global Vars:")
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

