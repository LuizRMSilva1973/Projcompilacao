#!/usr/bin/env python3
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Instr:
    op: str
    args: Tuple[str, ...]


class TacGen:
    def __init__(self):
        self.code: List[Instr] = []
        self.tmp = 0

    def newtmp(self) -> str:
        self.tmp += 1
        return f"t{self.tmp}"

    # Exemplos de nós esperados: Num, Var, BinOp, Assign (reutilize os do Lab 06 ou crie mínimos)
    def emit(self, op: str, *args: str) -> str:
        self.code.append(Instr(op, tuple(args)))
        return args[-1] if args else ""

    def gen_expr(self, e) -> str:
        # Duck typing com base em atributos esperados do Lab 06
        if hasattr(e, 'value') and not hasattr(e, 'op'):
            t = self.newtmp()
            self.emit("loadI", str(e.value), t)
            return t
        if hasattr(e, 'name') and not hasattr(e, 'op'):
            t = self.newtmp()
            self.emit("load", e.name, t)
            return t
        if hasattr(e, 'op') and hasattr(e, 'left') and hasattr(e, 'right'):
            a = self.gen_expr(e.left)
            b = self.gen_expr(e.right)
            t = self.newtmp()
            op = {"+": "add", "*": "mul", "==": "cmpeq"}.get(getattr(e, 'op'), getattr(e, 'op'))
            self.emit(op, a, b, t)
            return t
        raise NotImplementedError(e)

    def gen_assign(self, name: str, e) -> None:
        t = self.gen_expr(e)
        self.emit("store", t, name)

    def dump(self) -> None:
        for i in self.code:
            print(i.op, *i.args)


def demo():
    # Exemplo mínimo independente
    class Num:  # shadow simples
        def __init__(self, v): self.value=v
    class Var:
        def __init__(self, n): self.name=n
    class BinOp:
        def __init__(self, op,l,r): self.op=op; self.left=l; self.right=r

    g = TacGen()
    g.gen_assign("x", BinOp("+", Num(1), BinOp("*", Num(2), Num(3))))
    g.dump()


if __name__ == "__main__":
    demo()
