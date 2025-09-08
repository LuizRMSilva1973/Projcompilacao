#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Optional, Dict, List, Union


# Tipos simples
class Type:
    INT = "int"
    BOOL = "bool"


@dataclass
class Expr:
    pass


@dataclass
class Num(Expr):
    value: int


@dataclass
class Var(Expr):
    name: str


@dataclass
class BinOp(Expr):
    op: str  # '+', '*', '=='
    left: Expr
    right: Expr


@dataclass
class Stmt:
    pass


@dataclass
class Assign(Stmt):
    name: str
    expr: Expr


@dataclass
class Program:
    body: List[Stmt]


@dataclass
class IfThenElse(Stmt):
    cond: Expr
    then_branch: Stmt
    else_branch: Optional[Stmt] = None


@dataclass
class Seq(Stmt):
    items: List[Stmt]


class SymbolTable:
    def __init__(self):
        self.table: Dict[str, str] = {}

    def declare(self, name: str, ty: str):
        self.table[name] = ty

    def lookup(self, name: str) -> Optional[str]:
        return self.table.get(name)


class TypeChecker:
    def __init__(self, symtab: Optional[SymbolTable] = None, *, allow_arith_on_bool: bool = False, eq_requires_same_type: bool = True):
        self.symtab = symtab or SymbolTable()
        self.errors: List[str] = []
        self.allow_arith_on_bool = allow_arith_on_bool
        self.eq_requires_same_type = eq_requires_same_type

    def error(self, msg: str):
        self.errors.append(msg)

    def check_expr(self, e: Expr) -> Optional[str]:
        if isinstance(e, Num):
            return Type.INT
        if isinstance(e, Var):
            t = self.symtab.lookup(e.name)
            if t is None:
                self.error(f"Variável não declarada: {e.name}")
            return t
        if isinstance(e, BinOp):
            lt = self.check_expr(e.left)
            rt = self.check_expr(e.right)
            if e.op in {"+", "*"}:
                if lt == Type.INT and rt == Type.INT:
                    return Type.INT
                if self.allow_arith_on_bool and lt == Type.BOOL and rt == Type.BOOL:
                    return Type.BOOL
                self.error(f"Operação {e.op} requer int,int; obtido {lt},{rt}")
                return None
            if e.op == "==":
                if lt is not None and (lt == rt or not self.eq_requires_same_type):
                    return Type.BOOL
                self.error(f"Comparação == requer operandos do mesmo tipo; obtido {lt},{rt}")
                return None
            self.error(f"Operador desconhecido: {e.op}")
            return None
        self.error(f"Expressão desconhecida: {e}")
        return None

    def check_stmt(self, s: Stmt):
        if isinstance(s, Assign):
            et = self.check_expr(s.expr)
            if et is None:
                return
            # declaração implícita com tipo da primeira atribuição
            current = self.symtab.lookup(s.name)
            if current is None:
                self.symtab.declare(s.name, et)
            elif current != et:
                self.error(f"Atribuição incompatível: {s.name}: {current} := {et}")
        elif isinstance(s, IfThenElse):
            ct = self.check_expr(s.cond)
            if ct != Type.BOOL:
                self.error(f"Condição de if deve ser bool; obtido {ct}")
            self.check_stmt(s.then_branch)
            if s.else_branch is not None:
                self.check_stmt(s.else_branch)
        elif isinstance(s, Seq):
            for it in s.items:
                self.check_stmt(it)
        else:
            self.error(f"Statement desconhecido: {s}")

    def check(self, prog: Program) -> List[str]:
        for st in prog.body:
            self.check_stmt(st)
        return self.errors


def demo():
    p = Program([
        Assign("x", Num(1)),
        Assign("y", BinOp("+", Var("x"), Num(2))),
        Assign("x", BinOp("==", Var("y"), Num(3))),  # erro: muda tipo
    ])
    tc = TypeChecker()
    errs = tc.check(p)
    for e in errs:
        print("Erro:", e)


if __name__ == "__main__":
    demo()
