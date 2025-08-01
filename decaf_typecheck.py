import decaf_ast

subtypes = set()
subtypes.add(("int", "float"))
all_class_names = []
all_supers = [] 

def add_subtype(type1, type2):
    subtypes.add((type1, type2))

def is_subtype(type1, type2):
    if type1 == type2:
        return True
    
    if (type1, type2) in subtypes:
        return True
    
    if "user(" in type2 and type1 == "null":
        return True
    
    if "user(" in type1 and "user(" in type2:
        tup1 = type1.replace("user(", "").replace(")", "")
        tup2 = type2.replace("user(", "").replace(")", "")
        if (tup1, tup2) in all_supers:
            return True
        
    if "class-literal(" in type1 and "class-literal(" in type2:
        tup1 = type1.replace("class-literal(", "").replace(")", "")
        tup2 = type2.replace("class-literal(", "").replace(")", "")
        if (tup1, tup2) in all_supers:
            return True
    return False


def typecheck(class_table):
    for class_name in class_table.classes:
        all_class_names.append(class_name)
        class_record = class_table.classes[class_name]
        if class_record.super != "":
            all_supers.append((class_record.name, class_record.super))

    for class_name in class_table.classes:
        field_tuples = []
        for field in class_table.classes[class_name].fields:
            field_tuples.append((field.type.type, field.name))
        for method in class_table.classes[class_name].methods:
            backpatch_types(class_table, field_tuples, method, method.body)
        for constructor in class_table.classes[class_name].constructors:
            backpatch_types(class_table, field_tuples, constructor, constructor.body)
    
    for class_record in class_table.classes:
        for method in class_table.classes[class_record].methods:
            print_error(class_table, method, method.body) 
        for constructor in class_table.classes[class_record].constructors:
            print_error(class_table, constructor, constructor.body)

def backpatch_types(class_table, field_tuples, fullrecord, record):
    if isinstance(record, decaf_ast.StatementRecord):
        type = record.statement_type
        match type:
            case "If":
                backpatch_types(class_table, field_tuples, fullrecord, record.if_condition)
                backpatch_types(class_table, field_tuples, fullrecord, record.then_statement)
                if record.else_statement != None:
                    backpatch_types(class_table, field_tuples, fullrecord, record.else_statement)
            case "While":
                backpatch_types(class_table, field_tuples, fullrecord, record.while_condition)
                backpatch_types(class_table, field_tuples, fullrecord, record.loop_body)
            case "For":
                backpatch_types(class_table, field_tuples, fullrecord, record.for_init)
                backpatch_types(class_table, field_tuples, fullrecord, record.for_condition)
                backpatch_types(class_table, field_tuples, fullrecord, record.for_update)
                backpatch_types(class_table, field_tuples, fullrecord, record.loop_body)
            case "Return":
                backpatch_types(class_table, field_tuples, fullrecord, record.return_val)
            case "Expr":
                backpatch_types(class_table, field_tuples, fullrecord, record.expression)
            case "Block":
                for stmt in record.block:
                    backpatch_types(class_table, field_tuples, fullrecord, stmt)
            case _:
                if type == "Break" or type == "Continue" or type == "Skip":
                    pass
                else:
                    print(type)
                    print(record)
                    print("error not a proper statement type")
        record.assign_type_correct()
        pass
    elif isinstance(record, decaf_ast.ExpressionRecord):
        type = record.expression_type
        match type:
            case "Constant":
                pass
            case "Variable":
                typesetted = 0
                for var in fullrecord.variable_table:
                    if var.name == record.var_symbol:
                        record.change_type(var.type.type)
                        typesetted = 1
                        break
                
                if typesetted == 1:
                    for tup in field_tuples:
                        if tup[1] == record.var_symbol:
                            record.change_type(tup[0])
                            break
                pass
            case "Unary":
                backpatch_types(class_table, field_tuples, fullrecord, record.unary_operand)
            case "Binary":
                backpatch_types(class_table, field_tuples, fullrecord, record.binary_operand1)
                backpatch_types(class_table, field_tuples, fullrecord, record.binary_operand2)
            case "Assign":
                backpatch_types(class_table, field_tuples, fullrecord, record.assign_left)
                backpatch_types(class_table, field_tuples, fullrecord, record.assign_right)
            case "Auto":
                backpatch_types(class_table, field_tuples, fullrecord, record.auto_operand)
            case "Field-access":
                backpatch_types(class_table, field_tuples, fullrecord, record.fmn_base)
            case "Method-call":
                backpatch_types(class_table, field_tuples, fullrecord, record.fmn_base)
                for expr in record.mn_args:
                    backpatch_types(class_table, field_tuples, fullrecord, expr)
            case "New-object":
                for expr in record.mn_args:
                    backpatch_types(class_table, field_tuples, fullrecord, expr)
            case "this":
                if isinstance(fullrecord, decaf_ast.ConstructorRecord):
                    class_name = fullrecord.name
                elif isinstance(fullrecord, decaf_ast.MethodRecord):
                    class_name = fullrecord.containing_class
                record.type = "user(" + class_name + ")"
            case "super":
                if isinstance(fullrecord, decaf_ast.ConstructorRecord):
                    class_name = fullrecord.name
                elif isinstance(fullrecord, decaf_ast.MethodRecord):
                    class_name = fullrecord.containing_class
                for tup in all_supers:
                    if tup[0] == class_name:
                        record.type = "user(" + tup[1] + ")"
                if "user(" not in record.type:
                    record.type = "error"
                pass
            case _:
                if type != "this" or type != "super":
                    print("Error not an expression type")
        record.assign_type()
        pass
    else:
        pass

