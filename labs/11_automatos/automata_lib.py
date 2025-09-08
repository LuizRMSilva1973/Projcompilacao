#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Dict, Set, Tuple, List, Optional, Tuple as Tup


# ===== Estruturas =====

@dataclass(frozen=True)
class State:
    id: int


@dataclass
class NFA:
    start: State
    accepts: Set[State]
    trans: Dict[Tuple[State, Optional[str]], Set[State]]  # símbolo ou None (ε)


@dataclass
class DFA:
    start: State
    accepts: Set[State]
    trans: Dict[Tuple[State, str], State]


# ===== Regex → NFA (Thompson) =====

OPS = {'|', '*', '+', '?', '(', ')', '.'}


def _insert_concat(regex: str) -> str:
    out = []
    prev = ''
    for c in regex:
        if prev:
            if (prev not in {'|', '(',} and c not in {'|', ')', '*', '+', '?'}):
                out.append('.')
            if (prev in {'*','+','?',')'} and c not in {'|', ')'}):
                out.append('.')
        out.append(c)
        prev = c
    return ''.join(out)


def _to_postfix(regex: str) -> str:
    prec = {'|':1, '.':2, '*':3, '+':3, '?':3}
    out: List[str] = []
    st: List[str] = []
    for c in regex:
        if c == '(':
            st.append(c)
        elif c == ')':
            while st and st[-1] != '(':
                out.append(st.pop())
            if not st:
                raise ValueError('Parênteses desbalanceados')
            st.pop()
        elif c in prec:
            while st and st[-1] in prec and prec[st[-1]] >= prec[c]:
                out.append(st.pop())
            st.append(c)
        else:
            out.append(c)
    while st:
        op = st.pop()
        if op == '(':
            raise ValueError('Parênteses desbalanceados')
        out.append(op)
    return ''.join(out)


def regex_to_nfa(regex: str) -> Tuple[NFA, Set[str]]:
    r = _insert_concat(regex)
    pf = _to_postfix(r)
    next_id = 0

    def new_state() -> State:
        nonlocal next_id
        s = State(next_id)
        next_id += 1
        return s

    def add_trans(trans: Dict[Tuple[State, Optional[str]], Set[State]], a: State, sym: Optional[str], b: State):
        trans.setdefault((a, sym), set()).add(b)

    stack: List[Tuple[State, State, Dict[Tuple[State, Optional[str]], Set[State]]]] = []
    alphabet: Set[str] = set()
    for c in pf:
        if c not in OPS:
            s = new_state(); t = new_state()
            tr: Dict[Tuple[State, Optional[str]], Set[State]] = {}
            add_trans(tr, s, c, t)
            alphabet.add(c)
            stack.append((s, t, tr))
        elif c == '.':
            if len(stack) < 2:
                raise ValueError("Regex inválida: concatenação (.) sem operandos suficientes")
            s2, t2, tr2 = stack.pop()
            s1, t1, tr1 = stack.pop()
            # liga t1 ->ε s2
            add_trans(tr1, t1, None, s2)
            tr1.update({k: (tr1.get(k,set()) | v) for k, v in tr2.items()})
            stack.append((s1, t2, tr1))
        elif c == '|':
            if len(stack) < 2:
                raise ValueError("Regex inválida: união (|) sem operandos suficientes")
            s2, t2, tr2 = stack.pop()
            s1, t1, tr1 = stack.pop()
            s = new_state(); t = new_state()
            tr: Dict[Tuple[State, Optional[str]], Set[State]] = {}
            # ε-transições
            add_trans(tr, s, None, s1); add_trans(tr, s, None, s2)
            add_trans(tr, t1, None, t); add_trans(tr, t2, None, t)
            # merge
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            for k,v in tr2.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
        elif c == '*':
            if len(stack) < 1:
                raise ValueError("Regex inválida: fecho (*) sem operando")
            s1, t1, tr1 = stack.pop()
            s = new_state(); t = new_state()
            tr: Dict[Tuple[State, Optional[str]], Set[State]] = {}
            add_trans(tr, s, None, s1)
            add_trans(tr, t1, None, t)
            add_trans(tr, s, None, t)  # vazio
            add_trans(tr, t1, None, s1)  # repetição
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
        elif c == '+':
            # uma ou mais: xx*
            if len(stack) < 1:
                raise ValueError("Regex inválida: operador + sem operando")
            s1, t1, tr1 = stack.pop()
            s = new_state(); t = new_state()
            tr: Dict[Tuple[State, Optional[str]], Set[State]] = {}
            add_trans(tr, s, None, s1)
            add_trans(tr, t1, None, t)
            add_trans(tr, t1, None, s1)
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
        elif c == '?':
            if len(stack) < 1:
                raise ValueError("Regex inválida: operador ? sem operando")
            s1, t1, tr1 = stack.pop()
            s = new_state(); t = new_state()
            tr: Dict[Tuple[State, Optional[str]], Set[State]] = {}
            add_trans(tr, s, None, s1)
            add_trans(tr, t1, None, t)
            add_trans(tr, s, None, t)
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
        else:
            raise ValueError(f"Operador não suportado: {c}")
    if len(stack) != 1:
        raise ValueError('Regex inválida: verifique parênteses e operadores')
    s, t, tr = stack[-1]
    return NFA(s, {t}, tr), alphabet


