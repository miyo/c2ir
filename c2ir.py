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
        else:
            print("Unknown ext: %s", decl)

    return module

def generate(dest_name, module):
    dest = open(dest_name, "w")
    module_name, _ = os.path.splitext(os.path.basename(dest_name))
    dest.write("(MODULE {}\n".format(module_name))

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
    if((len(names) == 1) and (names[0] == "int")):
        return "INT"
    else:
        return "UNKNOWN"

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

    slot_id = len(board.slots)
    slot = ir_ast.Slot(slot_id)
    slot.items.append(ir_ast.SlotItem("METHOD_EXIT", [slot_id+1]))
    board.slots.append(slot)
    
    slot_id = len(board.slots)
    slot = ir_ast.Slot(slot_id)
    slot.items.append(ir_ast.SlotItem("METHOD_ENTRY", [slot_id+1]))
    board.slots.append(slot)

    for item in body.block_items:
        parse_stmt(board, item)

    slot_id = len(board.slots)
    slot = ir_ast.Slot(slot_id)
    slot.items.append(ir_ast.SlotItem("JP", [0]))
    board.slots.append(slot)
    
    return board

def parse_stmt(board, item):
    if isinstance(item, c_ast.Return):
        parse_return(board, item)
    elif isinstance(item, c_ast.If):
        parse_if(board, item)
    elif isinstance(item, c_ast.For):
        parse_for(board, item)
    elif isinstance(item, c_ast.Compound):
        parse_compound(board, item)
    elif isinstance(item, c_ast.Decl):
        parse_decl(board, item)
    elif isinstance(item, c_ast.Switch):
        parse_switch(board, item)
    elif isinstance(item, c_ast.Case):
        parse_case(board, item)
    elif isinstance(item, c_ast.Default):
        parse_default(board, item)
    elif isinstance(item, c_ast.Assignment):
        parse_assignement(board, item)
    elif isinstance(item, c_ast.Break):
        parse_break(board, item)
    elif isinstance(item, c_ast.UnaryOp):
        parse_expr(board, item)
    else:
        print("Not supported stmt yet", item)

def parse_assignement(board, stmt):
    rhs = parse_expr(board, stmt.rvalue)
    lhs = parse_expr(board, stmt.lvalue)
    slot_id = len(board.slots)
    slot = ir_ast.Slot(slot_id)
    slot.items.append(ir_ast.AssignSlotItem(lhs, rhs))
    board.slots.append(slot)

def parse_break(board, stmt):
    pass
    
def parse_return(board, stmt):
    expr = parse_expr(board, stmt.expr)
    
    slot_id = len(board.slots)
    slot = ir_ast.Slot(slot_id)
    slot.items.append(ir_ast.ReturnSlotItem(expr))
    board.slots.append(slot)

def parse_if(board, stmt):
    cond = parse_expr(board, stmt.cond)
    parse_stmt(board, stmt.iftrue)
    parse_stmt(board, stmt.iftrue)

def parse_for(board, stmt):
    init = parse_stmt(board, stmt.init)
    cond = parse_expr(board, stmt.cond)
    update = parse_stmt(board, stmt.next)
    body = parse_stmt(board, stmt.stmt)
    
def parse_compound(board, stmt):
    for s in stmt.block_items:
        parse_stmt(board, s)
        
def parse_decl(board, stmt):
    original_name = stmt.name
    ir_name = original_name + "_" + board.uniq_id()
    v = ir_ast.Variable(ir_name, conv_type(stmt.type), method=board.name, original=original_name)
    if stmt.init is not None:
        # an assignment step to initialize is required
        expr = parse_expr(board, stmt.init)
    board.variables.append(v)
    
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
        return parse_unaryop(board, expr)
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
    slot = ir_ast.Slot(len(board.slots))
    board.slots.append(slot)
    item = ir_ast.BinaryOpSlotItem(conv_op(op, v.kind), [len(board.slots)], lhs, rhs, v)
    slot.items.append(item)
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
    slot = ir_ast.Slot(len(board.slots))
    board.slots.append(slot)
    item = ir_ast.BinaryOpSlotItem(ir_op, [len(board.slots)], v, c, v)
    slot.items.append(item)
    return v

def parse_id(board, expr):
    return board.search_variable(expr.name)

def parse_constant(board, expr):
    if expr.type == "int":
        kind = "INT"
    else:
        kind = "UNKNOWN"
    c = ir_ast.Constant("constant_{}".format(board.uniq_id()), kind, expr.value)
    board.variables.append(c)
    return c

def conv_op(op, kind):
    if op == "+":
        return "ADD"
    elif op == "-":
        return "SUB"
    elif op == "*":
        return "MUL32"
    elif op == "/":
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

