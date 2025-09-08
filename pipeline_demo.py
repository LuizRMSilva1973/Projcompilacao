#!/usr/bin/env python3
"""
Pipeline demo: TAC -> (opt) -> regalloc -> codegen -> simulate

Mostra o fluxo de geração de código do projeto usando os módulos dos labs.
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
    # Exemplo: x = 1 + 2 * 3
    tac = [
        ('loadI', ('1','t1')),
        ('loadI', ('2','t2')),
        ('loadI', ('3','t3')),
        ('mul', ('t2','t3','t4')),
        ('add', ('t1','t4','t5')),
        ('store', ('t5','x')),
    ]
    print('--- TAC (inicial) ---')
    for op, args in tac:
        print(op, *args)

    # Otimizações (folding + DCE)
    opt = _load('labs/09_opt/optimizer_template.py', 'opt')
    tac2 = opt.const_folding(tac)
    tac2 = opt.dead_code_elim(tac2, live_vars=['x'])
    print('\n--- TAC (otimizado) ---')
    for op, args in tac2:
        print(op, *args)

    # Alocação de registradores (linear-scan)
    regalloc = _load('labs/08_codegen/regalloc_linear.py', 'regalloc')
    mp = regalloc.allocate_registers(tac2, k=2)
    print('\n--- Regalloc (k=2) ---')
    print(mp)
    tac3 = regalloc.apply_mapping_to_tac(tac2, mp)

    # Codegen
    codegen = _load('labs/08_codegen/codegen_template.py', 'codegen')
    asm = codegen.codegen_from_tac(tac3)
    prog = [(a.op, a.args) for a in asm]
    print('\n--- Assembly ---')
    for op, args in prog:
        print(op, *args)

    # Simulador
    sim = _load('labs/10_backend/asm_sim_template.py', 'sim')
    m = sim.Machine()
    m.run(prog)
    print('\n--- Execução ---')
    print('regs:', m.regs)
    print('mem:', m.mem)


if __name__ == '__main__':
    main()

