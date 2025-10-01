#!/usr/bin/env bash
set -euo pipefail

echo "== 01_min (both) =="
python3 parsing_tester.py --grammar exemplos_simples/01_min.txt --input "id" --method both --trace

echo
echo "== 02_paren (both) =="
python3 parsing_tester.py --grammar exemplos_simples/02_paren.txt --input "( id )" --method both --trace

echo
echo "== 03_sum_ll1 (both) =="
python3 parsing_tester.py --grammar exemplos_simples/03_sum_ll1.txt --input "id + id * id" --method both --trace --show-tables

echo
echo "== 04_assign_slr (slr1) =="
python3 parsing_tester.py --grammar exemplos_simples/04_assign_slr.txt --input "id = id" --method slr1 --trace --show-tables --show-items

echo
echo "Pronto. Edite os arquivos em exemplos_simples/ e reexecute para testar variações."

