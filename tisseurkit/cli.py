import argparse
import sys

from .theme import print_banner
from .etapes import STEPS
from .guide import show_guide_terminal
from .outils import verifier_outils
from .pipeline import run_pipeline
from .menu import interactive_menu, lancer_chat_sur_dernier_rapport
from .gui import launch_gui

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
                         help="Génère aussi un rapport HTML (thème néon) en plus du .md")
    parser.add_argument("--html-pro", action="store_true",
                         help="Génère un rapport HTML thème PRO (sobre, corporatif)")
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

    html_out = args.html or args.html_pro
    html_theme = "pro" if args.html_pro else "neon"

    run_pipeline(args.target, args.url, args.modules, ia=ia,
                 assume_yes=args.oui, html_out=html_out, chat=args.chat,
                 mission=args.mission, html_theme=html_theme)
