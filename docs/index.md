# Compiladores — VisualAutomata

Projeto didático para a disciplina de Compiladores (Prof. Luiz Ricardo Mantovani da Silva).

- Repositório: https://github.com/LuizRMSilva1973/Projcompilacao
- Guia completo: veja o arquivo `README.md` no repositório.

## Comece aqui

- Requisitos: Python 3.8+ (Tkinter para GUI)
- GUI: `./run_gui.sh` (ou `python3 gui_app.py`)
- CLI (parsers): `python3 parsing_tester.py --grammar expr.txt --input "id + id * id" --method both --trace`
- CLI (autômatos): `python3 automata_cli.py --regex "(a|b)*abb" --steps --test abb`

## Aulas e materiais

- Plano de curso: [CURSO.md](../CURSO.md)
- Labs e templates: pasta [labs/](../labs)
- Exercícios de gramática: pasta [exercicios/](../exercicios)
- Exemplos SVG: pasta [exemplos_svg/](../exemplos_svg)

## Demos

- Pipeline: `python3 pipeline_demo.py`
- CFG/Liveness: `python3 cfg_demo.py`

## Observação

Para publicar esta página: habilite GitHub Pages nas configurações do repositório (Settings → Pages) selecionando `main` e diretório `/docs`.

