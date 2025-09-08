#!/usr/bin/env bash
set -euo pipefail

if [[ ${#} -lt 1 ]]; then
  echo "Uso: $0 --regex 'REGEX' [--test STR] [--export-nfa-svg nfa.svg] [--export-dfa-svg dfa.svg] [--export-nfa-dot nfa.dot] [--export-dfa-dot dfa.dot] [--steps]" >&2
  exit 1
fi

exec python3 automata_cli.py "$@"

