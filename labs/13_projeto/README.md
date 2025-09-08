# Lab 13–15 — Projeto Guiado de Compilador

Objetivo
- Integrar todos os estágios: Léxico → Sintaxe → Semântica → IR/TAC → Otimização → Codegen → Simulação.

Escopo sugerido
- Mini-linguagem com variáveis inteiras, expressões + e *, comparação ==, atribuição, if/then[/else] e sequência via ';'.

Passos
1) Defina tokens no `labs/02_lexica/lexer_template.py` (com ;, =, if/then/else, parênteses, id, num).
2) Crie a gramática em `minilang.txt` (use fatoração/sem LL(1) recursão à esquerda).
3) Use a GUI (Parser) para validar a sintaxe, exportar árvore em JSON e/ou SVG.
4) Conecte a AST (Lab 06) — adapte o parser para emitir AST (ou transfira da árvore de derivação manualmente).
5) Gere TAC (Lab 07), aplique otimizações (Lab 09) e gere assembly (Lab 08).
6) Execute no simulador (Lab 10) e valide resultados observáveis (memória final).

Entregáveis
- Gramática `.txt`, exemplos aceitos e rejeitados, relatório de decisões (FIRST/FOLLOW, conflitos e soluções).
- Código dos módulos (lexer, parser/AST, semântica, TAC, otimizador, codegen) e scripts.
- Demonstração na GUI (capturas ou SVGs/JSONs exportados).

