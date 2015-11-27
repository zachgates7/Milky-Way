import sys
import getopt


# Debug Globals


global inputEnabled
global outputEnabled
inputEnabled = True
outputEnabled = True


# Shorthand


def _is(val, typ):
    if isinstance(val, typ):
        return True
    return False

def _either(val1, val2, typ):
    if _is(val1, typ) or _is(val2, type):
        return True
    return False

def _both(val1, val2, typ):
    if _is(val1, typ) and _is(val2, typ):
        return True
    return False

def _any(vals, typ):
    for i in vals:
        if not _is(i, typ):
            return False
    return True

def _of(vals, typs):
    retval = [any(_is(i, j) for j in typs) for i in vals]
    return all(retval)


# Synced Lists


class Empty(object):
    pass


class ParallelLists(object):

    def __init__(self, *args):
        """Initialize lists with names in N"""
        self.lists = {i: [] for i in list(args)}

    def append(self, *args, **kwargs):
        """Push args to the list named kwargs['sl']"""
        K = kwargs['sl']
        for k, v in self.lists.items():
            for N in args:
                if k == K:
                    self.lists[k].append(N)
                else:
                    self.lists[k].append(Empty())

    def merge(self):
        """Merge lists into a single list"""
        merged = []
        for m in zip(*self.lists.values()):
            m = [n for n in m if not _is(n, Empty)]
            if len(m) == 1:
                merged.append(m[0])
            else:
                return []
        return merged


# Language Base


class Base(object):

    def __init__(self, program=""):
        """Initialize program"""
        if inputEnabled:
            opts, args = getopt.getopt(sys.argv[1:], "i:")
            op = {opt: arg for opt, arg in opts}
            if op.get("-i"):
                self.input = op.get("-i").splitlines()
            else:
                self.input = []
        self.stack = self.tokenize(program)
        self.run_ops()

    def tokenize(self, program):
        """Separate functions from data in the stack"""
        temp_stack = list(program)
        skip = []
        stacks = ParallelLists("opcodes", "data")
        stacks.append("", 0, sl="data")
        op, dt = "", ""
        for i in range(len(temp_stack)):
            j = temp_stack[i]
            if i not in skip:
                if j in self.op2func.keys():
                    if op:
                        stacks.append(op, sl="opcodes")
                        op = j
                    if dt:
                        stacks.append(dt, sl="data")
                        dt = ""
                    if self.op2func.get(j):
                        stacks.append(op + j, sl="opcodes")
                        op = ""
                elif j.isdigit():
                    if dt.isdigit():
                        dt += j
                    else:
                        if dt:
                            stacks.append(dt, sl="data")
                            op = ""
                        dt = j
                elif j in self.validTypes.keys():
                    if dt:
                        stacks.append(dt, sl="data")
                        dt = ""
                    rng, dat = self.parse_type(temp_stack, i)
                    skip += rng
                    stacks.append(dat, sl="data")
                    op = ""
                else:
                    raise Exception()
        if dt:
            stacks.append(dt, sl="data")
        stack = stacks.merge()
        for i in range(len(stack)):
            j = stack[i]
            if _is(j, str):
                if j.isdigit():
                    stack[i] = int(j)
        return stack

    def parse_type(self, stack, index):
        """Distinguish between opcodes and data types"""
        to_find = self.validTypes.get(stack[index])
        opener = stack[index]
        skip_from = int(index)
        stack_next = stack[index:][::-1][:-1]
        data = stack[index]
        opn, cls = 1, 0
        while stack_next:
            index += 1
            n = stack_next.pop()
            data += n
            if n == to_find:
                cls += 1
                if opn == cls:
                    stack_next = 1
                    break
            elif n == opener:
                opn += 1
            else:
                pass
        if not stack_next:
            data = "Empty()"
            index = skip_from + 1
        return [range(skip_from, index + 1), eval(data)]

    def run_ops(self):
        """Evaluate the program"""
        i = 0
        while i < len(self.stack):
            n = self.stack[i]
            cmd = self.op2func.get(n) if _is(n, str) else 0
            if cmd:
                self.stack.pop(i)
                stack_next = self.stack[i:]
                self.stack = self.stack[:i]
                to_stack = getattr(self, cmd)()
                self.stack += to_stack if to_stack else []
                self.stack += stack_next
                i = 0
            else:
                i += 1

    # Helper Functions

    def from_top(self, N=1):
        """Pop N items from the stack"""
        retval = [self.stack.pop() for i in range(N)]
        retval.reverse()
        if len(retval) == 1:
            return retval[0]
        return retval

    def is_length(self, N=1):
        """Check if the stack has N or more items"""
        if len(self.stack) < N:
            return False
        return True


# Function Container