def regex_to_nfa_with_log(regex: str) -> Tuple[NFA, Set[str], List[str]]:
    log: List[str] = []
    r = _insert_concat(regex)
    log.append(f"Com concatenação explícita: {r}")
    pf = _to_postfix(r)
    log.append(f"Posfixa: {pf}")
    next_id = 0
    def new_state() -> State:
        nonlocal next_id
        s = State(next_id)
        next_id += 1
        return s
    def add_trans(trans: Dict[Tuple[State, Optional[str]], Set[State]], a: State, sym: Optional[str], b: State):
        trans.setdefault((a, sym), set()).add(b)
    stack: List[Tuple[State, State, Dict[Tuple[State, Optional[str]], Set[State]]]] = []
    alphabet: Set[str] = set()
    for c in pf:
        if c not in OPS:
            s = new_state(); t = new_state(); tr = {}
            add_trans(tr, s, c, t)
            alphabet.add(c)
            stack.append((s, t, tr))
            log.append(f"Empilha símbolo '{c}'")
        elif c == '.':
            if len(stack) < 2:
                raise ValueError("Regex inválida: concatenação (.) sem operandos suficientes")
            s2, t2, tr2 = stack.pop(); s1, t1, tr1 = stack.pop()
            add_trans(tr1, t1, None, s2)
            for k,v in tr2.items(): tr1.setdefault(k,set()).update(v)
            stack.append((s1, t2, tr1))
            log.append("Concatenação (.)")
        elif c == '|':
            if len(stack) < 2:
                raise ValueError("Regex inválida: união (|) sem operandos suficientes")
            s2, t2, tr2 = stack.pop(); s1, t1, tr1 = stack.pop()
            s = new_state(); t = new_state(); tr = {}
            add_trans(tr, s, None, s1); add_trans(tr, s, None, s2)
            add_trans(tr, t1, None, t); add_trans(tr, t2, None, t)
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            for k,v in tr2.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
            log.append("União (|)")
        elif c == '*':
            if len(stack) < 1:
                raise ValueError("Regex inválida: fecho (*) sem operando")
            s1, t1, tr1 = stack.pop(); s = new_state(); t = new_state(); tr = {}
            add_trans(tr, s, None, s1); add_trans(tr, t1, None, t)
            add_trans(tr, s, None, t); add_trans(tr, t1, None, s1)
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
            log.append("Fecho de Kleene (*)")
        elif c == '+':
            if len(stack) < 1:
                raise ValueError("Regex inválida: operador + sem operando")
            s1, t1, tr1 = stack.pop(); s = new_state(); t = new_state(); tr = {}
            add_trans(tr, s, None, s1); add_trans(tr, t1, None, t); add_trans(tr, t1, None, s1)
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
            log.append("Uma ou mais (+)")
        elif c == '?':
            if len(stack) < 1:
                raise ValueError("Regex inválida: operador ? sem operando")
            s1, t1, tr1 = stack.pop(); s = new_state(); t = new_state(); tr = {}
            add_trans(tr, s, None, s1); add_trans(tr, t1, None, t); add_trans(tr, s, None, t)
            for k,v in tr1.items(): tr.setdefault(k,set()).update(v)
            stack.append((s, t, tr))
            log.append("Opcional (?)")
        else:
            raise ValueError(f"Operador não suportado: {c}")
    if len(stack) != 1:
        raise ValueError('Regex inválida: verifique parênteses e operadores')
    s, t, tr = stack[-1]
    return NFA(s, {t}, tr), alphabet, log


