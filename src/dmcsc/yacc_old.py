from lex import tokens
import ply.yacc as yacc

# Method parsing
def p_method(p):
    'method : METHODDEF paramlist codeblock'

def p_paramlist(p):
    """paramlist : paramlist PARAMDEFNAME
                 | paramlist PARAMLISTEND
                 | PARAMDEFNAME
                 | PARAMLISTEND
    """

def p_statement_assign(p):
    """statement : ASSIGN expression
                 | expression
    """

def p_codeblock(p):
    """ codeblock : CODEBLOCKSTART
                  | codeblock statement
                  | IF expression CODEBLOCKSTART
    """

#def p_statement(p):
#    """ statements : statements statement
#                   | statement
#    """

# Expression parsing

def p_expression(p):
    """expression : expression PLUS term
                  | expression MINUS term
                  | term
    """

def p_term(p):
    """term : term TIMES factor
            | term DIVIDE factor
            | factor
    """

def p_factor(p):
    """factor : NUMBER
              | VARREF
              | LPAREN expression RPAREN
    """


# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


# Build the parser
parser = yacc.yacc()