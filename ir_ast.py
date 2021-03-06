
class Module:

    __slots__ = ('name', 'boards', 'uniq_counter', 'variables')
    def __init__(self, name):
        self.name = name
        self.boards = []
        self.uniq_counter = 0
        self.variables = []
    
    def uniq_id(self):
        i = self.uniq_counter
        self.uniq_counter += 1
        return "{}_{}".format(self.name, i)

    def search_variable(self, name):
        for v in self.variables:
            if name == v.original:
                return v
        return None

class Board:
    
    __slots__ = ('name', 'kind', 'variables', 'module', 'slots', 'breakpoints')
    def __init__(self, module, name, kind):
        self.name = name
        self.kind = kind
        self.module = module
        self.variables = []
        self.slots = []
        self.breakpoints = []

    def uniq_id(self):
        i = self.module.uniq_counter
        self.module.uniq_counter += 1
        return "{}_{}".format(self.name, i)

    def search_variable(self, name):
        for v in self.variables:
            if name == v.original:
                return v
        return self.module.search_variable(name)

    def new_slot(self):
        slot = Slot(len(self.slots))
        self.slots.append(slot)
        return slot
    
class Variable:

    __slots__ = ('name', 'kind', 'variables', 'public', 'global_constant', 'method_param', 'original', 'method', 'private_method', 'volatile', 'member')
    def __init__(self, name, kind, public=False, global_constant=False, method_param=False, original=None, method=None, private_method=False, volatile=False, member=False):
        self.name = name
        self.kind = kind
        self.public = public
        self.global_constant = global_constant
        self.method_param = method_param
        if original is not None:
            self.original = original
        else:
            self.original = name
        self.method = method
        self.private_method = private_method
        self.volatile = volatile
        self.member = member

    def to_sexp(self):
        return "(VAR {} {} :public {} :global_constant {} :method_param {} :original {} :method {} :private_method {} :volatile {} :member {})".format(self.kind, self.name, self.conv_flag(self.public), self.conv_flag(self.global_constant), self.conv_flag(self.method_param), self.original, self.method, self.conv_flag(self.private_method), self.conv_flag(self.volatile), self.conv_flag(self.member))

    def conv_flag(self, f):
        if f == True:
            return "true"
        else:
            return "false"

class Constant:
    __slots__ = ('name', 'kind', 'value', 'original')
    def __init__(self, name, kind, value):
        self.name = name
        self.kind = kind
        self.value = value
        self.original = name

    def to_sexp(self):
        return "(CONSTANT {} {} {})".format(self.kind, self.name, self.value)

class Slot:
    __slots__ = ('id', 'items')
    def __init__(self, id):
        self.id = id
        self.items = []
    
    def to_sexp(self):
        str = "(SLOT {}".format(self.id)
        for item in self.items:
            str = str + " " + item.to_sexp()
        str += ")"
        return str

    def is_branch(self):
        for item in self.items:
            if item.is_branch():
                return True
        return False

    def append_item(self, item):
        self.items.append(item)
        if item.is_branch() == False:
            item.next_ids = [self.id+1]
    
class SlotItem:
    __slots__ = ('op', 'next_ids')
    def __init__(self, op, next_ids):
        self.op = op
        self.next_ids = next_ids
    
    def to_sexp(self):
        str = "({} {})".format(self.op, self.next_ids_str())
        return str

    def next_ids_str(self):
        str = ":next ("
        sep = ""
        for i in self.next_ids:
            str += "{}{}".format(sep, i)
            sep = " "
        str += ")"
        return str

    def is_branch(self):
        return False

class AssignSlotItem(SlotItem):
    __slots__ = ('lhs', 'rhs')
    def __init__(self, lhs, rhs):
        super().__init__("SET", [0])
        self.lhs = lhs
        self.rhs = rhs

    def to_sexp(self):
        str = "(SET {} (ASSIGN {}) {})".format(self.lhs.name, self.rhs.name, self.next_ids_str())
        return str

class ReturnSlotItem(SlotItem):
    __slots__ = ('v')
    def __init__(self, v):
        super().__init__("RETURN", [0])
        self.v = v

    def to_sexp(self):
        str = "(RETURN {} {})".format(self.v.name, self.next_ids_str())
        return str
    
    def is_branch(self):
        return True

class BinaryOpSlotItem(SlotItem):
    __slots__ = ('binary_op', 'next_ids', 'v0', 'v1', 'ret')
    def __init__(self, binary_op, next_ids, v0, v1, ret):
        super().__init__("SET", next_ids)
        self.binary_op = binary_op
        self.v0 = v0
        self.v1 = v1
        self.ret = ret
    
    def to_sexp(self):
        str = "({} {} ({} {} {}) {})".format(self.op, self.ret.name, self.binary_op, self.v0.name, self.v1.name, self.next_ids_str())
        return str

class JTSlotItem(SlotItem):
    
    __slots__ = ('cond')
    def __init__(self, cond):
        super().__init__("JT", [])
        self.cond = cond

    def to_sexp(self):
        str = "(JT {} {})".format(self.cond.name, self.next_ids_str())
        return str
    
    def is_branch(self):
        return True

class JPSlotItem(SlotItem):
    
    __slots__ = ('next_id')
    def __init__(self, next_id):
        super().__init__("JP", [next_id])

    def to_sexp(self):
        str = "(JP {})".format(self.next_ids_str())
        return str
    
    def is_branch(self):
        return True

class NopSlotItem(SlotItem):
    
    __slots__ = ('next_id')
    def __init__(self, next_id):
        super().__init__("JP", [next_id])

    def to_sexp(self):
        str = "(JP {})".format(self.next_ids_str())
        return str
    
class CallSlotItem(SlotItem):
    
    __slots__ = ('next_ids', 'name', 'args', 'ret')
    def __init__(self, next_ids, name, args, ret):
        super().__init__("SET", next_ids)
        self.name = name
        self.args = args
        self.ret = ret
    
    def to_sexp(self):
        args = "("
        src = ""
        for a in self.args:
            args += a.name + " "
            src += " " + a.name
        args += ")"
        
        str = "({} {} (CALL {} :no_wait false :name {} :args {}) {})".format(self.op, self.ret.name, src, self.name, args, self.next_ids_str())
        return str

class SelectSlotItem(SlotItem):
    
    __slots__ = ('next_ids', 'values', 'key')
    def __init__(self, next_ids, values, key):
        super().__init__("SELECT", next_ids)
        self.values = values
        self.key = key
    
    def patterns_str(self):
        str = ":patterns ("
        sep = ""
        for v in self.values:
            str += "{}{}".format(sep, v.name)
            sep = " "
        str += ")"
        return str
    
    def to_sexp(self):
        str = "({} {} :target {} {} {})".format(self.op, self.key.name, self.key.name, self.patterns_str(), self.next_ids_str())
        return str

    def is_branch(self):
        return True
