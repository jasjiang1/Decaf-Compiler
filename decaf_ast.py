import decaf_typecheck

class ClassTable:
    def __init__(self):
        self.classes = {}

    def add_class(self, class_record):
        if class_record.name in self.classes:
            exit(f"CLASS: Class {class_record.name} already exists")
        self.classes[class_record.name] = class_record
    
    def get_class(self, class_name):
        return self.classes.get(class_name)
    
    def __str__(self):
        for each_class in self.classes.values():
            print(each_class)
        return ""

class VariableTable:
    def __init__(self):
        self.variables = {}
        self.next_id = 1

    def add_variable(self, variable_record):
        if variable_record.name in self.variables:
            return "dupe"
        variable_record.set_id(self.next_id)
        self.next_id += 1
        self.variables[variable_record.name] = variable_record
        return "valid"

    def get_variable(self, variable_name):
        return self.variables.get(variable_name)
    
    def __iter__(self):
        self._iter_index = 0
        self._keys = list(self.variables.keys())
        return self
    
    def __next__(self):
        if self._iter_index < len(self._keys):
            key = self._keys[self._iter_index]  
            self._iter_index += 1  
            return self.variables[key]  
        else:
            raise StopIteration

class ClassRecord:
    def __init__(self, name, super = ""):
        self.name = name
        if super == None:
            self.super = ""
        else:
            self.super = super
        self.constructors = []
        self.methods = []
        self.fields = []

    def add_constructor(self, constructor):
        self.constructors.append(constructor)
    
    def add_method(self, method):
        self.methods.append(method)

    def add_field(self, field):
        for field_record in self.fields:
            if field_record.name ==field.name:
                exit(f"FIELD : Field {field.name} already exists in Class {self.name}")
        self.fields.append(field)

    def __str__(self):
        field_string = ""
        constructor_string = ""
        method_string = ""
        for field in self.fields:
            field_string += str(field) + "\n"
        for constructor in self.constructors:
            constructor_string += str(constructor) + "\n"
        for method in self.methods:
            method_string += str(method) + "\n"

        return f'''Class Name: {self.name}\nSuperclass Name: {self.super}\nFields:\n{field_string}Constructors:\n{constructor_string}Methods:\n{method_string}------------------------------------------------------------------------------\n'''
    
class ConstructorRecord:
    unique_id = 1

    def __init__(self, name, visibility, parameters, variable_table, body):
        self.id = ConstructorRecord.unique_id
        ConstructorRecord.unique_id += 1
        self.visibility = visibility
        self.parameters = parameters
        self.variable_table = variable_table
        self.body = body
        self.name = name

    def __str__(self):
        parameters_string = ""
        variables_string = ""
        for parameter in self.parameters:
            parameters_string += str(parameter) + ", "
        for variable in self.variable_table:
            variables_string += str(variable) + "\n"
        return f'''CONSTRUCTOR: {self.id}, {self.visibility} \nConstructor Parameters: {parameters_string} \nVariable Table: \n{variables_string}Constructor Body: \n{str(self.body)}'''

class MethodRecord:
    unique_id = 1

    def __init__(self, name, containing_class, visibility, applicability, parameters, return_type, variable_table, body):
        self.id = MethodRecord.unique_id
        MethodRecord.unique_id += 1
        self.name = name
        self.containing_class = containing_class
        self.visibility = visibility
        self.applicability = applicability
        self.parameters = parameters
        self.return_type =  return_type
        self.variable_table = variable_table
        self.body = body

    def __str__(self):
        parameters_string = ""
        variables_string = ""

        for index, parameter in enumerate(self.parameters):
            if index < len(self.parameters) - 1:
                addon = ", \n"
            else:
                addon = ""
            parameters_string += str(parameter.id) + addon

        for variable in self.variable_table:
            variables_string += str(variable) + "\n"
        return f'''METHOD: {self.id}, {self.name}, {self.containing_class}, {self.visibility}, {self.applicability}, {self.return_type} \nMethod Parameters: {parameters_string} \nVariable Table: \n{variables_string}Method Body: \n{str(self.body)}'''

