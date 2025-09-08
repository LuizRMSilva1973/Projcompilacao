#!/usr/bin/env python3
"""
Parsing Tester: LL(1) (top-down) and SLR(1) (bottom-up)

Usage examples:

  python parsing_tester.py --grammar my_grammar.txt --input "id + id * id" --method both --trace

Grammar file format:

  # Lines starting with # are comments
  %Terminals: id + * ( )
  %NonTerminals: E E' T T' F
  %Start: E
  %Productions:
  E  -> T E'
  E' -> + T E' | ε
  T  -> F T'
  T' -> * F T' | ε
  F  -> ( E ) | id

Notes:
  - ε denotes epsilon (empty string). You may also write 'epsilon' or 'eps'.
  - Tokens in input must be space-separated. The end marker '$' is implicit.
  - The script builds and runs LL(1) and SLR(1) parsers, reports conflicts, and can show traces.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional, Iterable, FrozenSet
import json

EPS = "ε"
END = "$"


@dataclass
class ParseTreeNode:
    symbol: str
    children: List["ParseTreeNode"]


@dataclass
class ParseResult:
    ok: bool
    tree: Optional[ParseTreeNode] = None
    derivations: List[Tuple[str, List[str]]] = None  # list of (A, alpha)
    kind: str = ""  # "LL-leftmost" or "SLR-rightmost-rev"


class Grammar:
    def __init__(self):
        self.terminals: Set[str] = set()
        self.nonterminals: Set[str] = set()
        self.start_symbol: Optional[str] = None
        # productions[A] = list of RHS alternatives, each RHS is a list of symbols (term or nonterm)
        self.productions: Dict[str, List[List[str]]] = defaultdict(list)
        # precedence and associativity for terminals
        self.precedence: Dict[str, int] = {}  # higher number = higher precedence
        self.assoc: Dict[str, str] = {}       # 'left' | 'right' | 'nonassoc'

    @staticmethod
    def _norm_sym(sym: str) -> str:
        s = sym.strip()
        # Treat only explicit 'epsilon' or 'eps' (case-insensitive) as ε.
        # Do NOT treat single-letter 'e'/'E' as epsilon to avoid clashing with common nonterminals like 'E'.
        if s.lower() in {"epsilon", "eps"}:
            return EPS
        return s

    @classmethod
    def from_file(cls, path: str) -> "Grammar":
        g = cls()
        section = None
        prec_level = 0
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("%"):
                    # Support both forms: "%Key: ..." and "%Key ..."
                    if ":" in line and line.split(":", 1)[0] in {"%Terminals", "%NonTerminals", "%Start", "%Productions"}:
                        header, rest = line.split(":", 1)
                        section = header.strip()
                        payload = rest.strip()
                    else:
                        parts = line.split(None, 1)
                        section = parts[0]
                        payload = parts[1].strip() if len(parts) > 1 else ""

                    if section == "%Terminals":
                        for t in payload.split():
                            if t:
                                g.terminals.add(cls._norm_sym(t))
                    elif section == "%NonTerminals":
                        for nt in payload.split():
                            if nt:
                                g.nonterminals.add(cls._norm_sym(nt))
                    elif section == "%Start":
                        g.start_symbol = cls._norm_sym(payload)
                    elif section == "%Productions":
                        # Following lines until next section header are productions
                        section = "%Productions"
                    elif section in {"%Left", "%Right", "%NonAssoc"}:
                        # precedence/associativity declarations
                        prec_level += 1
                        assoc = {
                            "%Left": "left",
                            "%Right": "right",
                            "%NonAssoc": "nonassoc",
                        }[section]
                        for tok in payload.replace(":", " ").split():
                            t = cls._norm_sym(tok)
                            if not t:
                                continue
                            g.terminals.add(t)
                            g.precedence[t] = prec_level
                            g.assoc[t] = assoc
                    else:
                        raise ValueError(f"Unknown section: {section}")
                    continue

                if section == "%Productions":
                    # Format: A -> alpha | beta | ...
                    if "->" not in line:
                        raise ValueError(f"Invalid production line (missing '->'): {line}")
                    lhs, rhs = [p.strip() for p in line.split("->", 1)]
                    lhs = cls._norm_sym(lhs)
                    if not lhs:
                        raise ValueError(f"Invalid production LHS: {line}")
                    g.nonterminals.add(lhs)
                    alts = [alt.strip() for alt in rhs.split("|")]
                    for alt in alts:
                        if alt == EPS or alt == "":
                            g.productions[lhs].append([EPS])
                        else:
                            symbols = [cls._norm_sym(tok) for tok in alt.split()]
                            g.productions[lhs].append(symbols)
                            for s in symbols:
                                if s not in g.nonterminals and s != EPS:
                                    # assume terminals unless declared as nonterminal
                                    g.terminals.add(s)

        if not g.start_symbol:
            raise ValueError("Start symbol not defined (%Start section)")
        # Ensure END marker is tracked as a terminal in parsers
        return g

    def __str__(self) -> str:
        lines = []
        lines.append(f"NonTerminals: {' '.join(sorted(self.nonterminals))}")
        lines.append(f"Terminals: {' '.join(sorted(self.terminals))}")
        lines.append(f"Start: {self.start_symbol}")
        lines.append("Productions:")
        for A in sorted(self.productions.keys()):
            rhs = [" ".join(prod) if prod != [EPS] else EPS for prod in self.productions[A]]
            lines.append(f"  {A} -> {' | '.join(rhs)}")
        return "\n".join(lines)


class FirstFollow:
    def __init__(self, grammar: Grammar):
        self.g = grammar
        self.first: Dict[str, Set[str]] = {sym: set() for sym in self.g.nonterminals | self.g.terminals}
        self.follow: Dict[str, Set[str]] = {nt: set() for nt in self.g.nonterminals}
        for t in self.g.terminals:
            self.first[t].add(t)
        # Ensure END marker is recognized in FIRST when used in LR(1) lookaheads
        if END not in self.first:
            self.first[END] = {END}
        self.compute()

    def first_of_seq(self, seq: List[str]) -> Set[str]:
        if not seq or seq == [EPS]:
            return {EPS}
        out: Set[str] = set()
        for i, sym in enumerate(seq):
            out |= (self.first[sym] - {EPS})
            if EPS not in self.first[sym]:
                break
        else:
            out.add(EPS)
        return out

    def compute(self):
        # FIRST
        changed = True
        while changed:
            changed = False
            for A, alts in self.g.productions.items():
                for alpha in alts:
                    before = len(self.first[A])
                    seq_first = self.first_of_seq(alpha)
                    self.first[A] |= (seq_first - {EPS})
                    if EPS in seq_first:
                        self.first[A].add(EPS)
                    if len(self.first[A]) != before:
                        changed = True

        # FOLLOW
        if self.g.start_symbol is None:
            raise ValueError("Start symbol not set in grammar")
        self.follow[self.g.start_symbol].add(END)
        changed = True
        while changed:
            changed = False
            for A, alts in self.g.productions.items():
                for alpha in alts:
                    for i, B in enumerate(alpha):
                        if B not in self.g.nonterminals:
                            continue
                        beta = alpha[i + 1 :]
                        first_beta = self.first_of_seq(beta)
                        before = len(self.follow[B])
                        self.follow[B] |= (first_beta - {EPS})
                        if EPS in first_beta or not beta:
                            self.follow[B] |= self.follow[A]
                        if len(self.follow[B]) != before:
                            changed = True


class LL1Parser:
    def __init__(self, grammar: Grammar, ff: Optional[FirstFollow] = None):
        self.g = grammar
        self.ff = ff or FirstFollow(grammar)
        # Table: M[A][a] = production (list of symbols)
        self.table: Dict[str, Dict[str, List[str]]] = defaultdict(dict)
        self.conflicts: List[Tuple[str, str, List[str], List[str]]] = []
        self._build_table()

    def _build_table(self):
        for A, alts in self.g.productions.items():
            for alpha in alts:
                first_alpha = self.ff.first_of_seq(alpha)
                for a in (first_alpha - {EPS}):
                    prev = self.table[A].get(a)
                    if prev is not None and prev != alpha:
                        self.conflicts.append((A, a, prev, alpha))
                    self.table[A][a] = alpha
                if EPS in first_alpha:
                    for b in self.ff.follow[A]:
                        prev = self.table[A].get(b)
                        if prev is not None and prev != alpha:
                            self.conflicts.append((A, b, prev, alpha))
                        self.table[A][b] = alpha

    def parse(self, tokens: List[str], trace: bool = False) -> ParseResult:
        if self.g.start_symbol is None:
            raise ValueError("Start symbol not set")
        input_stream = deque(tokens + [END])
        stack: List[str] = [END, self.g.start_symbol]
        # stack of tree nodes aligned with symbols (END has None)
        root = ParseTreeNode(self.g.start_symbol, [])
        node_stack: List[Optional[ParseTreeNode]] = [None, root]
        ok = True
        steps: List[Tuple[str, List[str]]] = []

        def print_trace(action: str):
            if trace:
                print(f"STACK: {' '.join(stack):<30} INPUT: {' '.join(list(input_stream)):<30} ACTION: {action}")

        print_trace("init")
        while True:
            top = stack[-1]
            a = input_stream[0]
            if top == a == END:
                print_trace("accept")
                break
            if top in self.g.terminals or top == END:
                if top == a:
                    stack.pop()
                    node_stack.pop()  # matched terminal consumed
                    input_stream.popleft()
                    print_trace("match")
                else:
                    print_trace("error: terminal mismatch")
                    ok = False
                    break
            else:
                entry = self.table.get(top, {}).get(a)
                if entry is None:
                    print_trace("error: no table entry")
                    ok = False
                    break
                stack.pop()
                parent_node = node_stack.pop()
                if parent_node is None:
                    # should not happen; just guard
                    parent_node = ParseTreeNode(top, [])
                # expand production
                if entry == [EPS]:
                    # ε production -> add explicit epsilon child for clarity
                    eps_node = ParseTreeNode(EPS, [])
                    parent_node.children.append(eps_node)
                else:
                    # create children in order, push in reverse
                    child_nodes = [ParseTreeNode(sym, []) for sym in entry]
                    parent_node.children.extend(child_nodes)
                    for sym, n in zip(reversed(entry), reversed(child_nodes)):
                        stack.append(sym)
                        node_stack.append(n)
                print_trace(f"output {top} -> {' '.join(entry)}")
                # record derivation step (leftmost derivation for LL)
                steps.append((top, list(entry)))
        return ParseResult(ok=ok, tree=(root if ok else None), derivations=steps, kind="LL-leftmost")

    def print_table(self):
        print("LL(1) Parse Table (non-empty entries):")
        keys = sorted(self.g.terminals | {END})
        for A in sorted(self.g.nonterminals):
            for a in keys:
                if a in self.table.get(A, {}):
                    prod = self.table[A][a]
                    rhs = EPS if prod == [EPS] else " ".join(prod)
                    print(f"  M[{A}, {a}] = {rhs}")
        if self.conflicts:
            print("LL(1) Conflicts:")
            for A, a, p1, p2 in self.conflicts:
                r1 = EPS if p1 == [EPS] else " ".join(p1)
                r2 = EPS if p2 == [EPS] else " ".join(p2)
                print(f"  Conflict at ({A}, {a}): {{ {r1} }} vs {{ {r2} }}")


# SLR(1) machinery
Item = Tuple[str, Tuple[str, ...], int]  # (A, alpha, dot_pos) for production A->alpha


class SLR1Parser:
    def __init__(self, grammar: Grammar, ff: Optional[FirstFollow] = None):
        self.g = grammar
        self.ff = ff or FirstFollow(grammar)
        if self.g.start_symbol is None:
            raise ValueError("Start symbol not set")
        self.aug_start = self.g.start_symbol + "'" if (self.g.start_symbol + "'") not in self.g.nonterminals else self.g.start_symbol + "_S"  # avoid clash
        # Augment grammar: S' -> S
        self.nonterminals = set(self.g.nonterminals)
        self.nonterminals.add(self.aug_start)
        def norm(rhs: List[str]) -> Tuple[str, ...]:
            t = tuple(rhs)
            return tuple() if t == (EPS,) else t
        self.productions: Dict[str, List[Tuple[str, ...]]] = {A: [norm(rhs) for rhs in rhss] for A, rhss in self.g.productions.items()}
        self.productions[self.aug_start] = [(self.g.start_symbol,)]
        self.terminals = set(self.g.terminals)
        self.terminals.add(END)

        # Canonical collection
        self.states: List[FrozenSet[Item]] = []
        self.transitions: Dict[Tuple[int, str], int] = {}

        # ACTION and GOTO
        self.ACTION: Dict[Tuple[int, str], Tuple[str, Optional[int], Optional[Tuple[str, ...]]]] = {}
        # value: (act, next_state, prod) where act in {'s','r','acc'}
        self.GOTO: Dict[Tuple[int, str], int] = {}
        self.conflicts: List[str] = []

        self._build_lr0_automaton()
        self._build_slr1_tables()

    def _closure(self, items: Iterable[Item]) -> FrozenSet[Item]:
        closure: Set[Item] = set(items)
        changed = True
        while changed:
            changed = False
            new_items: Set[Item] = set()
            for (A, alpha, dot) in closure:
                if dot < len(alpha):
                    B = alpha[dot]
                    if B in self.nonterminals:
                        for prod in self.productions.get(B, []):
                            it = (B, prod, 0)
                            if it not in closure:
                                new_items.add(it)
            if new_items:
                closure |= new_items
                changed = True
        return frozenset(closure)

    def _goto(self, I: FrozenSet[Item], X: str) -> FrozenSet[Item]:
        J: Set[Item] = set()
        for (A, alpha, dot) in I:
            if dot < len(alpha) and alpha[dot] == X:
                J.add((A, alpha, dot + 1))
        if not J:
            return frozenset()
        return self._closure(J)

    def _build_lr0_automaton(self):
        start_item = (self.aug_start, (self.g.start_symbol,), 0)
        I0 = self._closure([start_item])
        self.states = [I0]
        worklist = deque([0])
        while worklist:
            i = worklist.popleft()
            I = self.states[i]
            symbols = set()
            for (A, alpha, dot) in I:
                if dot < len(alpha):
                    symbols.add(alpha[dot])
            for X in symbols:
                J = self._goto(I, X)
                if not J:
                    continue
                try:
                    j = self.states.index(J)
                except ValueError:
                    self.states.append(J)
                    j = len(self.states) - 1
                    worklist.append(j)
                self.transitions[(i, X)] = j

    def _build_slr1_tables(self):
        for i, I in enumerate(self.states):
            # Shifts
            for (A, alpha, dot) in I:
                if dot < len(alpha):
                    a = alpha[dot]
                    if a in self.terminals:
                        j = self.transitions.get((i, a))
                        if j is not None:
                            self._add_action(i, a, ("s", j, None))

            # Reductions and accept
            for (A, alpha, dot) in I:
                if dot == len(alpha):
                    if A == self.aug_start:
                        self._add_action(i, END, ("acc", None, None))
                    else:
                        for a in self.ff.follow[A]:
                            self._add_action(i, a, ("r", None, (A, alpha)))

            # GOTO
            for X in self.nonterminals:
                j = self.transitions.get((i, X))
                if j is not None:
                    self.GOTO[(i, X)] = j

    def _add_action(self, i: int, a: str, entry: Tuple[str, Optional[int], Optional[Tuple[str, ...]]]):
        key = (i, a)
        prev = self.ACTION.get(key)
        if prev is None or prev == entry:
            self.ACTION[key] = entry
            return

        # Try precedence/associativity resolution for conflicts
        resolved = self._resolve_conflict(a, prev, entry)
        if resolved is not None:
            self.ACTION[key] = resolved
            # record that a conflict occurred but was resolved
            self.conflicts.append(f"Resolved conflict at state {i}, {a}: {prev} vs {entry} -> {resolved}")
        else:
            # keep the previous (first) action, record unresolved conflict
            self.conflicts.append(f"Conflict at state {i}, symbol {a}: {prev} vs {entry}")
            # do not overwrite

    def _prod_prec(self, prod: Tuple[str, Tuple[str, ...]]) -> Optional[int]:
        A, alpha = prod
        # rightmost terminal precedence
        for sym in reversed(alpha):
            if sym in self.g.terminals:
                return self.g.precedence.get(sym)
        return None

    def _resolve_conflict(
        self,
        lookahead: str,
        prev: Tuple[str, Optional[int], Optional[Tuple[str, ...]]],
        new: Tuple[str, Optional[int], Optional[Tuple[str, ...]]],
    ) -> Optional[Tuple[str, Optional[int], Optional[Tuple[str, ...]]]]:
        # Only attempt to resolve shift/reduce or reduce/shift or reduce/reduce
        kinds = {prev[0], new[0]}
        la_prec = self.g.precedence.get(lookahead)
        la_assoc = self.g.assoc.get(lookahead)

        # Helper to choose shift or reduce by precedence
        def choose_sr(reduce_entry: Tuple[str, Optional[int], Optional[Tuple[str, ...]]], shift_entry: Tuple[str, Optional[int], Optional[Tuple[str, ...]]]):
            prod = reduce_entry[2]
            prod_prec = self._prod_prec(prod) if prod else None
            # If only one precedence exists, prefer the one that exists: token -> shift; production -> reduce
            if la_prec is not None and prod_prec is None:
                return shift_entry
            if la_prec is None and prod_prec is not None:
                return reduce_entry
            if la_prec is None and prod_prec is None:
                return None
            # both have precedence
            if la_prec > prod_prec:
                return shift_entry
            if la_prec < prod_prec:
                return reduce_entry
            # equal precedence -> associativity decides
            if la_assoc == "left":
                return reduce_entry
            if la_assoc == "right":
                return shift_entry
            if la_assoc == "nonassoc":
                return ("err", None, None)
            return None

        if kinds == {"s", "r"}:
            # identify which is which
            if prev[0] == "r":
                return choose_sr(prev, new)
            else:
                return choose_sr(new, prev)

        if kinds == {"r"}:  # reduce/reduce
            prod1 = prev[2]
            prod2 = new[2]
            p1 = self._prod_prec(prod1) if prod1 else None
            p2 = self._prod_prec(prod2) if prod2 else None
            if p1 is not None or p2 is not None:
                if (p1 or -1) > (p2 or -1):
                    return prev
                if (p2 or -1) > (p1 or -1):
                    return new
            # equal or none -> cannot resolve deterministically
            return None

        # Other conflict types not handled
        return None

    def parse(self, tokens: List[str], trace: bool = False) -> ParseResult:
        input_stream = deque(tokens + [END])
        states: List[int] = [0]
        symbols: List[str] = []
        # parallel stack of parse tree nodes aligned with symbols
        node_stack: List[ParseTreeNode] = []
        steps: List[Tuple[str, List[str]]] = []

        def print_trace(action: str):
            if trace:
                st = ",".join(str(s) for s in states)
                sy = " ".join(symbols)
                print(f"STATES: [{st:<20}] SYMS: {sy:<20} INPUT: {' '.join(list(input_stream)):<30} ACTION: {action}")

        print_trace("init")
        ok = True
        while True:
            s = states[-1]
            a = input_stream[0]
            act = self.ACTION.get((s, a))
            if act is None:
                print_trace("error: no ACTION")
                ok = False
                break
            kind, j, prod = act
            if kind == "s":
                symbols.append(a)
                node_stack.append(ParseTreeNode(a, []))
                states.append(j if j is not None else -1)
                input_stream.popleft()
                print_trace(f"shift {a} -> {states[-1]}")
            elif kind == "r":
                if prod is None:
                    print_trace("error: invalid reduce entry")
                    ok = False
                    break
                A, alpha = prod
                k = len(alpha) if list(alpha) != [EPS] else 0
                if k > 0:
                    # pop 2k symbols/states
                    # collect children before popping for tree
                    children = node_stack[-k:]
                    symbols[-k:] = []
                    states[-k:] = []
                    node_stack[-k:] = []
                else:
                    children = [ParseTreeNode(EPS, [])]
                t = states[-1]
                goto_t = self.GOTO.get((t, A))
                if goto_t is None:
                    print_trace("error: no GOTO after reduce")
                    ok = False
                    break
                # build subtree and push
                node = ParseTreeNode(A, children)
                symbols.append(A)
                node_stack.append(node)
                states.append(goto_t)
                rhs = EPS if list(alpha) == [EPS] else " ".join(alpha)
                print_trace(f"reduce {A} -> {rhs}; goto {goto_t}")
                # record reduction (rightmost derivation in reverse for LR)
                steps.append((A, list(alpha)))
            elif kind == "acc":
                print_trace("accept")
                break
            else:
                print_trace("error: unknown ACTION kind")
                ok = False
                break
        root = node_stack[-1] if (ok and node_stack) else None
        return ParseResult(ok=ok, tree=root, derivations=steps, kind="SLR-rightmost-rev")

    def print_tables(self, show_items: bool = False):
        print("SLR(1) ACTION table (non-empty):")
        for (i, a), (kind, j, prod) in sorted(self.ACTION.items()):
            if kind == "s":
                print(f"  ACTION[{i}, {a}] = shift {j}")
            elif kind == "r":
                A, alpha = prod if prod else ("?", ())
                rhs = EPS if list(alpha) == [EPS] else " ".join(alpha)
                print(f"  ACTION[{i}, {a}] = reduce {A} -> {rhs}")
            elif kind == "acc":
                print(f"  ACTION[{i}, {a}] = accept")
        print("SLR(1) GOTO table (non-empty):")
        for (i, A), j in sorted(self.GOTO.items()):
            print(f"  GOTO[{i}, {A}] = {j}")
        if self.conflicts:
            print("SLR(1) Conflicts:")
            for c in self.conflicts:
                print("  ", c)
        if show_items:
            print("States (items):")
            for idx, I in enumerate(self.states):
                print(f"State {idx}:")
                for (A, alpha, dot) in sorted(I):
                    rhs = list(alpha)
                    rhs.insert(dot, "·")
                    print(f"  {A} -> {' '.join(rhs) if rhs else '·'}")
                outs = sorted([(sym, self.transitions[(idx, sym)]) for (i, sym) in self.transitions.keys() if i == idx], key=lambda x: x[0])
                for sym, j in outs:
                    print(f"   on {sym} -> {j}")


# LR(1) and LALR(1)
LR1Item = Tuple[str, Tuple[str, ...], int, str]


class LR1Parser(SLR1Parser):
    def __init__(self, grammar: Grammar, ff: Optional[FirstFollow] = None, mode: str = "lr1"):
        self.g = grammar
        self.ff = ff or FirstFollow(grammar)
        if self.g.start_symbol is None:
            raise ValueError("Start symbol not set")
        self.aug_start = self.g.start_symbol + "'" if (self.g.start_symbol + "'") not in self.g.nonterminals else self.g.start_symbol + "_S"
        self.nonterminals = set(self.g.nonterminals)
        self.nonterminals.add(self.aug_start)
        def norm(rhs: List[str]) -> Tuple[str, ...]:
            t = tuple(rhs)
            return tuple() if t == (EPS,) else t
        self.productions: Dict[str, List[Tuple[str, ...]]] = {A: [norm(rhs) for rhs in rhss] for A, rhss in self.g.productions.items()}
        self.productions[self.aug_start] = [(self.g.start_symbol,)]
        self.terminals = set(self.g.terminals)
        self.terminals.add(END)
        self.mode = mode

        self.states: List[FrozenSet[LR1Item]] = []
        self.transitions: Dict[Tuple[int, str], int] = {}
        self.ACTION: Dict[Tuple[int, str], Tuple[str, Optional[int], Optional[Tuple[str, ...]]]] = {}
        self.GOTO: Dict[Tuple[int, str], int] = {}
        self.conflicts: List[str] = []

        self._build_lr1_automaton()
        self._build_lr1_tables()

    def _closure_lr1(self, items: Iterable[LR1Item]) -> FrozenSet[LR1Item]:
        I: Set[LR1Item] = set(items)
        changed = True
        while changed:
            changed = False
            new_items: Set[LR1Item] = set()
            for (A, alpha, dot, la) in I:
                if dot < len(alpha):
                    B = alpha[dot]
                    if B in self.nonterminals:
                        beta = list(alpha[dot + 1 :])
                        beta_la = beta + [la]
                        first_beta = self.ff.first_of_seq(beta_la)
                        lookaheads = (first_beta - {EPS})
                        for prod in self.productions.get(B, []):
                            for a in lookaheads:
                                it = (B, prod, 0, a)
                                if it not in I:
                                    new_items.add(it)
            if new_items:
                I |= new_items
                changed = True
        return frozenset(I)

    def _goto_lr1(self, I: FrozenSet[LR1Item], X: str) -> FrozenSet[LR1Item]:
        J: Set[LR1Item] = set()
        for (A, alpha, dot, la) in I:
            if dot < len(alpha) and alpha[dot] == X:
                J.add((A, alpha, dot + 1, la))
        if not J:
            return frozenset()
        return self._closure_lr1(J)

    def _build_lr1_automaton(self):
        start_item: LR1Item = (self.aug_start, (self.g.start_symbol,), 0, END)
        I0 = self._closure_lr1([start_item])
        states: List[FrozenSet[LR1Item]] = [I0]
        work = [0]
        trans: Dict[Tuple[int, str], int] = {}
        while work:
            i = work.pop()
            I = states[i]
            symbols = set()
            for (A, alpha, dot, la) in I:
                if dot < len(alpha):
                    symbols.add(alpha[dot])
            for X in symbols:
                J = self._goto_lr1(I, X)
                if not J:
                    continue
                try:
                    j = states.index(J)
                except ValueError:
                    states.append(J)
                    j = len(states) - 1
                    work.append(j)
                trans[(i, X)] = j
        if self.mode == "lalr1":
            core_index: Dict[FrozenSet[Tuple[str, Tuple[str, ...], int]], int] = {}
            merged: List[Set[LR1Item]] = []
            idx_map: List[int] = []
            for I in states:
                core = frozenset((A, alpha, dot) for (A, alpha, dot, la) in I)
                idx = core_index.get(core)
                if idx is None:
                    idx = len(merged)
                    core_index[core] = idx
                    merged.append(set())
                idx_map.append(idx)
                merged[idx].update(I)
            self.states = [frozenset(S) for S in merged]
            for (i, X), j in trans.items():
                self.transitions[(idx_map[i], X)] = idx_map[j]
        else:
            self.states = states
            self.transitions = trans

    def _build_lr1_tables(self):
        for i, I in enumerate(self.states):
            for (A, alpha, dot, la) in I:
                if dot < len(alpha):
                    a = alpha[dot]
                    if a in self.terminals:
                        j = self.transitions.get((i, a))
                        if j is not None:
                            self._add_action(i, a, ("s", j, None))
            for (A, alpha, dot, la) in I:
                if dot == len(alpha):
                    if A == self.aug_start:
                        self._add_action(i, END, ("acc", None, None))
                    else:
                        self._add_action(i, la, ("r", None, (A, alpha)))
            for X in self.nonterminals:
                j = self.transitions.get((i, X))
                if j is not None:
                    self.GOTO[(i, X)] = j

    def parse(self, tokens: List[str], trace: bool = False) -> ParseResult:
        input_stream = deque(tokens + [END])
        states: List[int] = [0]
        symbols: List[str] = []
        node_stack: List[ParseTreeNode] = []
        steps: List[Tuple[str, List[str]]] = []

        def print_trace(action: str):
            if trace:
                st = ",".join(str(s) for s in states)
                sy = " ".join(symbols)
                print(f"STATES: [{st:<20}] SYMS: {sy:<20} INPUT: {' '.join(list(input_stream)):<30} ACTION: {action}")

        ok = True
        print_trace("init")
        while True:
            s = states[-1]
            a = input_stream[0]
            act = self.ACTION.get((s, a))
            if act is None:
                print_trace("error: no ACTION")
                ok = False
                break
            kind, j, prod = act
            if kind == 's':
                symbols.append(a)
                node_stack.append(ParseTreeNode(a, []))
                states.append(j if j is not None else -1)
                input_stream.popleft()
                print_trace(f"shift {a} -> {states[-1]}")
            elif kind == 'r':
                if prod is None:
                    print_trace("error: invalid reduce entry")
                    ok = False
                    break
                A, alpha = prod
                k = len(alpha) if list(alpha) != [EPS] else 0
                if k > 0:
                    children = node_stack[-k:]
                    symbols[-k:] = []
                    states[-k:] = []
                    node_stack[-k:] = []
                else:
                    children = [ParseTreeNode(EPS, [])]
                t = states[-1]
                goto_t = self.GOTO.get((t, A))
                if goto_t is None:
                    print_trace("error: no GOTO after reduce")
                    ok = False
                    break
                node = ParseTreeNode(A, children)
                symbols.append(A)
                node_stack.append(node)
                states.append(goto_t)
                rhs = EPS if list(alpha) == [EPS] else " ".join(alpha)
                print_trace(f"reduce {A} -> {rhs}; goto {goto_t}")
                steps.append((A, list(alpha)))
            elif kind == 'acc':
                print_trace("accept")
                break
            else:
                print_trace("error: unknown ACTION kind")
                ok = False
                break
        root = node_stack[-1] if (ok and node_stack) else None
        kind = "LR(1)-rightmost-rev" if self.mode == "lr1" else "LALR(1)-rightmost-rev"
        return ParseResult(ok=ok, tree=root, derivations=steps, kind=kind)

    def print_tables(self, show_items: bool = False):
        label = "LR(1)" if self.mode == "lr1" else "LALR(1)"
        print(f"{label} ACTION table (non-empty):")
        for (i, a), (k, j, prod) in sorted(self.ACTION.items()):
            if k == 's':
                print(f"  ACTION[{i}, {a}] = shift {j}")
            elif k == 'r':
                A, alpha = prod if prod else ("?", ())
                rhs = EPS if list(alpha) == [EPS] else " ".join(alpha)
                print(f"  ACTION[{i}, {a}] = reduce {A} -> {rhs}")
            elif k == 'acc':
                print(f"  ACTION[{i}, {a}] = accept")
        print(f"{label} GOTO table (non-empty):")
        for (i, A), j in sorted(self.GOTO.items()):
            print(f"  GOTO[{i}, {A}] = {j}")
        if show_items:
            print("States (items):")
            for idx, I in enumerate(self.states):
                print(f"State {idx}:")
                for (A, alpha, dot, la) in sorted(I):
                    rhs = list(alpha)
                    rhs.insert(dot, '·')
                    print(f"  {A} -> {' '.join(rhs) if rhs else '·'}, {la}")


def _compute_layout(root: ParseTreeNode):
    """Compute simple tidy-ish layout for a tree. Returns (pos, leafs, depth, nodes).
    pos maps node id to (x_index, depth).
    """
    pos: Dict[int, Tuple[float, int]] = {}
    leaf_counter = [0]
    max_depth = [0]
    nodes: List[ParseTreeNode] = []

    def dfs(n: ParseTreeNode, depth: int) -> float:
        max_depth[0] = max(max_depth[0], depth)
        nodes.append(n)
        if not n.children:
            x = float(leaf_counter[0])
            leaf_counter[0] += 1
            pos[id(n)] = (x, depth)
            return x
        xs: List[float] = []
        for c in n.children:
            xs.append(dfs(c, depth + 1))
        x = sum(xs) / len(xs) if xs else float(leaf_counter[0])
        pos[id(n)] = (x, depth)
        return x

    dfs(root, 0)
    return pos, leaf_counter[0], max_depth[0], nodes


def export_tree_svg(root: ParseTreeNode, path: str):
    """Export the given parse tree as a simple SVG image to the given path."""
    pos, leafs, depth, nodes = _compute_layout(root)
    HSPACE = 90
    VSPACE = 80
    MARGIN = 40
    width = int(max(leafs * HSPACE + 2 * MARGIN, 400))
    height = int(max((depth + 1) * VSPACE + 2 * MARGIN, 300))

    def node_center(n: ParseTreeNode):
        x, y = pos[id(n)]
        return (x * HSPACE + MARGIN, y * VSPACE + MARGIN)

    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<style> .node{fill:#e8f0fe;stroke:#3b82f6} .edge{stroke:#555;stroke-width:1.2} .label{font:12px sans-serif;fill:#111} </style>",
        "<rect width='100%' height='100%' fill='white'/>",
    ]
    # edges
    for n in nodes:
        cx, cy = node_center(n)
        for ch in n.children:
            c2x, c2y = node_center(ch)
            parts.append(f"<line class='edge' x1='{cx}' y1='{cy+12}' x2='{c2x}' y2='{c2y-12}' />")
    # nodes
    for n in nodes:
        cx, cy = node_center(n)
        label = n.symbol
        w = max(36, 8 * len(label) + 12)
        h = 26
        parts.append(f"<rect class='node' x='{cx - w/2:.2f}' y='{cy - h/2:.2f}' width='{w:.2f}' height='{h:.2f}' rx='4' ry='4' />")
        parts.append(f"<text class='label' x='{cx:.2f}' y='{cy+4:.2f}' text-anchor='middle'>{label}</text>")
    parts.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))


def _tree_to_dict(node: ParseTreeNode) -> Dict[str, object]:
    return {
        "symbol": node.symbol,
        "children": [_tree_to_dict(ch) for ch in node.children],
    }


def export_tree_json(root: ParseTreeNode, path: str, derivations: Optional[List[Tuple[str, List[str]]]] = None, kind: str = ""):
    """Export parse tree and optional derivations to JSON."""
    data = {
        "kind": kind,
        "tree": _tree_to_dict(root),
    }
    if derivations is not None:
        data["derivations"] = [{"A": A, "rhs": (rhs if rhs != [EPS] else [EPS])} for (A, rhs) in derivations]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def show_trees_gui(trees: List[Tuple[str, ParseTreeNode, Optional[List[Tuple[str, List[str]]]], str]]):
    """Display one or more parse trees in a Tkinter GUI with tabs, zoom/pan and export.
    trees: list of tuples (title, tree_root, derivation_steps, kind)
    kind is a short label like 'LL-leftmost' or 'SLR-rightmost-rev'.
    """
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except Exception as e:
        # Provide a clearer, actionable message for environments without Tk
        msg = (
            "Tkinter (tk) não está disponível neste Python. "
            "Para usar a opção --gui, instale o pacote do Tk de seu sistema.\n\n"
            "Ubuntu/Debian: sudo apt-get install -y python3-tk\n"
            "Fedora: sudo dnf install python3-tkinter\n"
            "Arch/Manjaro: sudo pacman -S tk\n"
            "macOS (Homebrew): brew install tcl-tk e use o Python do Homebrew\n"
            "Windows: normalmente já vem com o instalador do Python."
        )
        raise RuntimeError(msg) from e
    # Try optional Pillow for PNG export fallback
    try:
        from PIL import Image
        PIL_AVAILABLE = True
    except Exception:
        PIL_AVAILABLE = False

    def draw_tree_on(canvas: "tk.Canvas", root: ParseTreeNode):
        pos, leafs, depth, nodes = _compute_layout(root)
        HSPACE = 90
        VSPACE = 80
        MARGIN = 40
        WIDTH = int(max(leafs * HSPACE + 2 * MARGIN, 400))
        HEIGHT = int(max((depth + 1) * VSPACE + 2 * MARGIN, 300))

        def node_center(n: ParseTreeNode) -> Tuple[float, float]:
            x, y = pos[id(n)]
            return (x * HSPACE + MARGIN, y * VSPACE + MARGIN)

        # draw edges first
        for n in nodes:
            cx, cy = node_center(n)
            for ch in n.children:
                c2x, c2y = node_center(ch)
                canvas.create_line(cx, cy + 12, c2x, c2y - 12, fill="#555")

        # draw nodes
        for n in nodes:
            cx, cy = node_center(n)
            label = n.symbol
            w = max(36, 8 * len(label) + 12)
            h = 26
            canvas.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, fill="#e8f0fe", outline="#3b82f6")
            canvas.create_text(cx, cy, text=label, font=("TkDefaultFont", 10))

        canvas.configure(scrollregion=(0, 0, WIDTH, HEIGHT))
        canvas.config(width=min(WIDTH, 900), height=min(HEIGHT, 600))
        return (WIDTH, HEIGHT, nodes, pos, HSPACE, VSPACE, MARGIN)

    def export_svg(path: str, root: ParseTreeNode):
        export_tree_svg(root, path)

    root_win = tk.Tk()
    root_win.title("Árvore(s) de Derivação")
    nb = ttk.Notebook(root_win)
    nb.pack(fill="both", expand=True)

    for title, tree, steps, kind in trees:
        frame = ttk.Frame(nb)
        nb.add(frame, text=title)

        # toolbar
        toolbar = ttk.Frame(frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
        zoom_label = ttk.Label(toolbar, text=f"{title} ({kind})")
        zoom_label.pack(side="left")
        canvas = tk.Canvas(frame, background="white")
        hbar = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
        vbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        canvas.grid(row=1, column=0, sticky="nsew")
        vbar.grid(row=1, column=1, sticky="ns")
        hbar.grid(row=2, column=0, sticky="ew")

        # derivation viewer
        deriv_frame = ttk.Frame(frame)
        deriv_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=6, pady=4)
        ttk.Label(deriv_frame, text="Derivação" if kind.startswith("LL") else "Reduções (direita em reverso)").pack(anchor="w")
        deriv_text = tk.Text(deriv_frame, height=8, wrap="word")
        deriv_scroll = ttk.Scrollbar(deriv_frame, orient="vertical", command=deriv_text.yview)
        deriv_text.configure(yscrollcommand=deriv_scroll.set)
        deriv_text.pack(side="left", fill="both", expand=True)
        deriv_scroll.pack(side="right", fill="y")
        if steps:
            for A, alpha in steps:
                rhs = "ε" if alpha == [EPS] or alpha == ["ε"] else " ".join(alpha)
                deriv_text.insert("end", f"{A} -> {rhs}\n")
        deriv_text.configure(state="disabled")

        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        # initial draw
        draw_tree_on(canvas, tree)

        # zoom and pan controls
        def zoom(factor: float):
            # scale around center of current view
            x0 = canvas.canvasx(canvas.winfo_width() / 2)
            y0 = canvas.canvasy(canvas.winfo_height() / 2)
            canvas.scale("all", x0, y0, factor, factor)
            # expand scroll region to include scaled content
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)

        def reset_view():
            canvas.scale("all", 0, 0, 1.0, 1.0)  # no-op for now; could redraw
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
            canvas.xview_moveto(0.0)
            canvas.yview_moveto(0.0)

        def on_wheel(event):
            direction = 0
            if hasattr(event, 'delta') and event.delta != 0:
                direction = 1 if event.delta > 0 else -1
            else:
                n = getattr(event, 'num', 0)
                if n in (4, 5):
                    direction = 1 if n == 4 else -1
            zoom(1.1 if direction > 0 else 0.9)

        def on_button1_press(event):
            canvas.scan_mark(event.x, event.y)

        def on_button1_move(event):
            canvas.scan_dragto(event.x, event.y, gain=1)

        canvas.bind("<MouseWheel>", on_wheel)
        canvas.bind("<Button-4>", on_wheel)  # Linux scroll up
        canvas.bind("<Button-5>", on_wheel)  # Linux scroll down
        canvas.bind("<ButtonPress-1>", on_button1_press)
        canvas.bind("<B1-Motion>", on_button1_move)

        def do_export_svg():
            path = filedialog.asksaveasfilename(title="Salvar SVG", defaultextension=".svg", filetypes=[["SVG", ".svg"]])
            if path:
                try:
                    export_svg(path, tree)
                    messagebox.showinfo("Exportar SVG", f"Arquivo salvo em:\n{path}")
                except Exception as e:
                    messagebox.showerror("Exportar SVG", f"Falha ao exportar SVG: {e}")

        def do_export_ps():
            path = filedialog.asksaveasfilename(title="Salvar PostScript", defaultextension=".ps", filetypes=[["PostScript", ".ps"]])
            if path:
                try:
                    canvas.postscript(file=path, colormode='color')
                    messagebox.showinfo("Exportar PS", f"Arquivo salvo em:\n{path}")
                except Exception as e:
                    messagebox.showerror("Exportar PS", f"Falha ao exportar PostScript: {e}")

        def do_export_png():
            if not PIL_AVAILABLE:
                messagebox.showwarning("Exportar PNG", "Pillow (PIL) não está disponível. Exporte SVG/PS ou instale Pillow para PNG.")
                return
            path = filedialog.asksaveasfilename(title="Salvar PNG", defaultextension=".png", filetypes=[["PNG", ".png"]])
            if path:
                try:
                    # Render via PostScript then convert
                    import io
                    ps = canvas.postscript(colormode='color')
                    img = Image.open(io.BytesIO(ps.encode('utf-8')))
                    img.save(path, 'PNG')
                    messagebox.showinfo("Exportar PNG", f"Arquivo salvo em:\n{path}")
                except Exception as e:
                    messagebox.showerror("Exportar PNG", f"Falha ao exportar PNG: {e}")

        # toolbar buttons
        ttk.Button(toolbar, text="Zoom +", command=lambda: zoom(1.1)).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Zoom -", command=lambda: zoom(0.9)).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Reset", command=reset_view).pack(side="right", padx=6)
        # export derivations (TXT/JSON)
        def do_export_deriv_txt():
            if not steps:
                messagebox.showinfo("Exportar Derivação", "Não há derivações para exportar.")
                return
            path = filedialog.asksaveasfilename(title="Salvar Derivação (TXT)", defaultextension=".txt", filetypes=[["Texto", ".txt"]])
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(f"# {title} ({kind})\n")
                        for A, alpha in steps:
                            rhs = "ε" if alpha == [EPS] or alpha == ["ε"] else " ".join(alpha)
                            f.write(f"{A} -> {rhs}\n")
                    messagebox.showinfo("Exportar Derivação", f"Arquivo salvo em:\n{path}")
                except Exception as e:
                    messagebox.showerror("Exportar Derivação", f"Falha ao exportar TXT: {e}")

        def do_export_deriv_json():
            import json
            if not steps:
                messagebox.showinfo("Exportar Derivação", "Não há derivações para exportar.")
                return
            path = filedialog.asksaveasfilename(title="Salvar Derivação (JSON)", defaultextension=".json", filetypes=[["JSON", ".json"]])
            if path:
                try:
                    data = {
                        "title": title,
                        "kind": kind,
                        "steps": [{"lhs": A, "rhs": ("ε" if alpha == [EPS] or alpha == ["ε"] else alpha)} for A, alpha in steps],
                    }
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("Exportar Derivação", f"Arquivo salvo em:\n{path}")
                except Exception as e:
                    messagebox.showerror("Exportar Derivação", f"Falha ao exportar JSON: {e}")

        ttk.Button(toolbar, text="Deriv. JSON", command=do_export_deriv_json).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Deriv. TXT", command=do_export_deriv_txt).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Export SVG", command=do_export_svg).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Export PS", command=do_export_ps).pack(side="right", padx=2)
        ttk.Button(toolbar, text="Export PNG", command=do_export_png).pack(side="right", padx=2)

    # Side-by-side comparison tab (LL vs SLR) if both available
    if len(trees) >= 2:
        comp = ttk.Frame(nb)
        nb.add(comp, text="Comparar")

        # Left and right panes
        left = ttk.Frame(comp)
        right = ttk.Frame(comp)
        left.grid(row=0, column=0, sticky="nsew")
        right.grid(row=0, column=1, sticky="nsew")
        comp.columnconfigure(0, weight=1)
        comp.columnconfigure(1, weight=1)
        comp.rowconfigure(0, weight=1)

        def build_panel(parent, title, tree, steps, kind):
            toolbar = ttk.Frame(parent)
            toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
            ttk.Label(toolbar, text=f"{title} ({kind})").pack(side="left")
            canvas = tk.Canvas(parent, background="white")
            hbar = ttk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
            vbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
            canvas.grid(row=1, column=0, sticky="nsew")
            vbar.grid(row=1, column=1, sticky="ns")
            hbar.grid(row=2, column=0, sticky="ew")
            parent.rowconfigure(1, weight=1)
            parent.columnconfigure(0, weight=1)

            # derivation box
            dv = ttk.Frame(parent)
            dv.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=6, pady=4)
            ttk.Label(dv, text="Derivação" if kind.startswith("LL") else "Reduções").pack(anchor="w")
            txt = tk.Text(dv, height=8, wrap="word")
            scr = ttk.Scrollbar(dv, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=scr.set)
            txt.pack(side="left", fill="both", expand=True)
            scr.pack(side="right", fill="y")
            if steps:
                for A, alpha in steps:
                    rhs = "ε" if alpha == [EPS] or alpha == ["ε"] else " ".join(alpha)
                    txt.insert("end", f"{A} -> {rhs}\n")
            txt.configure(state="disabled")

            # draw tree and basic interactions (zoom/pan similar)
            draw_tree_on(canvas, tree)

            def zoom(factor: float):
                x0 = canvas.canvasx(canvas.winfo_width() / 2)
                y0 = canvas.canvasy(canvas.winfo_height() / 2)
                canvas.scale("all", x0, y0, factor, factor)
                bbox = canvas.bbox("all")
                if bbox:
                    canvas.configure(scrollregion=bbox)

            def on_wheel(event):
                direction = 0
                if hasattr(event, 'delta') and event.delta != 0:
                    direction = 1 if event.delta > 0 else -1
                else:
                    n = getattr(event, 'num', 0)
                    if n in (4, 5):
                        direction = 1 if n == 4 else -1
                zoom(1.1 if direction > 0 else 0.9)

            def on_button1_press(event):
                canvas.scan_mark(event.x, event.y)

            def on_button1_move(event):
                canvas.scan_dragto(event.x, event.y, gain=1)

            canvas.bind("<MouseWheel>", on_wheel)
            canvas.bind("<Button-4>", on_wheel)
            canvas.bind("<Button-5>", on_wheel)
            canvas.bind("<ButtonPress-1>", on_button1_press)
            canvas.bind("<B1-Motion>", on_button1_move)

            # export buttons
            def do_export_svg():
                path = filedialog.asksaveasfilename(title="Salvar SVG", defaultextension=".svg", filetypes=[["SVG", ".svg"]])
                if path:
                    export_svg(path, tree)

            def do_export_ps():
                path = filedialog.asksaveasfilename(title="Salvar PostScript", defaultextension=".ps", filetypes=[["PostScript", ".ps"]])
                if path:
                    canvas.postscript(file=path, colormode='color')

            def do_export_png():
                if not PIL_AVAILABLE:
                    messagebox.showwarning("Exportar PNG", "Pillow não disponível.")
                    return
                path = filedialog.asksaveasfilename(title="Salvar PNG", defaultextension=".png", filetypes=[["PNG", ".png"]])
                if path:
                    import io
                    ps = canvas.postscript(colormode='color')
                    img = Image.open(io.BytesIO(ps.encode('utf-8')))
                    img.save(path, 'PNG')

            def do_export_deriv_txt():
                if not steps:
                    messagebox.showinfo("Exportar Derivação", "Não há derivações para exportar.")
                    return
                path = filedialog.asksaveasfilename(title="Salvar Derivação (TXT)", defaultextension=".txt", filetypes=[["Texto", ".txt"]])
                if path:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(f"# {title} ({kind})\n")
                        for A, alpha in steps:
                            rhs = "ε" if alpha == [EPS] or alpha == ["ε"] else " ".join(alpha)
                            f.write(f"{A} -> {rhs}\n")

            def do_export_deriv_json():
                import json
                if not steps:
                    messagebox.showinfo("Exportar Derivação", "Não há derivações para exportar.")
                    return
                path = filedialog.asksaveasfilename(title="Salvar Derivação (JSON)", defaultextension=".json", filetypes=[["JSON", ".json"]])
                if path:
                    data = {
                        "title": title,
                        "kind": kind,
                        "steps": [{"lhs": A, "rhs": ("ε" if alpha == [EPS] or alpha == ["ε"] else alpha)} for A, alpha in steps],
                    }
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

            ttk.Button(toolbar, text="Deriv. JSON", command=do_export_deriv_json).pack(side="right", padx=2)
            ttk.Button(toolbar, text="Deriv. TXT", command=do_export_deriv_txt).pack(side="right", padx=2)
            ttk.Button(toolbar, text="Export PNG", command=do_export_png).pack(side="right", padx=2)
            ttk.Button(toolbar, text="Export PS", command=do_export_ps).pack(side="right", padx=2)
            ttk.Button(toolbar, text="Export SVG", command=do_export_svg).pack(side="right", padx=2)

        # Ensure we pick LL for left and SLR for right if present
        left_item = None
        right_item = None
        for item in trees:
            if item[0].startswith("LL") and left_item is None:
                left_item = item
            elif item[0].startswith("SLR") and right_item is None:
                right_item = item
        # fallback to first two
        if left_item is None:
            left_item = trees[0]
        if right_item is None:
            right_item = trees[1 if len(trees) > 1 else 0]
        build_panel(left, *left_item)
        build_panel(right, *right_item)

    root_win.mainloop()


def auto_lex(s: str, g: Grammar) -> List[str]:
    """Tokenização simples baseada na lista de terminais da gramática.
    Regras suportadas:
      - Palavras-chave (terminais alfabéticos não 'id'/'num'): if, then, else, etc.
      - Operadores/pontuação presentes nos terminais (1+ chars), priorizando os mais longos.
      - Identificadores: se 'id' ∈ Terminals, reconhece [A-Za-z_][A-Za-z0-9_]* e produz 'id', exceto se corresponder a palavra-chave.
      - Números: se 'num' ∈ Terminals, reconhece [0-9]+ e produz 'num'.
    """
    import re

    text = s.strip()
    i = 0
    out: List[str] = []

    terms = set(g.terminals)

    # Palavras-chave: tokens alfanuméricos específicos presentes nos terminais
    keywords = sorted([t for t in terms if t.isalpha() and t not in {"id", "num"}], key=lambda x: -len(x))
    # Operadores/pontuação: ordene por tamanho desc para pegar multi-char primeiro
    punct_ops = sorted([t for t in terms if not t.isalnum()], key=lambda x: -len(x))

    re_ident = re.compile(r"[A-Za-z_][A-Za-z0-9_]*") if "id" in terms else None
    re_num = re.compile(r"[0-9]+") if "num" in terms else None

    while i < len(text):
        if text[i].isspace():
            i += 1
            continue

        # keywords
        matched = False
        for kw in keywords:
            L = len(kw)
            if text[i:i+L] == kw:
                # limitar por fronteira de palavra
                end_ok = (i+L == len(text)) or (not text[i+L].isalnum() and text[i+L] != '_')
                if end_ok:
                    out.append(kw)
                    i += L
                    matched = True
                    break
        if matched:
            continue

        # operators/punct
        for op in punct_ops:
            L = len(op)
            if L and text[i:i+L] == op:
                out.append(op)
                i += L
                matched = True
                break
        if matched:
            continue

        # numbers
        if re_num is not None:
            m = re_num.match(text, i)
            if m:
                out.append("num")
                i = m.end()
                continue

        # identifiers
        if re_ident is not None:
            m = re_ident.match(text, i)
            if m:
                out.append("id")
                i = m.end()
                continue

        # falha
        snippet = text[i:i+10]
        raise ValueError(f"Auto-lex falhou em posição {i}: '{snippet}'")

    # Validação final: todos tokens precisam existir nos terminais
    for t in out:
        if t not in terms:
            raise ValueError(f"Token '{t}' não pertence aos terminais da gramática")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="Teste de parsing ascendente (SLR(1)) e descendente (LL(1)) para uma gramática CFG.")
    p.add_argument("--grammar", required=True, help="Caminho do arquivo da gramática")
    p.add_argument("--input", dest="input_str", required=True, help="Cadeia de entrada (tokens separados por espaço; ou crua com --auto-lex)")
    p.add_argument("--method", choices=["ll1", "slr1", "lalr1", "lr1", "both", "all"], default="both", help="Método de parsing a testar")
    p.add_argument("--show-tables", action="store_true", help="Mostra tabelas (LL(1)/SLR(1))")
    p.add_argument("--show-items", action="store_true", help="Mostra itens LR(0) por estado (SLR(1))")
    p.add_argument("--trace", action="store_true", help="Mostra o passo-a-passo do parsing")
    p.add_argument("--auto-lex", action="store_true", help="Faz tokenização simples da entrada crua (id/num, palavras-chave e símbolos)")
    p.add_argument("--gui", action="store_true", help="Mostra a(s) árvore(s) de derivação em uma janela GUI")
    p.add_argument("--export-svg", help="Exporta árvore(s) em SVG sem abrir GUI. Se 'both', gera sufixos _ll1.svg e _slr1.svg.")
    args = p.parse_args(argv)

    g = Grammar.from_file(args.grammar)
    ff = FirstFollow(g)
    if args.auto_lex:
        tokens = auto_lex(args.input_str, g)
    else:
        tokens = [t for t in args.input_str.strip().split() if t]

    print("=== Gramática ===")
    print(g)
    print()
    print("=== FIRST ===")
    for k in sorted(ff.first.keys()):
        print(f"FIRST({k}) = {{ {', '.join(sorted(ff.first[k]))} }}")
    print("=== FOLLOW ===")
    for k in sorted(ff.follow.keys()):
        print(f"FOLLOW({k}) = {{ {', '.join(sorted(ff.follow[k]))} }}")
    print()

    result_ll1: Optional[ParseResult] = None
    result_slr: Optional[ParseResult] = None
    result_lalr: Optional[ParseResult] = None
    result_lr1: Optional[ParseResult] = None
    if args.method in ("ll1", "both"):
        print("=== LL(1) ===")
        ll1 = LL1Parser(g, ff)
        if args.show_tables:
            ll1.print_table()
        print("-- Execução --")
        result_ll1 = ll1.parse(tokens, trace=args.trace)
        print(f"Resultado LL(1): {'ACEITA' if result_ll1.ok else 'REJEITA'}")
        print()

    if args.method in ("slr1", "both", "all"):
        print("=== SLR(1) ===")
        slr = SLR1Parser(g, ff)
        if args.show_tables or args.show_items:
            slr.print_tables(show_items=args.show_items)
        print("-- Execução --")
        result_slr = slr.parse(tokens, trace=args.trace)
        print(f"Resultado SLR(1): {'ACEITA' if result_slr.ok else 'REJEITA'}")
        print()

    if args.method in ("lalr1", "all"):
        print("=== LALR(1) ===")
        lalr = LR1Parser(g, ff, mode="lalr1")
        if args.show_tables or args.show_items:
            lalr.print_tables(show_items=args.show_items)
        print("-- Execução --")
        result_lalr = lalr.parse(tokens, trace=args.trace)
        print(f"Resultado LALR(1): {'ACEITA' if result_lalr.ok else 'REJEITA'}")
        print()

    if args.method in ("lr1", "all"):
        print("=== LR(1) ===")
        lr1 = LR1Parser(g, ff, mode="lr1")
        if args.show_tables or args.show_items:
            lr1.print_tables(show_items=args.show_items)
        print("-- Execução --")
        result_lr1 = lr1.parse(tokens, trace=args.trace)
        print(f"Resultado LR(1): {'ACEITA' if result_lr1.ok else 'REJEITA'}")
        print()

    if args.method == "both" and result_ll1 is not None and result_slr is not None:
        agree = result_ll1.ok == result_slr.ok
        print(f"Concordância LL(1) vs SLR(1): {'SIM' if agree else 'NÃO'}")

    # Optional GUI tree visualization
    # Non-GUI SVG export
    if args.export_svg:
        out = args.export_svg
        if args.method == "ll1":
            if result_ll1 and result_ll1.ok and result_ll1.tree is not None:
                export_tree_svg(result_ll1.tree, out)
                print(f"SVG salvo em: {out}")
            else:
                print("LL(1) não aceitou a entrada; sem SVG.")
        elif args.method == "slr1":
            if result_slr and result_slr.ok and result_slr.tree is not None:
                export_tree_svg(result_slr.tree, out)
                print(f"SVG salvo em: {out}")
            else:
                print("SLR(1) não aceitou a entrada; sem SVG.")
        elif args.method == "lalr1":
            if result_lalr and result_lalr.ok and result_lalr.tree is not None:
                export_tree_svg(result_lalr.tree, out)
                print(f"SVG salvo em: {out}")
            else:
                print("LALR(1) não aceitou a entrada; sem SVG.")
        elif args.method == "lr1":
            if result_lr1 and result_lr1.ok and result_lr1.tree is not None:
                export_tree_svg(result_lr1.tree, out)
                print(f"SVG salvo em: {out}")
            else:
                print("LR(1) não aceitou a entrada; sem SVG.")
        else:  # both
            base = out
            if base.lower().endswith(".svg"):
                base = base[:-4]
            if result_ll1 and result_ll1.ok and result_ll1.tree is not None:
                p_ll = base + "_ll1.svg"
                export_tree_svg(result_ll1.tree, p_ll)
                print(f"SVG LL(1) salvo em: {p_ll}")
            else:
                print("LL(1) não aceitou a entrada; sem SVG LL(1).")
            if result_slr and result_slr.ok and result_slr.tree is not None:
                p_slr = base + "_slr1.svg"
                export_tree_svg(result_slr.tree, p_slr)
                print(f"SVG SLR(1) salvo em: {p_slr}")
            else:
                print("SLR(1) não aceitou a entrada; sem SVG SLR(1).")
            if result_lalr and result_lalr.ok and result_lalr.tree is not None:
                p_lalr = base + "_lalr1.svg"
                export_tree_svg(result_lalr.tree, p_lalr)
                print(f"SVG LALR(1) salvo em: {p_lalr}")
            if result_lr1 and result_lr1.ok and result_lr1.tree is not None:
                p_lr = base + "_lr1.svg"
                export_tree_svg(result_lr1.tree, p_lr)
                print(f"SVG LR(1) salvo em: {p_lr}")

    if args.gui:
        trees: List[Tuple[str, ParseTreeNode, Optional[List[Tuple[str, List[str]]]], str]] = []
        if result_ll1 and result_ll1.ok and result_ll1.tree is not None:
            trees.append(("LL(1)", result_ll1.tree, result_ll1.derivations, result_ll1.kind))
        if result_slr and result_slr.ok and result_slr.tree is not None:
            trees.append(("SLR(1)", result_slr.tree, result_slr.derivations, result_slr.kind))
        if result_lalr and result_lalr.ok and result_lalr.tree is not None:
            trees.append(("LALR(1)", result_lalr.tree, result_lalr.derivations, result_lalr.kind))
        if result_lr1 and result_lr1.ok and result_lr1.tree is not None:
            trees.append(("LR(1)", result_lr1.tree, result_lr1.derivations, result_lr1.kind))
        if trees:
            show_trees_gui(trees)
        else:
            print("Nenhuma árvore de derivação aceita para exibir (use --gui após uma análise bem-sucedida).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        sys.exit(1)
