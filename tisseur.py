#!/usr/bin/env python3
"""
Tisseur — cours Hacking 101

Point d'entrée. Le vrai code est découpé en modules dans le dossier
« tisseurkit/ » (une pièce par fichier). Tu n'as rien à monter : Python
assemble les pièces tout seul quand tu lances ce fichier.

TROIS FAÇONS DE LE LANCER :
    python3 tisseur.py                          -> menu interactif (terminal)
    python3 tisseur.py --gui                    -> interface graphique (fenêtre)
    python3 tisseur.py --target <ip> [options]  -> mode direct (scripts/automatisation)

EXEMPLES :
    python3 tisseur.py --target 192.168.56.102 --ia --mission "CTF: trouver le flag"
    python3 tisseur.py /chat          # rouvrir le chat IA sur le dernier rapport
    python3 tisseur.py --guide        # afficher le guide

LES PIÈCES (dans tisseurkit/) :
    theme.py     couleurs, bannière        guide.py     guide / aide
    etapes.py    liste des étapes (STEPS)  menu.py      menu interactif
    pipeline.py  moteur (run_pipeline)     gui.py       interface graphique
    ia.py        analyse + chat IA         cli.py       options ligne de commande
    outils.py    vérif outils, notifs      rapport.py   rapport HTML

⚠️ À utiliser seulement sur des machines que tu possèdes ou que t'as
le droit explicite de tester (ton lab Metasploitable2, etc.)
"""

from tisseurkit.cli import main

if __name__ == "__main__":
    main()