class FieldRecord:
    unique_id = 1

    def __init__(self, name, containing_class, visibility, applicability, type):
        self.id = FieldRecord.unique_id
        FieldRecord.unique_id += 1
        self.name = name
        self.containing_class = containing_class
        self.visibility = visibility
        self.applicability = applicability
        self.type = type
    def __str__(self):
        return f"FIELD {self.id}, {self.name}, {self.containing_class}, {self.visibility}, {self.applicability}, {str(self.type)}"

class VariableRecord:
    unique_id = 1
    def __init__(self, name, kind, type):
        self.id = None
        self.name = name
        self.kind = kind
        self.type = type
    
    def set_id(self, unique_id):
        self.id = unique_id

    def __str__(self):
        return f"VARIABLE {self.id}, {self.name}, {self.kind}, {self.type}"

class TypeRecord:
    def __init__(self, type):
        self.type = type
    
    def __str__(self):
        return f"{self.type}"

class StatementRecord:
    def __init__(self, statement_type, line_start, line_end, **args):
        self.statement_type = statement_type 
        self.line_start = line_start
        self.line_end = line_end

        self.if_condition = args.get("if_condition") 
        self.then_statement = args.get("then_statement") 
        self.else_statement = args.get("else_statement")

        self.while_condition = args.get("while_condition") 
        self.for_init = args.get("for_init") 
        self.for_condition = args.get("for_condition") 
        self.for_update = args.get("for_update") 
        self.loop_body = args.get("loop_body")

        self.return_val = args.get("return_val") 
        self.expression = args.get("expression") 
        self.block = args.get("block")
        self.type_correct = "yes"
        self.assign_type_correct()

    def change_type_correct(self, type_correct):
        self.type_correct = type_correct

    def assign_type_correct(self):
        statement_type = self.statement_type
        line_start = self.line_start
        line_end = self.line_end
        if (statement_type == "If"):
            if self.if_condition.type != "boolean" and self.if_condition.type != "tbd":
                self.type_correct = "error"
            if self.then_statement.type_correct == "error":
                self.type_correct = "error"
            if self.else_statement != None:
                if self.else_statement.type_correct == "error":
                    self.type_correct = "error"
        if (statement_type == "While"):
            if self.while_condition.type != "boolean" and self.while_condition.type != "tbd":
                self.type_correct = "error"
            if self.loop_body != [] or self.loop_body != None:
                for statement in self.loop_body.block:
                    if statement.type_correct == "error":
                        self.type_correct = "error"
        if (statement_type == "For"):
            if self.for_condition.type != "boolean" and self.for_condition.type != "tbd":
                self.type_correct = "error"
            if self.for_init.type_correct == "error":
                self.type_correct = "error"
            if self.for_update.type_correct == "error":
                self.type_correct = "error"
            if self.loop_body != [] or self.loop_body != None:
                for statement in self.loop_body.block:
                    if statement.type_correct == "error":
                        self.type_correct = "error"
        if (statement_type == "Return"):
            self.type_correct = "tbd"
        if (statement_type == "Expr"):
            if self.expression.type == "error":
                self.type_correct = "error"   
        if (statement_type == "Block"):
            if self.block != [] or self.block != None:
                for statement in self.block:
                    if isinstance(statement, StatementRecord):
                        if statement.type_correct == "error":
                            self.type_correct = "error" 

    def remove_statement(self):
        if self.statement_type == "Block":
            pop_indices = []
            all_vars = []
            for index, stmt in enumerate(self.block):
                if not isinstance(stmt, StatementRecord):
                    pop_indices.append(index)
            for index in reversed(pop_indices):
                all_vars.append(self.block[index])
                self.block.pop(index)
            return all_vars

    def __str__(self): 
        statement_string = ""
        if self.statement_type == "If":
            if self.else_statement != None:
                addon = ", " + str(self.else_statement)
            else:
                addon = ""
            statement_string = str(self.if_condition) + ", "  + str(self.then_statement) + addon
        elif self.statement_type == "While":
            addon = ""
            if self.loop_body != [] and self.loop_body != None:
                for stmt in self.loop_body.block:
                    addon += ", " + str(stmt)
            statement_string = str(self.while_condition) + ", " + addon
        elif self.statement_type == "For":
            addon = ""
            if self.loop_body != [] and self.loop_body != None:
                for stmt in self.loop_body.block:
                    addon += ", " + str(stmt)
            statement_string = str(self.for_init) + ", " + str(self.for_condition) + ", " + str(self.for_update) + addon
        elif self.statement_type == "Return":
            statement_string = str(self.return_val)
        elif self.statement_type == "Expr":
            statement_string = str(self.expression)
        elif self.statement_type == "Block":
            statement_string += "[\n"
            if self.block != None:
                addon = ", "
                for index, x in enumerate(self.block):
                    if index < len(self.block) - 1:
                        addon = ", \n"
                    else:
                        addon = ""
                    statement_string += str(x) + addon
            statement_string += "\n]"
        elif self.statement_type == "Break":
            pass
        elif self.statement_type == "Continue":
            pass
        elif self.statement_type == "Skip":
            pass
        else:
            exit(f"invalid statement type {self.statement_type}")

        return f"{self.statement_type}({statement_string})"

