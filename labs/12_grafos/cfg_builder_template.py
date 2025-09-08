#!/usr/bin/env python3
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple


@dataclass
class Block:
    label: str
    instrs: List[Tuple[str, Tuple[str,...]]]


def split_basic_blocks(code: List[Tuple[str, Tuple[str,...]]]) -> List[Block]:
    # Espera instruções com pseudo-op 'LABEL', 'JMP', 'CJMP'
    leaders: Set[int] = {0}
    labels_to_idx: Dict[str, int] = {}
    for i, (op, args) in enumerate(code):
        if op == 'LABEL':
            labels_to_idx[args[0]] = i
            leaders.add(i)
        elif op in ('JMP','CJMP') and i+1 < len(code):
            leaders.add(i+1)
    starts = sorted(leaders)
    blocks: List[Block] = []
    for j, s in enumerate(starts):
        e = starts[j+1] if j+1 < len(starts) else len(code)
        label = None
        if code[s][0] == 'LABEL':
            label = code[s][1][0]
            s = s+1
        blocks.append(Block(label or f"B{j}", code[s:e]))
    return blocks


def build_cfg(blocks: List[Block]) -> Dict[str, Set[str]]:
    succ: Dict[str, Set[str]] = {b.label: set() for b in blocks}
    label_to_block = {b.label: b for b in blocks}
    # Mapear labels em código
    # Simplificação: se termina com JMP L, adiciona aresta; se CJMP _, adiciona aresta condicional + fallthrough
    for i, b in enumerate(blocks):
        if not b.instrs:
            if i+1 < len(blocks):
                succ[b.label].add(blocks[i+1].label)
            continue
        last = b.instrs[-1]
        if last[0] == 'JMP':
            succ[b.label].add(last[1][0])
        elif last[0] == 'CJMP':
            succ[b.label].add(last[1][1])  # destino
            if i+1 < len(blocks):
                succ[b.label].add(blocks[i+1].label)
        else:
            if i+1 < len(blocks):
                succ[b.label].add(blocks[i+1].label)
    return succ


def demo():
    code = [
        ('LABEL', ('L0',)),
        ('ADD', ('t1','t2','t3')),
        ('CJMP', ('t3','L1')),
        ('MUL', ('t4','t5','t6')),
        ('JMP', ('L2',)),
        ('LABEL', ('L1',)),
        ('ADD', ('t7','t8','t9')),
        ('LABEL', ('L2',)),
        ('MOV', ('t9','x')),
    ]
    blocks = split_basic_blocks(code)
    cfg = build_cfg(blocks)
    for b in blocks:
        print('Block', b.label, 'instrs:', len(b.instrs))
    print('CFG:')
    for k,v in cfg.items():
        print(' ', k, '->', sorted(v))


if __name__ == '__main__':
    demo()

