import sys

from .theme import colore, C_DEL, C_HELP, SIGNATURE

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
