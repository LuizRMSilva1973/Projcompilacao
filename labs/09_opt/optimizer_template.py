#!/usr/bin/env python3
from typing import List, Tuple


Tac = Tuple[str, Tuple[str, ...]]


def const_folding(tac: List[Tac]) -> List[Tac]:
    out: List[Tac] = []
    env = {}
    for op, args in tac:
        if op == 'loadI':
            imm, dst = args
            env[dst] = int(imm)
            out.append((op, args))
        elif op in ('add','mul'):
            a, b, dst = args
            av = env.get(a)
            bv = env.get(b)
            if av is not None and bv is not None:
                val = av + bv if op == 'add' else av * bv
                out.append(('loadI', (str(val), dst)))
                env[dst] = val
            else:
                out.append((op, args))
                env.pop(dst, None)
        else:
            out.append((op, args))
            if len(args) >= 1:
                env.pop(args[-1], None)
    return out


def dead_code_elim(tac: List[Tac], live_vars: List[str]) -> List[Tac]:
    live = set(live_vars)
    out: List[Tac] = []
    for op, args in reversed(tac):
        if op == 'store':
            src, dst = args
            if dst in live:
                out.append((op, args))
                live.add(src)
        elif op in ('loadI','load'):
            src, dst = args
            if dst in live:
                out.append((op, args))
                if op == 'load':
                    live.add(src)
        elif op in ('add','mul','cmpeq'):
            a, b, dst = args
            if dst in live:
                out.append((op, args))
                live.update([a,b])
        else:
            out.append((op, args))
    return list(reversed(out))


def demo():
    tac = [
        ('loadI', ('1','t1')),
        ('loadI', ('2','t2')),
        ('mul', ('t1','t2','t3')),
        ('loadI', ('0','t4')),
        ('add', ('t3','t4','t5')),
        ('store', ('t5','x')),
        ('store', ('t4','y')),  # morto
    ]
    tac2 = const_folding(tac)
    tac3 = dead_code_elim(tac2, live_vars=['x'])
    print('--- orig')
    for i in tac: print(i)
    print('--- fold')
    for i in tac2: print(i)
    print('--- dce')
    for i in tac3: print(i)


if __name__ == '__main__':
    demo()