class Standard(Base):
    
    validTypes = {"(": ")", "[": "]", "{": "}", '"': '"'}
    op2func = {
        ";": "swap_top",
        "<": "rot_left",
        "≤": "rot_left_nth",
        ">": "rot_right",
        "≥": "rot_right_nth",
        "^": "pop_top",
        "|": "pop_nth",
        ":": "dup_top",
        "+": "add",
        "-": "subtract",
        "*": "multiply",
        "/": "divide",
        "a": "log_not",
        "b": "log_eqs",
        "c": "log_and",
        "d": "log_or",
        "e": "log_gthan",
        "f": "log_lthan",
        "g": "root",
        "h": "power",
        "i": "prime",
        "j": "absval",
        "k": "negabsval",
        "l": "scinot",
        "m": "dmod",
        "n": "modulo",
    }
    
    if inputEnabled:
        inputFuncs = {
            "'": "full_input",
            "_": "line_input",
        }
        op2func.update(inputFuncs)

    if outputEnabled:
        outputFuncs = {
            "!": "out_top",
            "#": "out_nth",
        }
        op2func.update(outputFuncs)

    def __init__(self, program=""):
        """Initialize parent class"""
        self.has_out = False
        Base.__init__(self, program)
        if outputEnabled:
            if not self.has_out:
                to_out = repr(self.stack.pop(0)).replace("'", '"')
                sys.stdout.write(to_out)
            sys.stdout.write('\n')

    # I/O Functions

    ## Input

    if inputEnabled:

        def full_input(self):
            """Push the full input to the stack: [a b] => [a b c]"""
            retval = '\n'.join(self.input)
            return [retval]

        def line_input(self):
            """Push the foremost line to the stack: [a b] => [a b c]"""
            retval = self.input.pop(0)
            return [retval]

    ## Output

    if outputEnabled:

        def out_top(self):
            """Output the TOS without pop-ing: [a b c] => [a b c]"""
            to_out = repr(self.stack[-1]).replace("'", '"')
            sys.stdout.write(to_out)
            self.has_out = True

        def out_nth(self):
            """Output the Nth stack item without pop-ing it where N is the TOS: [a b c 2] => [a b c]"""
            A = self.from_top()
            to_out = repr(self.stack[A]).replace("'", '"')
            sys.stdout.write(to_out)
            self.has_out = True

    # Stack-Modifying Functions

    ## Rotation

    def swap_top(self):
        """Swap the top two stack elements: [a b c] => [a c b]"""
        A, B = self.from_top(2)
        return [B, A]

    def rot_left(self):
        """Rotate the stack leftward: [a b c] => [b c a]"""
        new_stack = self.stack[1:] + self.stack[:1]
        self.stack = new_stack

    def rot_left_nth(self):
        """Rotate the top N stack elements leftward where N is the TOS: [a b c d 3] => [a c d b]"""
        N = self.from_top()
        if _is(N, int):
            sub_stack = self.from_top(N)
            if len(sub_stack) > 1:
                new_sub_stack = sub_stack[1:] + sub_stack[:1]
            elif len(sub_stack):
                new_sub_stack = sub_stack
            else:
                new_sub_stack = []
            return new_sub_stack

    def rot_right(self):
        """Rotate the stack rightward: [a b c] => [c a b]"""
        new_stack = self.stack[-1:] + self.stack[:-1]
        self.stack = new_stack

    def rot_right_nth(self):
        """Rotate the top N stack elements rightward where N is the TOS: [a b c d 3] => [a d b c]"""
        N = self.from_top()
        if _is(N, int):
            sub_stack = self.from_top(N)
            if len(sub_stack) > 1:
                new_sub_stack = sub_stack[-1:] + sub_stack[:-1]
            elif len(sub_stack):
                new_sub_stack = sub_stack
            else:
                new_sub_stack = []
            return new_sub_stack

    ## Removal

    def pop_top(self):
        """Pop the TOS without outputting it: [a b c] => [a b]"""
        self.stack.pop()

    def pop_nth(self):
        """Pop the Nth stack item without outputting it where N is the TOS: [a b c 1] => [a c]"""
        A = self.from_top()
        self.stack.pop(A)

    ## Amount Modifiers

    def dup_top(self):
        """Duplicate the TOS: [a b c] => [a b c c]"""
        A = self.from_top()
        return [A, A]

    # Logical Functions

    def log_not(self):
        """Perform logical not on the TOS: [0 0 1] => [0 0 0]"""
        A = self.from_top()
        retval = int(not bool(A))
        return [retval]

    def log_eqs(self):
        """Perform logical equals on the top two stack elements: [a a] => [1]"""
        A, B = self.from_top(2)
        retval = int(A == B)
        return [retval]

    def log_and(self):
        """Perform logical and on the top two stack elements: [0 1] => [0]"""
        A, B = self.from_top(2)
        retval = int(bool(A) and bool(B))
        return [retval]

    def log_or(self):
        """Perform logical or on the top two stack elements: [0 1] => [1]"""
        A, B = self.from_top(2)
        retval = int(bool(A) or bool(B))
        return [retval]

    def log_gthan(self):
        """Perform logical greater than on the top two stack elements: [1 2] => [0]"""
        A, B = self.from_top(2)
        retval = int(A > B)
        return [retval]

    def log_lthan(self):
        """Perform logical less than on the top two stack elements: [1 2] => [1]"""
        A, B = self.from_top(2)
        retval = int(A < B)
        return [retval]

    # Arithmetic Functions

    def add(self):
        """Push the sum the top two stack elements to the stack: [1 2] => [3]"""
        A, B = self.from_top(2)
        if type(A) == type(B):
            retval = A + B
        elif _either([A, B], str):
            retval = str(A) + str(B)
        elif _either([A, B], int):
            retval = round(A + B)
        elif _either([A, B], list):
            retval = list(A) + list(B)
        elif _both([A, B], tuple):
            retval = tuple(list(A) + list(B))
        else:
            return []
        return [retval]

    def subtract(self):
        """Push the difference of the top two stack elements to the stack: [5 2] => [3]"""
        A, B = self.from_top(2)
        if _both(A, B, str):
            if self.is_length(3):
                A, B, C = self.from_top(3)
                if not _is(A, int):
                    A = -1
            else:
                A = -1
                B, C = self.from_top(2)
            retval = B.replace(C, A)
        elif _both(A, B, int):
            retval = round(A - B)
        elif _either(A, B, float):
            retval = A - B
        elif _either(A, B, list):
            A = list(A)
            for i in B:
                while i in A:
                    A.remove(i)
            retval = A
        elif _both(A, B, tuple):
            A = list(A)
            for i in B:
                while i in A:
                    A.remove(i)
            retval = tuple(A)
        else:
            return []
        return [retval]

    def multiply(self):
        """Push the product of the top two stack elements to the stack: [5 5] => [25]"""
        A, B = self.from_top(2)
        if _is(A, str) and _is(B, int):
            retval = A * B
        elif _both(A, B, int):
            retval = round(A * B)
        elif _either(A, B, float):
            retval = A * B
        else:
            return []
        return [retval]

    def divide(self):
        """Push the quotient of the top two stack elements to the stack: [25 5] => [5]"""
        A, B = self.from_top(2)
        if _both(A, B, str):
            retval = A.count(B)
        elif _both(A, B, int):
            retval = round(A / B)
        elif _either(A, B, float):
            retval = A / B
        elif _is(A, list) or _is(A, tuple):
            retval = int(B in A)
        else:
            return []
        return [retval]

    # Loose Integer Functions

    def root(self):
        """Push the Nth root of the top stack element (default to 2) to the stack: [25] => [5]"""
        retval = []
        if self.is_length(2):
            A, B = self.from_top(2)
            if not _is(A, int) or not A:
                retval.append(A)
                A = 2
        else:
            A = 2
            B = self.from_top()
        k = 1 / A
        if _is(B, int):
            retval.append(round(B ** k))
        else:
            retval.append(B ** k)
        return retval

    def power(self):
        """Push the TOS to the power of second stack element to the stack: [3 3] => [27]"""
        A, B = self.from_top(2)
        if _of([A, B], [int, float]):
            retval = A ** B
        else:
            return []
        return [retval]

    def prime(self):
        """Push the primality of the TOS to the stack: [9] => [0]"""
        A = self.from_top()
        if _is(A, int):
            i = int(A) - 1
            while i > 1:
                if A % i == 0:
                    return [0]
                i -= 1
            return [1]
        else:
            return []

    def absval(self):
        """Push the absolute value of the TOS to the stack: [-3] => [3]"""
        A = self.from_top()
        if _of([A], [int, float]):
            retval = abs(A)
        else:
            return []
        return [retval]

    def negabsval(self):
        """Push the negative absolute value of the TOS to the stack: [3] => [-3]"""
        A = self.from_top()
        if _of([A], [int, float]):
            retval = -abs(A)
        else:
            return []
        return [retval]

    def scinot(self):
        """Push 10 to the Nth power to the stack: [5] => [100000]"""
        A = self.from_top()
        if _of([A], [int, float]):
            retval = 10 ** A
        else:
            return []
        return [retval]

    # Strict Integer Functions

    def dmod(self):
        """Push A/B and A%B to the stack where A and B are the top two stack elements: [10 5] => [2 0]"""
        A, B = self.from_top(2)
        if _both(A, B, int):
            retval = list(divmod(A, B))
        else:
            retval = []
        return retval

    def modulo(self):
        """Push A%B to the stack where A and B are the top two stack elements: [12 5] => [2]"""
        A, B = self.from_top(2)
        if _both(A, B, int):
            retval = A % B
        else:
            return []
        return [retval]
