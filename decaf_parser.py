import ply.yacc as yacc
from decaf_lexer import tokens
from decaf_ast import class_table
import decaf_ast
import decaf_typecheck

def print_production_info(pa):
    print(f"Production: {pa.slice}")
    print(f"Line number: {pa.lineno(1)}")
    print(f"Lex position: {pa.lexpos(1)}")
    print(f"Length: {len(pa)}")
    for i in range(len(pa)):
        print(f"p[{i}] = {pa[i]}")
    print("___________________________________")

precedence = (
    ('right', 'EQUALS'),
    ('left', 'OROR'),
    ('left', 'ANDAND'),
    ('left', 'EQUALSEQUALS', 'NOTEQ'),
    ('nonassoc','LT', 'GT', 'LTEQ', 'GTEQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('left', 'NOT'),
    ('nonassoc', 'IFX'),
    ('nonassoc', 'ELSE')
)

def p_program(p):
    'program : class_decl_list'
    for class_record in p[1]:
        class_table.add_class(class_record)
    decaf_typecheck.typecheck(class_table)
    p[0] = class_table
    return True

#Classes
def p_class_decl_list(p):
    '''class_decl_list : class_decl class_decl_list 
                       | empty'''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[1]] + p[2]
    

def p_class_decl(p):
    '''class_decl : CLASS ID extend LEFT_CB class_body_decl_list RIGHT_CB'''
    name = p[2]
    class_record = decaf_ast.ClassRecord(name, p[3])
    for body_decl in p[5]:
        if body_decl[0] == "Field":
            vis = body_decl[1]
            app = "instance"
            if body_decl[1] == "public static":
                vis = "public"
                app = "static"
            elif body_decl[1] == "private static":
                vis = "private"
                app = "static"
            elif body_decl[1] == "static":
                vis = "private"
                app = "static"
            for var in body_decl[3]:
                field_record = decaf_ast.FieldRecord(var, name, vis, app, body_decl[2])
                class_record.add_field(field_record)
        elif body_decl[0] == "Method":
            var_table = decaf_ast.VariableTable()
            formal_params = body_decl[4]
            formal_params_var = []
            if formal_params != None:
                for param in formal_params:
                    variable_record = decaf_ast.VariableRecord(param[0], param[1], param[2])
                    var_table.add_variable(variable_record)
                    formal_params_var.append(variable_record)
            var_type = body_decl[5].remove_statement()
            for var in body_decl[6]:
                if isinstance(var, tuple):
                    if formal_params_var != []:
                        for formal_param in formal_params_var:
                            if formal_param.name == var[1]:
                                pass
                type = None
                for var_and_type in var_type:
                    if var == var_and_type[1][0]:
                        type = var_and_type[0]
                        break
                if type == None and isinstance(var, tuple):
                    type = var[0]
                    
                if isinstance(var, tuple):
                    var = var[1]
                variable_record = decaf_ast.VariableRecord(var, "local", type)
                var_table.add_variable(variable_record)
            vis = body_decl[1]
            app = "instance"
            if body_decl[1] == "public static":
                vis = "public"
                app = "static"
            elif body_decl[1] == "private static":
                vis = "private"
                app = "static"

            replace_with_id(body_decl[5], var_table)  
            method_record = decaf_ast.MethodRecord(body_decl[3], name, vis, app, formal_params_var, body_decl[2], var_table, body_decl[5])            
            class_record.add_method(method_record)
            
        elif body_decl[0] == "Constructor":
            var_table = decaf_ast.VariableTable()
            formal_params = body_decl[3]
            formal_params_var = []
            if formal_params != None:
                for param in formal_params:
                    variable_record = decaf_ast.VariableRecord(param[0], param[1], param[2])
                    var_table.add_variable(variable_record)
                    formal_params_var.append(variable_record)
            var_type = body_decl[4].remove_statement()
            for var in body_decl[5]:
                if isinstance(var, tuple):
                    if formal_params_var != []:
                        for formal_param in formal_params_var:
                            if formal_param.name == var[0]:
                                pass
                type = None
                for var_and_type in var_type:
                    if var == var_and_type[1][0]:
                        type = var_and_type[0]
                        break
                if type == None and isinstance(var, tuple):
                    pass
                if isinstance(var, tuple):
                    var = var[1]
                variable_record = decaf_ast.VariableRecord(var, "local", type)
                var_table.add_variable(variable_record)

            vis = body_decl[1]
            if body_decl[1] == "public static":
                vis = "public"
            elif body_decl[1] == "private static":
                vis = "private"

            replace_with_id(body_decl[4], var_table)  
            constructor_record = decaf_ast.ConstructorRecord(name, vis, formal_params_var, var_table, body_decl[4])
            class_record.add_constructor(constructor_record)
    p[0] = class_record
    