# ===== NFA → DFA (subset), e minimização (Hopcroft) =====

def _eclose(nfa: NFA, S: Set[State]) -> Set[State]:
    out = set(S)
    stack = list(S)
    while stack:
        q = stack.pop()
        for p in nfa.trans.get((q, None), set()):
            if p not in out:
                out.add(p); stack.append(p)
    return out


def nfa_to_dfa(nfa: NFA, alphabet: Set[str]) -> DFA:
    start_set = frozenset(_eclose(nfa, {nfa.start}))
    dfa_states: Dict[frozenset, State] = {start_set: State(0)}
    trans: Dict[Tuple[State, str], State] = {}
    accepts: Set[State] = set()
    work = [start_set]
    next_id = 1
    while work:
        S = work.pop()
        s_id = dfa_states[S]
        if any(q in nfa.accepts for q in S):
            accepts.add(s_id)
        for a in alphabet:
            move = set()
            for q in S:
                for p in nfa.trans.get((q, a), set()):
                    move.add(p)
            T = frozenset(_eclose(nfa, move)) if move else frozenset()
            if not T:
                continue
            if T not in dfa_states:
                dfa_states[T] = State(next_id); next_id += 1; work.append(T)
            trans[(s_id, a)] = dfa_states[T]
    return DFA(start=dfa_states[start_set], accepts=accepts, trans=trans)


def nfa_to_dfa_steps(nfa: NFA, alphabet: Set[str]):
    """Gera passos (texto) da construção por subconjuntos."""
    steps: List[str] = []
    start_set = frozenset(_eclose(nfa, {nfa.start}))
    dfa_states: Dict[frozenset, State] = {start_set: State(0)}
    trans: Dict[Tuple[State, str], State] = {}
    accepts: Set[State] = set()
    work = [start_set]
    next_id = 1
    steps.append(f"I0 = ε-closure({{q0}}) = {sorted([s.id for s in start_set])}")
    while work:
        S = work.pop(0)
        s_id = dfa_states[S]
        if any(q in nfa.accepts for q in S):
            accepts.add(s_id)
        for a in sorted(alphabet):
            move = set()
            for q in S:
                for p in nfa.trans.get((q, a), set()):
                    move.add(p)
            T = frozenset(_eclose(nfa, move)) if move else frozenset()
            if not T:
                steps.append(f"Do estado {s_id.id} com '{a}': movimento vazio")
                continue
            if T not in dfa_states:
                dfa_states[T] = State(next_id); steps.append(f"Novo estado q{next_id} = ε-closure(move({[q.id for q in S]}, '{a}')) = {sorted([t.id for t in T])}"); next_id += 1; work.append(T)
            trans[(s_id, a)] = dfa_states[T]
            steps.append(f"Transição: q{s_id.id} --{a}--> q{dfa_states[T].id}")
    return steps


def dfa_minimize(dfa: DFA, alphabet: Set[str]) -> DFA:
    # Hopcroft
    all_states = set([dfa.start]) | set([s for s,_ in dfa.trans.keys()]) | set(dfa.trans.values()) | set(dfa.accepts)
    P = [set(dfa.accepts), all_states - set(dfa.accepts)]
    W = [set(dfa.accepts)]
    def trans_to(s: State, a: str) -> Optional[State]:
        return dfa.trans.get((s, a))
    while W:
        A = W.pop()
        for a in alphabet:
            X = set(s for s in all_states if trans_to(s,a) in A)
            newP = []
            for Y in P:
                i = Y & X
                d = Y - X
                if i and d:
                    newP.extend([i,d])
                    if Y in W:
                        W.remove(Y); W.extend([i,d])
                    else:
                        W.append(i if len(i) <= len(d) else d)
                else:
                    newP.append(Y)
            P = newP
    # construir DFA reduzido
    rep = {next(iter(B)): idx for idx,B in enumerate(P) if B}
    state_map: Dict[State, State] = {}
    for B in P:
        if not B: continue
        ridx = len(state_map)
        srep = next(iter(B))
        snew = State(ridx)
        for s in B:
            state_map[s] = snew
    start = state_map[dfa.start]
    accepts = {state_map[s] for s in dfa.accepts}
    trans: Dict[Tuple[State,str], State] = {}
    for (s,a), t in dfa.trans.items():
        trans[(state_map[s], a)] = state_map[t]
    return DFA(start, accepts, trans)


