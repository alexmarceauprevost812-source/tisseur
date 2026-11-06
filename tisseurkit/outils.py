import os
import sys
import shutil
import subprocess

from .theme import colore, MUTED_HEX, C_OK, C_ERR, C_DEL, C_HELP, C_SCAN

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
