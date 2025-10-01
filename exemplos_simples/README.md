Exemplos simples de gramáticas e entradas para testar rapidamente o `parsing_tester.py`.

Como rodar rapidamente (LL, SLR e ambos):
- LL(1): `python3 parsing_tester.py --grammar <arquivo> --input "<tokens>" --method ll1 --trace --show-tables`
- SLR(1): `python3 parsing_tester.py --grammar <arquivo> --input "<tokens>" --method slr1 --trace --show-tables --show-items`
- Ambos: `python3 parsing_tester.py --grammar <arquivo> --input "<tokens>" --method both --trace`

Arquivos:
- 01_min.txt — gramática mínima: `S -> id`.
- 02_paren.txt — parênteses somente: `E -> ( E ) | id`.
- 03_sum_ll1.txt — soma e produto LL(1) fatorada.
- 04_assign_slr.txt — atribuição simples ideal para SLR(1).

Exemplos de execução:
- `python3 parsing_tester.py --grammar exemplos_simples/01_min.txt --input "id" --method both --trace`
- `python3 parsing_tester.py --grammar exemplos_simples/02_paren.txt --input "( id )" --method both --trace`
- `python3 parsing_tester.py --grammar exemplos_simples/03_sum_ll1.txt --input "id + id * id" --method both --trace --show-tables`
- `python3 parsing_tester.py --grammar exemplos_simples/04_assign_slr.txt --input "id = id" --method slr1 --trace --show-items`

