# ------------------------------------------------------------
# calclex.py
#
# tokenizer for a simple expression evaluator for
# numbers and +,-,*,/
# ------------------------------------------------------------
import ply.lex as lex
import re

states = (
    ('nodebody', 'inclusive'),
    ('ccode', 'exclusive'), # Method body
    ('paramlist', 'exclusive'), # Method body
    ('statement', 'exclusive'), # Method body
    ('expression', 'exclusive'), # Method body
    ('singleexpr', 'exclusive')
)

# List of token names.   This is always required
tokens = (
    'NUMBER',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'STRING',
    "PARAMLISTSTART",
    "PARAMLISTEND",
    "METHODDEF",
    "PARAMDEFNAME",
    "CODEBLOCKSTART",
    "CODEBLOCKEND",
    "ASSIGN",
    "IF",
    "VARREF",
    "NODELEAF",
    "NODEVARDECL",
    "NODEVARINIT"
)

## Top / Class Level Definitions

def t_NODELEAF(t):
    r"[^\s\r\n\(\)]+[\r\n\(]+"
    t.value = t.value.strip("\n\r")
    cur_path = t.lexer.tree_path if hasattr(t.lexer, "tree_path") else []
    indent = t.lexer.indent if hasattr(t.lexer, "indent") else 0
    cur_path = cur_path[0:indent]
    t.lexer.tree_path = cur_path + [t.value]
    t.value = "/".join(t.lexer.tree_path)
    t.lexer.indent = 0
    components = t.value.split("/")
    if "var" in components:
        nameidx = components.index("var") + 1
        if len(components) != nameidx + 1:
            return

        varname = components[nameidx]
        t.value = {"parent": "/".join(components[:nameidx - 1]), "name": varname}

        t.type = "NODEVARDECL"
        return t
    elif "proc" in components:
        nameidx = components.index("proc") + 1
        if len(components) != nameidx + 1:
            return

        procname = components[nameidx][:-1]
        t.value = {"parent": "/".join(components[:nameidx - 1]), "name": procname}
        t.type = "METHODDEF"
        t.lexer.code_base_indent = indent
        t.lexer.push_state("ccode")
        t.lexer.push_state("paramlist")
        return t


def t_NODEVARINIT(t):
    r"[^\s\r\n]+\s*=\s*[^\s\r\n]+[\r\n]*"
    t.value = t.value.strip("\n\r ")
    t.lexer.indent = 0
    return t

def t_level(t):
    r"[\t ]+"
    level = t.value.count(" ") / 4 + t.value.count("\t")
    indent = t.lexer.indent if hasattr(t.lexer, "indent") else 0
    t.lexer.indent = indent + level

def t_newline(t):
    r"[\r\n]+"
    t.lexer.indent = 0

def t_nodebody_METHODDEF(t):
    r"[^/\s]+\("
    t.value = t.value[:-1]
    t.lexer.push_state("ccode")
    t.lexer.push_state("paramlist")
    return t

## Param List rules

def t_paramlist_PARAMDEFNAME(t):
    r"[^\),]+"
    t.value = t.value.strip()

    default = None
    typename = None
    if "=" in t.value:
        c = t.value.split("=")
        t.value = c[0].strip()
        default = c[1].strip()

    if " as " in t.value:
        c = t.value.split(" as ")
        t.value = c[0].strip()
        typename = c[1].strip()

    if "/" in t.value:
        c = filter(lambda x: len(x) > 0, t.value.split("/"))
        t.value = c[-1]
        typename = "/".join(c[0:-1])

    t.value = {"name": t.value, "type": typename, "default": default}
    return t


def t_paramlist_next(t):
    r","

def t_paramlist_PARAMLISTEND(t):
    r"\)[\r\n]+"
    t.lexer.pop_state()
    return t

## Code block rules

def t_ccode_CODEBLOCKSTART(t):
    r'[\t\s]+'

    buf = t.value
    level = 0
    sparse_spacing = 0

    while len(buf) > 0:
        if buf.startswith("\t"):
            tokrange = buf.rfind("\t")
            working = buf[0:tokrange + 1]
            buf = buf[tokrange + 1:]
            level += len(working)
        elif buf.startswith("\n"):
            buf = buf[buf.rfind("\n") + 1:]
            level = 0
            sparse_spacing = 0

        elif buf.startswith(" "):
            tokrange = buf.rfind(" ")
            working = buf[0:tokrange + 1]
            buf = buf[tokrange + 1:]
            sparse_spacing += len(working)

    if sparse_spacing % 4 == 0:
        level = sparse_spacing / 4 + level - t.lexer.code_base_indent # Don't include node indenting
    else:
        level = 0

    if level > 0:
        cur_level = t.lexer.level if hasattr(t.lexer, "level") else 0
        if level > cur_level:
            if level - cur_level == 1:
                t.lexer.push_state("statement")
                t.value = level
                t.lexer.level = level
                return t
        elif level < cur_level:
            t.lexer.push_state("statement")
            t.value = level
            t.lexer.level = level
            t.type = "CODEBLOCKEND"
            return t
        elif level == cur_level:
            t.lexer.push_state("statement")

    else:
        prev_level = t.lexer.level
        t.lexer.level = 0
        t.lexer.pop_state()

        if(prev_level > 0):
            t.type = "CODEBLOCKEND"
            return t

## Statement rules

def t_statement_end(t):
    r'[\r\n]'
    t.lexer.pop_state()

def t_statement_IF(t):
    r"if\s*\("
    t.lexer.push_state("singleexpr")
    t.lexer.push_state("expression")
    return t

def t_statement_ASSIGN(t):
    r"[^=]+\s*="
    t.value = t.value[:-1].strip()
    t.lexer.pop_state() #After the expression, we don't want to go back into statement
    t.lexer.push_state("expression")
    return t


## Expression rules

# Regular expression rules for simple tokens
t_expression_PLUS = r'\+'
t_expression_MINUS = r'-'
t_expression_TIMES = r'\*'
t_expression_DIVIDE = r'/'
t_expression_LPAREN = r'\('
t_expression_RPAREN = r'\)'

def t_singleexpr_end(t):
    r"\)"
    t.lexer.pop_state()

def t_expression_STRING(t):
    r'"[^"]+"'
    t.value = t.value[1:-1]
    t.lexer.pop_state()
    return t

# A regular expression rule with some action code
def t_expression_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    t.lexer.pop_state()
    return t

def t_expression_VARREF(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.lexer.pop_state()
    return t

## Code Body:

# Rules for the ccode state
#def t_ccode_rbrace(t):
#    r'\t'
#    t.lexer.level -= 1

#    if t.lexer.level == 0:
#        t.type = "CCODE"
#        t.lexer.begin("INITIAL")
#        return t


# A string containing ignored characters (spaces and tabs)
t_ignore = ''
t_ccode_ignore = ''
t_paramlist_ignore = ' '
t_expression_ignore = ' '
t_statement_ignore = ' '
t_singleexpr_ignore = ' '


# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Error handling rule
def t_ccode_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Error handling rule
def t_paramlist_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Error handling rule
def t_expression_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Error handling rule
def t_statement_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()

