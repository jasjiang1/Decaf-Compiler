import sys
from decaf_lexer import lexer
from decaf_parser import parser
from decaf_ast import class_table
from decaf_codegen import AbstractCodeGenerator
from decaf_absmc import write_to_file

def check_syntax(filename):
    with open(filename, 'r') as f:
        data = f.read()
    parser.parse(data, lexer = lexer)
    gen_code = AbstractCodeGenerator()
    gen_code.generate_code(class_table)
    write_to_file(gen_code.final_string)

def main():
    filename = sys.argv[1]
    check_syntax(filename)

if __name__ == '__main__':
    main()