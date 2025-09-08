#!/usr/bin/env python3
"""
CLI para construção de NFA/DFA a partir de regex, teste de cadeias e export em SVG/DOT.

Exemplos:
  python3 automata_cli.py --regex "(a|b)*abb" --export-dfa-svg dfa.svg --export-nfa-dot nfa.dot --test abb
  python3 automata_cli.py --regex "a(b|c)+" --steps
"""
import argparse
import os
import importlib.util

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_PATH = os.path.join(BASE_DIR, 'labs', '11_automatos', 'automata_lib.py')
spec = importlib.util.spec_from_file_location('automata_lib', LIB_PATH)
if spec is None or spec.loader is None:
    raise ImportError('Não foi possível carregar automata_lib')
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)  # type: ignore


def main():
    ap = argparse.ArgumentParser(description='Automata CLI (regex → NFA/DFA/min)')
    ap.add_argument('--regex', required=True, help='Expressão regular (usa | . * + ? e parênteses)')
    ap.add_argument('--test', help='Cadeia a testar (sem espaço)')
    ap.add_argument('--export-nfa-svg')
    ap.add_argument('--export-dfa-svg')
    ap.add_argument('--export-nfa-dot')
    ap.add_argument('--export-dfa-dot')
    ap.add_argument('--steps', action='store_true', help='Imprime passos (Thompson, subset e minimização)')
    args = ap.parse_args()

    nfa, alpha, log = lib.regex_to_nfa_with_log(args.regex)
    dfa = lib.nfa_to_dfa(nfa, alpha)
    mdfa = lib.dfa_minimize(dfa, alpha)
    if args.steps:
        print('Passos (Thompson):')
        for l in log: print('-', l)
        print('Passos (subset):')
        for s in lib.nfa_to_dfa_steps(nfa, alpha): print('-', s)
        print('Passos (minimização):')
        steps, parts = lib.dfa_minimize_steps(mdfa, alpha)
        for l in steps: print('-', l)
    if args.test is not None:
        ok = lib.dfa_accepts(mdfa, list(args.test))
        print('Teste:', 'ACEITA' if ok else 'REJEITA')
    if args.export_nfa_svg:
        lib.automaton_to_svg_nfa(nfa, alpha, args.export_nfa_svg)
        print('NFA SVG salvo em:', args.export_nfa_svg)
    if args.export_dfa_svg:
        lib.automaton_to_svg_dfa(mdfa, alpha, args.export_dfa_svg)
        print('DFA SVG salvo em:', args.export_dfa_svg)
    if args.export_nfa_dot:
        lib.export_dot_nfa(nfa, args.export_nfa_dot)
        print('NFA DOT salvo em:', args.export_nfa_dot)
    if args.export_dfa_dot:
        lib.export_dot_dfa(mdfa, args.export_dfa_dot)
        print('DFA DOT salvo em:', args.export_dfa_dot)


if __name__ == '__main__':
    main()