def dfa_minimize_steps(dfa: DFA, alphabet: Set[str]) -> Tup[List[str], List[List[List[int]]]]:
    """Passos (texto) da minimização de Hopcroft), com snapshots de partições.
    Retorna (steps, snapshots), onde snapshots é uma lista de partições; cada partição é
    uma lista de blocos, e cada bloco é uma lista de ids de estados.
    """
    steps: List[str] = []
    snaps: List[List[List[int]]] = []
    all_states = set([dfa.start]) | set([s for s,_ in dfa.trans.keys()]) | set(dfa.trans.values()) | set(dfa.accepts)
    P = [set(dfa.accepts), all_states - set(dfa.accepts)]
    W = [set(dfa.accepts)]
    steps.append(f"Partição inicial: A={sorted([s.id for s in P[0]])}, N={sorted([s.id for s in P[1]])}")
    snaps.append([sorted([s.id for s in B]) for B in P if B])
    def trans_to(s: State, a: str) -> Optional[State]:
        return dfa.trans.get((s, a))
    while W:
        A = W.pop()
        steps.append(f"Refina com A={sorted([s.id for s in A])}")
        for a in sorted(alphabet):
            X = set(s for s in all_states if trans_to(s,a) in A)
            newP = []
            for Y in P:
                i = Y & X
                d = Y - X
                if i and d:
                    newP.extend([i,d])
                    if Y in W:
                        W.remove(Y); W.extend([i,d])
                    else:
                        W.append(i if len(i) <= len(d) else d)
                    steps.append(f"Divide {sorted([s.id for s in Y])} em {sorted([s.id for s in i])} e {sorted([s.id for s in d])} pela letra '{a}'")
                else:
                    newP.append(Y)
            P = newP
            snaps.append([sorted([s.id for s in B]) for B in P if B])
    steps.append("Partição final: " + ", ".join([str(sorted([s.id for s in B])) for B in P if B]))
    snaps.append([sorted([s.id for s in B]) for B in P if B])
    return steps, snaps


def export_dot_nfa(nfa: NFA, path: str):
    """Exporta NFA em formato DOT (Graphviz)."""
    lines = ["digraph NFA {", "  rankdir=LR;", "  node [shape=circle];"]
    # estados
    states = list({nfa.start} | set(nfa.accepts) | {s for (s,_), _ in nfa.trans.items()} | {t for _, S in nfa.trans.items() for t in S})
    idx = {s:i for i,s in enumerate(states)}
    # início
    lines.append("  __start [shape=point];")
    lines.append(f"  __start -> q{idx[nfa.start]};")
    # finais
    for s in states:
        shape = 'doublecircle' if s in nfa.accepts else 'circle'
        lines.append(f"  q{idx[s]} [shape={shape}];")
    # transições
    for (s, sym), T in nfa.trans.items():
        for t in T:
            label = sym if sym is not None else 'ε'
            lines.append(f"  q{idx[s]} -> q{idx[t]} [label=\"{label}\"];")
    lines.append("}")
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def export_dot_dfa(dfa: DFA, path: str):
    """Exporta DFA em formato DOT (Graphviz)."""
    lines = ["digraph DFA {", "  rankdir=LR;", "  node [shape=circle];"]
    states = list({dfa.start} | {s for s,_ in dfa.trans.keys()} | set(dfa.trans.values()))
    idx = {s:i for i,s in enumerate(states)}
    lines.append("  __start [shape=point];")
    lines.append(f"  __start -> q{idx[dfa.start]};")
    for s in states:
        shape = 'doublecircle' if s in dfa.accepts else 'circle'
        lines.append(f"  q{idx[s]} [shape={shape}];")
    for (s,a), t in dfa.trans.items():
        lines.append(f"  q{idx[s]} -> q{idx[t]} [label=\"{a}\"];")
    lines.append("}")
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ===== Execução e SVG =====

def dfa_accepts(dfa: DFA, s: List[str]) -> bool:
    q = dfa.start
    for a in s:
        q = dfa.trans.get((q, a))
        if q is None:
            return False
    return q in dfa.accepts


