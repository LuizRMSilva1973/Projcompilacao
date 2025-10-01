#!/usr/bin/env python3
"""
GUI didática para Lexer e Parser (LL(1)/SLR(1)).
Reaproveita o parsing_tester.py e o lexer do Lab 02 quando disponível.
"""
import os
import sys
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception as e:
    sys.stderr.write(
        (
            "Erro: Tkinter (tk) não está disponível neste Python.\n"
            "Para executar a GUI, instale o pacote do Tk do seu sistema.\n\n"
            "Ubuntu/Debian: sudo apt-get install -y python3-tk\n"
            "Fedora: sudo dnf install python3-tkinter\n"
            "Arch/Manjaro: sudo pacman -S tk\n"
            "macOS (Homebrew): brew install tcl-tk e use o Python do Homebrew\n"
            "Windows: normalmente já vem com o instalador do Python.\n"
        )
    )
    sys.exit(1)
import importlib.util
from typing import Optional, List, Tuple
from typing import Any, Dict as _Dict
# Cache simples para evitar múltiplas instâncias do mesmo módulo (tipos incompatíveis)
_MODULE_CACHE: _Dict[str, Any] = {}

# Base dir e helper para carregar módulos por caminho
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_module(relpath: str, modname: str):
    path = os.path.join(BASE_DIR, relpath)
    key = os.path.abspath(path)
    if key in _MODULE_CACHE:
        return _MODULE_CACHE[key]
    spec = importlib.util.spec_from_file_location(modname, path)
    if not spec or not spec.loader:
        raise ImportError(f"Não foi possível carregar {relpath}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    _MODULE_CACHE[key] = mod
    return mod

try:
    lexer_template = _load_module('labs/02_lexica/lexer_template.py', 'lab02_lexer')
except Exception:
    lexer_template = None

# Importa parsers e GUI de árvores
from parsing_tester import Grammar, FirstFollow, LL1Parser, SLR1Parser, ParseTreeNode, show_trees_gui, export_tree_svg, auto_lex


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VisualAutomata — GUI Didática")
        self.geometry("1000x700")
        self._settings_path = os.path.join(BASE_DIR, 'gui_settings.json')
        self._settings = {}
        self._load_settings()
        self._build_ui()
        self.parsers = {}
        # restore selections if available
        if self._settings.get('grammar_path'):
            self.grammar_path.set(self._settings.get('grammar_path',''))
        if self._settings.get('parser_method'):
            self.method.set(self._settings.get('parser_method','both'))
        self.var_auto.set(bool(self._settings.get('parser_auto_lex', False)))
        self.var_trace.set(bool(self._settings.get('parser_trace', True)))
        self.var_tables.set(bool(self._settings.get('parser_tables', True)))
        self.var_items.set(bool(self._settings.get('parser_items', False)))
        self.var_arith_bool.set(bool(self._settings.get('sem_arith_bool', False)))
        self.var_eq_same.set(bool(self._settings.get('sem_eq_same', True)))
        if self._settings.get('regex_last'):
            self.re_input.delete(0,'end'); self.re_input.insert(0, self._settings.get('regex_last',''))
        if self._settings.get('regex_test_last'):
            self.re_test.delete(0,'end'); self.re_test.insert(0, self._settings.get('regex_test_last',''))
        if hasattr(self, 'auto_view') and self._settings.get('auto_view'):
            self.auto_view.set(self._settings.get('auto_view','dfa'))
        # Codegen/regalloc (se existir)
        if hasattr(self, 'var_regalloc') and 'codegen_regalloc' in self._settings:
            try:
                self.var_regalloc.set(bool(self._settings.get('codegen_regalloc', False)))
            except Exception:
                pass
        if hasattr(self, 'reg_k') and 'codegen_k' in self._settings:
            try:
                self.reg_k.set(int(self._settings.get('codegen_k', 3)))
            except Exception:
                pass
        # save on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # atalhos de teclado
        self.bind('<Control-e>', lambda e: self.run_parser())
        self.bind('<Control-g>', lambda e: self._browse_grammar())
        self.bind('<Control-s>', lambda e: self.export_svg())
        self.bind('<Control-j>', lambda e: self.export_json())
        self.bind('<Control-c>', lambda e: self.compare_trees())
        self.bind('<Control-b>', lambda e: self.build_automata())
        self.bind('<Control-t>', lambda e: self.test_automata())
        self.bind('<Control-i>', lambda e: self.import_tree_from_parser())
        self.bind('<Control-y>', lambda e: self.run_semantics())
        # atalhos de aula (1..0 = 1..10)
        for key, num in [('1',1),('2',2),('3',3),('4',4),('5',5),('6',6),('7',7),('8',8),('9',9),('0',10)]:
            self.bind(f'<Control-Key-{key}>', lambda e, n=num: self._select_lesson(n))
            # auto-execução: Ctrl+Alt+num
            self.bind(f'<Control-Alt-Key-{key}>', lambda e, n=num: self._select_lesson(n, True))

    def _build_ui(self):
        # menu
        self._build_menu()
        nb = ttk.Notebook(self)
        self.nb = nb
        nb.pack(fill="both", expand=True)
        self.lexer_tab = self._build_lexer_tab(nb)
        self.parser_tab = self._build_parser_tab(nb)
        nb.add(self.lexer_tab, text="Lexer")
        nb.add(self.parser_tab, text="Parser")
        self.sema_tab = self._build_semantics_tab(nb)
        nb.add(self.sema_tab, text="Semântica")
        self.ir_tab = self._build_ir_tab(nb)
        nb.add(self.ir_tab, text="IR/TAC")
        self.codegen_tab = self._build_codegen_tab(nb)
        nb.add(self.codegen_tab, text="Codegen")
        self.opt_tab = self._build_opt_tab(nb)
        nb.add(self.opt_tab, text="Otimização")
        self.sim_tab = self._build_sim_tab(nb)
        nb.add(self.sim_tab, text="Simulador")
        self.automata_tab = self._build_automata_tab(nb)
        nb.add(self.automata_tab, text="Autômatos")
        self.cfg_tab = self._build_cfg_tab(nb)
        nb.add(self.cfg_tab, text="CFG/Grafos")
        self.project_tab = self._build_project_tab(nb)
        nb.add(self.project_tab, text="Projeto")

    # ===== Lexer =====
    def _build_lexer_tab(self, parent):
        frame = ttk.Frame(parent)
        top = ttk.Frame(frame)
        top.pack(fill="x", padx=8, pady=6)

        ttk.Label(top, text="Entrada:").pack(side="left")
        self.lex_input = tk.Text(frame, height=8)
        self.lex_input.pack(fill="x", padx=8)

        btns = ttk.Frame(frame)
        btns.pack(fill="x", padx=8, pady=6)
        ttk.Button(btns, text="Rodar Lexer (Lab 02)", command=self.run_lexer).pack(side="left")
        ttk.Button(btns, text="Limpar", command=lambda: self.lex_output.delete('1.0','end')).pack(side="left", padx=6)
        ttk.Button(btns, text="Exemplo 1", command=self.fill_lexer_example).pack(side="right")
        ttk.Button(btns, text="Exemplo 2", command=self.fill_lexer_example2).pack(side="right", padx=6)

        self.lex_output = tk.Text(frame, height=20)
        self.lex_output.pack(fill="both", expand=True, padx=8, pady=6)
        self.lex_output.insert('end', "Carregue Lab 02 ou use o template padrão.\n")
        return frame

    def _build_menu(self):
        m = tk.Menu(self)
        # Exemplos
        exm = tk.Menu(m, tearoff=0)
        self._examples_gram = tk.Menu(exm, tearoff=0)
        self._populate_grammar_examples(self._examples_gram)
        exm.add_cascade(label='Gramáticas', menu=self._examples_gram)
        # Submenu separado para exemplos simples
        self._examples_simple = tk.Menu(exm, tearoff=0)
        self._populate_simple_examples(self._examples_simple)
        exm.add_cascade(label='Exemplos Simples', menu=self._examples_simple)
        self._examples_regex = tk.Menu(exm, tearoff=0)
        self._populate_regex_examples(self._examples_regex)
        exm.add_cascade(label='Regex (bank)', menu=self._examples_regex)
        m.add_cascade(label='Exemplos', menu=exm)
        # Aulas (prefills)
        lessons = tk.Menu(m, tearoff=0)
        lessons.add_command(label='Aula 1 — Introdução', command=lambda: self._select_lesson(1))
        lessons.add_command(label='Aula 2 — Léxica', command=lambda: self._select_lesson(2))
        lessons.add_command(label='Aula 3 — Gramáticas', command=lambda: self._select_lesson(3))
        lessons.add_command(label='Aula 4 — LL(1)', command=lambda: self._select_lesson(4))
        lessons.add_command(label='Aula 5 — SLR/LR', command=lambda: self._select_lesson(5))
        lessons.add_command(label='Aula 6 — Semântica', command=lambda: self._select_lesson(6))
        lessons.add_command(label='Aula 7 — IR/TAC', command=lambda: self._select_lesson(7))
        lessons.add_command(label='Aula 8 — Codegen', command=lambda: self._select_lesson(8))
        lessons.add_command(label='Aula 9 — Otimização', command=lambda: self._select_lesson(9))
        lessons.add_command(label='Aula 10 — Back-end', command=lambda: self._select_lesson(10))
        lessons.add_command(label='Aula 11 — Autômatos', command=lambda: self._select_lesson(11))
        lessons.add_command(label='Aula 12 — Grafos', command=lambda: self._select_lesson(12))
        lessons.add_separator()
        lessons.add_command(label='Aula 13 — Projeto (integração)', command=lambda: self._select_lesson(13))
        lessons.add_command(label='Aula 14 — Projeto (integração)', command=lambda: self._select_lesson(14))
        m.add_cascade(label='Aulas', menu=lessons)
        # Aulas (auto)
        lessons_auto = tk.Menu(m, tearoff=0)
        lessons_auto.add_command(label='Aula 1 — (auto)', command=lambda: self._select_lesson(1, True))
        lessons_auto.add_command(label='Aula 2 — (auto)', command=lambda: self._select_lesson(2, True))
        lessons_auto.add_command(label='Aula 3 — (auto)', command=lambda: self._select_lesson(3, True))
        lessons_auto.add_command(label='Aula 4 — (auto)', command=lambda: self._select_lesson(4, True))
        lessons_auto.add_command(label='Aula 5 — (auto)', command=lambda: self._select_lesson(5, True))
        lessons_auto.add_command(label='Aula 6 — (auto)', command=lambda: self._select_lesson(6, True))
        lessons_auto.add_command(label='Aula 7 — (auto)', command=lambda: self._select_lesson(7, True))
        lessons_auto.add_command(label='Aula 8 — (auto)', command=lambda: self._select_lesson(8, True))
        lessons_auto.add_command(label='Aula 9 — (auto)', command=lambda: self._select_lesson(9, True))
        lessons_auto.add_command(label='Aula 10 — (auto)', command=lambda: self._select_lesson(10, True))
        lessons_auto.add_command(label='Aula 11 — (auto)', command=lambda: self._select_lesson(11, True))
        lessons_auto.add_command(label='Aula 12 — (auto)', command=lambda: self._select_lesson(12, True))
        lessons_auto.add_separator()
        lessons_auto.add_command(label='Aula 13 — Projeto (auto)', command=lambda: self._select_lesson(13, True))
        lessons_auto.add_command(label='Aula 14 — Projeto (auto)', command=lambda: self._select_lesson(14, True))
        m.add_cascade(label='Aulas (auto)', menu=lessons_auto)
        # Cenas (salvar/carregar)
        scenes = tk.Menu(m, tearoff=0)
        scenes.add_command(label='Salvar cena...', command=self.save_scene)
        scenes.add_command(label='Carregar cena...', command=lambda: self.load_scene(False))
        scenes.add_command(label='Carregar cena (auto)...', command=lambda: self.load_scene(True))
        m.add_cascade(label='Cenas', menu=scenes)
        # Ajuda
        helpm = tk.Menu(m, tearoff=0)
        def show_help():
            win = tk.Toplevel(self)
            win.title('Ajuda — Guia Rápido')
            txt = tk.Text(win, width=100, height=30)
            txt.pack(fill='both', expand=True)
            txt.insert('end', (
                'Parser:\n'
                '- Selecione gramática (.txt), entrada e método (LL/SLR/LALR/LR).\n'
                '- Use auto-lex para entradas sem espaços.\n'
                '- Exporte árvores em SVG/JSON; use “Comparar” para ver métodos lado a lado.\n'
                '- Atalhos: Ctrl+E (Executar), Ctrl+G (Abrir gramática), Ctrl+S (Export SVG), Ctrl+J (Export JSON), Ctrl+C (Comparar).\n\n'
                'Semântica:\n'
                '- Importe árvore do Parser ou JSON para AST; ajuste regras de tipo e analise.\n'
                '- Envie para IR/TAC e siga para Otimização, Codegen e Simulador.\n'
                '- Atalhos: Ctrl+I (Importar árvore do Parser), Ctrl+Y (Analisar tipos).\n\n'
                'Autômatos:\n'
                '- Digite a regex ou carregue exemplos; construa NFA/DFA e minimize.\n'
                '- Navegue passos (Subset/Minimização); alterne NFA/DFA no canvas.\n'
                '- Exporte em SVG/DOT. Atalhos: Ctrl+B (Construir), Ctrl+T (Testar).\n\n'
                'Atalhos:\n'
                '- Exportar e comparação ficam nos botões de cada aba.\n'
            ))
            txt.configure(state='disabled')
        helpm.add_command(label='Guia Rápido', command=show_help)
        m.add_cascade(label='Ajuda', menu=helpm)
        self.config(menu=m)

    def _select_lesson(self, n: int, auto: bool = False):
        try:
            # Helper para selecionar a aba
            def goto(tab):
                try:
                    self.nb.select(tab)
                except Exception:
                    pass
            if n == 1:
                # Introdução: parser expr
                self.fill_parser_example(); goto(self.parser_tab)
                if auto:
                    self.run_parser()
            elif n == 2:
                # Léxica
                self.fill_lexer_example(); goto(self.lexer_tab)
                if auto:
                    self.run_lexer()
            elif n == 3:
                # Gramáticas: expr com tabelas
                self.fill_parser_example(); self.method.set('both'); self.var_tables.set(True); goto(self.parser_tab)
                if auto:
                    self.run_parser()
            elif n == 4:
                # LL(1): expr com LL e tabelas
                self.fill_parser_example(); self.method.set('ll1'); self.var_tables.set(True); goto(self.parser_tab)
                if auto:
                    self.run_parser()
            elif n == 5:
                # SLR/LR: dangling else para ver conflitos
                self.fill_parser_example_dangling(); self.var_items.set(True); self.var_tables.set(True); goto(self.parser_tab)
                if auto:
                    self.run_parser()
            elif n == 6:
                # Semântica
                self.fill_sema_example(); goto(self.sema_tab)
                if auto:
                    self.run_semantics()
            elif n == 7:
                # IR/TAC
                self.fill_ir_example(); goto(self.ir_tab)
                if auto:
                    self.run_tac()
            elif n == 8:
                # Codegen + regalloc spill
                self.fill_codegen_example_spill(); self.var_regalloc.set(True); self.reg_k.set(2); goto(self.codegen_tab)
                if auto:
                    self.run_codegen()
            elif n == 9:
                # Otimização
                self.fill_opt_example(); goto(self.opt_tab)
                if auto:
                    self.run_fold(); self.run_dce()
            elif n == 10:
                # Back-end
                self.fill_sim_example2(); goto(self.sim_tab)
                if auto:
                    self.run_sim()
            elif n == 11:
                # Autômatos
                self.fill_automata_example(); goto(self.automata_tab)
                if auto:
                    self.build_automata(); self.test_automata()
            elif n == 12:
                # Grafos/CFG
                self.fill_cfg_example2(); goto(self.cfg_tab)
                if auto:
                    self.run_cfg(); self.run_liveness(); self.run_intervals()
            elif n in (13, 14):
                goto(self.project_tab)
                try:
                    messagebox.showinfo('Projeto', 'Veja CURSO.md e a aba Projeto para integrar Léxico→Sintaxe→Semântica→IR→Otim.→Codegen→Back-end.')
                except Exception:
                    pass
        except Exception:
            pass

    def save_scene(self):
        try:
            import json
            from tkinter import filedialog, messagebox
            scene = {
                'active_tab': self.nb.index(self.nb.select()) if hasattr(self,'nb') else 0,
                # Parser
                'parser': {
                    'grammar_path': self.grammar_path.get() if hasattr(self,'grammar_path') else '',
                    'input': self.input_str.get() if hasattr(self,'input_str') else '',
                    'method': self.method.get() if hasattr(self,'method') else 'both',
                    'auto_lex': bool(self.var_auto.get()) if hasattr(self,'var_auto') else False,
                    'trace': bool(self.var_trace.get()) if hasattr(self,'var_trace') else True,
                    'tables': bool(self.var_tables.get()) if hasattr(self,'var_tables') else True,
                    'items': bool(self.var_items.get()) if hasattr(self,'var_items') else False,
                    'output': self.out_text.get('1.0','end') if hasattr(self,'out_text') else '',
                },
                # Semantics
                'sema': {
                    'text': self.sema_input.get('1.0','end') if hasattr(self,'sema_input') else '',
                    'arith_bool': bool(self.var_arith_bool.get()) if hasattr(self,'var_arith_bool') else False,
                    'eq_same': bool(self.var_eq_same.get()) if hasattr(self,'var_eq_same') else True,
                    'output': self.sema_output.get('1.0','end') if hasattr(self,'sema_output') else '',
                },
                # Codegen
                'codegen': {
                    'regalloc': bool(self.var_regalloc.get()) if hasattr(self,'var_regalloc') else False,
                    'k': int(self.reg_k.get()) if hasattr(self,'reg_k') else 3,
                    'output': self.codegen_output.get('1.0','end') if hasattr(self,'codegen_output') else '',
                },
                # Automata
                'auto': {
                    'regex': self.re_input.get() if hasattr(self,'re_input') else '',
                    'test': self.re_test.get() if hasattr(self,'re_test') else '',
                    'view': self.auto_view.get() if hasattr(self,'auto_view') else 'dfa',
                    'output': self.auto_output.get('1.0','end') if hasattr(self,'auto_output') else '',
                },
                # CFG
                'cfg': {
                    'code': self.cfg_input.get('1.0','end') if hasattr(self,'cfg_input') else '',
                    'output': self.cfg_output.get('1.0','end') if hasattr(self,'cfg_output') else '',
                },
                # IR/TAC, Otimização e Simulador
                'ir': {
                    'output': self.ir_output.get('1.0','end') if hasattr(self,'ir_output') else '',
                },
                'opt': {
                    'output': self.opt_output.get('1.0','end') if hasattr(self,'opt_output') else '',
                },
                'sim': {
                    'output': self.sim_output.get('1.0','end') if hasattr(self,'sim_output') else '',
                },
                # pipeline artifacts (tac/asm/mapping)
                'pipeline': {
                    'tac': [[op, list(args)] for (op, args) in (self.tac_list or [])] if hasattr(self,'tac_list') and self.tac_list else [],
                    'asm': [[op, list(args)] for (op, args) in (self.asm_prog or [])] if hasattr(self,'asm_prog') and self.asm_prog else [],
                    'regmap': dict(self.last_regalloc_map) if hasattr(self,'last_regalloc_map') and self.last_regalloc_map else {},
                }
            }
            path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
            if not path:
                return
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(scene, f, ensure_ascii=False, indent=2)
            try:
                messagebox.showinfo('OK', 'Cena salva.')
            except Exception:
                pass
        except Exception as e:
            try:
                messagebox.showerror('Erro', f'Falha ao salvar cena: {e}')
            except Exception:
                pass

    def load_scene(self, auto: bool = False):
        try:
            import json
            from tkinter import filedialog, messagebox
            path = filedialog.askopenfilename(filetypes=[('JSON','*.json'),('All','*.*')])
            if not path:
                return
            with open(path, 'r', encoding='utf-8') as f:
                scene = json.load(f)
            # Parser
            p = scene.get('parser', {})
            if hasattr(self,'grammar_path'): self.grammar_path.set(p.get('grammar_path',''))
            if hasattr(self,'input_str'): self.input_str.set(p.get('input',''))
            if hasattr(self,'method'): self.method.set(p.get('method','both'))
            if hasattr(self,'var_auto'): self.var_auto.set(bool(p.get('auto_lex', False)))
            if hasattr(self,'var_trace'): self.var_trace.set(bool(p.get('trace', True)))
            if hasattr(self,'var_tables'): self.var_tables.set(bool(p.get('tables', True)))
            if hasattr(self,'var_items'): self.var_items.set(bool(p.get('items', False)))
            if hasattr(self,'out_text'):
                self.out_text.delete('1.0','end'); self.out_text.insert('end', p.get('output',''))
            # Semantics
            s = scene.get('sema', {})
            if hasattr(self,'sema_input'):
                self.sema_input.delete('1.0','end'); self.sema_input.insert('end', s.get('text',''))
            if hasattr(self,'var_arith_bool'): self.var_arith_bool.set(bool(s.get('arith_bool', False)))
            if hasattr(self,'var_eq_same'): self.var_eq_same.set(bool(s.get('eq_same', True)))
            if hasattr(self,'sema_output'):
                self.sema_output.delete('1.0','end'); self.sema_output.insert('end', s.get('output',''))
            # Codegen
            c = scene.get('codegen', {})
            if hasattr(self,'var_regalloc'): self.var_regalloc.set(bool(c.get('regalloc', False)))
            if hasattr(self,'reg_k'):
                try:
                    self.reg_k.set(int(c.get('k', 3)))
                except Exception:
                    pass
            if hasattr(self,'codegen_output'):
                self.codegen_output.delete('1.0','end'); self.codegen_output.insert('end', c.get('output',''))
            # Automata
            a = scene.get('auto', {})
            if hasattr(self,'re_input'):
                self.re_input.delete(0,'end'); self.re_input.insert(0, a.get('regex',''))
            if hasattr(self,'re_test'):
                self.re_test.delete(0,'end'); self.re_test.insert(0, a.get('test',''))
            if hasattr(self,'auto_view'):
                try:
                    self.auto_view.set(a.get('view','dfa'))
                except Exception:
                    pass
            if hasattr(self,'auto_output'):
                self.auto_output.delete('1.0','end'); self.auto_output.insert('end', a.get('output',''))
            # CFG
            cfg = scene.get('cfg', {})
            if hasattr(self,'cfg_input'):
                self.cfg_input.delete('1.0','end'); self.cfg_input.insert('end', cfg.get('code',''))
            if hasattr(self,'cfg_output'):
                self.cfg_output.delete('1.0','end'); self.cfg_output.insert('end', cfg.get('output',''))
            # IR/OPT/SIM outputs
            irs = scene.get('ir', {})
            if hasattr(self,'ir_output'):
                self.ir_output.delete('1.0','end'); self.ir_output.insert('end', irs.get('output',''))
            opts = scene.get('opt', {})
            if hasattr(self,'opt_output'):
                self.opt_output.delete('1.0','end'); self.opt_output.insert('end', opts.get('output',''))
            sims = scene.get('sim', {})
            if hasattr(self,'sim_output'):
                self.sim_output.delete('1.0','end'); self.sim_output.insert('end', sims.get('output',''))
            # pipeline
            pipe = scene.get('pipeline', {})
            try:
                self.tac_list = [(op, tuple(args)) for op, args in pipe.get('tac', [])]
            except Exception:
                self.tac_list = None
            try:
                self.asm_prog = [(op, tuple(args)) for op, args in pipe.get('asm', [])]
            except Exception:
                self.asm_prog = None
            try:
                self.last_regalloc_map = dict(pipe.get('regmap', {})) or None
            except Exception:
                self.last_regalloc_map = None
            # Active tab
            try:
                idx = int(scene.get('active_tab', 0))
                self.nb.select(idx)
            except Exception:
                pass
            try:
                messagebox.showinfo('OK', 'Cena carregada.')
            except Exception:
                pass
            # Auto-run pipeline com seleção de ações, se solicitado
            if auto:
                actions = None
                try:
                    actions = self._choose_auto_actions()
                except Exception:
                    actions = None
                if not actions:
                    return
                try:
                    if actions.get('parser') and p.get('grammar_path'):
                        self.run_parser()
                except Exception:
                    pass
                try:
                    if actions.get('semantics') and s.get('text'):
                        self.run_semantics()
                except Exception:
                    pass
                try:
                    if actions.get('tac') and self.sema_input.get('1.0','end').strip():
                        self.run_tac()
                except Exception:
                    pass
                try:
                    if actions.get('codegen') and self.tac_list:
                        self.run_codegen()
                except Exception:
                    pass
                try:
                    if actions.get('sim') and self.asm_prog:
                        self.run_sim()
                except Exception:
                    pass
                try:
                    if actions.get('auto_build') and a.get('regex'):
                        self.build_automata()
                    if actions.get('auto_test') and a.get('regex') and a.get('test'):
                        self.test_automata()
                except Exception:
                    pass
                try:
                    if cfg.get('code'):
                        if actions.get('cfg'):
                            self.run_cfg()
                        if actions.get('liveness'):
                            self.run_liveness()
                        if actions.get('intervals'):
                            self.run_intervals()
                except Exception:
                    pass
        except Exception as e:
            try:
                messagebox.showerror('Erro', f'Falha ao carregar cena: {e}')
            except Exception:
                pass

    def _choose_auto_actions(self):
        # Janela modal com checkboxes de quais etapas auto-executar
        top = tk.Toplevel(self)
        top.title('Ações ao carregar cena')
        top.transient(self)
        try:
            top.grab_set()
        except Exception:
            pass
        vars_ = {
            'parser': tk.BooleanVar(value=True),
            'semantics': tk.BooleanVar(value=True),
            'tac': tk.BooleanVar(value=True),
            'codegen': tk.BooleanVar(value=True),
            'sim': tk.BooleanVar(value=True),
            'auto_build': tk.BooleanVar(value=True),
            'auto_test': tk.BooleanVar(value=True),
            'cfg': tk.BooleanVar(value=True),
            'liveness': tk.BooleanVar(value=True),
            'intervals': tk.BooleanVar(value=True),
        }
        ttk.Label(top, text='Selecione as ações a executar:').pack(anchor='w', padx=10, pady=6)
        box = ttk.Frame(top); box.pack(padx=10, pady=4)
        left = ttk.Frame(box); left.pack(side='left', padx=8)
        right = ttk.Frame(box); right.pack(side='left', padx=8)
        ttk.Checkbutton(left, text='Parser', variable=vars_['parser']).pack(anchor='w')
        ttk.Checkbutton(left, text='Semântica', variable=vars_['semantics']).pack(anchor='w')
        ttk.Checkbutton(left, text='Gerar TAC', variable=vars_['tac']).pack(anchor='w')
        ttk.Checkbutton(left, text='Codegen', variable=vars_['codegen']).pack(anchor='w')
        ttk.Checkbutton(left, text='Simulador', variable=vars_['sim']).pack(anchor='w')
        ttk.Checkbutton(right, text='Autômatos: Construir', variable=vars_['auto_build']).pack(anchor='w')
        ttk.Checkbutton(right, text='Autômatos: Testar', variable=vars_['auto_test']).pack(anchor='w')
        ttk.Checkbutton(right, text='CFG: Gerar', variable=vars_['cfg']).pack(anchor='w')
        ttk.Checkbutton(right, text='CFG: Vivacidade', variable=vars_['liveness']).pack(anchor='w')
        ttk.Checkbutton(right, text='CFG: Intervalos', variable=vars_['intervals']).pack(anchor='w')
        buttons = ttk.Frame(top); buttons.pack(fill='x', padx=10, pady=8)
        result = {'ok': False}
        def ok():
            result['ok'] = True
            top.destroy()
        def cancel():
            result['ok'] = False
            top.destroy()
        ttk.Button(buttons, text='OK', command=ok).pack(side='right')
        ttk.Button(buttons, text='Cancelar', command=cancel).pack(side='right', padx=6)
        try:
            self.wait_window(top)
        except Exception:
            pass
        if not result.get('ok'):
            return None
        return {k: bool(v.get()) for k, v in vars_.items()}

    def _populate_grammar_examples(self, menu: tk.Menu):
        # Lista alguns arquivos .txt conhecidos e dos exercícios
        examples = []
        def add(path, label=None, input_str=''):
            if os.path.isfile(path):
                examples.append((path, label or os.path.basename(path), input_str))
        add(os.path.join(BASE_DIR, 'expr.txt'), 'expr.txt', 'id + id * id')
        add(os.path.join(BASE_DIR, 'if_else.txt'), 'if_else.txt', 'if id then id=id else id=id')
        exdir = os.path.join(BASE_DIR, 'exercicios')
        if os.path.isdir(exdir):
            mapping = {
                'ex3_fatoracao_antes.txt': 'id ( id , id )',
                'ex3_fatoracao_depois.txt': 'id ( id , id )',
                'ex4_rec_esq_antes.txt': 'id + id * id',
                'ex4_rec_esq_depois.txt': 'id + id * id',
                'ex5_ambigua_antes.txt': 'id + id * id',
                'ex5_ambigua_prec.txt': 'id + id * id',
                'ex2_else_com.txt': 'if id then id=id else id=id',
                'ex2_else_sem.txt': 'if id then id=id else id=id',
                'ex2_assign_only_slr.txt': 'id = id',
            }
            for fname, inp in mapping.items():
                add(os.path.join(exdir, fname), fname, inp)
        # preencher menu
        menu.delete(0, 'end')
        for path, label, inp in examples:
            menu.add_command(label=label, command=lambda p=path, i=inp: self._apply_grammar_example(p, i))

    def _populate_simple_examples(self, menu: tk.Menu):
        # Submenu com os exemplos simples do diretório exemplos_simples
        try:
            items = []
            def add(label: str, path: str, inp: str):
                if os.path.isfile(path):
                    items.append((label, path, inp))
            sdir = os.path.join(BASE_DIR, 'exemplos_simples')
            mapping = [
                ('01 — mínimo (S->id)', '01_min.txt', 'id'),
                ('02 — parênteses', '02_paren.txt', '( id )'),
                ('03 — soma/prod LL(1)', '03_sum_ll1.txt', 'id + id * id'),
                ('04 — atribuição (SLR)', '04_assign_slr.txt', 'id = id'),
            ]
            for label, fname, inp in mapping:
                add(label, os.path.join(sdir, fname), inp)
            menu.delete(0, 'end')
            for label, path, inp in items:
                menu.add_command(label=label, command=lambda p=path, i=inp: self._apply_grammar_example(p, i))
        except Exception:
            pass

    def _apply_grammar_example(self, path: str, input_str: str):
        self.grammar_path.set(path)
        if input_str:
            self.input_str.set(input_str)
        # heurística: ativa auto-lex para if_else e para entradas sem espaços
        if 'if_else' in os.path.basename(path) or (input_str and ' ' not in input_str):
            self.var_auto.set(True)
        else:
            self.var_auto.set(False)

    def _populate_regex_examples(self, menu: tk.Menu):
        # Carrega examples do regex_bank e cria itens
        try:
            bank_path = os.path.join(BASE_DIR, 'labs', '11_automatos', 'regex_bank.txt')
            items = []
            if os.path.isfile(bank_path):
                with open(bank_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if not s or s.startswith('#'):
                            continue
                        parts = [p.strip() for p in s.split(';')]
                        regex = parts[0]
                        acc = parts[1] if len(parts) > 1 else ''
                        test = acc.split(',')[0].strip() if acc else ''
                        items.append((regex, test))
            menu.delete(0, 'end')
            for regex, test in items:
                menu.add_command(label=regex, command=lambda r=regex, t=test: self._apply_regex_example(r, t))
        except Exception:
            pass

    def _apply_regex_example(self, regex: str, test: str):
        if hasattr(self, 're_input'):
            self.re_input.delete(0, 'end'); self.re_input.insert(0, regex)
        if hasattr(self, 're_test'):
            self.re_test.delete(0, 'end');
            if test:
                self.re_test.insert(0, test)

    def _load_settings(self):
        try:
            import json
            if os.path.isfile(self._settings_path):
                with open(self._settings_path,'r',encoding='utf-8') as f:
                    self._settings = json.load(f)
        except Exception:
            self._settings = {}

    def _save_settings(self):
        try:
            import json
            s = {
                'grammar_path': self.grammar_path.get(),
                'parser_method': self.method.get(),
                'parser_auto_lex': bool(self.var_auto.get()),
                'parser_trace': bool(self.var_trace.get()),
                'parser_tables': bool(self.var_tables.get()),
                'parser_items': bool(self.var_items.get()),
                'sem_arith_bool': bool(self.var_arith_bool.get()) if hasattr(self,'var_arith_bool') else False,
                'sem_eq_same': bool(self.var_eq_same.get()) if hasattr(self,'var_eq_same') else True,
                'regex_last': self.re_input.get() if hasattr(self,'re_input') else '',
                'regex_test_last': self.re_test.get() if hasattr(self,'re_test') else '',
                'auto_view': self.auto_view.get() if hasattr(self,'auto_view') else 'dfa',
                'codegen_regalloc': bool(self.var_regalloc.get()) if hasattr(self,'var_regalloc') else False,
                'codegen_k': int(self.reg_k.get()) if hasattr(self,'reg_k') else 3,
            }
            with open(self._settings_path,'w',encoding='utf-8') as f:
                json.dump(s,f,ensure_ascii=False,indent=2)
        except Exception:
            pass

    def _on_close(self):
        self._save_settings()
        self.destroy()

    def run_lexer(self):
        text = self.lex_input.get('1.0', 'end').rstrip('\n')
        self.lex_output.delete('1.0', 'end')
        try:
            if lexer_template and hasattr(lexer_template, 'lex'):
                tokens = lexer_template.lex(text)
                for t in tokens:
                    self.lex_output.insert('end', f"{t.kind:<10} {t.lexeme!r}\n")
            else:
                # fallback simples: separa por espaço
                for i, tok in enumerate([t for t in text.split() if t]):
                    self.lex_output.insert('end', f"TOK{ i:03d }: {tok}\n")
        except Exception as e:
            self.lex_output.insert('end', f"Erro: {e}\n")

    def fill_lexer_example(self):
        try:
            example = "# Exemplo de entrada para o lexer\nif x then y = 3\nz = y + 4\n"
            self.lex_input.delete('1.0','end')
            self.lex_input.insert('end', example)
            self.lex_output.delete('1.0','end')
            self.lex_output.insert('end', 'Exemplo preenchido. Clique em "Rodar Lexer".\n')
        except Exception as e:
            self.lex_output.insert('end', f"Erro ao preencher exemplo: {e}\n")

    def fill_lexer_example2(self):
        try:
            example = """# Exemplo com comentários e números
// linha de comentário
if total == 10 then count = count + 1
/* bloco
 de comentário */
msg = num
"""
            self.lex_input.delete('1.0','end')
            self.lex_input.insert('end', example)
            self.lex_output.delete('1.0','end')
            self.lex_output.insert('end', 'Exemplo 2 preenchido. Clique em "Rodar Lexer".\n')
        except Exception as e:
            self.lex_output.insert('end', f"Erro ao preencher exemplo 2: {e}\n")

    # ===== Parser =====
    def _build_parser_tab(self, parent):
        frame = ttk.Frame(parent)
        # Controls
        controls = ttk.LabelFrame(frame, text="Config")
        controls.pack(fill="x", padx=8, pady=6)

        # Grammar file
        gf = ttk.Frame(controls)
        gf.pack(fill="x", pady=4)
        ttk.Label(gf, text="Gramática:").pack(side="left")
        self.grammar_path = tk.StringVar()
        e = ttk.Entry(gf, textvariable=self.grammar_path)
        e.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(gf, text="Abrir...", command=self._browse_grammar).pack(side="left")

        # Input
        inf = ttk.Frame(controls)
        inf.pack(fill="x", pady=4)
        ttk.Label(inf, text="Entrada:").pack(side="left")
        self.input_str = tk.StringVar()
        ei = ttk.Entry(inf, textvariable=self.input_str)
        ei.pack(side="left", fill="x", expand=True, padx=6)
        self.var_auto = tk.BooleanVar(value=False)
        ttk.Checkbutton(inf, text="auto-lex", variable=self.var_auto).pack(side="left")

        # Options
        opts = ttk.Frame(controls)
        opts.pack(fill="x", pady=4)
        ttk.Label(opts, text="Método:").pack(side="left")
        self.method = tk.StringVar(value="both")
        ttk.Radiobutton(opts, text="LL(1)", value="ll1", variable=self.method).pack(side="left")
        ttk.Radiobutton(opts, text="SLR(1)", value="slr1", variable=self.method).pack(side="left")
        ttk.Radiobutton(opts, text="LALR(1)", value="lalr1", variable=self.method).pack(side="left")
        ttk.Radiobutton(opts, text="LR(1)", value="lr1", variable=self.method).pack(side="left")
        ttk.Radiobutton(opts, text="Todos", value="all", variable=self.method).pack(side="left")
        self.var_trace = tk.BooleanVar(value=True)
        self.var_tables = tk.BooleanVar(value=True)
        self.var_items = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="trace", variable=self.var_trace).pack(side="left", padx=(12,0))
        ttk.Checkbutton(opts, text="tabelas", variable=self.var_tables).pack(side="left")
        ttk.Checkbutton(opts, text="itens LR(0)", variable=self.var_items).pack(side="left")

        # Actions
        actions = ttk.Frame(frame)
        actions.pack(fill="x", padx=8)
        ttk.Button(actions, text="Executar", command=self.run_parser).pack(side="left")
        ttk.Button(actions, text="Ver Árvore(s)", command=self.show_trees).pack(side="left", padx=6)
        ttk.Button(actions, text="Exportar SVG...", command=self.export_svg).pack(side="left")
        ttk.Button(actions, text="Exportar JSON...", command=self.export_json).pack(side="left", padx=6)
        ttk.Button(actions, text="Comparar (lado a lado)", command=self.compare_trees).pack(side="left")
        ttk.Button(actions, text="Exemplo expr", command=self.fill_parser_example).pack(side="right")
        ttk.Button(actions, text="Exemplo if-else", command=self.fill_parser_example_ifelse).pack(side="right", padx=6)
        ttk.Button(actions, text="Exemplo resolvido (%Right else)", command=self.fill_parser_example_else_resolved).pack(side="right")
        ttk.Button(actions, text="Exemplo dangling else", command=self.fill_parser_example_dangling).pack(side="right", padx=6)

        # Dica didática rápida
        ttk.Label(frame, text="Dica: use os exemplos 'dangling else' e 'resolvido' para comparar conflitos no SLR (ACTION/GOTO). Marque 'tabelas' e 'itens LR(0)' para ver detalhes; use 'Comparar' para árvores/derivações.").pack(anchor='w', padx=8, pady=(4,0))

        # Output
        self.out_text = tk.Text(frame)
        self.out_text.pack(fill="both", expand=True, padx=8, pady=6)

        # Store last results
        self.result_ll1 = None
        self.result_slr = None
        self.result_lalr = None
        self.result_lr1 = None
        self.last_grammar = None
        return frame

    def _browse_grammar(self):
        path = filedialog.askopenfilename(title="Selecione a gramática", filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if path:
            self.grammar_path.set(path)

    def fill_parser_example(self):
        try:
            expr = os.path.join(BASE_DIR, 'expr.txt')
            if os.path.isfile(expr):
                self.grammar_path.set(expr)
            self.input_str.set('id + id * id')
            self.var_auto.set(False)
            self.method.set('both')
            self.out_text.delete('1.0','end')
            self.out_text.insert('end', 'Exemplo preenchido. Clique em "Executar".\n')
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao preencher exemplo: {e}')

    def fill_parser_example_ifelse(self):
        try:
            g = os.path.join(BASE_DIR, 'if_else.txt')
            if os.path.isfile(g):
                self.grammar_path.set(g)
            self.input_str.set('if id then id=id else id=id')
            self.var_auto.set(True)
            self.method.set('slr1')
            self.out_text.delete('1.0','end')
            self.out_text.insert('end', 'Exemplo if-else preenchido. Clique em "Executar".\n')
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao preencher exemplo if-else: {e}')

    def fill_parser_example_dangling(self):
        try:
            g = os.path.join(BASE_DIR, 'exercicios', 'ex2_else_sem.txt')
            if os.path.isfile(g):
                self.grammar_path.set(g)
            else:
                # fallback: usa if_else.txt como aproximação
                self.grammar_path.set(os.path.join(BASE_DIR, 'if_else.txt'))
            self.input_str.set('if id then id=id else id=id')
            self.var_auto.set(True)
            self.method.set('slr1')
            self.out_text.delete('1.0','end')
            self.out_text.insert('end', 'Exemplo dangling else (sem %Right else) preenchido. Clique em "Executar" e observe conflitos.\n')
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao preencher exemplo dangling else: {e}')

    def fill_parser_example_else_resolved(self):
        try:
            g = os.path.join(BASE_DIR, 'exercicios', 'ex2_else_com.txt')
            if os.path.isfile(g):
                self.grammar_path.set(g)
            else:
                self.grammar_path.set(os.path.join(BASE_DIR, 'if_else.txt'))
            self.input_str.set('if id then id=id else id=id')
            self.var_auto.set(True)
            self.method.set('slr1')
            self.out_text.delete('1.0','end')
            self.out_text.insert('end', 'Exemplo resolvido com %Right else preenchido. Clique em "Executar" e compare com o caso sem %Right else.\n')
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao preencher exemplo resolvido: {e}')

    def run_parser(self):
        self.out_text.delete('1.0', 'end')
        gpath = self.grammar_path.get().strip()
        inp = self.input_str.get().strip()
        if not os.path.isfile(gpath):
            messagebox.showerror("Erro", "Informe um arquivo de gramática válido.")
            return
        try:
            g = Grammar.from_file(gpath)
            ff = FirstFollow(g)
            if self.var_auto.get():
                tokens = auto_lex(inp, g)
            else:
                tokens = [t for t in inp.split() if t]
            # reset stored parsers/results
            self.parsers = {}
            self.out_text.insert('end', "=== Gramática ===\n")
            self.out_text.insert('end', str(g) + "\n\n")
            self.out_text.insert('end', "=== FIRST ===\n")
            for k in sorted(ff.first.keys()):
                self.out_text.insert('end', f"FIRST({k}) = {{ {', '.join(sorted(ff.first[k]))} }}\n")
            self.out_text.insert('end', "=== FOLLOW ===\n")
            for k in sorted(ff.follow.keys()):
                self.out_text.insert('end', f"FOLLOW({k}) = {{ {', '.join(sorted(ff.follow[k]))} }}\n")
            self.out_text.insert('end', "\n")

            self.result_ll1 = None
            self.result_slr = None
            method = self.method.get()
            if method in ("ll1", "both", "all"):
                self.out_text.insert('end', "=== LL(1) ===\n")
                ll1 = LL1Parser(g, ff)
                if self.var_tables.get():
                    # print only non-empty entries
                    keys = sorted(g.terminals | {'$'})
                    self.out_text.insert('end', "LL(1) Parse Table (non-empty entries):\n")
                    for A in sorted(g.nonterminals):
                        for a in keys:
                            if a in ll1.table.get(A, {}):
                                prod = ll1.table[A][a]
                                rhs = 'ε' if prod == ['ε'] else (prod[0] if prod == ['ε'] else (' '.join(prod)))
                                self.out_text.insert('end', f"  M[{A}, {a}] = {rhs}\n")
                self.result_ll1 = ll1.parse(tokens, trace=self.var_trace.get())
                self.parsers['LL(1)'] = ll1
                self.out_text.insert('end', f"Resultado LL(1): {'ACEITA' if self.result_ll1.ok else 'REJEITA'}\n\n")

            if method in ("slr1", "both", "all"):
                self.out_text.insert('end', "=== SLR(1) ===\n")
                slr = SLR1Parser(g, ff)
                if self.var_tables.get() or self.var_items.get():
                    from io import StringIO
                    buf = StringIO()
                    # Reutiliza print_tables do SLR
                    slr.print_tables(show_items=self.var_items.get())
                self.result_slr = slr.parse(tokens, trace=self.var_trace.get())
                self.parsers['SLR(1)'] = slr
                self.out_text.insert('end', f"Resultado SLR(1): {'ACEITA' if self.result_slr.ok else 'REJEITA'}\n\n")

            if method in ("lalr1", "all"):
                self.out_text.insert('end', "=== LALR(1) ===\n")
                from parsing_tester import LR1Parser
                lalr = LR1Parser(g, ff, mode='lalr1')
                if self.var_tables.get() or self.var_items.get():
                    lalr.print_tables(show_items=self.var_items.get())
                self.result_lalr = lalr.parse(tokens, trace=self.var_trace.get())
                self.parsers['LALR(1)'] = lalr
                self.out_text.insert('end', f"Resultado LALR(1): {'ACEITA' if self.result_lalr.ok else 'REJEITA'}\n\n")

            if method in ("lr1", "all"):
                self.out_text.insert('end', "=== LR(1) ===\n")
                from parsing_tester import LR1Parser
                lr1 = LR1Parser(g, ff, mode='lr1')
                if self.var_tables.get() or self.var_items.get():
                    lr1.print_tables(show_items=self.var_items.get())
                self.result_lr1 = lr1.parse(tokens, trace=self.var_trace.get())
                self.parsers['LR(1)'] = lr1
                self.out_text.insert('end', f"Resultado LR(1): {'ACEITA' if self.result_lr1.ok else 'REJEITA'}\n\n")

            self.last_grammar = g
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def show_trees(self):
        trees = []
        if self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree is not None:
            trees.append(("LL(1)", self.result_ll1.tree, self.result_ll1.derivations, self.result_ll1.kind))
        if self.result_slr and self.result_slr.ok and self.result_slr.tree is not None:
            trees.append(("SLR(1)", self.result_slr.tree, self.result_slr.derivations, self.result_slr.kind))
        if getattr(self, 'result_lalr', None) and self.result_lalr.ok and self.result_lalr.tree is not None:
            trees.append(("LALR(1)", self.result_lalr.tree, self.result_lalr.derivations, self.result_lalr.kind))
        if getattr(self, 'result_lr1', None) and self.result_lr1.ok and self.result_lr1.tree is not None:
            trees.append(("LR(1)", self.result_lr1.tree, self.result_lr1.derivations, self.result_lr1.kind))
        if trees:
            show_trees_gui(trees)
        else:
            messagebox.showinfo("Info", "Nenhuma árvore aceita para exibir.")

    def _draw_tree_on_canvas(self, canvas: tk.Canvas, root):
        # Desenha uma árvore simples
        def compute(n):
            nodes = []
            pos = {}
            leaf_counter = [0]
            max_depth = [0]
            def dfs(x, depth):
                max_depth[0] = max(max_depth[0], depth)
                nodes.append(x)
                if not x.children:
                    i = leaf_counter[0]; leaf_counter[0]+=1
                    pos[id(x)] = (float(i), depth)
                    return float(i)
                xs=[]
                for c in x.children:
                    xs.append(dfs(c, depth+1))
                x0 = sum(xs)/len(xs) if xs else float(leaf_counter[0])
                pos[id(x)] = (x0, depth)
                return x0
            dfs(n,0)
            return pos, leaf_counter[0], max_depth[0], nodes
        pos, leafs, depth, nodes = compute(root)
        HSPACE=90; VSPACE=80; MARGIN=20
        def center(x):
            u,v = pos[id(x)]; return (u*HSPACE+MARGIN, v*VSPACE+MARGIN)
        canvas.delete('all')
        for n in nodes:
            cx,cy = center(n)
            for ch in n.children:
                x2,y2 = center(ch)
                canvas.create_line(cx, cy+12, x2, y2-12, fill='#555')
        for n in nodes:
            cx,cy = center(n)
            label = n.symbol
            w=max(36, 8*len(label)+12); h=26
            canvas.create_rectangle(cx-w/2, cy-h/2, cx+w/2, cy+h/2, fill='#e8f0fe', outline='#3b82f6')
            canvas.create_text(cx, cy, text=label)
        bbox = canvas.bbox('all')
        if bbox:
            canvas.configure(scrollregion=bbox)

    def compare_trees(self):
        trees=[]
        if self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree is not None:
            trees.append(('LL(1)', self.result_ll1.tree))
        if self.result_slr and self.result_slr.ok and self.result_slr.tree is not None:
            trees.append(('SLR(1)', self.result_slr.tree))
        if self.result_lalr and self.result_lalr.ok and self.result_lalr.tree is not None:
            trees.append(('LALR(1)', self.result_lalr.tree))
        if self.result_lr1 and self.result_lr1.ok and self.result_lr1.tree is not None:
            trees.append(('LR(1)', self.result_lr1.tree))
        if not trees:
            messagebox.showinfo('Info','Nenhuma árvore aceita para comparar.')
            return
        win = tk.Toplevel(self)
        win.title('Comparar Árvores')
        top = ttk.Frame(win)
        top.pack(fill='x', padx=8, pady=6)
        # resumo de métricas
        summary = []
        for name, parser in self.parsers.items():
            try:
                states = getattr(parser, 'states', None)
                nstates = len(states) if states is not None else '-'
                nconf = len(getattr(parser, 'conflicts', []))
                # entradas de ação ou tabela
                action_entries = None
                if hasattr(parser, 'ACTION') and isinstance(getattr(parser, 'ACTION'), dict):
                    action_entries = len(getattr(parser, 'ACTION'))
                elif hasattr(parser, 'table') and isinstance(getattr(parser, 'table'), dict):
                    action_entries = sum(len(v) for v in getattr(parser, 'table').values())
                ae = f", ações={action_entries}" if action_entries is not None else ''
                summary.append(f"{name}: estados={nstates}, conflitos={nconf}{ae}")
            except Exception:
                pass
        ttk.Label(top, text=' | '.join(summary)).pack(anchor='w')
        grid = ttk.Frame(win)
        grid.pack(fill='both', expand=True)
        cols = min(2, len(trees))
        for i,(title, root) in enumerate(trees):
            frame = ttk.Frame(grid, borderwidth=1, relief='sunken')
            frame.grid(row=i//cols, column=i%cols, sticky='nsew', padx=6, pady=6)
            ttk.Label(frame, text=title).pack(anchor='w')
            canvas = tk.Canvas(frame, background='white', width=480, height=360)
            hbar = ttk.Scrollbar(frame, orient='horizontal', command=canvas.xview)
            vbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
            canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
            canvas.pack(side='left', fill='both', expand=True)
            vbar.pack(side='right', fill='y')
            hbar.pack(side='bottom', fill='x')
            self._draw_tree_on_canvas(canvas, root)

    def _draw_tree_on_canvas(self, canvas: tk.Canvas, root):
        # Desenha uma árvore simples, inspirado no export SVG
        def compute(n):
            nodes = []
            pos = {}
            leaf_counter = [0]
            max_depth = [0]
            def dfs(x, depth):
                max_depth[0] = max(max_depth[0], depth)
                nodes.append(x)
                if not x.children:
                    i = leaf_counter[0]; leaf_counter[0]+=1
                    pos[id(x)] = (float(i), depth)
                    return float(i)
                xs=[]
                for c in x.children:
                    xs.append(dfs(c, depth+1))
                x0 = sum(xs)/len(xs) if xs else float(leaf_counter[0])
                pos[id(x)] = (x0, depth)
                return x0
            dfs(n,0)
            return pos, leaf_counter[0], max_depth[0], nodes
        pos, leafs, depth, nodes = compute(root)
        HSPACE=90; VSPACE=80; MARGIN=20
        def center(x):
            u,v = pos[id(x)]; return (u*HSPACE+MARGIN, v*VSPACE+MARGIN)
        canvas.delete('all')
        # edges
        for n in nodes:
            cx,cy = center(n)
            for ch in n.children:
                x2,y2 = center(ch)
                canvas.create_line(cx, cy+12, x2, y2-12, fill='#555')
        # nodes
        for n in nodes:
            cx,cy = center(n)
            label = n.symbol
            w=max(36, 8*len(label)+12); h=26
            canvas.create_rectangle(cx-w/2, cy-h/2, cx+w/2, cy+h/2, fill='#e8f0fe', outline='#3b82f6')
            canvas.create_text(cx, cy, text=label)
        bbox = canvas.bbox('all')
        if bbox:
            canvas.configure(scrollregion=bbox)

    def compare_trees(self):
        trees=[]
        if self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree is not None:
            trees.append(('LL(1)', self.result_ll1.tree))
        if self.result_slr and self.result_slr.ok and self.result_slr.tree is not None:
            trees.append(('SLR(1)', self.result_slr.tree))
        if getattr(self, 'result_lalr', None) and self.result_lalr.ok and self.result_lalr.tree is not None:
            trees.append(('LALR(1)', self.result_lalr.tree))
        if getattr(self, 'result_lr1', None) and self.result_lr1.ok and self.result_lr1.tree is not None:
            trees.append(('LR(1)', self.result_lr1.tree))
        if not trees:
            messagebox.showinfo('Info','Nenhuma árvore aceita para comparar.')
            return
        win = tk.Toplevel(self)
        win.title('Comparar Árvores')
        grid = ttk.Frame(win)
        grid.pack(fill='both', expand=True)
        cols = min(2, len(trees))
        for i,(title, root) in enumerate(trees):
            frame = ttk.Frame(grid, borderwidth=1, relief='sunken')
            frame.grid(row=i//cols, column=i%cols, sticky='nsew')
            ttk.Label(frame, text=title).pack(anchor='w')
            canvas = tk.Canvas(frame, background='white', width=480, height=360)
            hbar = ttk.Scrollbar(frame, orient='horizontal', command=canvas.xview)
            vbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
            canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
            canvas.pack(side='left', fill='both', expand=True)
            vbar.pack(side='right', fill='y')
            hbar.pack(side='bottom', fill='x')
            self._draw_tree_on_canvas(canvas, root)

    def export_svg(self):
        if not (self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree) and not (self.result_slr and self.result_slr.ok and self.result_slr.tree):
            messagebox.showinfo("Info", "Execute e obtenha uma árvore aceita antes de exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", ".svg")])
        if not path:
            return
        try:
            if self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree is not None and self.method.get() in ("ll1", "both", "all"):
                base = path[:-4] if path.lower().endswith('.svg') else path
                export_tree_svg(self.result_ll1.tree, base + "_ll1.svg")
            if self.result_slr and self.result_slr.ok and self.result_slr.tree is not None and self.method.get() in ("slr1", "both", "all"):
                base = path[:-4] if path.lower().endswith('.svg') else path
                export_tree_svg(self.result_slr.tree, base + "_slr1.svg")
            if getattr(self, 'result_lalr', None) and self.result_lalr.ok and self.result_lalr.tree is not None and self.method.get() in ("lalr1", "all"):
                base = path[:-4] if path.lower().endswith('.svg') else path
                export_tree_svg(self.result_lalr.tree, base + "_lalr1.svg")
            if getattr(self, 'result_lr1', None) and self.result_lr1.ok and self.result_lr1.tree is not None and self.method.get() in ("lr1", "all"):
                base = path[:-4] if path.lower().endswith('.svg') else path
                export_tree_svg(self.result_lr1.tree, base + "_lr1.svg")
            messagebox.showinfo("OK", "SVG(s) exportado(s).")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def export_json(self):
        # Exporta árvore(s) aceitas em JSON
        if not (self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree) and not (self.result_slr and self.result_slr.ok and self.result_slr.tree):
            messagebox.showinfo("Info", "Execute e obtenha uma árvore aceita antes de exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", ".json")])
        if not path:
            return
        try:
            base = path[:-5] if path.lower().endswith('.json') else path
            if self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree is not None and self.method.get() in ("ll1", "both", "all"):
                from parsing_tester import export_tree_json
                export_tree_json(self.result_ll1.tree, base + "_ll1.json", self.result_ll1.derivations, self.result_ll1.kind)
            if self.result_slr and self.result_slr.ok and self.result_slr.tree is not None and self.method.get() in ("slr1", "both", "all"):
                from parsing_tester import export_tree_json
                export_tree_json(self.result_slr.tree, base + "_slr1.json", self.result_slr.derivations, self.result_slr.kind)
            if getattr(self, 'result_lalr', None) and self.result_lalr.ok and self.result_lalr.tree is not None and self.method.get() in ("lalr1", "all"):
                from parsing_tester import export_tree_json
                export_tree_json(self.result_lalr.tree, base + "_lalr1.json", self.result_lalr.derivations, self.result_lalr.kind)
            if getattr(self, 'result_lr1', None) and self.result_lr1.ok and self.result_lr1.tree is not None and self.method.get() in ("lr1", "all"):
                from parsing_tester import export_tree_json
                export_tree_json(self.result_lr1.tree, base + "_lr1.json", self.result_lr1.derivations, self.result_lr1.kind)
            messagebox.showinfo("OK", "JSON exportado(s).")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ===== Semântica =====
    def _build_semantics_tab(self, parent):
        # Módulos serão carregados sob demanda
        frame = ttk.Frame(parent)
        info = ttk.Label(frame, text="Programa (linhas do tipo: x = 1, y = x + 2, z = y * 3, w = y == 3)")
        info.pack(anchor='w', padx=8, pady=4)
        self.sema_input = tk.Text(frame, height=10)
        self.sema_input.pack(fill='x', padx=8)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', padx=8, pady=6)
        ttk.Button(btns, text="Analisar Tipos", command=self.run_semantics).pack(side='left')
        ttk.Button(btns, text="Enviar para IR/TAC", command=self.push_ast_to_ir).pack(side='left', padx=6)
        ttk.Button(btns, text="Importar árvore do Parser", command=self.import_tree_from_parser).pack(side='left', padx=6)
        ttk.Button(btns, text="Importar árvore JSON...", command=self.import_tree_json).pack(side='left', padx=6)
        ttk.Button(btns, text="Visualizar AST", command=self.show_ast_current).pack(side='left', padx=6)
        ttk.Button(btns, text="Exemplo OK", command=self.fill_sema_example).pack(side='right')
        ttk.Button(btns, text="Exemplo (erro)", command=self.fill_sema_example_error).pack(side='right', padx=6)
        # Opções de regras de tipo
        opts = ttk.Frame(frame)
        opts.pack(fill='x', padx=8, pady=4)
        self.var_arith_bool = tk.BooleanVar(value=False)
        self.var_eq_same = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="Permitir aritmética em bool", variable=self.var_arith_bool).pack(side='left')
        ttk.Checkbutton(opts, text="'==' exige mesmo tipo", variable=self.var_eq_same).pack(side='left', padx=12)
        ttk.Label(frame, text="Dica: importe árvore do Parser para gerar AST automaticamente; ajuste regras de tipo nos checkboxes e analise os erros listados abaixo.").pack(anchor='w', padx=8, pady=(2,0))
        self.sema_output = tk.Text(frame, height=20)
        self.sema_output.pack(fill='both', expand=True, padx=8, pady=6)
        self.ast_prog = None
        return frame

    def _parse_simple_program(self, text: str):
        # Constrói AST simples a partir de linhas "var = expr"
        lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
        Program, Assign, Var, Num, BinOp = lab06.Program, lab06.Assign, lab06.Var, lab06.Num, lab06.BinOp
        stmts = []
        import re
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            if '=' not in s:
                raise ValueError(f"Linha inválida (esperado '='): {s}")
            name, expr = s.split('=', 1)
            name = name.strip()
            tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|\d+|==|\+|\*|\(|\)", expr)
            pos = 0
            def peek():
                return tokens[pos] if pos < len(tokens) else None
            def eat(tok=None):
                nonlocal pos
                if tok is None or peek() == tok:
                    t = peek(); pos += 1; return t
                raise ValueError(f"Esperado {tok}, obtido {peek()}")
            def parse_primary():
                t = peek()
                if t is None:
                    raise ValueError("Expressão incompleta")
                if t.isdigit():
                    eat(); return Num(int(t))
                if re.match(r"[A-Za-z_]", t):
                    eat(); return Var(t)
                if t == '(':
                    eat('(')
                    e = parse_expr()
                    eat(')')
                    return e
                raise ValueError(f"Token inesperado: {t}")
            def parse_term():
                e = parse_primary()
                while peek() == '*':
                    eat('*')
                    e = BinOp('*', e, parse_primary())
                return e
            def parse_add():
                e = parse_term()
                while peek() == '+':
                    eat('+')
                    e = BinOp('+', e, parse_term())
                return e
            def parse_expr():
                e = parse_add()
                if peek() == '==':
                    eat('==')
                    e = BinOp('==', e, parse_add())
                return e
            ast_e = parse_expr()
            if pos != len(tokens):
                raise ValueError(f"Sobrou input em: {' '.join(tokens[pos:])}")
            stmts.append(Assign(name, ast_e))
        return Program(stmts)

    def run_semantics(self):
        self.sema_output.delete('1.0','end')
        try:
            lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
            prog = self._parse_simple_program(self.sema_input.get('1.0','end'))
            tc = lab06.TypeChecker(allow_arith_on_bool=self.var_arith_bool.get(), eq_requires_same_type=self.var_eq_same.get())
            errs = tc.check(prog)
            self.ast_prog = prog
            if errs:
                for e in errs:
                    self.sema_output.insert('end', f"Erro: {e}\n")
            else:
                self.sema_output.insert('end', "Sem erros de tipo.\n")
        except Exception as e:
            self.sema_output.insert('end', f"Erro: {e}\n")

    def fill_sema_example(self):
        try:
            example = "x = 1\ny = x + 2\nz = y * 3\nw = y == 3\n"
            self.sema_input.delete('1.0','end')
            self.sema_input.insert('end', example)
            self.sema_output.delete('1.0','end')
            self.sema_output.insert('end', 'Exemplo preenchido. Clique em "Analisar Tipos".\n')
        except Exception as e:
            self.sema_output.insert('end', f"Erro ao preencher exemplo: {e}\n")

    def fill_sema_example_error(self):
        try:
            # Deve gerar erro de tipo (bool em aritmética)
            example = "x = 1\ny = x == 2\nz = y + 3\n"
            self.sema_input.delete('1.0','end')
            self.sema_input.insert('end', example)
            self.sema_output.delete('1.0','end')
            self.sema_output.insert('end', 'Exemplo com erro preenchido. Clique em "Analisar Tipos".\n')
        except Exception as e:
            self.sema_output.insert('end', f"Erro ao preencher exemplo: {e}\n")

    def push_ast_to_ir(self):
        if not self.ast_prog:
            messagebox.showinfo("Info", "Analise um programa primeiro.")
            return
        try:
            self.ir_input.delete('1.0','end')
            self.ir_input.insert('end', "AST disponível na memória. Clique 'Gerar TAC'.")
        except Exception:
            pass

    def import_tree_from_parser(self):
        # Usa a última árvore aceita (ordem: LR(1) > LALR(1) > SLR(1) > LL(1)) e converte para AST
        tree = None
        if getattr(self, 'result_lr1', None) and self.result_lr1.ok and self.result_lr1.tree is not None:
            tree = self.result_lr1.tree
        elif getattr(self, 'result_lalr', None) and self.result_lalr.ok and self.result_lalr.tree is not None:
            tree = self.result_lalr.tree
        elif self.result_slr and self.result_slr.ok and self.result_slr.tree is not None:
            tree = self.result_slr.tree
        elif self.result_ll1 and self.result_ll1.ok and self.result_ll1.tree is not None:
            tree = self.result_ll1.tree
        if tree is None:
            messagebox.showinfo('Info','Nenhuma árvore aceita disponível. Rode o Parser primeiro.')
            return
        try:
            lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
            # heurística simples: se gramática tem 'E'/'T'/'F', trate como expressão; se tiver 'Stmt', trate como if/else/assign
            gpath = self.grammar_path.get().lower()
            if 'if_else' in gpath or 'stmt' in gpath:
                prog = lab06.Program([ self._stmt_from_if_tree(tree) ])
            else:
                expr_ast = self._expr_from_tree(tree)
                prog = lab06.Program([lab06.Assign('x', expr_ast)])
            self.ast_prog = prog
            # Atualiza painel
            self.sema_input.delete('1.0','end')
            self.sema_input.insert('end', '<AST importada do Parser>\n')
            self.sema_output.insert('end', 'Árvore importada como AST.\n')
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao converter árvore para AST: {e}')

    def import_tree_json(self):
        # Carrega JSON exportado pelo Parser e converte para AST (expr ou if/else)
        path = filedialog.askopenfilename(title='Selecione JSON da árvore', filetypes=[('JSON','*.json'), ('All','*.*')])
        if not path:
            return
        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            tree_dict = data.get('tree') or data
            def build_node(d):
                from parsing_tester import ParseTreeNode
                n = ParseTreeNode(d['symbol'], [])
                for ch in d.get('children', []):
                    n.children.append(build_node(ch))
                return n
            root = build_node(tree_dict)
            # usa heurística conforme caminho da gramática
            lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
            gpath = self.grammar_path.get().lower()
            if 'if_else' in gpath or 'stmt' in gpath:
                prog = lab06.Program([ self._stmt_from_if_tree(root) ])
            else:
                expr_ast = self._expr_from_tree(root)
                prog = lab06.Program([lab06.Assign('x', expr_ast)])
            self.ast_prog = prog
            self.sema_input.delete('1.0','end')
            self.sema_input.insert('end', '<AST importada de JSON>\n')
            self.sema_output.insert('end', 'Árvore JSON importada e convertida em AST.\n')
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao importar árvore JSON: {e}')

    def _expr_from_tree(self, node):
        # Converte a gramática expr.txt em AST (Var/Num/BinOp) — aceita id/num, +, * e parênteses
        lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
        def parse_E(n):
            # E -> T E'
            t = parse_T(n.children[0])
            return parse_Ep(n.children[1], t)
        def parse_Ep(n, left):
            # E' -> + T E' | ε
            if not n.children or (len(n.children)==1 and n.children[0].symbol in ('ε',)):
                return left
            # '+' T E'
            t = parse_T(n.children[1])
            new_left = lab06.BinOp('+', left, t)
            return parse_Ep(n.children[2], new_left)
        def parse_T(n):
            # T -> F T'
            f = parse_F(n.children[0])
            return parse_Tp(n.children[1], f)
        def parse_Tp(n, left):
            # T' -> * F T' | ε
            if not n.children or (len(n.children)==1 and n.children[0].symbol in ('ε',)):
                return left
            f = parse_F(n.children[1])
            new_left = lab06.BinOp('*', left, f)
            return parse_Tp(n.children[2], new_left)
        def parse_F(n):
            if len(n.children)==1 and n.children[0].symbol == 'id':
                return lab06.Var('id')
            if len(n.children)==3 and n.children[0].symbol == '(':
                return parse_E(n.children[1])
            # opcional: num
            if len(n.children)==1 and n.children[0].symbol == 'num':
                return lab06.Num(0)
            raise ValueError('Forma de F desconhecida')
        return parse_E(node)

    def _stmt_from_if_tree(self, node):
        # Converte a árvore de if_else.txt numa AST simples (Assign, IfThenElse, Seq)
        lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
        # Espera S -> StmtList; StmtList -> Stmt ; StmtList | Stmt; Stmt -> id = E | if E then Stmt | if E then Stmt else Stmt
        def parse_S(n):
            return parse_StmtList(n.children[0])
        def parse_StmtList(n):
            if len(n.children) == 1:
                return parse_Stmt(n.children[0])
            # Stmt ; StmtList
            first = parse_Stmt(n.children[0])
            rest = parse_StmtList(n.children[2])
            # flatten
            items = []
            if isinstance(first, lab06.Seq): items.extend(first.items)
            else: items.append(first)
            if isinstance(rest, lab06.Seq): items.extend(rest.items)
            else: items.append(rest)
            return lab06.Seq(items)
        def parse_Stmt(n):
            # alternatives
            if len(n.children) >= 3 and n.children[1].symbol == '=':
                # id = E
                name = 'id'
                expr = self._expr_from_tree(n.children[2])
                return lab06.Assign(name, expr)
            if n.children and n.children[0].symbol == 'if':
                # if E then Stmt [else Stmt]
                cond = self._expr_from_tree(n.children[1])
                thenb = parse_Stmt(n.children[3])
                if len(n.children) > 4 and n.children[4].symbol == 'else':
                    elseb = parse_Stmt(n.children[5])
                else:
                    elseb = None
                return lab06.IfThenElse(cond, thenb, elseb)
            # fallback
            return lab06.Seq([])
        return parse_S(node)

    # ===== IR/TAC =====
    def _build_ir_tab(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Geração de TAC a partir da AST do painel Semântica").pack(anchor='w', padx=8, pady=4)
        self.ir_input = tk.Text(frame, height=4)
        self.ir_input.pack(fill='x', padx=8)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', padx=8, pady=6)
        ttk.Button(btns, text="Gerar TAC", command=self.run_tac).pack(side='left')
        ttk.Button(btns, text="Enviar para Codegen", command=self.push_tac_to_codegen).pack(side='left', padx=6)
        ttk.Button(btns, text="Demo 3 casos", command=self.ir_demo_three_cases).pack(side='right')
        ttk.Button(btns, text="Exemplo 1", command=self.fill_ir_example).pack(side='right', padx=6)
        ttk.Button(btns, text="Exemplo 2", command=self.fill_ir_example2).pack(side='right')
        ttk.Label(frame, text="Dica: cada expressão vira temporários tN e instruções (load/loadI, add, mul, cmpeq, store). Use o botão abaixo para inspecionar o TAC gerado.").pack(anchor='w', padx=8, pady=(2,0))
        self.ir_output = tk.Text(frame, height=22)
        self.ir_output.pack(fill='both', expand=True, padx=8, pady=6)
        self.tac_list = None
        return frame

    def run_tac(self):
        self.ir_output.delete('1.0','end')
        try:
            if not self.ast_prog:
                raise ValueError("AST não disponível. Use a aba Semântica.")
            lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
            lab07 = _load_module('labs/07_ast_ir/tac_template.py', 'lab07_tac')
            gen = lab07.TacGen()
            # Program.body é lista de Assign
            for st in self.ast_prog.body:
                if isinstance(st, lab06.Assign):
                    gen.gen_assign(st.name, st.expr)
                else:
                    raise ValueError("Apenas Assign suportado neste demo.")
            self.tac_list = [(i.op, i.args) for i in gen.code]
            for op, args in self.tac_list:
                self.ir_output.insert('end', f"{op} {' '.join(args)}\n")
        except Exception as e:
            self.ir_output.insert('end', f"Erro: {e}\n")

    def ir_demo_three_cases(self):
        # Gera três casos de AST -> typecheck -> TAC e imprime aqui
        self.ir_output.delete('1.0','end')
        try:
            lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
            lab07 = _load_module('labs/07_ast_ir/tac_template.py', 'lab07_tac')
            Program, Assign, Var, Num, BinOp = lab06.Program, lab06.Assign, lab06.Var, lab06.Num, lab06.BinOp
            cases = [
                ("Exemplo 1: atribuicoes e expressoes", Program([
                    Assign("x", Num(1)),
                    Assign("y", BinOp("+", Var("x"), Num(2))),
                    Assign("z", BinOp("*", Var("y"), Num(3))),
                ])),
                ("Exemplo 2: precedencia via AST", Program([
                    Assign("w", BinOp("*", Num(10), BinOp("+", Num(2), Num(3)))),
                ])),
                ("Exemplo 3: erro de tipos (int -> bool)", Program([
                    Assign("x", Num(1)),
                    Assign("x", BinOp("==", Var("x"), Num(2))),
                ])),
            ]
            ast_views = []
            for title, prog in cases:
                self.ir_output.insert('end', f"\n=== {title} ===\n")
                # Typecheck
                tc = lab06.TypeChecker()
                errs = tc.check(prog)
                if errs:
                    self.ir_output.insert('end', "-- Erros de tipo --\n")
                    for e in errs:
                        self.ir_output.insert('end', f"  - {e}\n")
                else:
                    self.ir_output.insert('end', "-- Tipagem OK --\n")
                # TAC
                gen = lab07.TacGen()
                for st in prog.body:
                    if isinstance(st, lab06.Assign):
                        gen.gen_assign(st.name, st.expr)
                self.ir_output.insert('end', "-- TAC --\n")
                for instr in gen.code:
                    self.ir_output.insert('end', f"{instr.op} {' '.join(instr.args)}\n")
                # AST view para visualização
                ast_views.append((title, self._ast_to_view(prog)))
            # Não altera self.tac_list (este é um demo múltiplo)
            # Exibir árvores AST lado a lado
            self._show_ast_views(ast_views)
        except Exception as e:
            self.ir_output.insert('end', f"Erro no demo: {e}\n")

    def _ast_to_view(self, node):
        # Converte AST (Lab 06) em um nó simples com 'symbol' e 'children'
        lab06 = _load_module('labs/06_semantica/ast_template.py', 'lab06_ast')
        class V:
            __slots__ = ('symbol','children')
            def __init__(self, symbol, children=None):
                self.symbol = symbol
                self.children = children or []
        if isinstance(node, lab06.Program):
            return V('Program', [self._ast_to_view(s) for s in node.body])
        if isinstance(node, lab06.Seq):
            return V('Seq', [self._ast_to_view(s) for s in node.items])
        if isinstance(node, lab06.Assign):
            return V(f'Assign {node.name}', [self._ast_to_view(node.expr)])
        if isinstance(node, lab06.IfThenElse):
            ch = [V('cond', [self._ast_to_view(node.cond)]), V('then', [self._ast_to_view(node.then_branch)])]
            if node.else_branch is not None:
                ch.append(V('else', [self._ast_to_view(node.else_branch)]))
            return V('If', ch)
        if isinstance(node, lab06.BinOp):
            return V(node.op, [self._ast_to_view(node.left), self._ast_to_view(node.right)])
        if isinstance(node, lab06.Var):
            return V(f'Var({node.name})')
        if isinstance(node, lab06.Num):
            return V(f'Num({node.value})')
        return V(str(node))

    def _show_ast_views(self, titled_roots):
        # Abre janela para mostrar árvores AST lado a lado (até 2 por linha)
        if not titled_roots:
            return
        win = tk.Toplevel(self)
        win.title('AST — Demo 3 casos')
        # toolbar geral (exportar todas)
        tbar = ttk.Frame(win)
        tbar.pack(fill='x', padx=6, pady=4)
        ttk.Label(tbar, text='Exportar todas:').pack(side='left')
        def _slug(s: str) -> str:
            import re
            s = s.strip().lower().replace(' ', '_')
            return re.sub(r"[^a-z0-9_\-]+", "", s)[:40] or 'ast'
        def export_all_svg():
            try:
                from tkinter import filedialog
                base = filedialog.asksaveasfilename(title='Salvar todas (SVG, usa como prefixo)', defaultextension='.svg', filetypes=[["SVG",".svg"]])
                if not base:
                    return
                # remove extension to use as prefix
                if base.lower().endswith('.svg'):
                    base = base[:-4]
                pt = _load_module('parsing_tester.py', 'pt_export')
                for idx, (title, root) in enumerate(titled_roots, start=1):
                    out = f"{base}_{idx}_{_slug(title)}.svg"
                    pt.export_tree_svg(root, out)
            except Exception as e:
                try:
                    messagebox.showerror('Erro', f'Falha ao exportar todas (SVG): {e}')
                except Exception:
                    pass
        def export_all_json():
            try:
                from tkinter import filedialog
                base = filedialog.asksaveasfilename(title='Salvar todas (JSON, usa como prefixo)', defaultextension='.json', filetypes=[["JSON",".json"]])
                if not base:
                    return
                if base.lower().endswith('.json'):
                    base = base[:-5]
                pt = _load_module('parsing_tester.py', 'pt_export')
                for idx, (title, root) in enumerate(titled_roots, start=1):
                    out = f"{base}_{idx}_{_slug(title)}.json"
                    pt.export_tree_json(root, out, derivations=None, kind='AST')
            except Exception as e:
                try:
                    messagebox.showerror('Erro', f'Falha ao exportar todas (JSON): {e}')
                except Exception:
                    pass
        ttk.Button(tbar, text='SVG (prefixo)', command=export_all_svg).pack(side='left', padx=4)
        ttk.Button(tbar, text='JSON (prefixo)', command=export_all_json).pack(side='left')
        grid = ttk.Frame(win)
        grid.pack(fill='both', expand=True)
        cols = 2
        for i, (title, root) in enumerate(titled_roots):
            frame = ttk.Frame(grid, borderwidth=1, relief='sunken')
            frame.grid(row=i//cols, column=i%cols, sticky='nsew', padx=6, pady=6)
            # toolbar por árvore
            bar = ttk.Frame(frame)
            bar.pack(fill='x')
            ttk.Label(bar, text=title).pack(side='left')
            btns = ttk.Frame(bar)
            btns.pack(side='right')
            def export_svg(root=root, t=title):
                try:
                    from tkinter import filedialog
                    path = filedialog.asksaveasfilename(title=f"Exportar AST '{t}' (SVG)", defaultextension='.svg', filetypes=[["SVG",".svg"]])
                    if not path:
                        return
                    pt = _load_module('parsing_tester.py', 'pt_export')
                    pt.export_tree_svg(root, path)
                except Exception as e:
                    try:
                        messagebox.showerror('Erro', f'Falha ao exportar SVG: {e}')
                    except Exception:
                        pass
            def export_json(root=root, t=title):
                try:
                    from tkinter import filedialog
                    path = filedialog.asksaveasfilename(title=f"Exportar AST '{t}' (JSON)", defaultextension='.json', filetypes=[["JSON",".json"]])
                    if not path:
                        return
                    pt = _load_module('parsing_tester.py', 'pt_export')
                    # kind='AST' (sem derivations)
                    pt.export_tree_json(root, path, derivations=None, kind='AST')
                except Exception as e:
                    try:
                        messagebox.showerror('Erro', f'Falha ao exportar JSON: {e}')
                    except Exception:
                        pass
            ttk.Button(btns, text='Export SVG', command=export_svg).pack(side='right', padx=2)
            ttk.Button(btns, text='Export JSON', command=export_json).pack(side='right', padx=2)
            canvas = tk.Canvas(frame, background='white', width=520, height=380)
            hbar = ttk.Scrollbar(frame, orient='horizontal', command=canvas.xview)
            vbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
            canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
            canvas.pack(side='left', fill='both', expand=True)
            vbar.pack(side='right', fill='y')
            hbar.pack(side='bottom', fill='x')
            self._draw_tree_on_canvas(canvas, root)

    def show_ast_current(self):
        # Visualiza a AST atual (Semântica). Se não existir, tenta parse do texto.
        try:
            if not getattr(self, 'ast_prog', None):
                prog = self._parse_simple_program(self.sema_input.get('1.0','end'))
                self.ast_prog = prog
            root = self._ast_to_view(self.ast_prog)
            self._show_ast_views([("AST atual", root)])
        except Exception as e:
            try:
                messagebox.showerror('Erro', f'Falha ao visualizar AST: {e}')
            except Exception:
                pass

    def fill_ir_example(self):
        try:
            # Preenche a aba Semântica com exemplo e prepara AST
            self.fill_sema_example()
            prog = self._parse_simple_program(self.sema_input.get('1.0','end'))
            self.ast_prog = prog
            self.ir_input.delete('1.0','end')
            self.ir_input.insert('end', 'AST exemplo pronta. Clique em "Gerar TAC".\n')
            self.ir_output.delete('1.0','end')
        except Exception as e:
            self.ir_output.insert('end', f"Erro ao preparar exemplo: {e}\n")

    def fill_ir_example2(self):
        try:
            # Exemplo com expressão aninhada
            self.sema_input.delete('1.0','end')
            self.sema_input.insert('end', 'x = (1 + 2) * (3 + 4)\n')
            prog = self._parse_simple_program(self.sema_input.get('1.0','end'))
            self.ast_prog = prog
            self.ir_input.delete('1.0','end')
            self.ir_input.insert('end', 'AST exemplo 2 pronta. Clique em "Gerar TAC".\n')
            self.ir_output.delete('1.0','end')
        except Exception as e:
            self.ir_output.insert('end', f"Erro ao preparar exemplo 2: {e}\n")

    def push_tac_to_codegen(self):
        if not self.tac_list:
            messagebox.showinfo("Info", "Gere TAC primeiro.")
            return
        try:
            self.codegen_output.delete('1.0','end')
            self.codegen_output.insert('end', "TAC disponível. Clique 'Gerar Assembly'.")
        except Exception:
            pass

    # ===== Codegen =====
    def _build_codegen_tab(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Geração de assembly a partir do TAC").pack(anchor='w', padx=8, pady=4)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', padx=8, pady=6)
        # Opções de alocação de registradores
        opts = ttk.Frame(frame)
        opts.pack(fill='x', padx=8)
        self.var_regalloc = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Alocar registradores (linear-scan)", variable=self.var_regalloc).pack(side='left')
        ttk.Label(opts, text="K regs:").pack(side='left', padx=(12,4))
        self.reg_k = tk.IntVar(value=3)
        spin = tk.Spinbox(opts, from_=1, to=32, width=4, textvariable=self.reg_k)
        spin.pack(side='left')
        ttk.Button(btns, text="Gerar Assembly", command=self.run_codegen).pack(side='left')
        ttk.Button(btns, text="Enviar ao Simulador", command=self.push_asm_to_sim).pack(side='left', padx=6)
        ttk.Button(btns, text="Exemplo simples", command=self.fill_codegen_example).pack(side='right')
        ttk.Button(btns, text="Exemplo spill", command=self.fill_codegen_example_spill).pack(side='right', padx=6)
        ttk.Label(frame, text="Dica: habilite alocação com K pequeno (ex.: 2) para observar spill; o mapping aparece no topo. Envie o assembly gerado ao Simulador.").pack(anchor='w', padx=8, pady=(2,0))
        self.codegen_output = tk.Text(frame)
        self.codegen_output.pack(fill='both', expand=True, padx=8, pady=6)
        self.asm_prog = None
        self.last_regalloc_map = None
        return frame

    def run_codegen(self):
        self.codegen_output.delete('1.0','end')
        try:
            if not self.tac_list:
                raise ValueError("TAC não disponível. Gere na aba IR/TAC.")
            tac_to_use = list(self.tac_list)
            self.last_regalloc_map = None
            if hasattr(self, 'var_regalloc') and bool(self.var_regalloc.get()):
                regalloc = _load_module('labs/08_codegen/regalloc_linear.py', 'lab08_regalloc')
                try:
                    k = int(self.reg_k.get()) if hasattr(self, 'reg_k') else 3
                except Exception:
                    k = 3
                k = max(1, min(32, k))
                mp = regalloc.allocate_registers(tac_to_use, k=k)
                self.last_regalloc_map = mp
                self.codegen_output.insert('end', f"; regalloc k={k}: {mp}\n")
                tac_to_use = regalloc.apply_mapping_to_tac(tac_to_use, mp)
            lab08 = _load_module('labs/08_codegen/codegen_template.py', 'lab08_codegen')
            asm = lab08.codegen_from_tac(tac_to_use)
            self.asm_prog = [(a.op, a.args) for a in asm]
            for op, args in self.asm_prog:
                self.codegen_output.insert('end', f"{op} {' '.join(args)}\n")
        except Exception as e:
            self.codegen_output.insert('end', f"Erro: {e}\n")

    def fill_codegen_example(self):
        try:
            # TAC exemplo simples
            self.tac_list = [
                ('loadI', ('1','t1')),
                ('loadI', ('2','t2')),
                ('mul', ('t1','t2','t3')),
                ('store', ('t3','x')),
            ]
            self.codegen_output.delete('1.0','end')
            self.codegen_output.insert('end', 'TAC exemplo preparado. Clique em "Gerar Assembly".\n')
        except Exception as e:
            self.codegen_output.insert('end', f"Erro ao preparar exemplo: {e}\n")

    def fill_codegen_example_spill(self):
        try:
            # TAC que cria muitos temporários para provocar spill com K pequeno
            self.tac_list = [
                ('loadI', ('1','t1')),
                ('loadI', ('2','t2')),
                ('loadI', ('3','t3')),
                ('add', ('t1','t2','t4')),
                ('mul', ('t3','t4','t5')),
                ('add', ('t5','t2','t6')),
                ('mul', ('t6','t1','t7')),
                ('store', ('t7','x')),
            ]
            self.codegen_output.delete('1.0','end')
            self.codegen_output.insert('end', 'TAC com muitos temporários preparado. Habilite regalloc e use K=2, depois "Gerar Assembly".\n')
        except Exception as e:
            self.codegen_output.insert('end', f"Erro ao preparar exemplo spill: {e}\n")

    def push_asm_to_sim(self):
        if not self.asm_prog:
            messagebox.showinfo("Info", "Gere assembly primeiro.")
            return
        try:
            self.sim_output.delete('1.0','end')
            self.sim_output.insert('end', "Assembly pronto. Clique 'Executar'.")
        except Exception:
            pass

    # ===== Otimização =====
    def _build_opt_tab(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Otimizações em TAC").pack(anchor='w', padx=8, pady=4)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', padx=8, pady=6)
        ttk.Button(btns, text="Constant Folding", command=self.run_fold).pack(side='left')
        ttk.Button(btns, text="Dead Code Elim", command=self.run_dce).pack(side='left', padx=6)
        ttk.Button(btns, text="Aplicar como atual", command=self.apply_opt).pack(side='left', padx=6)
        ttk.Button(btns, text="Exemplo 1", command=self.fill_opt_example).pack(side='right')
        ttk.Button(btns, text="Exemplo 2", command=self.fill_opt_example2).pack(side='right', padx=6)
        ttk.Label(frame, text="Dica: rode Folding e depois DCE; use 'Aplicar como atual' para enviar o TAC otimizado ao Codegen/Simulador.").pack(anchor='w', padx=8, pady=(2,0))
        self.opt_output = tk.Text(frame)
        self.opt_output.pack(fill='both', expand=True, padx=8, pady=6)
        self.opt_tac = None
        return frame

    def run_fold(self):
        self.opt_output.delete('1.0','end')
        if not self.tac_list:
            self.opt_output.insert('end', 'Gere TAC primeiro.\n')
            return
        lab09 = _load_module('labs/09_opt/optimizer_template.py', 'lab09_opt')
        self.opt_tac = lab09.const_folding(self.tac_list)
        for op, args in self.opt_tac:
            self.opt_output.insert('end', f"{op} {' '.join(args)}\n")

    def run_dce(self):
        if not self.opt_tac:
            self.opt_output.insert('end', 'Execute folding primeiro.\n')
            return
        lab09 = _load_module('labs/09_opt/optimizer_template.py', 'lab09_opt')
        dce = lab09.dead_code_elim(self.opt_tac, live_vars=['x'])
        self.opt_tac = dce
        self.opt_output.insert('end', '\n-- após DCE --\n')
        for op, args in dce:
            self.opt_output.insert('end', f"{op} {' '.join(args)}\n")

    def apply_opt(self):
        if self.opt_tac:
            self.tac_list = list(self.opt_tac)
            messagebox.showinfo('OK', 'TAC otimizado aplicado.')

    def fill_opt_example(self):
        try:
            # TAC passível de folding e DCE
            self.tac_list = [
                ('loadI', ('1','t1')),
                ('loadI', ('2','t2')),
                ('add', ('t1','t2','t3')),
                ('mul', ('t3','t2','t4')),
                ('store', ('t4','x')),
            ]
            self.opt_tac = list(self.tac_list)
            self.opt_output.delete('1.0','end')
            self.opt_output.insert('end', 'TAC exemplo preparado:\n')
            for op, args in self.opt_tac:
                self.opt_output.insert('end', f"{op} {' '.join(args)}\n")
            self.opt_output.insert('end', '\nClique em Constant Folding e depois em Dead Code Elim.\n')
        except Exception as e:
            self.opt_output.insert('end', f"Erro ao preparar exemplo: {e}\n")

    def fill_opt_example2(self):
        try:
            # Instruções com resultados não usados (y) e cálculo redundante
            self.tac_list = [
                ('loadI', ('10','t1')),
                ('loadI', ('0','t2')),
                ('add', ('t1','t2','t3')),
                ('store', ('t3','y')),
                ('add', ('t1','t1','t4')),
                ('store', ('t4','x')),
            ]
            self.opt_tac = list(self.tac_list)
            self.opt_output.delete('1.0','end')
            self.opt_output.insert('end', 'TAC exemplo 2 preparado:\n')
            for op, args in self.opt_tac:
                self.opt_output.insert('end', f"{op} {' '.join(args)}\n")
            self.opt_output.insert('end', '\nCom live_vars=[\'x\'], DCE deve remover store em y e seus produtores.\n')
        except Exception as e:
            self.opt_output.insert('end', f"Erro ao preparar exemplo 2: {e}\n")

    # ===== Simulador =====
    def _build_sim_tab(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Simulador de assembly (toy)").pack(anchor='w', padx=8, pady=4)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', padx=8, pady=6)
        ttk.Button(btns, text="Executar", command=self.run_sim).pack(side='left')
        ttk.Button(btns, text="Exemplo 1", command=self.fill_sim_example).pack(side='right')
        ttk.Button(btns, text="Exemplo 2", command=self.fill_sim_example2).pack(side='right', padx=6)
        ttk.Label(frame, text="Dica: ao executar, verifique mapping (se houver), a listagem do assembly e os estados finais de registradores e memória.").pack(anchor='w', padx=8, pady=(2,0))
        self.sim_output = tk.Text(frame)
        self.sim_output.pack(fill='both', expand=True, padx=8, pady=6)
        return frame

    def run_sim(self):
        self.sim_output.delete('1.0','end')
        try:
            if not self.asm_prog:
                raise ValueError('Gere assembly na aba Codegen.')
            if getattr(self, 'last_regalloc_map', None):
                self.sim_output.insert('end', f"; mapping: {self.last_regalloc_map}\n")
            self.sim_output.insert('end', "; assembly:\n")
            for op, args in self.asm_prog:
                self.sim_output.insert('end', f"{op} {' '.join(args)}\n")
            lab10 = _load_module('labs/10_backend/asm_sim_template.py', 'lab10_sim')
            m = lab10.Machine()
            m.run(self.asm_prog)
            self.sim_output.insert('end', f"\nregs: {m.regs}\n")
            self.sim_output.insert('end', f"mem: {m.mem}\n")
        except Exception as e:
            self.sim_output.insert('end', f"Erro: {e}\n")

    def fill_sim_example(self):
        try:
            self.asm_prog = [
                ('MOVI', ('1','t1')),
                ('MOVI', ('2','t2')),
                ('ADD', ('t1','t2','t3')),
                ('MOV', ('t3','x')),
            ]
            self.last_regalloc_map = None
            self.sim_output.delete('1.0','end')
            self.sim_output.insert('end', 'Assembly exemplo preparado. Clique em "Executar".\n')
            for op, args in self.asm_prog:
                self.sim_output.insert('end', f"{op} {' '.join(args)}\n")
        except Exception as e:
            self.sim_output.insert('end', f"Erro ao preparar exemplo: {e}\n")

    def fill_sim_example2(self):
        try:
            # Usa comparação e move resultado para memória
            self.asm_prog = [
                ('MOVI', ('3','t1')),
                ('MOVI', ('3','t2')),
                ('CMPEQ', ('t1','t2','t3')),
                ('MOV', ('t3','flag')),
            ]
            self.last_regalloc_map = None
            self.sim_output.delete('1.0','end')
            self.sim_output.insert('end', 'Assembly exemplo 2 preparado. Clique em "Executar".\n')
            for op, args in self.asm_prog:
                self.sim_output.insert('end', f"{op} {' '.join(args)}\n")
        except Exception as e:
            self.sim_output.insert('end', f"Erro ao preparar exemplo 2: {e}\n")

    # ===== Autômatos =====
    def _build_automata_tab(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Regex (usa |, *, +, ?, parênteses e concatenação implícita)").pack(anchor='w', padx=8, pady=4)
        self.re_input = ttk.Entry(frame)
        self.re_input.pack(fill='x', padx=8)
        inrow = ttk.Frame(frame)
        inrow.pack(fill='x', padx=8, pady=4)
        ttk.Label(inrow, text="Cadeia de teste (símbolos sem espaço)").pack(side='left')
        self.re_test = ttk.Entry(inrow)
        self.re_test.pack(side='left', fill='x', expand=True, padx=6)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', padx=8, pady=6)
        ttk.Button(btns, text='Construir NFA/DFA/Min', command=self.build_automata).pack(side='left')
        ttk.Button(btns, text='Testar Cadeia', command=self.test_automata).pack(side='left', padx=6)
        ttk.Button(btns, text='Exportar NFA (SVG)', command=self.export_nfa_svg).pack(side='left')
        ttk.Button(btns, text='Exportar DFA (SVG)', command=self.export_dfa_svg).pack(side='left', padx=6)
        ttk.Button(btns, text='Exportar NFA (DOT)', command=self.export_nfa_dot).pack(side='left')
        ttk.Button(btns, text='Exportar DFA (DOT)', command=self.export_dfa_dot).pack(side='left', padx=6)
        ttk.Button(btns, text='Exemplo 1', command=self.fill_automata_example).pack(side='right')
        ttk.Button(btns, text='Exemplo 2', command=self.fill_automata_example2).pack(side='right', padx=6)
        ttk.Label(frame, text="Dica: use Prev/Next para passos do subset/minimização; alterne entre ver DFA e NFA e exporte SVG/DOT para documentação.").pack(anchor='w', padx=8, pady=(2,0))
        bank = ttk.Frame(frame)
        bank.pack(fill='x', padx=8, pady=4)
        ttk.Label(bank, text='Exemplos (regex_bank):').pack(side='left')
        self.regex_combo = ttk.Combobox(bank, state='readonly', width=40)
        self.regex_combo.pack(side='left', padx=6)
        ttk.Button(bank, text='Carregar', command=self.load_regex_bank).pack(side='left')
        ttk.Button(bank, text='Usar', command=self.use_selected_regex).pack(side='left', padx=6)
        stepbar = ttk.Frame(frame)
        stepbar.pack(fill='x', padx=8, pady=6)
        ttk.Label(stepbar, text='Subset passos:').pack(side='left')
        ttk.Button(stepbar, text='Prev', command=self.auto_subset_prev).pack(side='left')
        ttk.Button(stepbar, text='Next', command=self.auto_subset_next).pack(side='left', padx=4)
        ttk.Label(stepbar, text='Minimização passos:').pack(side='left', padx=12)
        ttk.Button(stepbar, text='Prev', command=self.auto_min_prev).pack(side='left')
        ttk.Button(stepbar, text='Next', command=self.auto_min_next).pack(side='left', padx=4)
        # Canvas e opções de visualização
        viz = ttk.Frame(frame)
        viz.pack(fill='both', expand=True)
        viewbar = ttk.Frame(viz)
        viewbar.pack(fill='x', padx=8)
        self.auto_view = tk.StringVar(value='dfa')
        ttk.Radiobutton(viewbar, text='Ver DFA', value='dfa', variable=self.auto_view, command=lambda: self._draw_dfa_canvas()).pack(side='left')
        ttk.Radiobutton(viewbar, text='Ver NFA', value='nfa', variable=self.auto_view, command=lambda: self._draw_dfa_canvas()).pack(side='left', padx=6)
        self.auto_canvas = tk.Canvas(viz, background='white', height=280)
        self.auto_canvas.pack(fill='x', padx=8, pady=6)
        self.auto_output = tk.Text(viz, height=12)
        self.auto_output.pack(fill='both', expand=True, padx=8, pady=6)
        self._auto_nfa = None
        self._auto_dfa = None
        self._auto_alpha = None
        self._subset_steps = []
        self._subset_idx = 0
        self._min_steps = []
        self._min_idx = 0
        return frame

    def build_automata(self):
        self.auto_output.delete('1.0','end')
        try:
            lib = _load_module('labs/11_automatos/automata_lib.py', 'auto_lib')
            regex = self.re_input.get().strip()
            if not regex:
                raise ValueError('Informe uma regex.')
            nfa, alpha, log = lib.regex_to_nfa_with_log(regex)
            dfa = lib.nfa_to_dfa(nfa, alpha)
            mdfa = lib.dfa_minimize(dfa, alpha)
            self._auto_nfa = nfa
            self._auto_dfa = mdfa
            self._auto_alpha = alpha
            # passos
            self._subset_steps = lib.nfa_to_dfa_steps(nfa, alpha)
            self._subset_idx = 0
            self._min_steps, self._min_parts = lib.dfa_minimize_steps(mdfa, alpha)
            self._min_idx = 0
            self.auto_output.insert('end', f"Regex: {regex}\n")
            self.auto_output.insert('end', f"Alfabeto: {sorted(list(alpha))}\n")
            self.auto_output.insert('end', f"DFA estados: {len({dfa.start} | set([s for s,_ in dfa.trans.keys()]) | set(dfa.trans.values()))}\n")
            self.auto_output.insert('end', f"DFA (min) estados: {len({mdfa.start} | set([s for s,_ in mdfa.trans.keys()]) | set(mdfa.trans.values()))}\n")
            self.auto_output.insert('end', "\nPassos (Thompson):\n")
            for ln in log:
                self.auto_output.insert('end', f"- {ln}\n")
            self.auto_output.insert('end', "\nSubset (primeiro passo):\n")
            if self._subset_steps:
                self.auto_output.insert('end', self._subset_steps[0] + "\n")
            self.auto_output.insert('end', "\nMinimização (primeiro passo):\n")
            if self._min_steps:
                self.auto_output.insert('end', self._min_steps[0] + "\n")
            parts0 = self._min_parts[0] if getattr(self, '_min_parts', None) else None
            self._draw_dfa_canvas(partitions=parts0)
        except Exception as e:
            self.auto_output.insert('end', f"Erro: {e}\n")

    def test_automata(self):
        if not self._auto_dfa:
            self.auto_output.insert('end', 'Construa o automato primeiro.\n')
            return
        try:
            lib = _load_module('labs/11_automatos/automata_lib.py', 'auto_lib')
            s = list(self.re_test.get().strip())
            ok = lib.dfa_accepts(self._auto_dfa, s)
            self.auto_output.insert('end', f"Teste: {'ACEITA' if ok else 'REJEITA'}\n")
        except Exception as e:
            self.auto_output.insert('end', f"Erro: {e}\n")

    def export_dfa_svg(self):
        if not self._auto_dfa:
            messagebox.showinfo('Info','Construa o automato primeiro.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.svg', filetypes=[('SVG','.svg')])
        if not path:
            return
        try:
            lib = _load_module('labs/11_automatos/automata_lib.py', 'auto_lib')
            lib.automaton_to_svg_dfa(self._auto_dfa, self._auto_alpha or set(), path)
            messagebox.showinfo('OK', 'SVG exportado.')
        except Exception as e:
            messagebox.showerror('Erro', str(e))

    def export_nfa_dot(self):
        if not self._auto_nfa:
            messagebox.showinfo('Info','Construa o automato primeiro.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.dot', filetypes=[('DOT','.dot')])
        if not path:
            return
        try:
            lib = _load_module('labs/11_automatos/automata_lib.py', 'auto_lib')
            lib.export_dot_nfa(self._auto_nfa, path)
            messagebox.showinfo('OK', 'DOT exportado.')
        except Exception as e:
            messagebox.showerror('Erro', str(e))

    def export_dfa_dot(self):
        if not self._auto_dfa:
            messagebox.showinfo('Info','Construa o automato primeiro.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.dot', filetypes=[('DOT','.dot')])
        if not path:
            return
        try:
            lib = _load_module('labs/11_automatos/automata_lib.py', 'auto_lib')
            lib.export_dot_dfa(self._auto_dfa, path)
            messagebox.showinfo('OK', 'DOT exportado.')
        except Exception as e:
            messagebox.showerror('Erro', str(e))

    def _show_subset_step(self):
        if not self._subset_steps:
            return
        self.auto_output.insert('end', f"\n[Subset passo {self._subset_idx+1}/{len(self._subset_steps)}]\n")
        self.auto_output.insert('end', self._subset_steps[self._subset_idx] + "\n")
        self._draw_dfa_canvas(highlight=self._subset_steps[self._subset_idx])

    def auto_subset_prev(self):
        if self._subset_idx > 0:
            self._subset_idx -= 1
            self._show_subset_step()

    def auto_subset_next(self):
        if self._subset_idx < len(self._subset_steps) - 1:
            self._subset_idx += 1
            self._show_subset_step()

    def _show_min_step(self):
        if not self._min_steps:
            return
        self.auto_output.insert('end', f"\n[Min passo {self._min_idx+1}/{len(self._min_steps)}]\n")
        self.auto_output.insert('end', self._min_steps[self._min_idx] + "\n")
        parts = None
        if getattr(self, '_min_parts', None) and self._min_idx < len(self._min_parts):
            parts = self._min_parts[self._min_idx]
        self._draw_dfa_canvas(highlight=self._min_steps[self._min_idx], partitions=parts)

    def auto_min_prev(self):
        if self._min_idx > 0:
            self._min_idx -= 1
            self._show_min_step()

    def auto_min_next(self):
        if self._min_idx < len(self._min_steps) - 1:
            self._min_idx += 1
            self._show_min_step()

    def _draw_dfa_canvas(self, highlight: str = '', partitions=None):
        # Desenha DFA (ou NFA se selecionado) com destaques básicos
        if not (self._auto_dfa or self._auto_nfa):
            self.auto_canvas.delete('all')
            return
        view = getattr(self, 'auto_view', None).get() if hasattr(self, 'auto_view') else 'dfa'
        if view == 'nfa' and self._auto_nfa:
            nfa = self._auto_nfa
            states = list({nfa.start} | set(nfa.accepts) | {s for (s,_), _ in nfa.trans.items()} | {t for _, S in nfa.trans.items() for t in S})
            idx = {s:i for i,s in enumerate(states)}
            cols = max(1, int(len(states)**0.5))
            HSPACE = 140; VSPACE = 120; R = 18
            def pos(i):
                r = i // cols; c = i % cols
                return (40 + c*HSPACE, 40 + r*VSPACE)
            self.auto_canvas.delete('all')
            for (s, sym), T in nfa.trans.items():
                for t in T:
                    x1,y1 = pos(idx[s]); x2,y2 = pos(idx[t])
                    self.auto_canvas.create_line(x1, y1, x2, y2, fill='#555', arrow='last')
                    self.auto_canvas.create_text((x1+x2)/2, (y1+y2)/2 - 6, text=(sym or 'ε'), fill='#111')
            for s in states:
                x,y = pos(idx[s])
                outline = '#16a34a' if s in nfa.accepts else '#111'
                self.auto_canvas.create_oval(x-R, y-R, x+R, y+R, outline=outline, width=3, fill='#fff')
                if s == nfa.start:
                    self.auto_canvas.create_line(x-30, y, x-R, y, arrow='last')
                self.auto_canvas.create_text(x, y, text=f"q{idx[s]}")
            return
        dfa = self._auto_dfa
        states = list({dfa.start} | {s for s,_ in dfa.trans.keys()} | set(dfa.trans.values()))
        idx = {s:i for i,s in enumerate(states)}
        n = len(states)
        cols = max(1, int(n**0.5))
        HSPACE = 140; VSPACE = 120; R = 18
        def pos(i):
            r = i // cols; c = i % cols
            return (40 + c*HSPACE, 40 + r*VSPACE)
        self.auto_canvas.delete('all')
        # parse highlight
        edge_hi = None
        node_hi = set()
        import re
        m = re.search(r"Transição: q(\d+) --(.)--> q(\d+)", highlight)
        if m:
            edge_hi = (int(m.group(1)), int(m.group(3)), m.group(2))
        m2 = re.search(r"Novo estado q(\d+)", highlight)
        if m2:
            node_hi.add(int(m2.group(1)))
        # build partition color map
        color_palette = ['#ef4444','#22c55e','#3b82f6','#f59e0b','#8b5cf6','#06b6d4','#84cc16','#e879f9']
        part_color = {}
        if partitions:
            for pi, block in enumerate(partitions):
                col = color_palette[pi % len(color_palette)]
                for sid in block:
                    part_color[sid] = col
        for (s,a),t in dfa.trans.items():
            x1,y1 = pos(idx[s]); x2,y2 = pos(idx[t])
            mx,my = (x1+x2)/2, (y1+y2)/2
            base_edge = part_color.get(idx[s], '#555')
            color = '#d97706' if edge_hi and edge_hi[0]==idx[s] and edge_hi[1]==idx[t] else base_edge
            self.auto_canvas.create_line(x1, y1, x2, y2, fill=color, arrow='last')
            self.auto_canvas.create_text(mx, (y1+y2)/2 - 6, text=a, fill='#111')
        for s in states:
            x,y = pos(idx[s])
            base = part_color.get(idx[s], '#111')
            outline = '#d946ef' if idx[s] in node_hi else (base if base != '#111' else ('#16a34a' if s in dfa.accepts else '#111'))
            self.auto_canvas.create_oval(x-R, y-R, x+R, y+R, outline=outline, width=3, fill='#fff')
            if s == dfa.start:
                self.auto_canvas.create_line(x-30, y, x-R, y, arrow='last')
            self.auto_canvas.create_text(x, y, text=f"q{idx[s]}")

    def export_nfa_svg(self):
        if not self._auto_nfa:
            messagebox.showinfo('Info','Construa o automato primeiro.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.svg', filetypes=[('SVG','.svg')])
        if not path:
            return
        try:
            lib = _load_module('labs/11_automatos/automata_lib.py', 'auto_lib')
            lib.automaton_to_svg_nfa(self._auto_nfa, self._auto_alpha or set(), path)
            messagebox.showinfo('OK', 'SVG exportado.')
        except Exception as e:
            messagebox.showerror('Erro', str(e))

    def load_regex_bank(self):
        # Lê labs/11_automatos/regex_bank.txt e popula o combobox
        self.regex_combo.set('')
        try:
            bank_path = os.path.join(BASE_DIR, 'labs', '11_automatos', 'regex_bank.txt')
            examples = []
            if os.path.isfile(bank_path):
                with open(bank_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if not s or s.startswith('#'):
                            continue
                        parts = [p.strip() for p in s.split(';')]
                        if not parts:
                            continue
                        regex = parts[0]
                        acc = parts[1] if len(parts) > 1 else ''
                        rej = parts[2] if len(parts) > 2 else ''
                        examples.append((regex, acc, rej))
            self._regex_examples = examples
            self.regex_combo['values'] = [e[0] for e in examples]
            if examples:
                self.regex_combo.current(0)
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao carregar regex_bank: {e}')

    def use_selected_regex(self):
        try:
            idx = self.regex_combo.current()
            if idx < 0:
                return
            regex, acc, rej = self._regex_examples[idx]
            self.re_input.delete(0, 'end')
            self.re_input.insert(0, regex)
            # preenche teste com primeiro aceito, se existir
            sample = ''
            if acc:
                sample = acc.split(',')[0].strip()
            self.re_test.delete(0, 'end')
            if sample:
                self.re_test.insert(0, sample)
        except Exception as e:
            messagebox.showerror('Erro', f'Falha ao usar exemplo: {e}')

    def fill_automata_example(self):
        try:
            if hasattr(self, 're_input'):
                self.re_input.delete(0, 'end'); self.re_input.insert(0, '(a|b)*abb')
            if hasattr(self, 're_test'):
                self.re_test.delete(0, 'end'); self.re_test.insert(0, 'abb')
            if hasattr(self, 'auto_output'):
                self.auto_output.delete('1.0','end')
                self.auto_output.insert('end', 'Exemplo preenchido. Clique em "Construir" e depois "Testar Cadeia".\n')
        except Exception as e:
            try:
                messagebox.showerror('Erro', f'Falha ao preencher exemplo: {e}')
            except Exception:
                pass

    def fill_automata_example2(self):
        try:
            if hasattr(self, 're_input'):
                self.re_input.delete(0, 'end'); self.re_input.insert(0, 'a(b|c)+')
            if hasattr(self, 're_test'):
                self.re_test.delete(0, 'end'); self.re_test.insert(0, 'ab')
            if hasattr(self, 'auto_output'):
                self.auto_output.delete('1.0','end')
                self.auto_output.insert('end', 'Exemplo 2 preenchido. Clique em "Construir" e depois "Testar Cadeia".\n')
        except Exception as e:
            try:
                messagebox.showerror('Erro', f'Falha ao preencher exemplo 2: {e}')
            except Exception:
                pass

    # ===== CFG / Grafos =====
    def _build_cfg_tab(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="CFG a partir de TAC com LABEL/JMP/CJMP").pack(anchor='w', padx=8, pady=4)
        self.cfg_input = tk.Text(frame, height=10)
        self.cfg_input.pack(fill='x', padx=8)
        btns = ttk.Frame(frame)
        btns.pack(fill='x', padx=8, pady=6)
        ttk.Button(btns, text='Gerar CFG', command=self.run_cfg).pack(side='left')
        ttk.Button(btns, text='Vivacidade (IN/OUT)', command=self.run_liveness).pack(side='left', padx=6)
        ttk.Button(btns, text='Intervalos lineares', command=self.run_intervals).pack(side='left')
        ttk.Button(btns, text='Exemplo 1', command=self.fill_cfg_example).pack(side='right')
        ttk.Button(btns, text='Exemplo 2', command=self.fill_cfg_example2).pack(side='right', padx=6)
        ttk.Label(frame, text="Dica: gere CFG e depois Vivacidade; IN/OUT ajuda DCE e Intervalos ajudam na alocação de registradores.").pack(anchor='w', padx=8, pady=(2,0))
        self.cfg_output = tk.Text(frame)
        self.cfg_output.pack(fill='both', expand=True, padx=8, pady=6)
        return frame

    def run_cfg(self):
        self.cfg_output.delete('1.0','end')
        try:
            code = []
            for line in self.cfg_input.get('1.0','end').splitlines():
                s = line.strip()
                if not s: continue
                parts = s.split()
                op = parts[0].upper()
                args = tuple(parts[1:])
                code.append((op, args))
            lab12 = _load_module('labs/12_grafos/cfg_builder_template.py', 'lab12_cfg')
            blocks = lab12.split_basic_blocks(code)
            cfg = lab12.build_cfg(blocks)
            for b in blocks:
                self.cfg_output.insert('end', f"Bloco {b.label}: {len(b.instrs)} instrs\n")
            self.cfg_output.insert('end', '\nCFG:\n')
            for k,v in cfg.items():
                self.cfg_output.insert('end', f"  {k} -> {sorted(list(v))}\n")
        except Exception as e:
            self.cfg_output.insert('end', f"Erro: {e}\n")

    def _parse_cfg_input(self):
        code = []
        for line in self.cfg_input.get('1.0','end').splitlines():
            s = line.strip()
            if not s:
                continue
            parts = s.split()
            op = parts[0].upper()
            args = tuple(parts[1:])
            code.append((op, args))
        return code

    def run_liveness(self):
        self.cfg_output.delete('1.0','end')
        try:
            code = self._parse_cfg_input()
            lab12 = _load_module('labs/12_grafos/cfg_builder_template.py', 'lab12_cfg')
            live = _load_module('labs/12_grafos/liveness_template.py', 'lab12_live')
            blocks = lab12.split_basic_blocks(code)
            cfg = lab12.build_cfg(blocks)
            blocks_by_label = {b.label: b.instrs for b in blocks}
            IN, OUT, USE, DEF = live.liveness(blocks_by_label, cfg)
            self.cfg_output.insert('end', 'CFG:\n')
            for k,v in cfg.items():
                self.cfg_output.insert('end', f"  {k} -> {sorted(list(v))}\n")
            self.cfg_output.insert('end', '\nUSE/DEF:\n')
            for b in blocks_by_label:
                self.cfg_output.insert('end', f"  {b}: USE={sorted(list(USE[b]))} DEF={sorted(list(DEF[b]))}\n")
            self.cfg_output.insert('end', '\nIN/OUT:\n')
            for b in blocks_by_label:
                self.cfg_output.insert('end', f"  {b}: IN={sorted(list(IN[b]))} OUT={sorted(list(OUT[b]))}\n")
        except Exception as e:
            self.cfg_output.insert('end', f"Erro: {e}\n")

    def run_intervals(self):
        self.cfg_output.delete('1.0','end')
        try:
            code = self._parse_cfg_input()
            live = _load_module('labs/12_grafos/liveness_template.py', 'lab12_live')
            ivals = live.live_intervals_linear(code)
            self.cfg_output.insert('end', 'Intervalos lineares (posições start..end):\n')
            for t, (a,b) in sorted(ivals.items()):
                self.cfg_output.insert('end', f"  {t}: {a}..{b}\n")
        except Exception as e:
            self.cfg_output.insert('end', f"Erro: {e}\n")

    def fill_cfg_example(self):
        try:
            example = """
LABEL L0
MOVI 1 t1
MOVI 2 t2
ADD t1 t2 t3
CJMP t3 L1
MUL t3 t2 t4
JMP L2
LABEL L1
ADD t1 t1 t4
LABEL L2
MOV t4 x
""".strip()
            self.cfg_input.delete('1.0','end')
            self.cfg_input.insert('end', example + "\n")
            self.cfg_output.delete('1.0','end')
            self.cfg_output.insert('end', 'Exemplo preenchido. Clique em Gerar CFG ou Vivacidade.\n')
        except Exception as e:
            self.cfg_output.insert('end', f"Erro ao preencher exemplo: {e}\n")

    def fill_cfg_example2(self):
        try:
            example = """
LABEL L0
MOVI 1 t1
CJMP t1 L1
MOVI 0 t2
JMP L2
LABEL L1
MOVI 2 t2
CJMP t2 L3
ADD t1 t2 t3
JMP L2
LABEL L3
MUL t1 t2 t3
LABEL L2
MOV t3 x
""".strip()
            self.cfg_input.delete('1.0','end')
            self.cfg_input.insert('end', example + "\n")
            self.cfg_output.delete('1.0','end')
            self.cfg_output.insert('end', 'Exemplo 2 preenchido. Clique em Gerar CFG/Vivacidade/Intervalos.\n')
        except Exception as e:
            self.cfg_output.insert('end', f"Erro ao preencher exemplo 2: {e}\n")

    # ===== Projeto =====
    def _build_project_tab(self, parent):
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="Projeto guiado (Aulas 13–15): veja CURSO.md; integre léxico→sintaxe→semântica→IR→Codegen→Otim.→Back-end.").pack(anchor='w', padx=8, pady=8)
        return frame


if __name__ == "__main__":
    App().mainloop()
