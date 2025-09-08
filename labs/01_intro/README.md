# Lab 01 — Introdução

Objetivos
- Configurar ambiente, executar exemplos e visualizar árvores de derivação.

Passos
- Rode: `python3 parsing_tester.py --grammar expr.txt --input "id + id * id" --method both --trace --show-tables`
- GUI: `python3 parsing_tester.py --grammar expr.txt --input "id + id * id" --method both --gui`
- SVG: `python3 parsing_tester.py --grammar expr.txt --input "id + id * id" --method both --export-svg saida.svg`
- Auto-lex: `python3 parsing_tester.py --grammar expr.txt --input "(id+id)*id" --method both --auto-lex --trace`

Perguntas
- Qual árvore é gerada (LL x SLR)? Há conflitos?
- O que `FIRST/FOLLOW` indicam para `expr.txt`?

