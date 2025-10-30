# Minimal Lisp interpreter in Python
# Supports primitives: quote, atom, eq, car, cdr, cons, cond, lambda, defun
# plus a few helpers for printing and examples.
# This code will parse strings into S-expressions, evaluate them in an environment,
# and show example evaluations at the end.
from icecream import ic

from typing import Any, List, Union, Dict, Tuple, Callable
import math
import sys

LispVal = Union[str, int, List['LispVal']]  # symbol, number, or list

# Parser: tokenize and parse into nested Python lists and atoms
def tokenize(s: str) -> List[str]:
    # add spaces around parentheses and quote shorthand
    s = s.replace("'", " ' ")
    s = s.replace('(', ' ( ').replace(')', ' ) ')
    return [tok for tok in s.split() if tok != ""]

def atomize(token: str) -> LispVal:
    # try integer
    try:
        return int(token)
    except ValueError:
        return token  # symbol

def parse(tokens: List[str]) -> LispVal:
    if len(tokens) == 0:
        raise SyntaxError("unexpected EOF while reading")
    token = tokens.pop(0)
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(parse(tokens))
            if len(tokens) == 0:
                raise SyntaxError("unexpected EOF while reading list")
        tokens.pop(0)  # pop ')'
        return L
    elif token == ')':
        raise SyntaxError("unexpected )")
    elif token == "'":
        # shorthand: 'x => (quote x)
        return ['quote', parse(tokens)]
    else:
        return atomize(token)

def parse_str(s: str) -> LispVal:
    return parse(tokenize(s))

# Printing Lisp values
def is_list(x: Any) -> bool:
    return isinstance(x, list)

def lisp_to_str(x: Any) -> str:
    if isinstance(x, list):
        return '(' + ' '.join(lisp_to_str(e) for e in x) + ')' if x else 'NIL'
    elif x is True:
        return 'T'
    elif x is False or x is None:
        return 'NIL'
    else:
        return str(x)

# Environment and closure representation
class Closure:
    def __init__(self, params, body, env):
        self.params = params  # list of symbols
        self.body = body      # single expression (for simplicity)
        self.env = env        # environment where defined (for closures)

    def __repr__(self):
        return f"<Closure params={self.params} body={self.body}>"

Env = Dict[str, Any]

def make_global_env() -> Env:
    env: Env = {}

    def prim_atom(args):
        if len(args) != 1:
            raise TypeError("atom expects 1 arg")
        a = args[0]
        # Lisp: NIL (空リスト) は atom と見なされることがあるが実装による。
        is_atom = (not isinstance(a, list)) or (isinstance(a, list) and a == [])
        return env['T'] if is_atom else env['NIL']

    def prim_eq(args):
        if len(args) != 2:
            raise TypeError("eq expects 2 args")
        a, b = args
        # eq はアトム比較を想定（リスト比較は false にする実装もある）
        # ここでは簡便のため Python の等価で判定するが、
        # 真偽は Lisp 値で返す。
        equal = False
        # If either is a list, decide behaviour: we'll treat structural equality as okay
        if isinstance(a, list) or isinstance(b, list):
            equal = (a == b)
        else:
            equal = (a == b)
        return env['T'] if equal else env['NIL']

    # 既存の cons/car/cdr や算術プリミティブはそのまま
    def prim_cons(args):
        if len(args) != 2:
            raise TypeError("cons expects 2 args")
        a, b = args
        if not isinstance(b, list):
            raise TypeError("cons second argument must be a list")
        return [a] + b

    def prim_car(args):
        if len(args) != 1:
            raise TypeError("car expects 1 arg")
        a = args[0]
        if not isinstance(a, list) or a == []:
            return []  # NIL
        return a[0]

    def prim_cdr(args):
        if len(args) != 1:
            raise TypeError("cdr expects 1 arg")
        a = args[0]
        if not isinstance(a, list) or a == []:
            return []  # NIL
        return a[1:]

    # Basic arithmetic (convenience)
    def prim_add(args):
        return sum(x for x in args)

    def prim_sub(args):
        if len(args) == 0:
            raise TypeError("'-' expects at least 1 arg")
        if len(args) == 1:
            return -args[0]
        res = args[0]
        for x in args[1:]:
            res -= x
        return res

    def prim_mul(args):
        res = 1
        for x in args:
            res *= x
        return res

    def prim_div(args):
        if len(args) < 2:
            raise TypeError("'/' expects at least 2 args")
        res = args[0]
        for x in args[1:]:
            res = res // x if isinstance(res, int) and isinstance(x, int) else res / x
        return res



    # register primitives and constants
    env.update({
        'atom': prim_atom,
        'eq': prim_eq,
        'cons': prim_cons,
        'car': prim_car,
        'cdr': prim_cdr,
        '+': prim_add,
        '-': prim_sub,
        '*': prim_mul,
        '/': prim_div,
        'T': True,
        'NIL': [],
    })
    return env


global_env = make_global_env()

# Evaluator: eval and apply
def is_symbol(x):
    return isinstance(x, str)

