import sys

from .theme import colore, MUTED_HEX, C_DEL, print_banner
from .pipeline import run_pipeline
from .ia import chat_ia
from .rapport import dernier_rapport
from .guide import show_guide_terminal
from .gui import launch_gui

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
    """Demande les options de fin de scan. Renvoie (ia, html, chat, mission, theme)."""
    mission = input("Rapport de mission / objectif (optionnel, pour diriger l'IA) : ").strip()
    ia = _demander_moteur_ia() if _oui("Analyse IA locale à la fin ? (o/N) : ") else None
    rep = input("Rapport HTML ? 0) non (défaut)  1) néon  2) pro : ").strip()
    html_out = rep in ("1", "2")
    theme = "pro" if rep == "2" else "neon"
    chat = bool(ia) and _oui("Ouvrir le chat IA après le scan ? (o/N) : ")
    return ia, html_out, chat, mission, theme


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
                ia, html_out, chat, mission, theme = _demander_options()
                run_pipeline(target, None, None, ia=ia, html_out=html_out, chat=chat,
                             mission=mission, html_theme=theme)
            break
        elif choix == "2":
            target = input("IP de la cible : ").strip()
            mods = input("Modules (séparés par virgule, ex: Reconnaissance,Scanning) : ").strip()
            if target:
                ia, html_out, chat, mission, theme = _demander_options()
                run_pipeline(target, None, mods or None, ia=ia, html_out=html_out, chat=chat,
                             mission=mission, html_theme=theme)
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