class ExpressionRecord:
    def __init__(self, expression_type, line_start, line_end, **args):
        self.expression_type = expression_type
        self.line_start = line_start
        self.line_end = line_end

        self.constant = args.get("constant")
        self.value = args.get("value")
        self.var_symbol = args.get("value")
        self.unary_operator = args.get("unary_operator") 
        self.unary_operand = args.get("unary_operand") 

        self.binary_operator = args.get("binary_operator") 
        self.binary_operand1 = args.get("binary_operand1") 
        self.binary_operand2 = args.get("binary_operand2")

        self.assign_left = args.get("assign_left")
        self.assign_right = args.get("assign_right") 

        self.auto_operand = args.get("auto_operand")
        self.auto_type = args.get("auto_type") 
        self.auto_place = args.get("auto_place") 

        self.fmn_base = args.get("fmn_base") 
        self.fmn_name = args.get("fmn_name")
        self.mn_args = args.get("mn_args") 
        self.class_name = args.get("class_name")
        self.type = "tbd"
        self.assign_type()

    def change_type(self, type):
        self.type = type

    def assign_type(self):
        line_start = self.line_start
        line_end = self.line_end
        if (self.expression_type == "Constant"):
            consts = {"Integer-constant":"int", "Float-constant":"float", "String-constant":"string", "true":"boolean", "false":"boolean", "null":"null", "void":None}
            self.type = consts[self.constant]
        elif (self.expression_type == "Variable"):
            pass
        elif (self.expression_type == "Unary"):
            if self.unary_operator == "uminus":
                if self.unary_operand.type == "int" or self.unary_operand.type == "float":
                    self.type = self.unary_operand.type
                elif self.unary_operand.type != "tbd":
                    self.type = "error"
            elif self.unary_operator == "neg":
                if self.unary_operand.type == "boolean":
                    self.type = "boolean"
                elif self.unary_operand.type != "tbd":
                    self.type = "error"
        elif (self.expression_type == "Binary"):
            arith_ops = ["add", "sub", "mul", "div"]
            bool_ops = ["and", "or"]
            arith_comps = ["lt", "leq", "gt", "geq"]
            bool_comps = ["eq", "neq"]
            type1 = self.binary_operand1.type
            type2 = self.binary_operand2.type
            if self.binary_operator in arith_ops:
                if type1 == "int" and type2 == "int":
                    self.type = "int"
                elif type1 == "float" and (type2 == "int" or type2 == "float"):
                    self.type = "float"
                elif type2 == "float" and (type1 == "int" or type1 == "float"):
                    self.type = "float"
                elif type1 == "tbd" or type2 == "tbd":
                    self.type = "tbd"
                else:
                    self.type = "error"
            elif self.binary_operator in bool_ops:
                if type1 == "boolean" and type2 == "boolean":
                    self.type = "boolean"
                elif type1 == "tbd" or type2 == "tbd":
                    self.type = "tbd"
                else:
                    self.type = "error"
            elif self.binary_operator in arith_comps:
                if type1 == "int" or type1 == "float":
                    if type2 == "int" or type2 == "float":
                        self.type = "boolean"
                    elif type2 == "tbd":
                        pass
                    else:
                        self.type = "error"
                elif type1 == "tbd":
                    pass
                else:
                    self.type = "error"
            elif self.binary_operator in bool_comps:
                if decaf_typecheck.is_subtype(type1, type2) or decaf_typecheck.is_subtype(type2, type1):
                    self.type == "boolean"
                elif type1 == "tbd" or type2 == "tbd":
                    pass
                else:
                    self.type = "error"
        elif (self.expression_type == "Assign"):
            type1 = self.assign_left.type
            type2 = self.assign_right.type
            if decaf_typecheck.is_subtype(type2, type1):
                self.type = type2
            elif type1 == "tbd" or type2 == "tbd":
                pass
            else:
                self.type = "error"
        elif (self.expression_type == "Auto"):
            type1 = self.auto_operand.type
            if type1 == "int" or type1 == "float":
                self.type = type1
            elif type1 == "tbd":
                pass
            else:
                self.type = "error"
        elif (self.expression_type == "Field-access"):
            pass #must be done later
        elif (self.expression_type == "Method-call"):
            pass #must be done later
        elif (self.expression_type == "New-object"):
            pass #must be done later
        elif (self.expression_type == "this"):
            pass #must be done later
        elif (self.expression_type == "super"):
            pass #must be done later
        elif (self.expression_type == "Class-reference"):
            pass #must be done later

    def change_value(self, new_value):
        self.value = new_value

    def __str__(self):
        expression_string = ""
        no_value = ["null", "true", "false"]
        if self.expression_type == "Constant":
            addon = f"({self.value})" if self.constant not in no_value else ""
            expression_string = self.constant + addon
        elif self.expression_type == "Variable":
            expression_string = self.value
        elif self.expression_type == "Unary":
            if self.unary_operator != "":
                expression_string = self.unary_operator + ", " + str(self.unary_operand)
            else:
                expression_string = str(self.unary_operand)
        elif self.expression_type == "Binary":
            expression_string = self.binary_operator + ", " + str(self.binary_operand1) + ", " + str(self.binary_operand2)
        elif self.expression_type == "Assign":
            expression_string = str(self.assign_left) + ", " + str(self.assign_right)
        elif self.expression_type == "Auto":
            expression_string = str(self.auto_operand) + ", " + self.auto_type + ", " + self.auto_place
        elif self.expression_type == "Field-access":
            expression_string = str(self.fmn_base) + ", " + self.fmn_name
        elif self.expression_type == "Method-call":
            args_string = []
            for arg in self.mn_args:
                args_string.append(str(arg))
            expression_string = str(self.fmn_base) + ", " + self.fmn_name + ", " + str(args_string)
        elif self.expression_type == "New-object":
            args_string = []
            for arg in self.mn_args:
                args_string.append(str(arg))
            expression_string = self.fmn_name + ", " + str(args_string)
        elif self.expression_type == "this":
            return "This"
        elif self.expression_type == "super":
            return "Super"
            pass
        elif self.expression_type == "Class-reference":
            expression_string = self.class_name
        else:
            exit(f'Something went wrong {self.expression_type}')
        return f"{self.expression_type}({expression_string})"
    
class_table = ClassTable()

int_type = TypeRecord("int")
float_type = TypeRecord("float")
boolean_type = TypeRecord("boolean")
string_type = TypeRecord("string")

#In Class
in_class = ClassRecord("In")
in_methods = [
    MethodRecord("scan_int", in_class.name, "public", "static", [], int_type, VariableTable(), []),
    MethodRecord("scan_float", in_class.name, "public", "static", [], float_type, VariableTable(), [])
]

for method in in_methods:
    in_class.add_method(method)
class_table.add_class(in_class)

#Out Class
out_class = ClassRecord("Out")
out_methods = [
    MethodRecord("print", out_class.name, "public", "static", [VariableRecord("i", "formal", int_type)], int_type, VariableTable(), []),
    MethodRecord("print", out_class.name, "public", "static", [VariableRecord("f", "formal", float_type)], float_type, VariableTable(), []),
    MethodRecord("print", out_class.name, "public", "static", [VariableRecord("b", "formal", boolean_type)], boolean_type, VariableTable(), []),
    MethodRecord("print", out_class.name, "public", "static", [VariableRecord("s", "formal", string_type)], string_type, VariableTable(), [])
]
for method in out_methods:
    out_class.add_method(method)
class_table.add_class(out_class)