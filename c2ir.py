import sys
import os
from optparse import OptionParser

from pycparser import c_parser, c_ast

import ir_ast

def parse(src_name, module):
    f = open(src_name)
    text = f.read()
    f.close()
    
    parser = c_parser.CParser()
    ast = parser.parse(text, filename=src)
    for ext in ast.ext:
        if isinstance(ext, c_ast.FuncDef):
            module.boards.append(parse_funcdef(module, ext))
        elif isinstance(ext, c_ast.Decl):
            parse_global_decl(module, ext)
        else:
            print("Unknown ext: %s", ext)

    return module

def generate(dest_name, module):
    dest = open(dest_name, "w")
    module_name, _ = os.path.splitext(os.path.basename(dest_name))
    dest.write("(MODULE {}\n".format(module_name))
    dest.write("  (VARIABLES\n")
    for v in module.variables:
        dest.write("    {}\n".format(v.to_sexp()))
    dest.write("  )\n")

    for board in module.boards:
        dest.write(" (BOARD {} {} \n".format(board.kind, board.name))
        
        dest.write("  (VARIABLES\n")
        for v in board.variables:
            dest.write("    {}\n".format(v.to_sexp()))
        dest.write("  )\n")
        
        dest.write("  (SEQUENCER {}\n".format(board.name))
        for s in board.slots:
            dest.write("    {}\n".format(s.to_sexp()))
        dest.write("  )\n")
        dest.write(" ) \n")
        
    dest.write(")\n")
    dest.close()

def conv_type(t):
    names = t.type.names
    if((len(names) == 1) and (names[0] == "void")):
        return "VOID"
    elif((len(names) == 1) and (names[0] == "int")):
        return "INT"
    elif((len(names) == 1) and (names[0] == "char")):
        return "BYTE"
    elif((len(names) == 1) and (names[0] == "short")):
        return "SHORT"
    elif((len(names) == 1) and (names[0] == "long")):
        return "LONG"
    elif((len(names) == 1) and (names[0] == "float")):
        return "FLOAT"
    elif((len(names) == 1) and (names[0] == "double")):
        return "DOUBLE"
    else:
        return "UNKNOWN"

def parse_global_decl(module, stmt):
    original_name = stmt.name
    ir_name = original_name + "_" + module.uniq_id()
    v = ir_ast.Variable(ir_name, conv_type(stmt.type), method="null", original=original_name, public=True, member=True)
    slot = None
    if stmt.init is not None:
        # an assignment step to initialize is required
        pass
    module.variables.append(v)
    return slot

def parse_funcdef(module, func):
    decl = func.decl
    method_name = decl.name
    board = ir_ast.Board(module, decl.name, conv_type(decl.type.type))
    body = func.body
    
    for param_decl in decl.type.args.params:
        original_name = param_decl.name
        ir_name = original_name + "_" + module.uniq_id()
        v = ir_ast.Variable(ir_name, conv_type(param_decl.type), method_param=True, method=method_name, original=original_name)
        board.variables.append(v)

    slot = board.new_slot()
    slot.append_item(ir_ast.SlotItem("METHOD_EXIT", [slot.id+1]))
    
    slot = board.new_slot()
    slot.append_item(ir_ast.SlotItem("METHOD_ENTRY", [slot.id+1]))

    for item in body.block_items:
        parse_stmt(board, item)

    slot = board.new_slot()
    slot.append_item(ir_ast.JPSlotItem(0))
    
    return board

