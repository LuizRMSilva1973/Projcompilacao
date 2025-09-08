#!/usr/bin/env python3
"""
Template de vivacidade (liveness) e intervalos a partir de código (TAC/Assembly simples).

Fornece:
- compute_use_def(block): USE/DEF por bloco básico.
- liveness(blocks, succ): IN/OUT por bloco via iteração backward.
- live_intervals_linear(code): intervalos por posição para temporários tN.

Integra com cfg_builder_template.py para gerar blocos e CFG a partir de código
com rótulos e saltos ('LABEL', 'JMP', 'CJMP').
"""
from typing import Dict, List, Set, Tuple
import re

Instr = Tuple[str, Tuple[str, ...]]


def is_temp(x: str) -> bool:
    return bool(re.match(r'^t\d+$', x))


def uses_defs(instr: Instr) -> Tuple[Set[str], Set[str]]:
    op, args = instr
    opu = op.upper()
    uses: Set[str] = set()
    defs: Set[str] = set()
    if opu == 'MOVI':
        # imm, dst
        if len(args) >= 2 and is_temp(args[1]):
            defs.add(args[1])
    elif opu == 'MOV':
        if len(args) >= 1 and is_temp(args[0]):
            uses.add(args[0])
        if len(args) >= 2 and is_temp(args[1]):
            defs.add(args[1])
    elif opu in ('ADD','MUL','CMPEQ'):
        if len(args) >= 1 and is_temp(args[0]): uses.add(args[0])
        if len(args) >= 2 and is_temp(args[1]): uses.add(args[1])
        if len(args) >= 3 and is_temp(args[2]): defs.add(args[2])
    elif opu == 'STORE':
        if len(args) >= 1 and is_temp(args[0]): uses.add(args[0])
    # LABEL/JMP/CJMP ignoram temps ou usam apenas arg1 em CJMP
    elif opu == 'CJMP':
        if len(args) >= 1 and is_temp(args[0]): uses.add(args[0])
    return uses, defs


def compute_use_def(block: List[Instr]) -> Tuple[Set[str], Set[str]]:
    use: Set[str] = set()
    defs: Set[str] = set()
    for instr in block:
        u, d = uses_defs(instr)
        # USE considera apenas variáveis ainda não definidas no bloco
        use |= (u - defs)
        defs |= d
    return use, defs


def liveness(blocks: Dict[str, List[Instr]], succ: Dict[str, Set[str]]):
    IN: Dict[str, Set[str]] = {b: set() for b in blocks}
    OUT: Dict[str, Set[str]] = {b: set() for b in blocks}
    USE: Dict[str, Set[str]] = {}
    DEF: Dict[str, Set[str]] = {}
    for b, instrs in blocks.items():
        USE[b], DEF[b] = compute_use_def(instrs)
    changed = True
    while changed:
        changed = False
        for b in blocks:
            old_in = IN[b].copy()
            old_out = OUT[b].copy()
            OUT[b] = set().union(*(IN[s] for s in succ.get(b, set()))) if succ.get(b) else set()
            IN[b] = USE[b] | (OUT[b] - DEF[b])
            if IN[b] != old_in or OUT[b] != old_out:
                changed = True
    return IN, OUT, USE, DEF


def live_intervals_linear(code: List[Instr]) -> Dict[str, Tuple[int,int]]:
    starts: Dict[str, int] = {}
    ends: Dict[str, int] = {}
    for i, ins in enumerate(code):
        u, d = uses_defs(ins)
        for x in u | d:
            starts.setdefault(x, i)
            ends[x] = i
    return {t: (starts[t], ends[t]) for t in starts}


def demo():
    from cfg_builder_template import split_basic_blocks, build_cfg
    code = [
        ('LABEL', ('L0',)),
        ('MOVI', ('1','t1')),
        ('MOVI', ('2','t2')),
        ('ADD', ('t1','t2','t3')),
        ('CJMP', ('t3','L1')),
        ('MUL', ('t3','t2','t4')),
        ('JMP', ('L2',)),
        ('LABEL', ('L1',)),
        ('ADD', ('t1','t1','t4')),
        ('LABEL', ('L2',)),
        ('MOV', ('t4','x')),
    ]
    blocks = split_basic_blocks(code)
    blocks_by_label = {b.label: b.instrs for b in blocks}
    cfg = build_cfg(blocks)
    IN, OUT, USE, DEF = liveness(blocks_by_label, cfg)
    print('CFG:')
    for k,v in cfg.items():
        print(' ', k, '->', sorted(v))
    print('USE/DEF:')
    for b in blocks_by_label:
        print(' ', b, 'USE=', sorted(USE[b]), 'DEF=', sorted(DEF[b]))
    print('IN/OUT:')
    for b in blocks_by_label:
        print(' ', b, 'IN=', sorted(IN[b]), 'OUT=', sorted(OUT[b]))
    print('Intervals (linear):', live_intervals_linear(code))


if __name__ == '__main__':
    demo()

