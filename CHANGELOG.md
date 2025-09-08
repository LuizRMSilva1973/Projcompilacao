# Changelog

Todas as mudanças notáveis deste projeto.

## [v1.0-aulas] - 2025-09-08
- Identidade didática para a disciplina de Compiladores (README atualizado).
- GUI integrada com menu “Aulas” e “Aulas (auto)”, atalhos Ctrl+1..0 / Ctrl+Alt+1..0.
- “Cenas” (salvar/carregar estado em JSON; opção de autoexecução com escolha de ações).
- Parser LL(1)/SLR(1)/LALR(1)/LR(1) com FIRST/FOLLOW, tabelas e itens LR(0).
- Autômatos: RE→NFA (Thompson)→DFA (subset)→minimização (Hopcroft), CLI e GUI.
- CFG/Grafos: split em blocos, CFG, vivacidade (IN/OUT), intervalos lineares.
- IR/TAC, Otimização (constant folding, DCE) e Codegen (assembly didático).
- Alocação de registradores (linear‑scan) com K e spill; simulador aceita regs t*/r*.
- Demos: pipeline_demo.py e cfg_demo.py.
- Labs organizados por aula em `labs/` e exercícios em `exercicios/`.

[v1.0-aulas]: https://github.com/LuizRMSilva1973/Projcompilacao/releases/tag/v1.0-aulas
