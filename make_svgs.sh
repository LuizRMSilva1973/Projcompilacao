#!/usr/bin/env bash
set -euo pipefail

mkdir -p exemplos_svg

# Exercício 1 (precedência/associatividade) — LL(1) e auto-lex
python3 parsing_tester.py --grammar expr.txt --input "id + id * id" --method ll1 --export-svg exemplos_svg/ex1_ll1.svg
python3 parsing_tester.py --grammar expr.txt --input "id+id*id" --method ll1 --auto-lex --export-svg exemplos_svg/ex1_autolex_ll1.svg

# Exercício 3 (fatoração) — LL(1)
python3 parsing_tester.py --grammar exercicios/ex3_fatoracao_depois.txt --input "id ( id , id )" --method ll1 --export-svg exemplos_svg/ex3_ll1.svg
python3 parsing_tester.py --grammar exercicios/ex3_fatoracao_depois.txt --input "id(id,id)" --method ll1 --auto-lex --export-svg exemplos_svg/ex3_ll1_autolex.svg

# Exercício 5 (ambiguidade com precedência) — SLR(1)
python3 parsing_tester.py --grammar exercicios/ex5_ambigua_prec.txt --input "id + id * id" --method slr1 --export-svg exemplos_svg/ex5_slr1.svg
python3 parsing_tester.py --grammar exercicios/ex5_ambigua_prec.txt --input "id+id*id" --method slr1 --auto-lex --export-svg exemplos_svg/ex5_slr1_autolex.svg

# Exercício 2 (dangling else) — LL(1) com/sem %Right else
python3 parsing_tester.py --grammar exercicios/ex2_else_com.txt --input "if id then id=id else id=id" --method ll1 --auto-lex --export-svg exemplos_svg/ex2_com_ll1.svg
python3 parsing_tester.py --grammar exercicios/ex2_else_sem.txt --input "if id then id=id else id=id" --method ll1 --auto-lex --export-svg exemplos_svg/ex2_sem_ll1.svg

# Exercício 2b — SLR(1) subconjunto de atribuição
python3 parsing_tester.py --grammar exercicios/ex2_assign_only_slr.txt --input "id = id" --method slr1 --export-svg exemplos_svg/ex2_assign_only_slr.svg

echo "SVGs gerados em exemplos_svg/"