def parse_stmt(board, item):
    slot = None
    if isinstance(item, c_ast.Return):
        slot = parse_return(board, item)
    elif isinstance(item, c_ast.If):
        slot = parse_if(board, item)
    elif isinstance(item, c_ast.For):
        slot = parse_for(board, item)
    elif isinstance(item, c_ast.Compound):
        slot = parse_compound(board, item)
    elif isinstance(item, c_ast.Decl):
        slot = parse_decl(board, item)
    elif isinstance(item, c_ast.Switch):
        slot = parse_switch(board, item)
    elif isinstance(item, c_ast.Case):
        slot = parse_case(board, item)
    elif isinstance(item, c_ast.Default):
        slot = parse_default(board, item)
    elif isinstance(item, c_ast.Assignment):
        slot = parse_assignement(board, item)
    elif isinstance(item, c_ast.Break):
        slot = parse_break(board, item)
    elif isinstance(item, c_ast.UnaryOp):
        v, slot = parse_unaryop(board, item)
    elif isinstance(item, c_ast.EmptyStatement):
        slot = board.new_slot() # join slot
        slot.append_item(ir_ast.JPSlotItem(slot.id+1))
    else:
        print("Not supported stmt yet", item)
    return slot

def parse_assignement(board, stmt):
    rhs = parse_expr(board, stmt.rvalue)
    lhs = parse_expr(board, stmt.lvalue)
    slot = board.new_slot()
    slot.append_item(ir_ast.AssignSlotItem(lhs, rhs))
    return slot

def parse_break(board, stmt):
    pass
    
def parse_return(board, stmt):
    expr = parse_expr(board, stmt.expr)
    slot = board.new_slot()
    slot.append_item(ir_ast.ReturnSlotItem(expr))
    return slot

def parse_if(board, stmt):
    cond = parse_expr(board, stmt.cond)
    
    slot = board.new_slot()
    jt = ir_ast.JTSlotItem(cond)
    slot.append_item(jt)
    
    then_id = slot.id+1
    then_slot = parse_stmt(board, stmt.iftrue)
    else_id = then_slot.id+1
    else_slot = parse_stmt(board, stmt.iffalse)
    
    jt.next_ids = [then_id, else_id]
    
    slot = board.new_slot() # join slot
    slot.append_item(ir_ast.JPSlotItem(slot.id+1))

    if then_slot.is_branch() == False:
        then_slot.next_ids = [slot.id]
    if else_slot.is_branch() == False:
        else_slot.next_ids = [slot.id]
    
    return slot

def parse_for(board, stmt):
    init_slot = parse_stmt(board, stmt.init)
    
    cond_entry = len(board.slots)
    cond = parse_expr(board, stmt.cond)
    cond_slot = board.new_slot()
    jt = ir_ast.JTSlotItem(cond)
    cond_slot.append_item(jt)
    
    body_slot = parse_stmt(board, stmt.stmt)
    update_slot = parse_stmt(board, stmt.next)
    
    slot = board.new_slot()
    slot.append_item(ir_ast.JPSlotItem(slot.id+1))
    jt.next_ids = [body_slot.id, slot.id]

    if update_slot.is_branch() == False:
        for item in update_slot.items:
            item.next_ids = [cond_entry]
    
    return slot
    
def parse_compound(board, stmt):
    slot = None
    for s in stmt.block_items:
        slot = parse_stmt(board, s)
    return slot
        
def parse_decl(board, stmt):
    original_name = stmt.name
    ir_name = original_name + "_" + board.uniq_id()
    v = ir_ast.Variable(ir_name, conv_type(stmt.type), method=board.name, original=original_name)
    slot = None
    if stmt.init is not None:
        # an assignment step to initialize is required
        expr = parse_expr(board, stmt.init)
        slot = board.new_slot() # setup slot
        slot.append_item(ir_ast.AssignSlotItem(v, expr))
    board.variables.append(v)
    return slot
    
def parse_switch(board, stmt):
    cond = parse_expr(board, stmt.cond)
    parse_stmt(board, stmt.stmt)

def parse_case(board, stmt):
    key = parse_expr(board, stmt.expr)
    for s in stmt.stmts:
        parse_stmt(board, s)
        
def parse_default(board, stmt):
    pass

def get_kind(v0, v1):
    if v0.kind == v1.kind:
        return v0.kind
    else:
        return None
    
