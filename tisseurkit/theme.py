import sys

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