def automaton_to_svg_dfa(dfa: DFA, alphabet: Set[str], path: str):
    # Layout simples em grade
    states = list({dfa.start} | {s for s,_ in dfa.trans.keys()} | set(dfa.trans.values()))
    idx = {s:i for i,s in enumerate(states)}
    n = len(states)
    cols = max(1, int(n**0.5))
    HSPACE = 140; VSPACE = 120; R = 24
    def pos(i):
        r = i // cols; c = i % cols
        return (60 + c*HSPACE, 60 + r*VSPACE)
    parts = ["<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='800'>",
             "<style>.st{fill:#fff;stroke:#111;stroke-width:2}.acc{stroke:#3b82f6;stroke-width:3}.txt{font:12px sans-serif}.edge{stroke:#555;stroke-width:1;fill:none;marker-end:url(#a)}.lbl{font:11px sans-serif;fill:#111}</style>",
             "<defs><marker id='a' markerWidth='10' markerHeight='7' refX='10' refY='3.5' orient='auto'><polygon points='0 0, 10 3.5, 0 7' fill='#555'/></marker></defs>"]
    # edges
    for (s,a),t in dfa.trans.items():
        x1,y1 = pos(idx[s]); x2,y2 = pos(idx[t])
        mx,my = (x1+x2)/2, (y1+y2)/2
        parts.append(f"<path class='edge' d='M {x1} {y1} C {mx} {y1}, {mx} {y2}, {x2} {y2}' />")
        parts.append(f"<text class='lbl' x='{mx}' y='{(y1+y2)/2 - 6}' text-anchor='middle'>{a}</text>")
    # nodes
    for s in states:
        x,y = pos(idx[s])
        klass = 'st acc' if s in dfa.accepts else 'st'
        parts.append(f"<circle class='{klass}' cx='{x}' cy='{y}' r='{R}' />")
        if s == dfa.start:
            parts.append(f"<path class='edge' d='M {x-50} {y} L {x-R} {y}' />")
        parts.append(f"<text class='txt' x='{x}' y='{y+4}' text-anchor='middle'>q{idx[s]}</text>")
    parts.append("</svg>")
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))


def automaton_to_svg_nfa(nfa: NFA, alphabet: Set[str], path: str):
    # Layout simples: enumerar estados e desenhar transições com rótulos (inclui ε)
    states = list({nfa.start} | set(nfa.accepts) | {s for (s,_), _ in nfa.trans.items()} | {t for _, S in nfa.trans.items() for t in S})
    idx = {s:i for i,s in enumerate(states)}
    n = len(states)
    cols = max(1, int(n**0.5))
    HSPACE = 140; VSPACE = 120; R = 24
    def pos(i):
        r = i // cols; c = i % cols
        return (60 + c*HSPACE, 60 + r*VSPACE)
    parts = ["<svg xmlns='http://www.w3.org/2000/svg' width='1000' height='800'>",
             "<style>.st{fill:#fff;stroke:#111;stroke-width:2}.acc{stroke:#16a34a;stroke-width:3}.txt{font:12px sans-serif}.edge{stroke:#555;stroke-width:1;fill:none;marker-end:url(#a)}.lbl{font:11px sans-serif;fill:#111}</style>",
             "<defs><marker id='a' markerWidth='10' markerHeight='7' refX='10' refY='3.5' orient='auto'><polygon points='0 0, 10 3.5, 0 7' fill='#555'/></marker></defs>"]
    # edges
    for (s, sym), T in nfa.trans.items():
        for t in T:
            x1,y1 = pos(idx[s]); x2,y2 = pos(idx[t])
            mx,my = (x1+x2)/2, (y1+y2)/2
            parts.append(f"<path class='edge' d='M {x1} {y1} C {mx} {y1}, {mx} {y2}, {x2} {y2}' />")
            label = sym if sym is not None else 'ε'
            parts.append(f"<text class='lbl' x='{mx}' y='{(y1+y2)/2 - 6}' text-anchor='middle'>{label}</text>")
    # nodes
    for s in states:
        x,y = pos(idx[s])
        klass = 'st acc' if s in nfa.accepts else 'st'
        parts.append(f"<circle class='{klass}' cx='{x}' cy='{y}' r='{R}' />")
        if s == nfa.start:
            parts.append(f"<path class='edge' d='M {x-50} {y} L {x-R} {y}' />")
        parts.append(f"<text class='txt' x='{x}' y='{y+4}' text-anchor='middle'>q{idx[s]}</text>")
    parts.append("</svg>")
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
