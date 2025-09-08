# Lab 05 — Parsing Ascendente (SLR)

Objetivos
- Entender itens LR(0), ACTION/GOTO e conflitos shift/reduce.

Passos
- Itens e tabelas: `./run_slr1.sh exercicios/ex5_ambigua_antes.txt "id + id * id"` e depois `ex5_ambigua_prec.txt`.
- Dangling else: compare `exercicios/ex2_else_com.txt` vs `exercicios/ex2_else_sem.txt`.
- Caso SLR(1) aceito (subconjunto): `./run_slr1.sh exercicios/ex2_assign_only_slr.txt "id = id"`.

Desafios
- Explique, com base nos FOLLOWs, por que as reduções ocorrem nos lookaheads mostrados.
- Opcional (Bison/Yacc): escreva a mesma gramática num `.y`, adicione precedência/associatividade e compare as tabelas/relatórios de conflitos com o SLR do projeto.
