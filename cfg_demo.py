#!/usr/bin/env python3
"""
CFG + Liveness Demo: constrói blocos básicos e CFG a partir de TAC com LABEL/CJMP,
calcula USE/DEF por bloco e IN/OUT (vivacidade) e imprime resultados.
"""
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


def main():
    # Exemplo com fluxo e bifurcação condicional (CJMP)
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

    cfgb = _load('labs/12_grafos/cfg_builder_template.py', 'cfgb')
    live = _load('labs/12_grafos/liveness_template.py', 'live')

    blocks = cfgb.split_basic_blocks(code)
    blocks_by_label = {b.label: b.instrs for b in blocks}
    cfg = cfgb.build_cfg(blocks)

    IN, OUT, USE, DEF = live.liveness(blocks_by_label, cfg)

    print('--- Blocos ---')
    for b in blocks:
        print(f"{b.label}: {len(b.instrs)} instr")
        for op, args in b.instrs:
            print(' ', op, *args)

    print('\n--- CFG ---')
    for k, v in cfg.items():
        print(' ', k, '->', sorted(v))

    print('\n--- USE/DEF ---')
    for b in blocks_by_label:
        print(' ', b, 'USE=', sorted(USE[b]), 'DEF=', sorted(DEF[b]))

    print('\n--- IN/OUT ---')
    for b in blocks_by_label:
        print(' ', b, 'IN=', sorted(IN[b]), 'OUT=', sorted(OUT[b]))


if __name__ == '__main__':
    main()

