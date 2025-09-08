#!/usr/bin/env python3
from typing import Dict, Tuple, List


class Machine:
    def __init__(self):
        self.regs: Dict[str,int] = {}
        self.mem: Dict[str,int] = {}

    def get(self, x: str) -> int:
        if x.lstrip('-').isdigit():
            return int(x)
        return self.regs.get(x, self.mem.get(x, 0))

    def set(self, dst: str, val: int):
        # simples: nomes que começam com 't' ou 'r' são regs, outros memória
        if dst.startswith('t') or dst.startswith('r'):
            self.regs[dst] = val
        else:
            self.mem[dst] = val

    def run(self, prog: List[Tuple[str, Tuple[str,...]]]):
        pc = 0
        while pc < len(prog):
            op, args = prog[pc]
            if op == 'MOVI':
                imm, dst = args
                self.set(dst, int(imm))
            elif op == 'MOV':
                src, dst = args
                self.set(dst, self.get(src))
            elif op == 'ADD':
                a, b, dst = args
                self.set(dst, self.get(a) + self.get(b))
            elif op == 'MUL':
                a, b, dst = args
                self.set(dst, self.get(a) * self.get(b))
            elif op == 'CMPEQ':
                a, b, dst = args
                self.set(dst, 1 if self.get(a) == self.get(b) else 0)
            else:
                pass
            pc += 1


def demo():
    prog = [
        ('MOVI', ('1','t1')),
        ('MOVI', ('2','t2')),
        ('MUL', ('t1','t2','t3')),
        ('MOV', ('t3','x')),
    ]
    m = Machine()
    m.run(prog)
    print('regs:', m.regs)
    print('mem:', m.mem)


if __name__ == '__main__':
    demo()
