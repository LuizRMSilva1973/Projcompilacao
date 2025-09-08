# Lab 12 — Grafos em Compiladores

Objetivos
- Construir grafo de fluxo de controle (CFG) a partir de TAC.
- Identificar blocos básicos e sucessores.
- Extensão: análises de dados (vivacidade) e grafo de dependência simples.

Arquivos
- `cfg_builder_template.py`: decomposição em blocos e grafo.

Tarefas
- Dado TAC com rótulos e jumps, construa o grafo e exporte em formato simples (lista de adjacência).
- (Opcional) Detecte loops e ordens topológicas.

Extensão sugerida (análise de vivacidade e dependências)
- Vivacidade: compute USE/DEF por bloco, itere equações de dados (backward) e obtenha IN/OUT.
- Dependências: a partir de IN/OUT, construa um grafo de dependência de dados entre definições/uso de temporários.
- Discuta como essas análises influenciam otimizações (ex.: DCE) e alocação de registradores.

Uso (vivacidade pronta):
```
# Executa demo que monta CFG, calcula USE/DEF e IN/OUT, e imprime intervalos lineares
python3 labs/12_grafos/liveness_template.py
```
