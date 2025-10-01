#!/usr/bin/env python3
"""
Exemplos rápidos de AST (Lab 06) e geração de TAC (Lab 07).

Como usar:
  python3 ast_tac_demo.py

Mostra:
  - AST de pequenos programinhas
  - Erros de tipos (se houver)
  - TAC gerado (loadI/load/add/mul/cmpeq/store)
"""
from typing import List
import os, importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _load(relpath: str, modname: str):
    path = os.path.join(BASE_DIR, relpath)
    spec = importlib.util.spec_from_file_location(modname, path)
    if not spec or not spec.loader:
        raise ImportError(f"Não foi possível carregar {relpath}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod

# Reutiliza os nós e typechecker do Lab 06
ast6 = _load('labs/06_semantica/ast_template.py', 'ast6')
Program = ast6.Program
Assign = ast6.Assign
Seq = ast6.Seq
IfThenElse = ast6.IfThenElse
BinOp = ast6.BinOp
Var = ast6.Var
Num = ast6.Num
TypeChecker = ast6.TypeChecker

# Reutiliza o gerador de TAC do Lab 07
tac7 = _load('labs/07_ast_ir/tac_template.py', 'tac7')
TacGen = tac7.TacGen


def pp_ast(node, indent: int = 0) -> List[str]:
    sp = '  ' * indent
    out: List[str] = []
    if isinstance(node, Program):
        out.append(f"{sp}Program")
        for st in node.body:
            out += pp_ast(st, indent + 1)
    elif isinstance(node, Seq):
        out.append(f"{sp}Seq")
        for st in node.items:
            out += pp_ast(st, indent + 1)
    elif isinstance(node, Assign):
        out.append(f"{sp}Assign {node.name}")
        out += pp_ast(node.expr, indent + 1)
    elif isinstance(node, IfThenElse):
        out.append(f"{sp}If")
        out += pp_ast(node.cond, indent + 1)
        out.append(f"{sp}Then:")
        out += pp_ast(node.then_branch, indent + 1)
        if node.else_branch is not None:
            out.append(f"{sp}Else:")
            out += pp_ast(node.else_branch, indent + 1)
    elif isinstance(node, BinOp):
        out.append(f"{sp}{node.op}")
        out += pp_ast(node.left, indent + 1)
        out += pp_ast(node.right, indent + 1)
    elif isinstance(node, Var):
        out.append(f"{sp}Var({node.name})")
    elif isinstance(node, Num):
        out.append(f"{sp}Num({node.value})")
    else:
        out.append(f"{sp}{node}")
    return out


def gen_tac_from_program(p: Program) -> TacGen:
    g = TacGen()
    for st in p.body:
        if isinstance(st, Assign):
            g.gen_assign(st.name, st.expr)
        elif isinstance(st, Seq):
            for it in st.items:
                if isinstance(it, Assign):
                    g.gen_assign(it.name, it.expr)
        # IfThenElse e controle de fluxo não são cobertos neste demo simples
    return g


def exemplo_1() -> Program:
    # x = 1; y = x + 2; z = y * 3
    return Program([
        Assign("x", Num(1)),
        Assign("y", BinOp("+", Var("x"), Num(2))),
        Assign("z", BinOp("*", Var("y"), Num(3))),
    ])


def exemplo_2() -> Program:
    # w = 10 * ( 2 + 3 )
    return Program([
        Assign("w", BinOp("*", Num(10), BinOp("+", Num(2), Num(3)))),
    ])


def exemplo_3_com_erro() -> Program:
    # x = 1; x = (x == 2)  # erro: muda tipo de int para bool
    return Program([
        Assign("x", Num(1)),
        Assign("x", BinOp("==", Var("x"), Num(2))),
    ])


def run_case(p: Program, titulo: str):
    print(f"\n=== {titulo} ===")
    print("-- AST --")
    print("\n".join(pp_ast(p)))
    tc = TypeChecker()
    errs = tc.check(p)
    if errs:
        print("-- Erros de tipo --")
        for e in errs:
            print("  -", e)
    else:
        print("-- Tipagem OK --")
    print("-- TAC --")
    g = gen_tac_from_program(p)
    g.dump()


def main():
    run_case(exemplo_1(), "Exemplo 1: atribuicoes e expressoes")
    run_case(exemplo_2(), "Exemplo 2: precedencia via AST")
    run_case(exemplo_3_com_erro(), "Exemplo 3: erro de tipos (int -> bool)")


if __name__ == "__main__":
    main()
