import sys
import threading
import queue

from .theme import (ACCENT_HEX, NOIR_HEX, TEXTE_HEX, MUTED_HEX, BORDURE_HEX,
                    C_NET, C_HELP, C_DL, C_SCAN, C_GAMER, MODULE_COULEURS, SIGNATURE)
from .etapes import STEPS
from .pipeline import run_pipeline
from .guide import get_guide_text

# ============================================================
# INTERFACE GRAPHIQUE (Tkinter — tourne sur ton appareil, pas
# besoin du terminal une fois lancée)
# ============================================================
def launch_gui():
    try:
        import tkinter as tk
        from tkinter import scrolledtext, messagebox
    except ImportError:
        print("Tkinter n'est pas installé.")
        print("Sur Kali/Debian : sudo apt install python3-tk")
        sys.exit(1)

    class TisseurApp:
        def __init__(self, root):
            self.root = root
            root.title("Tisseur")
            root.configure(bg=NOIR_HEX)
            root.geometry("820x660")

            self.msg_queue = queue.Queue()

            tk.Label(
                root, text="TISSEUR", font=("Arial Black", 30, "bold"),
                fg=ACCENT_HEX, bg=NOIR_HEX,
            ).pack(pady=(14, 0))
            tk.Label(
                root, text="tisse tes commandes de pentest, une à la fois",
                font=("Arial", 10, "italic"), fg=C_SCAN, bg=NOIR_HEX,
            ).pack(pady=(0, 0))
            tk.Label(
                root, text=SIGNATURE,
                font=("Arial", 9), fg=MUTED_HEX, bg=NOIR_HEX,
            ).pack(pady=(0, 10))

            form = tk.Frame(root, bg=NOIR_HEX)
            form.pack(fill="x", padx=16)

            entry_style = dict(bg="#161616", fg=TEXTE_HEX, insertbackground=ACCENT_HEX,
                               relief="flat", highlightthickness=1,
                               highlightbackground=BORDURE_HEX, highlightcolor=ACCENT_HEX)

            tk.Label(form, text="Cible (IP) :", fg=TEXTE_HEX, bg=NOIR_HEX).grid(row=0, column=0, sticky="w")
            self.target_var = tk.StringVar()
            target_entry = tk.Entry(form, textvariable=self.target_var, width=28, **entry_style)
            target_entry.grid(row=0, column=1, sticky="w", padx=8, pady=3)
            self._add_context_menu(target_entry)

            tk.Label(form, text="URL (optionnel) :", fg=TEXTE_HEX, bg=NOIR_HEX).grid(row=1, column=0, sticky="w")
            self.url_var = tk.StringVar()
            url_entry = tk.Entry(form, textvariable=self.url_var, width=28, **entry_style)
            url_entry.grid(row=1, column=1, sticky="w", padx=8, pady=3)
            self._add_context_menu(url_entry)

            tk.Label(form, text="Mission (optionnel) :", fg=TEXTE_HEX, bg=NOIR_HEX).grid(row=2, column=0, sticky="w")
            self.mission_var = tk.StringVar()
            mission_entry = tk.Entry(form, textvariable=self.mission_var, width=28, **entry_style)
            mission_entry.grid(row=2, column=1, sticky="w", padx=8, pady=3)
            self._add_context_menu(mission_entry)
            tk.Label(form, text="(objectif donné à l'IA)", fg=MUTED_HEX, bg=NOIR_HEX).grid(row=2, column=2, sticky="w")

            mod_frame = tk.LabelFrame(root, text="Modules", fg=C_SCAN, bg=NOIR_HEX, labelanchor="nw")
            mod_frame.pack(fill="x", padx=16, pady=8)

            self.module_vars = {}
            all_modules = sorted(set(s[0] for s in STEPS))
            for i, mod in enumerate(all_modules):
                var = tk.BooleanVar(value=True)
                coul = MODULE_COULEURS.get(mod, TEXTE_HEX)
                tk.Checkbutton(
                    mod_frame, text=mod, variable=var, fg=coul, bg=NOIR_HEX,
                    selectcolor="#161616", activebackground=NOIR_HEX, activeforeground=coul,
                ).grid(row=0, column=i, padx=6, pady=4, sticky="w")
                self.module_vars[mod] = var

            # --- Panneau IA locale ---
            ia_frame = tk.LabelFrame(root, text="IA locale (analyse)", fg=C_GAMER, bg=NOIR_HEX, labelanchor="nw")
            ia_frame.pack(fill="x", padx=16, pady=(0, 8))

            self.ia_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                ia_frame, text="Analyser le rapport avec une IA locale à la fin",
                variable=self.ia_var, fg=C_GAMER, bg=NOIR_HEX,
                selectcolor="#161616", activebackground=NOIR_HEX, activeforeground=C_GAMER,
            ).grid(row=0, column=0, columnspan=4, padx=6, pady=(4, 0), sticky="w")

            tk.Label(ia_frame, text="Moteur :", fg=TEXTE_HEX, bg=NOIR_HEX).grid(row=1, column=0, padx=6, pady=4, sticky="w")
            self.ia_moteur_var = tk.StringVar(value="ollama")
            tk.OptionMenu(ia_frame, self.ia_moteur_var, "ollama", "llamacpp").grid(row=1, column=1, padx=4, pady=4, sticky="w")

            tk.Label(ia_frame, text="Modèle :", fg=TEXTE_HEX, bg=NOIR_HEX).grid(row=1, column=2, padx=6, pady=4, sticky="w")
            self.ia_modele_var = tk.StringVar(value="llama3")
            tk.Entry(ia_frame, textvariable=self.ia_modele_var, width=16, **entry_style).grid(row=1, column=3, padx=4, pady=4, sticky="w")

            self.html_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                ia_frame, text="Rapport HTML",
                variable=self.html_var, fg=C_DL, bg=NOIR_HEX,
                selectcolor="#161616", activebackground=NOIR_HEX, activeforeground=C_DL,
            ).grid(row=2, column=0, columnspan=2, padx=6, pady=(0, 4), sticky="w")

            self.html_pro_var = tk.BooleanVar(value=False)
            tk.Checkbutton(
                ia_frame, text="thème pro (sobre/corporatif)",
                variable=self.html_pro_var, fg=C_DL, bg=NOIR_HEX,
                selectcolor="#161616", activebackground=NOIR_HEX, activeforeground=C_DL,
            ).grid(row=2, column=2, columnspan=2, padx=6, pady=(0, 4), sticky="w")

            btn_frame = tk.Frame(root, bg=NOIR_HEX)
            btn_frame.pack(fill="x", padx=16, pady=4)

            self.launch_btn = tk.Button(
                btn_frame, text="Lancer", command=self.launch,
                bg=C_NET, fg="#0A0A0A", activebackground=C_SCAN, activeforeground="#0A0A0A",
                font=("Arial", 11, "bold"), relief="flat", padx=12,
            )
            self.launch_btn.pack(side="left")

            tk.Button(
                btn_frame, text="Guide", command=self.show_guide,
                bg="#161616", fg=C_HELP, activebackground="#1E1E1E", activeforeground=C_HELP,
                relief="flat", padx=12,
            ).pack(side="left", padx=8)

            tk.Button(
                btn_frame, text="Copier le rapport", command=self.copy_output,
                bg="#161616", fg=C_DL, activebackground="#1E1E1E", activeforeground=C_DL,
                relief="flat", padx=12,
            ).pack(side="left")

            self.output = scrolledtext.ScrolledText(
                root, bg="#070707", fg=TEXTE_HEX, insertbackground=ACCENT_HEX, font=("Consolas", 10),
            )
            self.output.pack(fill="both", expand=True, padx=16, pady=(8, 16))
            self._add_context_menu(self.output)

            self.root.after(100, self.poll_queue)

        def _add_context_menu(self, widget):
            # Menu clic-droit + raccourcis clavier fiables (indépendants du
            # layout du clavier, contrairement aux bindings Ctrl par défaut).
            import tkinter as tk
            menu = tk.Menu(widget, tearoff=0)
            menu.add_command(label="Couper", command=lambda: widget.event_generate("<<Cut>>"))
            menu.add_command(label="Copier", command=lambda: widget.event_generate("<<Copy>>"))
            menu.add_command(label="Coller", command=lambda: widget.event_generate("<<Paste>>"))
            menu.add_separator()
            menu.add_command(label="Tout sélectionner",
                             command=lambda: self._select_all(widget))

            def popup(event):
                widget.focus_set()
                menu.tk_popup(event.x_root, event.y_root)

            widget.bind("<Button-3>", popup)   # clic droit (Windows/Linux)
            widget.bind("<Button-2>", popup)   # clic droit (macOS)
            widget.bind("<Control-a>", lambda e: (self._select_all(widget), "break")[1])
            widget.bind("<Control-A>", lambda e: (self._select_all(widget), "break")[1])

        @staticmethod
        def _select_all(widget):
            try:
                if isinstance(widget, scrolledtext.ScrolledText):
                    widget.tag_add("sel", "1.0", "end-1c")
                else:
                    widget.select_range(0, "end")
                    widget.icursor("end")
            except Exception:
                pass

        def copy_output(self):
            text = self.output.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

        def log(self, text):
            self.msg_queue.put(text)

        def poll_queue(self):
            try:
                while True:
                    line = self.msg_queue.get_nowait()
                    self.output.insert("end", str(line) + "\n")
                    self.output.see("end")
            except queue.Empty:
                pass
            self.root.after(100, self.poll_queue)

        def show_guide(self):
            win = tk.Toplevel(self.root)
            win.title("Guide — Tisseur")
            win.configure(bg=NOIR_HEX)
            win.geometry("620x480")
            txt = scrolledtext.ScrolledText(win, bg="#070707", fg=TEXTE_HEX, font=("Consolas", 10))
            txt.pack(fill="both", expand=True, padx=10, pady=10)
            txt.insert("end", get_guide_text())
            txt.config(state="disabled")

        def launch(self):
            target = self.target_var.get().strip()
            if not target:
                messagebox.showwarning("Tisseur", "Entre une IP de cible.")
                return
            url = self.url_var.get().strip() or None
            selected = [m for m, v in self.module_vars.items() if v.get()]
            if not selected:
                messagebox.showwarning("Tisseur", "Sélectionne au moins un module.")
                return
            modules_str = ",".join(selected)

            # Confirmation d'autorisation (éthique).
            if not messagebox.askyesno(
                "Autorisation",
                f"As-tu l'autorisation EXPLICITE de tester {target} ?\n\n"
                "Teste seulement ce que tu possèdes ou as le droit de tester.",
            ):
                return

            mission = self.mission_var.get().strip()
            html_pro = self.html_pro_var.get()
            html_out = self.html_var.get() or html_pro
            html_theme = "pro" if html_pro else "neon"
            ia = None
            if self.ia_var.get():
                ia = {
                    "moteur": self.ia_moteur_var.get(),
                    "modele": self.ia_modele_var.get().strip() or None,
                    "url": None,
                }

            self.launch_btn.config(state="disabled")
            self.output.delete("1.0", "end")

            threading.Thread(
                target=self._run,
                args=(target, url, modules_str, ia, html_out, mission, html_theme),
                daemon=True,
            ).start()

        def _run(self, target, url, modules_str, ia=None, html_out=False, mission="", html_theme="neon"):
            # assume_yes=True : l'autorisation a déjà été confirmée par le dialogue.
            run_pipeline(target, url, modules_str, output=self.log, ia=ia,
                         assume_yes=True, html_out=html_out, mission=mission, html_theme=html_theme)
            self.root.after(0, lambda: self.launch_btn.config(state="normal"))

    root = tk.Tk()
    TisseurApp(root)
    root.mainloop()