def parse_expr(board, expr):
    if isinstance(expr, c_ast.BinaryOp):
        return parse_binaryop(board, expr)
    elif isinstance(expr, c_ast.UnaryOp):
        expr, slot = parse_unaryop(board, expr)
        return expr
    elif isinstance(expr, c_ast.ID):
        return parse_id(board, expr)
    elif isinstance(expr, c_ast.Constant):
        return parse_constant(board, expr)
    else:
        print("Not supported expr yet", expr)
        return None

def parse_binaryop(board, expr):
    op = expr.op
    rhs = parse_expr(board, expr.right)
    lhs = parse_expr(board, expr.left)
    v = ir_ast.Variable("binary_op_{}".format(board.uniq_id()), get_kind(lhs, rhs), method=board.name)
    board.variables.append(v)
    slot = board.new_slot()
    ir_op = conv_op(op, v.kind)
    item = ir_ast.BinaryOpSlotItem(ir_op, [len(board.slots)], lhs, rhs, v)
    if is_boolean_op(ir_op):
        v.kind = "BOOLEAN"
    slot.append_item(item)
    return v

def parse_unaryop(board, expr):
    op = expr.op
    v = parse_expr(board, expr.expr)
    ir_op = ""
    if op == "p++":
        ir_op = "ADD"
    elif op == "--":
        ir_op = "SUB"
    else:
        print("not supported unary operation yet", op)
        
    kind = "INT"
    c = ir_ast.Constant("constant_{}".format(board.uniq_id()), kind, 1)
    board.variables.append(c)
    slot = board.new_slot()
    item = ir_ast.BinaryOpSlotItem(ir_op, [len(board.slots)], v, c, v)
    slot.append_item(item)
    return v,slot

def parse_id(board, expr):
    return board.search_variable(expr.name)

def parse_constant(board, expr):
    if expr.type == "int":
        kind = "INT"
    elif expr.type == "char":
        kind = "CHAR"
    elif expr.type == "short":
        kind = "SHORT"
    elif expr.type == "long":
        kind = "LONG"
    elif expr.type == "float":
        kind = "FLOAT"
    elif expr.type == "double":
        kind = "DOUBLE"
    else:
        kind = "UNKNOWN"
    c = ir_ast.Constant("constant_{}".format(board.uniq_id()), kind, expr.value)
    board.variables.append(c)
    return c

def is_boolean_op(op):
    if op == "LT":
        return True
    elif op == "COMPEQ":
        return True
    else:
        return False

def conv_op(op, kind):
    if op == "+":
        if kind == "FLOAT":
            return "FADD32"
        elif kind == "DOUBLE":
            return "FADD64"
        else:
            return "ADD"
    elif op == "-":
        if kind == "FLOAT":
            return "FSUB32"
        elif kind == "DOUBLE":
            return "FSUB64"
        else:
            return "SUB"
    elif op == "*":
        if kind == "FLOAT":
            return "FMUL32"
        elif kind == "DOUBLE":
            return "FMUL64"
        elif kind == "LONG":
            return "MUL64"
        else:
            return "MUL32"
    elif op == "/":
        if kind == "FLOAT":
            return "FDIV32"
        elif kind == "DOUBLE":
            return "FDIV64"
        elif kind == "LONG":
            return "DIV64"
        else:
            return "DIV32"
    elif op == "==":
        return "COMPEQ"
    elif op == "<":
        return "LT"
    else:
        print("Not supported the operation yet", op)
        return "UNKNOWN"
        
    
if __name__ == '__main__':
    usage = "Usage: %prog [options] C-sources"
    p = OptionParser(usage)
    p.add_option("-m", "--module", dest="module", help="specify the module name to generate")
    opts, args = p.parse_args()

    if opts.module is not None:
        module_name = opts.module
    else:
        module_name, _ = os.path.splitext(os.path.basename(args[0]))

    module = ir_ast.Module(module_name)
    dest = module_name + ".ir"
        
    for arg in args:
        print("Parse {}".format(arg))
        src = arg
        name, ext = os.path.splitext(src)
        parse(src, module)

    print("Generate {}".format(dest))
    generate(dest, module)

