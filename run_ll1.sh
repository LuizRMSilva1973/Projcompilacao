#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Uso: $0 <gramatica.txt> \"tokens separados por espaço\" [opções extras]" >&2
  echo "Ex.: $0 expr.txt \"id + id * id\" --trace --show-tables" >&2
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
  --method ll1 \
  --trace --show-tables "$@"
