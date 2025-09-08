#!/usr/bin/env python3
"""
Lexer template (Lab 02)

Usage:
  python3 lexer_template.py --input "if x then y=3"
  python3 lexer_template.py --file programa.txt
"""
import re
import argparse
from dataclasses import dataclass
from typing import List, Optional


# 1) Defina aqui os tokens. A ordem importa (palavras‑chave antes de id, operadores multi‑char antes dos de 1 char).
TOKEN_SPECS = [
    ("WHITESPACE", r"[ \t\r\n]+"),
    ("COMMENT", r"//[^\n]*"),
    # Palavras‑chave
    ("IF", r"\bif\b"),
    ("THEN", r"\bthen\b"),
    ("ELSE", r"\belse\b"),
    # Operadores/pontuação
    ("EQ", r"=="),
    ("ASSIGN", r"="),
    ("PLUS", r"\+"),
    ("STAR", r"\*"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("SEMI", r";"),
    # Identificadores e números
    ("NUM", r"\b\d+\b"),
    ("ID", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
]


@dataclass
class Token:
    kind: str
    lexeme: str
    pos: int


def build_master_regex():
    parts = []
    for name, pattern in TOKEN_SPECS:
        parts.append(f"(?P<{name}>{pattern})")
    return re.compile("|".join(parts))


def lex(text: str) -> List[Token]:
    master = build_master_regex()
    pos = 0
    out: List[Token] = []
    while pos < len(text):
        m = master.match(text, pos)
        if not m:
            snippet = text[pos:pos+16]
            raise ValueError(f"Token inválido em posição {pos}: {snippet!r}")
        kind = m.lastgroup
        lexeme = m.group(kind)
        if kind not in {"WHITESPACE", "COMMENT"}:
            out.append(Token(kind, lexeme, pos))
        pos = m.end()
    return out


def main(argv: Optional[List[str]] = None):
    ap = argparse.ArgumentParser(description="Lexer didático (Lab 02)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--input", help="Entrada crua")
    g.add_argument("--file", help="Arquivo de entrada")
    args = ap.parse_args(argv)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.input
    tokens = lex(text)
    for t in tokens:
        print(f"{t.kind:<10} {t.lexeme!r} @ {t.pos}")


if __name__ == "__main__":
    main()

