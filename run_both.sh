#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Uso: $0 <gramatica.txt> <entrada> [--auto-lex] [opções extras]" >&2
  echo "- <entrada>: se usar --auto-lex, pode ser sem espaços (ex.: (id+id)*id)" >&2
  echo "Ex.: $0 expr.txt \"id + id * id\"" >&2
  echo "Ex.: $0 expr.txt \"(id+id)*id\" --auto-lex --trace" >&2
}

if [[ ${#} -lt 2 ]]; then
  usage
  exit 1
fi

GRAMMAR="$1"
INPUT="$2"
shift 2 || true

exec python3 parsing_tester.py \
  --grammar "${GRAMMAR}" \
  --input "${INPUT}" \
  --method both "$@"

