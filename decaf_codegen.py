import decaf_ast

class AbstractCodeGenerator:
    def __init__(self):
        self.temp_register_counter = 0
        self.arg_register_counter = 0
        self.break_stack = []
        self.continue_stack = []
        self.constructor_method_map = {}

        self.cur_method_constructor = None
        self.instance_fields = {}  
        self.static_fields = {}  
        self.heap = []  

        self.temp_registers = {}
        self.arg_registers = {}
        self.class_table = None
        self.final_string = ""

        self.label_queue = []
        self.label_count = 1

    def get_temp_register(self):
        reg = f"t{self.temp_register_counter}"
        self.temp_register_counter += 1
        return reg

    def get_arg_register(self):
        reg = f"a{self.arg_register_counter}"
        self.arg_register_counter += 1
        return reg

    def generate_code(self, class_table):
        self.class_table = class_table
        self.map_fields(class_table)
        for class_obj in class_table.classes.values():
            self.final_string += f"# ===Class {class_obj.name}=== \n"
            for constructor in class_obj.constructors:
                self.cur_method_constructor = constructor
                self.generate_constructor_code(constructor)
            for method in class_obj.methods:
                self.cur_method_constructor = method
                self.final_string += f"M_{method.name}_{method.id}:\n"
                self.generate_method_code(method)
        self.final_string += ".static_data 0"

    def map_fields(self, class_table):
        for class_obj in class_table.classes.values():
            for field in class_obj.fields:
                if field.applicability == "static":
                    self.static_fields[f"{class_obj.name} = {field.name}"] = {"name": field.name, "type":field.type.type, "id":field.id}
                else:
                    self.instance_fields[f"{class_obj.name} = {field.name}"] = {"name": field.name, "type":field.type.type, "id":field.id}

    def generate_constructor_code(self, constructor):
        self.reset_registers()
        for var in constructor.variable_table:
            if var.kind == "formal":
                self.arg_registers[self.get_arg_register()] = {"name":var.name, "type":var.type.type, "value":None, "id":var.id}
            else:
                self.temp_registers[self.get_temp_register()] = {"name":var.name, "type":var.type.type, "value":None, "id":var.id}
        if isinstance(constructor.body, decaf_ast.StatementRecord):
            for stmt in constructor.body.block:
                self.generate_stmt_or_expr_code(stmt)
        else:
            for stmt in constructor.body:
                self.generate_stmt_or_expr_code(stmt)

    def generate_method_code(self, method):
        self.reset_registers()
        if method.visibility == "instance":
            self.get_arg_register()
        for var in method.variable_table:
            if var.kind == "formal":
                self.arg_registers[self.get_arg_register()] = {"name":var.name, "type":var.type.type, "value":None, "id":var.id}
            else:
                self.temp_registers[self.get_temp_register()] = {"name":var.name, "type":var.type.type, "value":None, "id":var.id}
        if isinstance(method.body, decaf_ast.StatementRecord):
            for stmt in method.body.block:
                self.generate_stmt_or_expr_code(stmt)
        else:
            for stmt in method.body:
                self.generate_stmt_or_expr_code(stmt)

    def generate_stmt_or_expr_code(self, stmt_or_expr):
        if isinstance(stmt_or_expr, decaf_ast.StatementRecord):
            stype = stmt_or_expr.statement_type
            match stype:
                case "If":
                    cond = self.generate_stmt_or_expr_code(stmt_or_expr.if_condition)
                    then = self.generate_stmt_or_expr_code(stmt_or_expr.then_statement)
                    els = None
                    if stmt_or_expr.else_statement != None:
                        els = self.generate_stmt_or_expr_code(stmt_or_expr.else_statement)
                    if els != None:
                        addon = f"\nelse: {els}"
                    else:
                        addon = ""
                    if "binary" in cond:
                        if_num = self.label_count
                        self.label_count += 1
                        cond_temp = cond.split()[1]
                        self.final_string += f"bz {cond_temp}, if_{if_num}_else\n"
                        self.final_string += f"if_{if_num}_then:\n"
                        for stmt in then:
                            self.generate_stmt_or_expr_code(stmt)
                        self.final_string += f"jmp if_{if_num}_end\n"
                        self.final_string += f"if_{if_num}_else:\n"
                        if els != None:
                            for stmt in els:
                                self.generate_stmt_or_expr_code(stmt)
                        self.label_queue.append(f"if_{if_num}_end:\n")
                        while self.label_queue:
                            self.final_string += self.label_queue.pop(0)

                case "While":
                    body = self.generate_stmt_or_expr_code(stmt_or_expr.loop_body)
                    while_num =self.label_count
                    self.label_count += 1
                    cond_label = f"while_{while_num}_cond"
                    self.final_string += cond_label + ":\n"
                    cond = self.generate_stmt_or_expr_code(stmt_or_expr.while_condition)
                    if "binary" in cond:
                        cond_temp = cond.split()[1]
                        while_end = f"while_{while_num}_end"
                        self.final_string += f"bz {cond_temp}, {while_end}\n"
                        self.final_string += f"while_{while_num}_body:\n"
                        for stmt in body:
                            self.generate_stmt_or_expr_code(stmt)
                        self.final_string += f"jmp {cond_label}\n"
                        self.final_string += while_end + ":\n"
                case "For":
                    init = self.generate_stmt_or_expr_code(stmt_or_expr.for_init)
                    for_num = self.label_count
                    self.label_count += 1
                    cond_label = f"for_{for_num}_cond"
                    body_label = f"for_{for_num}_body"
                    update_label = f"for_{for_num}_update"
                    end_label = f"for_{for_num}_end"

                    self.final_string += cond_label + ":\n"
                    cond = self.generate_stmt_or_expr_code(stmt_or_expr.for_condition)
                    if "binary" in cond:
                        cond_temp = cond.split()[1]
                        self.final_string += f"bz {cond_temp}, {end_label}\n"
                        self.final_string += body_label + ":\n"
                        body = self.generate_stmt_or_expr_code(stmt_or_expr.loop_body)
                        for stmt in body:
                            self.generate_stmt_or_expr_code(stmt)
                        self.final_string += update_label + ":\n"
                        update = self.generate_stmt_or_expr_code(stmt_or_expr.for_update)
                        self.final_string += f"jmp {cond_label}\n"
                        self.final_string += end_label + ":\n"
                case "Return":
                    ret = self.generate_stmt_or_expr_code(stmt_or_expr.return_val)
                case "Expr":
                    ret = self.generate_stmt_or_expr_code(stmt_or_expr.expression)
                    return ret
                case "Block":
                    return stmt_or_expr.block
                case _:
                    if type == "Break" or type == "Continue" or type == "Skip":
                        return type
                    else:
                        pass
        elif isinstance(stmt_or_expr, decaf_ast.ExpressionRecord):
            etype = stmt_or_expr.expression_type
            match etype:
                case "Constant":
                    if stmt_or_expr.constant == "true" or stmt_or_expr.constant == "false" or stmt_or_expr.constant == "null":
                        return stmt_or_expr.constant
                    else:
                        return stmt_or_expr.value
                case "Variable":
                    return str(stmt_or_expr)
                case "Unary":
                    operator = stmt_or_expr.unary_operator
                    operand = self.generate_stmt_or_expr_code(stmt_or_expr.unary_operand)
                    if (operator == ""):
                        return f"{operand}"
                    elif operator == "uminus":
                        new_temp = self.get_temp_register()
                        self.final_string += f"move_immed_i {new_temp}, -1\n"
                        that_temp = self.get_register_from_Variable(operand)
                        self.final_string += f"imul {new_temp}, {new_temp}, {that_temp}\n"
                        return f"unary {new_temp}"
                    elif operator == "neg":
                        new_temp = self.get_temp_register()
                        self.final_string += f"move immed_i {new_temp}, 1\n"
                        that_temp = self.get_register_from_Variable(operand)
                        self.final_string += f"isub {new_temp}, {new_temp}, {that_temp}\n"
                        return f"unary {new_temp}"
                    else:
                        pass
                    return f"unary {operator} {operand}"
                case "Binary":
                    operator = stmt_or_expr.binary_operator
                    op1 = self.generate_stmt_or_expr_code(stmt_or_expr.binary_operand1)
                    op2 = self.generate_stmt_or_expr_code(stmt_or_expr.binary_operand2)
                    op1_temp = self.get_register_from_Variable(op1)
                    op2_temp = self.get_register_from_Variable(op2)
                    new_temp = self.get_temp_register()
                    i_or_f = ""
                    op1_type = self.get_type_from_Variable(op1)
                    op2_type = self.get_type_from_Variable(op2)
                    if op1_type == "float" or op2_type == "float":
                        i_or_f = "f"
                    elif op1_type == "int" or op2_type == "int":
                        i_or_f = "i"
                    else:
                        pass
                    match operator:
                        case "add":
                            self.final_string += f"{i_or_f}add {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "mul":
                            self.final_string += f"{i_or_f}mul {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "sub":
                            self.final_string += f"{i_or_f}sub {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "div":
                            self.final_string += f"{i_or_f}div {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "and":
                            self.final_string += f"imul {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "or":
                            self.final_string += f"move_immed_i {new_temp}, 1\n"
                            now_old_temp = new_temp
                            new_temp = self.get_temp_register()
                            self.final_string += f"iadd {new_temp}, {op1_temp}, {op2_temp}\n"
                            self.final_string += f"igeq {new_temp}, {new_temp}, {now_old_temp}\n"
                            return f"binary {new_temp}"
                        case "lt":
                            self.final_string += f"{i_or_f}lt {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "leq":
                            self.final_string += f"{i_or_f}leq {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "gt":
                            self.final_string += f"{i_or_f}gt {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "geq":
                            self.final_string += f"{i_or_f}get {new_temp}, {op1_temp}, {op2_temp}\n"
                            return f"binary {new_temp}"
                        case "eq": 
                            self.final_string += f"{i_or_f}geq {new_temp}, {op1_temp}, {op2_temp}\n"
                            now_old_temp = new_temp
                            new_temp = self.get_temp_register()
                            self.final_string += f"{i_or_f}leq {new_temp}, {op1_temp}, {op2_temp}\n"
                            self.final_string += f"imul {new_temp}, {new_temp}, {now_old_temp}\n"
                            return f"binary {new_temp}"
                        case "neq":                             
                            self.final_string += f"{i_or_f}gt {new_temp}, {op1_temp}, {op2_temp}\n"
                            now_old_temp = new_temp
                            new_temp = self.get_temp_register()
                            self.final_string += f"{i_or_f}lt {new_temp}, {op1_temp}, {op2_temp}\n"
                            self.final_string += f"iadd {new_temp}, {new_temp}, {now_old_temp}\n"
                            return f"binary {new_temp}"
                        case _:
                            pass
                    return f"binary {op1} {operator} {op2}"
                case "Assign":
                    left = self.generate_stmt_or_expr_code(stmt_or_expr.assign_left)
                    right = self.generate_stmt_or_expr_code(stmt_or_expr.assign_right)
                    if (isinstance(right, int) or isinstance(right, float)):
                        new_temp = self.get_temp_register()
                        i_or_f = "i" if isinstance(right, int) else "f"
                        self.final_string += f"move_immed_{i_or_f} {new_temp}, {right}\n"
                        self.move_registers(left, new_temp)
                    else:
                        if "unary" in right or "binary" in right:
                            right_temp = right.split()[1]
                            self.move_registers(left, right_temp)
                        elif right == "true" or right == "false":
                            new_temp = self.get_temp_register()
                            tf = 0 if right == "false" else 1
                            self.final_string += f"move_immed_i {new_temp}, {tf}\n"
                            self.move_registers(left, new_temp)
                    return f"{left} = {right}"
                case "Auto":
                    operand = self.generate_stmt_or_expr_code(stmt_or_expr.auto_operand)
                    autotype = stmt_or_expr.auto_type
                    new_temp = self.get_temp_register()
                    that_temp = self.get_register_from_Variable(operand)
                    self.final_string += f"move {new_temp}, {that_temp}\n"
                    new_temp = self.get_temp_register()
                    self.final_string += f"move_immed_i {new_temp}, 1\n"
                    if (autotype == "inc"):
                        self.final_string += f"iadd {that_temp}, {that_temp}, {new_temp}\n"
                        pass
                    else:
                        self.final_string += f"isub {that_temp}, {that_temp}, {new_temp}\n"
                        pass
                    
                    if (stmt_or_expr.auto_place == "post"):
                        return f"{operand}{autotype}"
                    else:
                        return f"{autotype}{operand}"
                case "Field-access":
                    base = self.generate_stmt_or_expr_code(stmt_or_expr.fmn_base)
                    name = stmt_or_expr.fmn_name
                    return f"{base}.{name}"
                case "Method-call":
                    base = self.generate_stmt_or_expr_code(stmt_or_expr.fmn_base)
                    name = stmt_or_expr.fmn_name
                    args_string = ""
                    for arg in stmt_or_expr.mn_args:
                        args_string += arg + ", "
                    if args_string != "":
                        args_string = args_string[:-2]
                    return f"{base}.{name} ({args_string})"               
                case "New-object":
                    name = stmt_or_expr.fmn_name
                    args_string = ""
                    for arg in stmt_or_expr.mn_args:
                        args_string += arg + ", "
                    if args_string != "":
                        args_string = args_string[:-2]
                    return f"new {name} ({args_string})"
                case "this":
                    return "this"
                case "super":
                    return "super"
                case _:
                    print("nnot any valid expression type")
                    pass
                    
        else:
            pass

    def reset_registers(self):
        self.temp_register_counter = 0
        self.arg_register_counter = 0
        self.temp_registers = {}
        self.arg_registers = {}
    
    def get_register_from_Variable(self, var_str):
        var_id = int(var_str.split('(')[1][:-1])
        initial_temp = ""
        for key, value in self.temp_registers.items():
            if value['id'] == var_id:
                initial_temp = key
                break
        return initial_temp

    def move_registers(self, left, new_temp):
        left_id = int(left.split('(')[1][:-1])
        initial_temp = ""
        for key, value in self.temp_registers.items():
            if value['id'] == left_id:
                initial_temp = key
                break
        self.final_string += f"move {initial_temp}, {new_temp}\n"

    def get_type_from_Variable(self, var_str):
        var_id = int(var_str.split('(')[1][:-1])
        for key, value in self.temp_registers.items():
            if value['id'] == var_id:
                return value['type']
        return None