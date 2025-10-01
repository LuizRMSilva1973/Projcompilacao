# Changelog

Todas as mudanças notáveis deste projeto.

## [v1.1-exemplos-ast] - 2025-10-01
- Exemplos simples de gramáticas em `exemplos_simples/` e script `run_exemplos.sh`.
- GUI: submenu “Exemplos Simples” no menu Exemplos.
- IR/TAC (GUI): botão “Demo 3 casos” com visualização das 3 árvores AST e exportação individual/lote (SVG/JSON).
- Semântica (GUI): “Visualizar AST” e exportação da AST atual (SVG/JSON).
- Demo de linha de comando: `ast_tac_demo.py` (AST → typecheck → TAC) com saída clara.
- README atualizado com instruções de uso.

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
[v1.1-exemplos-ast]: https://github.com/LuizRMSilva1973/Projcompilacao/releases/tag/v1.1-exemplos-ast