def print_error(class_table, cur_record, record):
    if isinstance(record, decaf_ast.StatementRecord):
        type = record.statement_type
        match type:
            case "If":
                if record.type_correct == "error":
                    if record.if_condition.type == "error" or record.if_condition.type != "boolean":
                        exit(f"IF statement - Condition not boolean at line {record.line_start} at character {record.line_end}")
                    elif record.then_statement.type_correct == "error":
                        exit(f"IF statement - Type error in THEN statement at line {record.line_start} at character {record.line_end}")
                    elif record.else_statement != None and record.else_statement.type_correct == "error":
                        exit(f"IF statement - Type error in ELSE statement at line {record.line_start} at character {record.line_end}")
                    else:
                        print("if is error without parts being error")
                print_error(class_table, cur_record, record.if_condition)
                print_error(class_table, cur_record, record.then_statement)
                if record.else_statement != None:
                    print_error(class_table, cur_record, record.else_statement)
            case "While":
                if record.type_correct == "error":
                    if record.while_condition.type == "error" or record.while_condition.type != "boolean":
                        exit(f"WHILE statement - Condition not boolean at line {record.line_start} at character {record.line_end}")
                    elif record.loop_body.type_correct == "error":
                        exit(f"WHILE statement - Type error in loop body at line {record.line_start} at character {record.line_end}")
                    else:
                        print("while error without parts being error")  
                print_error(class_table, cur_record, record.while_condition)
                print_error(class_table, cur_record, record.loop_body)
            case "For":
                if record.type_correct == "error":
                    if record.for_init.type_correct == "error":
                        exit(f"FOR statement - Type error in initialization at line {record.line_start} at character {record.line_end}")
                    if record.for_condition.type == "error" or record.for_condition.type != "boolean":
                        exit(f"FOR statement - Condition not boolean at line {record.line_start} at character {record.line_end}")
                    elif record.for_update.type_correct == "error":
                        exit(f"FOR statement - Type error in update at line {record.line_start} at character {record.line_end}")
                    elif record.loop_body.type_correct == "error":
                        exit(f"FOR statement - Type error in loop body at line {record.line_start} at character {record.line_end}")
                    else:
                        print("for error without any part being error")
                print_error(class_table, cur_record, record.for_init)
                print_error(class_table, cur_record, record.for_condition)
                print_error(class_table, cur_record, record.for_update)
                print_error(class_table, cur_record, record.loop_body)
            case "Return":
                return_type = cur_record.return_type
                if return_type != None:
                    if return_type != "void" and isinstance(record.return_val, decaf_ast.StatementRecord):
                        exit(f"RETURN statement - NON-VOID method returns nothing at line {record.line_start} at character {record.line_end}")
                    elif return_type == "void" and isinstance(record.return_val, decaf_ast.ExpressionRecord):
                        exit(f"RETURN statement - VOID method returns a value at line {record.line_start} at character {record.line_end}")
                    else:
                        record.type_correct = "yes"
                print_error(class_table, cur_record, record.return_val)
            case "Expr":
                print_error(class_table, cur_record, record.expression)
            case "Block":
                for stmt in record.block:
                    print_error(class_table, cur_record, stmt)
            case _:
                if type != "Break" or type != "Continue" or type != "Skip":
                    print("error not a proper statement type")
        record.assign_type_correct()
        pass
    elif isinstance(record, decaf_ast.ExpressionRecord):
        type = record.expression_type
        match type:
            case "Constant":
                pass
            case "Variable":
                pass
            case "Unary":
                if record.type == "error":
                    if record.unary_operator == "uminus":
                        exit(f"UNARY MINUS - Expression is not a number")
                    elif record.unary_operator == "neg":
                        exit(f"UNARY NEGATION - Expression is not a boolean")
                print_error(class_table, cur_record, record.unary_operand)
            case "Binary":
                if record.type == "error":
                    arith_ops = ["add", "sub", "mul", "div"]
                    bool_ops = ["and", "or"]
                    arith_comps = ["lt", "leq", "gt", "geq"]
                    bool_comps = ["eq", "neq"]
                    if record.binary_operator in arith_ops:
                        exit(f"BINARY ARITHMETIC {record.binary_operator} - Operand is not a number")
                    elif record.binary_operator in bool_ops:
                        exit(f"BINARY BOOLEAN {record.binary_operator} - Operand it not a boolean")
                    elif record.binary_operator in arith_comps:
                        exit(f"BINARY ARITHMETIC {record.binary_operator} - Operand is not a number")
                    elif record.binary_operator in bool_comps:
                        exit(f"BINARY EQUALITY {record.binary_operator} - Operands are not subtypes")
                    else:
                        print("invalid binary operator???")
                print_error(class_table, cur_record, record.binary_operand1)
                print_error(class_table, cur_record, record.binary_operand2)
            case "Assign":
                print_error(class_table, cur_record, record.assign_left)
                print_error(class_table, cur_record, record.assign_right)
            case "Auto":
                if record.type == "error":
                    exit(f"AUTO - Operand is not a number at line {record.line_start} at character {record.line_end}")
                print_error(class_table, cur_record, record.auto_operand)
            case "Field-access":
                #done later
                print_error(class_table, cur_record, record.fmn_base)
            case "Method-call":
                #done later
                print_error(class_table, cur_record, record.fmn_base)
                for expr in record.mn_args:
                    print_error(class_table, cur_record, expr)
            case "New-object":
                #done later
                all_types_from_new = []
                all_param_types = []
                for expr in record.mn_args:
                    all_types_from_new.append(expr.type)
                if record.fmn_name in all_class_names:
                    class_record = class_table.classes[record.fmn_name]
                    constructor = class_record.constructors[0]
                    for param in constructor.parameters:
                        all_param_types.append(param.type)
                if all_param_types != all_types_from_new:
                    exit("New object has inadequate parameters")

                for expr in record.mn_args:
                    print_error(class_table, cur_record, expr)
            case "this":
                if record.type == "error":
                    exit("THIS error")
            case "super":
                if record.type == "error":
                    exit("SUPER error")
            case _:
                if type != "this" or type != "super":
                    print("Error not an expression type")
        record.assign_type()
        pass