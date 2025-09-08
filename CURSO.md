# Plano de Curso — VisualAutomata/Compiladores

Este documento mapeia as aulas do curso aos recursos, exemplos e exercícios do repositório, com sugestões de prática guiada. O material cobre do introdutório (Aula 1) ao projeto integrado (Aula 13–14).

## Visão Geral
- Aulas 1–5: totalmente cobertas com `parsing_tester.py`, GUI e exercícios.
- Aulas 6–12: labs prontos com templates executáveis para AST, TAC, codegen, otimização, backend, autômatos e grafos.
- Aulas 13–14: roteiro de projeto integrado em `labs/13_projeto` e na GUI (aba “Projeto”).

## Aulas e Labs (mapeamento)

1) Introdução aos Compiladores
- Lab: `labs/01_intro/`
- Conteúdo: fundamentos, pipeline do compilador, ambiente de execução do projeto.
- Prática: rodar LL/SLR no `parsing_tester.py`, abrir GUI (`--gui`) e exportar SVGs.

2) Análise Léxica
- Lab: `labs/02_lexica/`
- Conteúdo: tokens, lexemas, regex e AFD (conceitual).
- Prática: implementar `lexer_template.py`; usar aba “Lexer” da GUI; opcional: `--auto-lex` no parser.

3) Análise Sintática — Conceitos e Gramáticas
- Lab: `labs/03_gramaticas/`
- Conteúdo: CFG, derivações, árvores, ambiguidades e fatoração.
- Prática: usar `template_gramatica.txt` e os arquivos de `exercicios/` (Ex. 3–5).

4) Parsing Descendente — LL(1)
- Lab: `labs/04_ll1/`
- Conteúdo: FIRST/FOLLOW, tabela preditiva, fatoração e eliminação de recursão à esquerda.
- Prática: `run_ll1.sh`, `--show-tables`, exercícios 3–4.

5) Parsing Ascendente — SLR/LALR/LR(1)
- Lab: `labs/05_slr1/`
- Conteúdo: itens LR(0)/LR(1), ACTION/GOTO, conflitos e precedência/associatividade.
- Prática: `run_slr1.sh`, `--show-items`, exercícios 2 e 5; GUI também suporta LALR(1) e LR(1).
- Ferramentas: o repositório adota implementações em Python; opcionalmente, proponha Bison/Yacc em sala para comparação.

6) Análise Semântica
- Lab: `labs/06_semantica/`
- Conteúdo: AST, tabela de símbolos, tipagem e verificação de tipos; reporte de erros.
- Prática: completar `ast_template.py`; usar aba “Semântica” (importar árvore do Parser e checar tipos).

7) Representações Intermediárias
- Lab: `labs/07_ast_ir/`
- Conteúdo: AST → TAC (código de 3 endereços) e listas de instruções.
- Prática: completar `tac_template.py`; enviar AST → IR pela GUI.

8) Geração de Código
- Lab: `labs/08_codegen/`
- Conteúdo: TAC → assembly didático; noções de alocação de registradores (atividade sugerida).
- Prática: completar `codegen_template.py`; simular no Lab 10; desafio: linear-scan simples para mapear temporários.

9) Otimização de Código
- Lab: `labs/09_opt/`
- Conteúdo: constant folding e dead code elimination (DCE) sobre TAC.
- Prática: completar `optimizer_template.py`; comparar antes/depois na GUI (aba “Otimização”).

10) Back-end e Geração Final
- Lab: `labs/10_backend/`
- Conteúdo: assembly simples e simulador; organização básica de execução.
- Prática: usar `asm_sim_template.py` para executar o código e inspecionar registradores/memória.

11) Autômatos e Linguagens Formais
- Lab: `labs/11_automatos/`
- Conteúdo: RE → NFA (Thompson) → DFA (subset) → minimização (Hopcroft); simulador e export.
- Prática: GUI (aba “Autômatos”) e `automata_cli.py` para testar e exportar NFA/DFA/DOT/SVG.

12) Grafos em Compiladores
- Lab: `labs/12_grafos/`
- Conteúdo: CFG a partir de TAC; blocos básicos e sucessores. Sugerido: análise de vivacidade/dependência.
- Prática: completar `cfg_builder_template.py`; opcional: adicionar data‑flow (liveness) como extensão.

13–14) Projeto Guiado de Compilador
- Lab: `labs/13_projeto/`
- Conteúdo: planejamento da mini‑linguagem, gramática e tokens; integração de todos os módulos.
- Prática: roteiro no README do lab + aba “Projeto” da GUI.

## Observações
- A GUI integra etapas: Parser → Semântica → IR/TAC → Otimização → Codegen → Simulador, além de Autômatos e CFG.
- Onde a ementa cita Lex/Flex/Yacc/Bison, este projeto oferece versões em Python de propósito didático, independentes de ferramentas externas. É possível propor atividades paralelas com essas ferramentas para comparação.

## Próximos Passos (sugestões)
- Incluir atividade guiada de alocação de registradores (linear‑scan) no Lab 08/10.
- Estender o Lab 12 com análise de vivacidade e grafo de dependência simples.
