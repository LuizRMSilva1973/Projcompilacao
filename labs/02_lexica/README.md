# Lab 02 — Análise Léxica

Objetivos
- Definir tokens, padrões (regex) e construir um analisador léxico simples em Python.

Arquivos
- `lexer_template.py`: template de lexer sem dependências externas.

Tarefas
- Complete a lista `TOKEN_SPECS` com tokens da sua linguagem (palavras‑chave, operadores, `id`, `num`, espaço e comentários).
- Teste com entradas curtas: `python3 lexer_template.py --input "if x then y=3"`.
- Teste por arquivo: `python3 lexer_template.py --file exemplo.txt`.

Desafios
- Adicione reconhecimento de números inteiros e identificadores com sublinhado.
- Trate comentários de linha (`// ...`) e/ou bloco (`/* ... */`).

