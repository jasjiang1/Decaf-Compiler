import ply.lex as lex
tokens = [
    'ID',
    'STRING_CONST',
    'FLOAT_CONST',
    'INT_CONST',    
    'PLUS', 
    'PLUSPLUS',
    'MINUS',
    'MINUSMINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'LEFT_CB',
    'RIGHT_CB',
    'SEMICOLON',
    'COMMA',
    'DECIMAL',
    'EQUALS',
    'EQUALSEQUALS',
    'ANDAND',
    'OROR',
    'NOT',
    'NOTEQ',
    'LT',
    'GT',
    'LTEQ',
    'GTEQ'
]

t_ANDAND = r'\&\&'
t_OROR = r'\|\|'
t_NOT = r'\!'
t_NOTEQ = r'\!\='
t_LT = r'\<'
t_LTEQ = r'\<\='
t_GT = r'\>'
t_GTEQ = r'\>\='
t_EQUALS = r'\='
t_EQUALSEQUALS = r'\=\='
t_DECIMAL = r'\.'
t_COMMA = r','
t_SEMICOLON = r';'
t_LEFT_CB = r'{'
t_RIGHT_CB = r'}'
t_PLUS = r'\+'
t_PLUSPLUS = r'\+\+'
t_MINUS = r'-'
t_MINUSMINUS = r'--'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_STRING_CONST = r'"([^"]*)"'
reserved = {
    'boolean': 'BOOLEAN',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'class': 'CLASS',
    'else': 'ELSE',
    'extends': 'EXTENDS',
    'false': 'FALSE',
    'float': 'FLOAT',
    'for': 'FOR',
    'if': 'IF',
    'int': 'INT',
    'new': 'NEW',
    'null': 'NULL',
    'private': 'PRIVATE',
    'public': 'PUBLIC',
    'return': 'RETURN',
    'static': 'STATIC',
    'super': 'SUPER',
    'this': 'THIS',
    'true': 'TRUE',
    'void': 'VOID',
    'while': 'WHILE'
}
tokens += list(reserved.values())

def t_FLOAT_CONST(t):
    r'(\d+\.\d+)' 
    t.value = float(t.value)
    return t

def t_INT_CONST(t):
    r'\d+'
    t.value = int(t.value)
    return t  

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID') 
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += 1
    
def t_SINGLE_LINE(t):
    r'\/\/.*'
    pass

def t_MULTI_LINE(t):
    r'\/\*[\s\S]*?\*\/'
    pass
t_ignore = ' \t'

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex()