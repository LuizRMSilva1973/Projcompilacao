#!/usr/bin/env python3
"""
Alocação linear de registradores (linear-scan) para TAC simples.

Ideia:
- Calcula intervalos de vida de temporários t1, t2, ... com base em usos/definições.
- Atribui cada temporário a um registrador físico r0..r{K-1} quando possível;
  caso contrário, faz spill para memória (nome 'spill_tN').
- Em seguida, aplica a renomeação no TAC e deixa a geração de código mapear
  para assembly. A nossa máquina trata operandos de memória de forma transparente.

Observação: o simulador (Lab 10) foi ajustado para considerar nomes que começam
com 't' ou 'r' como registradores.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable
import re

Tac = Tuple[str, Tuple[str, ...]]


@dataclass
class Interval:
    temp: str
    start: int
    end: int


_TEMP_RE = re.compile(r"^t\d+$")


def _is_temp(x: str) -> bool:
    return bool(_TEMP_RE.match(x))


def _uses_defs_of(instr: Tac) -> Tuple[List[str], List[str]]:
    op, args = instr
    op_l = op.lower()
    uses: List[str] = []
    defs: List[str] = []
    if op_l == 'loadi':
        # imm, dst
        if len(args) >= 2 and _is_temp(args[1]):
            defs.append(args[1])
    elif op_l == 'load':
        # src, dst
        if len(args) >= 1 and _is_temp(args[0]):
            uses.append(args[0])
        if len(args) >= 2 and _is_temp(args[1]):
            defs.append(args[1])
    elif op_l in ('add', 'mul', 'cmpeq'):
        # a, b, dst
        if len(args) >= 1 and _is_temp(args[0]):
            uses.append(args[0])
        if len(args) >= 2 and _is_temp(args[1]):
            uses.append(args[1])
        if len(args) >= 3 and _is_temp(args[2]):
            defs.append(args[2])
    elif op_l == 'store':
        # src, dstVar
        if len(args) >= 1 and _is_temp(args[0]):
            uses.append(args[0])
    # demais ops (LABEL, JMP, CJMP...) ignorados aqui
    return uses, defs


def live_intervals(tac: List[Tac]) -> List[Interval]:
    starts: Dict[str, int] = {}
    ends: Dict[str, int] = {}
    for i, ins in enumerate(tac):
        uses, defs = _uses_defs_of(ins)
        for u in uses:
            if u not in starts:
                starts[u] = i
            ends[u] = i
        for d in defs:
            if d not in starts:
                starts[d] = i
            # se não houver uso posterior, pelo menos vive até esta definição
            ends.setdefault(d, i)
    intervals = [Interval(t, starts[t], ends.get(t, starts[t])) for t in starts]
    intervals.sort(key=lambda it: it.start)
    return intervals


def allocate_registers(tac: List[Tac], k: int = 3) -> Dict[str, str]:
    """Retorna um mapeamento temp->(rX|spill_tN) usando linear-scan com K registradores.
    """
    intervals = live_intervals(tac)
    regs = [f"r{i}" for i in range(k)]
    free: List[str] = regs.copy()
    # active: list of (end, temp, reg) sorted by end
    active: List[Tuple[int, str, str]] = []
    mapping: Dict[str, str] = {}

    def expire_old(start: int):
        nonlocal active, free
        still: List[Tuple[int, str, str]] = []
        for end, t, r in active:
            if end >= start:
                still.append((end, t, r))
            else:
                free.append(r)
        active = sorted(still)

    for it in intervals:
        expire_old(it.start)
        if free:
            r = free.pop()
            mapping[it.temp] = r
            active.append((it.end, it.temp, r))
            active.sort()
        else:
            # spill o com maior end (último)
            spill_end, spill_t, spill_r = active[-1]
            if spill_end > it.end:
                # troca: novo ocupa registrador, spill vai para memória
                mapping[it.temp] = spill_r
                mapping[spill_t] = f"spill_{spill_t}"
                active[-1] = (it.end, it.temp, spill_r)
                active.sort()
            else:
                # mantém spill do atual
                mapping[it.temp] = f"spill_{it.temp}"
    return mapping


def apply_mapping_to_tac(tac: List[Tac], mapping: Dict[str, str]) -> List[Tac]:
    def map_name(x: str) -> str:
        return mapping.get(x, x)
    out: List[Tac] = []
    for op, args in tac:
        out.append((op, tuple(map_name(a) for a in args)))
    return out


def demo():
    tac: List[Tac] = [
        ('loadI', ('1','t1')),
        ('loadI', ('2','t2')),
        ('loadI', ('3','t3')),
        ('mul', ('t2','t3','t4')),
        ('add', ('t1','t4','t5')),
        ('store', ('t5','x')),
    ]
    mapping = allocate_registers(tac, k=2)
    print('mapping:', mapping)
    mapped = apply_mapping_to_tac(tac, mapping)
    from codegen_template import codegen_from_tac
    asm = codegen_from_tac(mapped)
    for a in asm:
        print(a.op, *a.args)


if __name__ == '__main__':
    demo()

