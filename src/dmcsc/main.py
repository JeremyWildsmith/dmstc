from lex import lexer
from yacc import parser
import sys

lexer.input(
'''
/obj/item/organ/appendix()

\tx = 20
\t\ty = 30


\tr = 55
'''
)

print("calc >\n")
with open("input", "r") as f:
    data = f.read()

    if False:
        result = parser.parse(data)

        print(result)
    else:
        lexer.input(data)
        while True:
            tok = lexer.token()
            if not tok:
                break  # No more input
            print(tok)