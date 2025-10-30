# Retry running the fixed minimal Lisp interpreter and tests.
import re
from typing import Any, Dict, List

Env = Dict[str, Any]

def tokenize(src: str) -> List[str]:
    return re.findall(r"\(|\)|'|[^\s()']+", src)

def parse(tokens: List[str]):
    if len(tokens) == 0:
        raise SyntaxError("unexpected EOF")
    token = tokens.pop(0)
    if token == '(':
        lst = []
        while tokens[0] != ')':
            lst.append(parse(tokens))
        tokens.pop(0)
        return lst
    elif token == "'":
        return ['quote', parse(tokens)]
    elif token == ')':
        raise SyntaxError("unexpected )")
    else:
        return atom(token)

def atom(token: str):
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token

def make_global_env() -> Env:
    env: Env = {}

    def prim_cons(a, b):
        if not isinstance(b, list):
            raise TypeError("cons second argument must be a list")
        return [a] + b

    def prim_car(a):
        return [] if not isinstance(a, list) or not a else a[0]

    def prim_cdr(a):
        return [] if not isinstance(a, list) or not a else a[1:]

    def prim_atom(a):
        is_atom = not isinstance(a, list) or a == []
        return env['T'] if is_atom else env['NIL']

    def prim_eq(a, b):
        return env['T'] if a == b else env['NIL']

    def prim_add(*args): return sum(args)
    def prim_sub(x, *rest):
        if not rest:
            return -x
        r = x
        for v in rest:
            r -= v
        return r
    def prim_mul(*args):
        r = 1
        for x in args:
            r *= x
        return r
    def prim_div(x, *rest):
        r = x
        for v in rest:
            r = r / v
        return r

    env.update({
        'cons': prim_cons,
        'car': prim_car,
        'cdr': prim_cdr,
        'atom': prim_atom,
        'eq': prim_eq,
        '+': prim_add,
        '-': prim_sub,
        '*': prim_mul,
        '/': prim_div,
        'T': True,
        'NIL': [],
    })
    return env

def eval_lisp(x, env: Env):
    if isinstance(x, str):
        return env.get(x, x)
    elif not isinstance(x, list):
        return x

    if len(x) == 0:
        return []

    op = x[0]

    if op == 'quote':
        return x[1]

    if op == 'atom':
        return env['atom'](eval_lisp(x[1], env))

    if op == 'eq':
        return env['eq'](eval_lisp(x[1], env), eval_lisp(x[2], env))

    if op in ('cons', 'car', 'cdr'):
        args = [eval_lisp(arg, env) for arg in x[1:]]
        return env[op](*args)

    if op == 'cond':
        for clause in x[1:]:
            test_val = eval_lisp(clause[0], env)
            if test_val != []:
                return eval_lisp(clause[1], env)
        return []

    if op == 'defun':
        _, name, params, body = x
        def fn(*args):
            local_env = env.copy()
            for k, v in zip(params, args):
                local_env[k] = v
            return eval_lisp(body, local_env)
        env[name] = fn
        return name

    if op == 'lambda':
        _, params, body = x
        def fn(*args):
            local_env = env.copy()
            for k, v in zip(params, args):
                local_env[k] = v
            return eval_lisp(body, local_env)
        return fn

    func = eval_lisp(op, env)
    args = [eval_lisp(arg, env) for arg in x[1:]]
    if callable(func):
        return func(*args)
    raise TypeError(f"{func} is not callable")

def lisp_to_str(v):
    if v == []: return 'NIL'
    if v is True: return 'T'
    if isinstance(v, list): return '(' + ' '.join(map(lisp_to_str, v)) + ')'
    return str(v)

def run(src: str, env: Env):
    toks = tokenize(src)
    ast = parse(toks)
    val = eval_lisp(ast, env)
    print(f"{src} => {lisp_to_str(val)}")

# run tests
env = make_global_env()
run("(eq 'a 'a)", env)
run("(eq 'a 'b)", env)
run("(atom 'a)", env)
run("(atom '(a b))", env)
run("(cond ((eq 'a 'b) 'no) ((atom 'a) 'yes))", env)
run("(defun fact (n) (cond ((eq n 0) 1) (T (* n (fact (- n 1))))))", env)
run("(fact 5)", env)