def eval_lisp(x: LispVal, env: Env) -> Any:
    print(x, type(x), env.get("fact"), end="")
    # Atoms: numbers or symbols
    if is_symbol(x):
        # symbol lookup
        print(" is SYMBOL", env.get(x, x))
        if x == 'NIL':
            return []  # treat NIL specially
        return env.get(x, x)  # if not in env, return symbol itself (self-evaluating fallback)
    print()
    if not isinstance(x, list):
        # number literal
        return x

    # Empty list is NIL
    if x == []:
        return []

    # Special forms
    head = x[0]
    if head == 'quote':
        # (quote <exp>) => return exp without evaluating
        _, exp = x
        return exp
    if head == 'atom':
        # (atom expr)
        _, e = x
        v = eval_lisp(e, env)
        return global_env['atom']([v])
    if head == 'eq':
        _, a, b = x
        va = eval_lisp(a, env)
        vb = eval_lisp(b, env)
        return global_env['eq']([va, vb])
    if head == 'cons':
        _, a, b = x
        va = eval_lisp(a, env)
        vb = eval_lisp(b, env)
        return global_env['cons']([va, vb])
    if head == 'car':
        _, a = x
        va = eval_lisp(a, env)
        return global_env['car']([va])
    if head == 'cdr':
        _, a = x
        va = eval_lisp(a, env)
        return global_env['cdr']([va])
    if head == 'cond':
        # (cond (test1 expr1) (test2 expr2) ... )
        for clause in x[1:]:
            if not isinstance(clause, list) or len(clause) != 2:
                raise SyntaxError("cond clauses must be (test expr) pairs")
            test, expr = clause
            tval = eval_lisp(test, env)
            # any non-NIL (empty list) is true
            if tval != []:
                return eval_lisp(expr, env)
        return []  # NIL if no clause matched
    if head == 'lambda':
        # (lambda (params...) body)
        _, params, body = x
        return Closure(params, body, env.copy())
    if head == 'defun':
        # (defun name (params...) body)
        _, name, params, body = x
        closure = Closure(params, body, env.copy())
        env[name] = closure
        return name  # return function name
    if head == 'setq':
        # (setq name expr)
        _, name, expr = x
        val = eval_lisp(expr, env)
        env[name] = val
        return name

    # Otherwise function application
    # Evaluate operator then arguments
    op = eval_lisp(head, env)
    args = [eval_lisp(arg, env) for arg in x[1:]]

    # If op is a Python primitive function
    if callable(op):
        return op(args)
    # If op is a Closure (user-defined function)
    if isinstance(op, Closure):
        if len(op.params) != len(args):
            raise TypeError("argument count mismatch")
        # create new env frame from closure env
        new_env = op.env.copy()
        # bind params to args
        for p, a in zip(op.params, args):
            new_env[p] = a
        # evaluate body in new env
        return eval_lisp(op.body, new_env)

    # If op is still a symbol not bound, treat as error
    raise NameError(f"unknown operator: {op}")

# Simple REPL function for demonstration (not interactive here)
def run_and_print(expr: str, env=None):
    if env is None:
        env = global_env
    parsed = parse_str(expr)
    val = eval_lisp(parsed, env)
    print(f"{expr}  =>  {lisp_to_str(val)}")
    return val

# --- Demonstrations ---
examples = [
    # "(quote a)",
    # "'(1 2 3)",
    # "(cons 1 '(2 3))",
    # "(car '(1 2 3))",
    # "(cdr '(1 2 3))",
    # "(atom 'a)",
    # "(atom '(a b))",
    # "(eq 'a 'a)",
    # "(eq 'a 'b)",
    # "(cond ((eq 'a 'b) 'no) ((atom 'a) 'yes))",
    # define and use a function: (defun add1 (x) (+ x 1))
    "(defun add1 (x) (+ x 1))",
    "(add1 10)",
    # # lambda usage
    # "((lambda (x) (+ x 2)) 5)",
    # simple recursive factorial (using defun and cond)
    "(defun fact (n) (cond ((eq n 0) 1) (T (* n (fact (- n 1))))))",
    "(fact 5)",
]

# create a fresh env copy for demos (so defs persist within the demo run)
demo_env = make_global_env()

for ex in examples:
    try:
        run_and_print(ex, demo_env)
    except Exception as e:
        print(f"{ex}  =>  Error: {e}")

## # show how to use parser+evaluator programmably
## print("\nParsed representation example:")
## parsed = parse_str("(cons 1 (quote (2 3)))")
## print(parsed)
## print("Evaluated:", lisp_to_str(eval_lisp(parsed, demo_env)))

# Provide a small helper REPL for local usage (commented out)
## repl_code = """
## # To use interactive REPL locally, uncomment and run:
## # env = make_global_env()
## # while True:
## #     try:
## #         s = input('lisp> ')
## #         if not s:
## #             continue
## #         val = eval_lisp(parse_str(s), env)
## #         print(lisp_to_str(val))
## #     except Exception as e:
## #         print('Error:', e)
## """
## print("\nInterpreter ready. See examples above for usage.")