def p_extend(p):
    '''extend : EXTENDS ID
              | empty'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = p[1]
    

def p_class_body_decl_list(p):
    '''class_body_decl_list : class_body_decl recall_body_list'''
    p[0] = [p[1]] + p[2]
    

def p_recall_body_list(p):
    '''recall_body_list : class_body_decl_list
                        | empty'''
    if p[1] == None:
        p[0] = []
    else:
        p[0] = p[1]
    

def p_class_body_decl(p):
    '''class_body_decl : field_decl
                       | method_decl
                       | constructor_decl'''
    p[0] = p[1]
    

#Fields, Methods, Constructors
def p_field_decl(p):
    '''field_decl : modifier var_decl'''
    p[0] = ["Field", p[1]] + p[2] 
    
def p_method_decl(p):
    '''method_decl : modifier type ID LPAREN formalsE RPAREN block
                   | modifier VOID ID LPAREN formalsE RPAREN block'''
    all_var_expressions = set()
    vars = get_var_from_block(p[7])
    for var in vars:
        all_var_expressions.add(var)
    p[0] = ["Method", p[1], p[2], p[3], p[5], p[7], all_var_expressions]
    
def p_constructor_decl(p):
    '''constructor_decl : modifier ID LPAREN formalsE RPAREN block'''
    all_var_expressions = set()
    vars = get_var_from_block(p[6])
    for var in vars:
        all_var_expressions.add(var)
    p[0] = ["Constructor", p[1], p[2], p[4], p[6], all_var_expressions]
    

def p_modifier(p):
    '''modifier : PUBLIC STATIC 
                | PRIVATE STATIC 
                | PUBLIC 
                | PRIVATE 
                | STATIC 
                | empty'''
    if len(p) == 2:
        if p[1] == None:
            p[0] = "private"
        else:
            p[0] = p[1]
    else:
        p[0] = p[1] + " " + p[2]
    

def p_var_decl(p):
    '''var_decl : type var_list SEMICOLON'''
    p[0] = [p[1], p[2]]
    

def p_var_list(p):
    '''var_list : ID COMMA var_list
                | ID'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]
    

def p_type(p):
    '''type : INT 
            | FLOAT 
            | BOOLEAN 
            | VOID
            | ID'''
    type = p[1]
    if p[1] != "int" and p[1] != "float" and p[1] != "boolean" and p[1] != "void":
        type = f"user({p[1]})"
    p[0] = decaf_ast.TypeRecord(type)
    

