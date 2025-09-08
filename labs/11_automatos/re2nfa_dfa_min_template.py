#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Set, Dict, Tuple, List, FrozenSet


@dataclass(frozen=True)
class NFAState:
    id: int


@dataclass
class NFA:
    start: NFAState
    accepts: Set[NFAState]
    trans: Dict[Tuple[NFAState, str], Set[NFAState]]  # símbolo ou 'ε'


@dataclass(frozen=True)
class DFAState:
    id: int


@dataclass
class DFA:
    start: DFAState
    accepts: Set[DFAState]
    trans: Dict[Tuple[DFAState, str], DFAState]


def thompson_from_regex(regex: str) -> NFA:
    # TODO: implementar parser de regex e construção de Thompson
    raise NotImplementedError


def subset_construction(nfa: NFA, alphabet: Set[str]) -> DFA:
    # TODO: implementar conversão NFA -> DFA
    raise NotImplementedError


def hopcroft_minimize(dfa: DFA, alphabet: Set[str]) -> DFA:
    # TODO: implementar minimização de DFA
    raise NotImplementedError


def demo():
    print("Preencha as funções e rode exemplos.")


if __name__ == '__main__':
    demo()

