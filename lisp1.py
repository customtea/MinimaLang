# Revised Minimal Lisp interpreter (fixed parser/run behavior)
# This version's `loads` always returns a list of top-level expressions.
# Then `run` evaluates each in sequence and returns the last value.

import math
from typing import Any, List, Dict

Symbol = str
ListExpr = list
Number = (int, float)

def tokenize(src: str):
    src = src.replace('(', ' ( ').replace(')', ' ) ')
    return src.split()

def parse(tokens: List[str]):
    if len(tokens) == 0:
        raise SyntaxError("unexpected EOF while reading")
    token = tokens.pop(0)
    if token == '(':
        L = []
        while tokens[0] != ')':
            L.append(parse(tokens))
        tokens.pop(0)
        return L
    elif token == ')':
        raise SyntaxError("unexpected )")
    else:
        return atom(token)

def atom(token: str):
    if token.startswith('"') and token.endswith('"') and len(token) >= 2:
        return token[1:-1]
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)

def loads(src: str):
    tokens = tokenize(src)
    exprs = []
    while tokens:
        exprs.append(parse(tokens))
    return exprs  # always a list of expressions

class Env(dict):
    def __init__(self, params=(), args=(), outer=None):
        super().__init__()
        self.update(zip(params, args))
        self.outer = outer
    def find(self, var: Symbol):
        if var in self:
            return self
        elif self.outer is not None:
            return self.outer.find(var)
        else:
            return None

class Procedure:
    def __init__(self, params, body, env: Env):
        self.params = params
        self.body = body
        self.env = env
    def __call__(self, *args):
        local = Env(self.params, args, outer=self.env)
        return eval_lisp(self.body, local)
    def __repr__(self):
        return f"<Procedure params={self.params} body={self.body}>"

import operator as op
def _lisp_list(*args): return list(args)
PRIMITIVES = {
    '+': lambda *a: sum(a),
    '-': lambda a, *rest: a - sum(rest) if rest else -a,
    '*': lambda *a: math.prod(a),
    '/': lambda a, b: a / b,
    '>': lambda a,b: a > b,
    '<': lambda a,b: a < b,
    '>=': lambda a,b: a >= b,
    '<=': lambda a,b: a <= b,
    '=': lambda a,b: a == b,
    'eq?': lambda a,b: a is b or a == b,
    'cons': lambda a,b: [a] + (b if isinstance(b, list) else [b]),
    'car': lambda a: a[0],
    'cdr': lambda a: a[1:],
    'list': _lisp_list,
    'list?': lambda a: isinstance(a, list),
    'null?': lambda a: a == [],
    'print': lambda *a: print(*a),
}

def _apply(fn, args):
    if isinstance(fn, Procedure):
        return fn(*args)
    else:
        raise TypeError("Apply: not a function: " + repr(fn))

global_env = Env()
global_env.update(PRIMITIVES)
global_env.update({
    'true': True,
    'false': False,
    'nil': [],
})

def is_symbol(x): return isinstance(x, str)
def is_list(x): return isinstance(x, list)

def eval_lisp(x: Any, env: Env = None):
    if env is None:
        env = global_env
    if is_symbol(x):
        found = env.find(x)
        if found:
            return found[x]
        else:
            raise NameError(f"Undefined symbol: {x}")
    elif isinstance(x, Number) or isinstance(x, str) or x is True or x is False or x == []:
        return x
    assert is_list(x), "eval expects list or atom"
    if len(x) == 0:
        return []
    head = x[0]
    if head == 'quote':
        _, expr = x
        return expr
    elif head == 'if':
        _, test, conseq, alt = x
        result = eval_lisp(test, env)
        branch = conseq if result else alt
        return eval_lisp(branch, env)
    elif head == 'define' or head == 'set!':
        _, name, expr = x
        val = eval_lisp(expr, env)
        holder = env.find(name)
        if holder:
            holder[name] = val
        else:
            env[name] = val
        return name
    elif head == 'lambda':
        _, params, body = x
        return Procedure(params, body, env)
    elif head == 'begin':
        result = None
        for expr in x[1:]:
            result = eval_lisp(expr, env)
        return result
    else:
        proc = eval_lisp(head, env)
        args = [eval_lisp(exp, env) for exp in x[1:]]
        if callable(proc):
            return proc(*args)
        elif isinstance(proc, Procedure):
            return proc(*args)
        else:
            raise TypeError("Not a function: " + repr(proc))

def run(src: str):
    exprs = loads(src)
    last = None
    for ex in exprs:
        last = eval_lisp(ex, global_env)
    return last

# Demo
examples = [
    '(define fact (lambda (n) (if (= n 0) 1 (* n (fact (- n 1))))))',
    '(fact 5)',
    '(define map (lambda (f xs) (if (null? xs) (quote ()) (cons (f (car xs)) (map f (cdr xs))))))',
    '(map (lambda (x) (* x x)) (list 1 2 3 4))',
]

print("Running demo expressions...")
for e in examples:
    print("=>", e)
    val = run(e)
    print("   ->", val)

print("\nDemonstrating eval and apply:")
run('(define add (lambda (a b) (+ a b)))')
print(" eval: (eval (quote (add 2 3))) -> (using python-level call to eval_lisp) ->", eval_lisp(['add', 2, 3], global_env))
print(" apply: (apply add (list 10 20)) ->", _apply(global_env['add'], [10,20]))

__all__ = ['loads', 'run', 'global_env', 'Env', 'Procedure', 'eval_lisp']