def p_formals(p):
    '''formals : formal_param COMMA formals
               | formal_param'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]
    

def p_formalsE(p):
    '''formalsE : formal_param COMMA formals
                | formal_param
                | empty'''
    if len(p) == 2:
        if p[1] == None:
            p[0] = None
        else:
            p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]
    

def p_formal_param(p):
    '''formal_param : type ID'''
    p[0] = [p[2], "formal", p[1]]
    

#Statements

def p_block(p):
    '''block : LEFT_CB statement_list RIGHT_CB'''
    p[0] = decaf_ast.StatementRecord("Block", p.lineno(1), p.lexpos(1), block = p[2])
    

def p_statement_list(p):
    '''statement_list : statement statement_list 
                      | empty '''
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = [p[1]] + p[2]
    

def p_statement(p):
    '''statement : if_else
                 | if
                 | WHILE LPAREN expression RPAREN statement
                 | FOR LPAREN statement_expressionE SEMICOLON expressionE SEMICOLON statement_expressionE RPAREN statement
                 | RETURN expressionE SEMICOLON
                 | statement_expression SEMICOLON
                 | BREAK SEMICOLON
                 | CONTINUE SEMICOLON
                 | block
                 | var_decl
                 | SEMICOLON'''
    if len(p) == 6:
        p[0] = decaf_ast.StatementRecord("While", p.lineno(1), p.lexpos(1), while_condition = p[3], loop_body = p[5])
    elif len(p) == 10:
        init = p[3]
        condition = p[5]
        update = p[7]
        if p[3] == None:
            init = decaf_ast.StatementRecord("Skip", p.lineno(1), p.lexpos(1))
        if p[5] == None:
            condition = decaf_ast.StatementRecord("Skip", p.lineno(1), p.lexpos(1))
        if p[7] == None:
            update = decaf_ast.StatementRecord("Skip", p.lineno(1), p.lexpos(1))
        p[0] = decaf_ast.StatementRecord("For", p.lineno(1), p.lexpos(1), for_init = init, for_condition = condition, for_update = update, loop_body = p[9])
    elif len(p) == 4:
        ret = p[2]
        if p[2] == None:
            ret = decaf_ast.StatementRecord("Skip", p.lineno(1), p.lexpos(1))
        p[0] = decaf_ast.StatementRecord("Return", p.lineno(1), p.lexpos(1), return_val = ret)
    elif len(p) == 3:
        if p[1] == "break" or p[1] == "continue":
            p[0] = decaf_ast.StatementRecord(p[1].capitalize(), p.lineno(1), p.lexpos(1))
        else:
            p[0] = p[1]
    elif len(p) == 2:
        if p[1] != ";":
            productions = p.slice
            if str(productions[1]) == "var_decl":
                p[0] = p[1]
            else:
                p[0] = p[1]        
    else:
        print("error")
    

def p_if(p):
    '''if : IF LPAREN expression RPAREN statement %prec IFX'''
    p[0] = decaf_ast.StatementRecord("If", p.lineno(1), p.lexpos(1), if_condition = p[3], then_statement = p[5])
    

def p_if_else(p):
    '''if_else : IF LPAREN expression RPAREN statement ELSE statement'''
    p[0] = decaf_ast.StatementRecord("If", p.lineno(1), p.lexpos(1), if_condition = p[3], then_statement = p[5], else_statement = p[7])
    

def p_statement_expression(p):
    '''statement_expression : assign
                            | method_invocation
                            '''
    p[0] = decaf_ast.StatementRecord("Expr", p.lineno(1), p.lexpos(1), expression = p[1])
    

def p_statement_expressionE(p):
    '''statement_expressionE : assign
                             | method_invocation
                             | empty
                            '''
    p[0] = decaf_ast.StatementRecord("Expr", p.lineno(1), p.lexpos(1), expression = p[1])
    

#Expressions

def p_literal(p):
    '''literal : INT_CONST 
               | FLOAT_CONST 
               | STRING_CONST 
               | NULL 
               | TRUE 
               | FALSE'''
    consttype = ""
    if (p[1] == "null" or p[1] == "true" or p[1] == "false"):
        p[0] = decaf_ast.ExpressionRecord("Constant", p.lineno(1), p.lexpos(1), constant = p[1])
    else:
        if (isinstance(p[1], int)):
            consttype = "Integer-constant"
        elif (isinstance(p[1], float)):
            consttype = "Float-constant"
        elif (isinstance(p[1], str)):
            consttype = "String-constant"
        else:
            print("error")
        p[0] = decaf_ast.ExpressionRecord("Constant", p.lineno(1), p.lexpos(1), constant = consttype, value = p[1])    
    

def p_primary(p):
    '''primary : literal
               | THIS
               | SUPER
               | LPAREN expression RPAREN
               | NEW ID LPAREN arguments_list RPAREN
               | field_access
               | method_invocation'''
    if len(p) == 2:
        if p[1] == "this":
            p[1] = decaf_ast.ExpressionRecord("this", p.lineno(1), p.lexpos(1))
        elif p[1] == "super":
            p[1] = decaf_ast.ExpressionRecord("super", p.lineno(1), p.lexpos(1))
        p[0] = p[1]
    elif len(p) == 4:
        p[0] = p[2]
    elif len(p) == 6:
        if p[4] == None:
            list = []
        else:
            list = p[4]
        p[0] = [p[1], p[2], list]
        p[0] = decaf_ast.ExpressionRecord("New-object", p.lineno(1), p.lexpos(1), fmn_name = p[2], mn_args = list)
    
    

def p_arguments_list(p):
    '''arguments_list : arguments
                      | empty'''
    
    p[0] = p[1]
    

def p_arguments(p):
    '''arguments : expression
                 | arguments COMMA expression'''
    
    if len(p) == 2:
        p[0] = [p[1]]
    elif len(p) == 4:
        p[0] = p[1] + p[3]
    

def p_field_access(p):
    '''field_access : primary DECIMAL ID
                    | ID'''
    if len(p) == 2:
        p[0] = decaf_ast.ExpressionRecord("Variable", p.lineno(1), p.lexpos(1), value = p[1])
    elif len(p) == 4:
        p[0] = decaf_ast.ExpressionRecord("Field-access", p.lineno(1), p.lexpos(1), fmn_name = p[3], fmn_base = p[1])    
    

def p_method_invocation(p):
    '''method_invocation : field_access LPAREN arguments_list RPAREN'''
    p[0] = [p[1], p[3]]
    base = p[1].fmn_base
    name = p[1].fmn_name
    if p[3] == None:
        list = []
    else:
        list = p[3]
    p[0] = decaf_ast.ExpressionRecord("Method-call", p.lineno(1), p.lexpos(1), fmn_base = base, fmn_name = name, mn_args = list)
    
    

def p_expression(p):
    '''expression : primary
                  | assign
                  | expression arith_or_bool 
                  | unary_op expression'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] == "" or p[1] == "uminus" or p[1] == "neg":
            if p[1] == "" or p[1] == "uminus":
                if (p[2].expression_type != "Constant"):
                    pass
            p[0] = decaf_ast.ExpressionRecord("Unary", p.lineno(1), p.lexpos(1), unary_operator = p[1], unary_operand = p[2])
        else:
            ops = {"+":"add", "-":"sub", "/":"div", "*":"mul", 
                "&&":"and", "||":"or", "==":"eq", "!=":"neq",
                "<":"lt", ">":"gt", "<=":"leq", ">=":"geq"}
            p[0] = decaf_ast.ExpressionRecord("Binary", p.lineno(1), p.lexpos(1), binary_operator = ops[p[2][0]], binary_operand1 = p[1], binary_operand2 = p[2][1])
    
    

