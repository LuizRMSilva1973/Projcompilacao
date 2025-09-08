# Lab 08 — Geração de Código

Objetivos
- Traduzir TAC para uma linguagem de máquina simples (toy assembly) e/ou stack machine.

Arquivos
- `codegen_template.py`: mapeia instruções TAC (add, mul, cmpeq, load/loadI, store) para assembly.

Tarefas
- Defina um formato de instrução (ex.: `MOV`, `ADD`, `MUL`, `CMP`, `STORE`).
- Gere código e simule manualmente a execução (ou use o simulador do Lab 10).

Extensão sugerida (alocação de registradores)
- Objetivo: mapear temporários `t1, t2, ...` para um conjunto finito de registradores (ex.: `r0..r3`) com spill em memória.
- Passos:
  - Construa intervalos de vida (liveness) lineares por ordem de emissão do TAC.
  - Faça uma alocação linear-scan simples: quando não houver registrador livre, derrame (spill) o temporário menos recente para memória.
  - Insira loads/stores ao entrar/sair de trechos que usam um temporário derramado.
  - Compare desempenho/clareza do assembly antes/depois da alocação.

Rodar o demo pronto (na raiz do repo):
```
python3 labs/08_codegen/regalloc_linear.py
```

Integração manual em Python:
```
python3 - << 'PY'
import importlib.util, os

base = os.path.dirname(__file__) if '__file__' in globals() else os.getcwd()
def load(rel, name):
    p = os.path.join(base, rel)
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

regalloc = load('labs/08_codegen/regalloc_linear.py', 'regalloc')
codegen = load('labs/08_codegen/codegen_template.py', 'codegen')

tac = [
    ('loadI', ('1','t1')),
    ('loadI', ('2','t2')),
    ('loadI', ('3','t3')),
    ('mul', ('t2','t3','t4')),
    ('add', ('t1','t4','t5')),
    ('store', ('t5','x')),
]
mp = regalloc.allocate_registers(tac, k=2)
asm = codegen.codegen_from_tac(regalloc.apply_mapping_to_tac(tac, mp))
for a in asm:
    print(a.op, *a.args)
PY
```

Observação: o simulador de assembly (Lab 10) reconhece nomes que começam com `t` ou `r` como registradores.
