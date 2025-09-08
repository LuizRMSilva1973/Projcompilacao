#!/usr/bin/env python3
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Asm:
    op: str
    args: Tuple[str, ...]


def codegen_from_tac(tac: List[Tuple[str, Tuple[str, ...]]]) -> List[Asm]:
    out: List[Asm] = []
    for op, args in tac:
        if op == 'loadI':
            imm, dst = args
            out.append(Asm('MOVI', (imm, dst)))
        elif op == 'load':
            src, dst = args
            out.append(Asm('MOV', (src, dst)))
        elif op == 'store':
            src, dst = args
            out.append(Asm('MOV', (src, dst)))
        elif op in ('add','mul','cmpeq'):
            a, b, dst = args
            m = {'add':'ADD','mul':'MUL','cmpeq':'CMPEQ'}[op]
            out.append(Asm(m, (a,b,dst)))
        else:
            out.append(Asm(';UNK', (op, *args)))
    return out


def demo():
    tac = [
        ('loadI', ('1','t1')),
        ('loadI', ('2','t2')),
        ('loadI', ('3','t3')),
        ('mul', ('t2','t3','t4')),
        ('add', ('t1','t4','t5')),
        ('store', ('t5','x')),
    ]
    asm = codegen_from_tac(tac)
    for a in asm:
        print(a.op, *a.args)


if __name__ == '__main__':
    demo()