def p_expressionE(p):
    '''expressionE : primary
                   | assign
                   | expression arith_or_bool 
                   | unary_op expression
                   | empty'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        if p[1] == "" or p[1] == "uminus" or p[1] == "neg":
            p[0] = decaf_ast.ExpressionRecord("Unary", p.lineno(1), p.lexpos(1), unary_operator = p[1], unary_operand = p[2])
        else:
            ops = {"+":"add", "-":"sub", "/":"div", "*":"mul", 
                "&&":"and", "||":"or", "==":"eq", "!=":"neq",
                "<":"lt", ">":"gt", "<=":"leq", ">=":"geq"}
            p[0] = decaf_ast.ExpressionRecord("Binary", p.lineno(1), p.lexpos(1), binary_operator = ops[p[2][0]], binary_operand1 = p[1], binary_operand2 = p[2][1])
    
    

def p_arith_or_bool(p):
    '''arith_or_bool : arith_op expression
                     | bool_op expression'''
    p[0] = [p[1], p[2]]
    
    

def p_assign(p):
    '''assign : field_access EQUALS expression
              | field_access PLUSPLUS
              | PLUSPLUS field_access
              | field_access MINUSMINUS
              | MINUSMINUS field_access'''
    
    if len(p) == 4:
        p[0] = decaf_ast.ExpressionRecord("Assign", p.lineno(1), p.lexpos(1), assign_left = p[1], assign_right = p[3])
    else:
        if (p[1] == "++" or p[2] == "++"):
            inc_or_dec = "inc"
        elif (p[1] == "--" or p[2] == "--"):
            inc_or_dec = "dec"
        if (p[1] == "++" or p[1] == "--"):
            pre_or_post = "pre"
            exp = p[2]
        elif (p[2] == "++" or p[2] == "--"):
            pre_or_post = "post"
            exp = p[1]
        p[0] = decaf_ast.ExpressionRecord("Auto", p.lineno(1), p.lexpos(1), auto_operand = exp, auto_type = inc_or_dec, auto_place = pre_or_post)
    
    

def p_arith_op(p):
    '''arith_op : PLUS
                | MINUS
                | TIMES
                | DIVIDE'''
    p[0] = p[1]
    
    

def p_bool_op(p):
    '''bool_op : ANDAND
               | OROR
               | EQUALSEQUALS
               | NOTEQ
               | LTEQ             
               | LT
               | GTEQ             
               | GT'''
    p[0] = p[1]
    
    

def p_unary_op(p): #used to be uplus and uminus check later
    '''unary_op : PLUS 
                | MINUS
                | NOT'''
    if p[1] == "+":
        p[0] = ""
    elif p[1] == "-":
        p[0] = "uminus"
    elif p[1] == "!":
        p[0] = "neg"    
    

def p_empty(p):
    '''empty :'''
    

def p_error(p):
    if p:
        print(f"ERROR\nType {p.type}\nLine {p.lineno}\nPosition {p.lexpos}")
        exit()
    else:
        print("ERROR\nEOF")
        exit()

parser = yacc.yacc(debug = False)

def replace_with_id(statement, var_table):
    if isinstance(statement, decaf_ast.StatementRecord):
        if statement.statement_type == "If":
            replace_with_id(statement.if_condition, var_table)
            replace_with_id(statement.then_statement, var_table)
            replace_with_id(statement.else_statement, var_table)
        elif statement.statement_type == "While":
            replace_with_id(statement.while_condition, var_table)
            replace_with_id(statement.loop_body, var_table)
        elif statement.statement_type == "For":
            replace_with_id(statement.for_init, var_table)
            replace_with_id(statement.for_condition, var_table)
            replace_with_id(statement.for_update, var_table)
            replace_with_id(statement.loop_body, var_table)
        elif statement.statement_type == "Return":
            replace_with_id(statement.return_val, var_table)
        elif statement.statement_type == "Expr":
            replace_with_id(statement.expression, var_table)
        elif statement.statement_type == "Block":
            for stmt in statement.block:
                replace_with_id(stmt, var_table)
        
    elif isinstance(statement, decaf_ast.ExpressionRecord):
        if statement.expression_type == "Variable":
            for var in var_table:
                if var.name == statement.value:
                    statement.change_value(var.id)
        elif statement.expression_type == "Unary":
            replace_with_id(statement.unary_operand, var_table)
        elif statement.expression_type == "Binary":
            replace_with_id(statement.binary_operand1, var_table)
            replace_with_id(statement.binary_operand2, var_table)
        elif statement.expression_type == "Assign":
            replace_with_id(statement.assign_left, var_table)
            replace_with_id(statement.assign_right, var_table)
        elif statement.expression_type == "Auto":
            replace_with_id(statement.auto_operand, var_table)
        elif statement.expression_type == "Field-access":
            replace_with_id(statement.fmn_base, var_table)
        elif statement.expression_type == "Method-Call":
            replace_with_id(statement.fmn_base, var_table)
            for expr in statement.mn_args:
                replace_with_id(expr, var_table)
        elif statement.expression_type == "New-object":
            for expr in statement.mn_args:
                replace_with_id(expr, var_table)
        

def get_var_from_block(statement):
    ret = []
    if isinstance(statement, decaf_ast.StatementRecord):
        if statement.statement_type == "If":
            ret += get_var_from_block(statement.if_condition)
            ret += get_var_from_block(statement.then_statement)
            ret += get_var_from_block(statement.else_statement)
        elif statement.statement_type == "While":
            ret += get_var_from_block(statement.while_condition)
            ret += get_var_from_block(statement.loop_body)
        elif statement.statement_type == "For":
            ret += get_var_from_block(statement.for_init)
            ret += get_var_from_block(statement.for_condition)
            ret += get_var_from_block(statement.for_update)
            ret += get_var_from_block(statement.loop_body)
        elif statement.statement_type == "Return":
            ret += get_var_from_block(statement.return_val)
        elif statement.statement_type == "Expr":
            ret += get_var_from_block(statement.expression)
        elif statement.statement_type == "Block":
            for stmt in statement.block:
                ret += get_var_from_block(stmt)
        
    elif isinstance(statement, decaf_ast.ExpressionRecord):
        if statement.expression_type == "Variable":
            ret.append(statement.value)
        elif statement.expression_type == "Unary":
            ret += get_var_from_block(statement.unary_operand)
        elif statement.expression_type == "Binary":
            ret += get_var_from_block(statement.binary_operand1)
            ret += get_var_from_block(statement.binary_operand2)
        elif statement.expression_type == "Assign":
            ret += get_var_from_block(statement.assign_left)
            ret += get_var_from_block(statement.assign_right)
        elif statement.expression_type == "Auto":
            ret += get_var_from_block(statement.auto_operand)
        elif statement.expression_type == "Field-access":
            ret += get_var_from_block(statement.fmn_base)
        elif statement.expression_type == "Method-Call":
            ret += get_var_from_block(statement.fmn_base)
            for expr in statement.mn_args:
                ret += get_var_from_block(expr)
        elif statement.expression_type == "New-object":
            for expr in statement.mn_args:
                ret += get_var_from_block(expr)
        
    elif isinstance(statement, list):
        for var in statement[1][0]:
            ret.append((statement[0], var))
    return ret
