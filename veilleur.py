#!/usr/bin/env python3
"""
Le Veilleur — gardien de ton réseau (famille Tisseur)

Pendant que Tisseur AUDITE une cible, Le Veilleur PROTÈGE ton propre
réseau : il regarde qui est connecté chez toi et t'AVERTIT dès qu'un
appareil INCONNU apparaît.

⚠️ À utiliser seulement sur TON réseau (celui que tu possèdes). Scanner
le réseau de quelqu'un d'autre sans permission, c'est pas correct.

USAGE :
    python3 veilleur.py                 -> un scan + rapport (interactif)
    python3 veilleur.py --watch         -> surveille en continu (boucle)
    python3 veilleur.py --watch 30      -> surveille, scan aux 30 secondes
    python3 veilleur.py --liste         -> montre les appareils connus
    python3 veilleur.py --oui           -> fait confiance aux appareils actuels
    python3 veilleur.py --reseau 192.168.0.0/24   -> précise le réseau
    python3 veilleur.py --ia            -> l'IA locale commente les inconnus

RÉUTILISE les pièces de Tisseur : thème, notifications, IA locale.
"""

import argparse
import subprocess
import sys
import os
import re
import json
import time
import shutil
import datetime

# On réutilise les pièces déjà bâties dans tisseurkit.
from tisseurkit.theme import colore, SIGNATURE, C_NET, C_OK, C_ERR, C_DEL, C_HELP, C_SCAN, C_GAMER, MUTED_HEX, BORDURE_HEX, ACCENT_HEX
from tisseurkit.outils import notifier, detect_gestionnaire

FICHIER_CONNUS = "veilleur_connus.json"

LOGO_VEILLEUR = r"""
 _   _ ___ ___ _    _    ___ _   _ ___
| | | | __|_ _| |  | |  | __| | | | _ \
| |_| | _| | || |__| |__| _|| |_| |   /
 \___/|___|___|____|____|___|\___/|_|_\
"""


def print_banner():
    tty = sys.stdout.isatty()
    lignes = LOGO_VEILLEUR.strip("\n").split("\n")
    largeur = max(len(l) for l in lignes)
    for l in lignes:
        print(colore(l, C_OK, tty))
    print(colore("— le gardien de ton réseau —".center(largeur), C_SCAN, tty))
    print(colore(SIGNATURE.center(largeur), MUTED_HEX, tty))
    print()


# ============================================================
# DÉTECTION DU RÉSEAU LOCAL
# ============================================================
def detect_reseau():
    """Essaie de trouver le sous-réseau local, ex: 192.168.0.0/24."""
    try:
        out = subprocess.run(["ip", "-o", "-f", "inet", "addr", "show"],
                             capture_output=True, text=True, timeout=10).stdout
        # Cherche une adresse privée en /24 (on ignore loopback 127.)
        for m in re.finditer(r"inet (\d+\.\d+\.\d+)\.\d+/(\d+)", out):
            base, masque = m.group(1), m.group(2)
            if not base.startswith("127."):
                return f"{base}.0/{masque if masque == '24' else '24'}"
    except Exception:
        pass
    return None


# ============================================================
# SCAN DES APPAREILS (plusieurs méthodes, la meilleure dispo)
# ============================================================
def _scan_arpscan(reseau):
    out = subprocess.run(["arp-scan", reseau] if reseau else ["arp-scan", "--localnet"],
                         capture_output=True, text=True, timeout=120).stdout
    appareils = []
    for ligne in out.splitlines():
        m = re.match(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]{17})\s*(.*)", ligne)
        if m:
            appareils.append({"ip": m.group(1), "mac": m.group(2).lower(),
                              "nom": (m.group(3) or "").strip()})
    return appareils


def _scan_nmap(reseau):
    out = subprocess.run(["nmap", "-sn", reseau], capture_output=True, text=True, timeout=180).stdout
    appareils = []
    ip = None
    for ligne in out.splitlines():
        m_ip = re.search(r"Nmap scan report for (?:.*\()?(\d+\.\d+\.\d+\.\d+)\)?", ligne)
        if m_ip:
            ip = m_ip.group(1)
        m_mac = re.search(r"MAC Address: ([0-9A-Fa-f:]{17})\s*\(([^)]*)\)", ligne)
        if m_mac and ip:
            appareils.append({"ip": ip, "mac": m_mac.group(1).lower(), "nom": m_mac.group(2).strip()})
            ip = None
    return appareils


def _scan_ipneigh():
    out = subprocess.run(["ip", "neigh"], capture_output=True, text=True, timeout=15).stdout
    appareils = []
    for ligne in out.splitlines():
        m = re.search(r"(\d+\.\d+\.\d+\.\d+).*lladdr ([0-9a-fA-F:]{17})", ligne)
        if m:
            appareils.append({"ip": m.group(1), "mac": m.group(2).lower(), "nom": ""})
    return appareils


def scanner(reseau, output=print):
    """Renvoie la liste des appareils connectés, avec la meilleure méthode dispo."""
    tty = (output is print) and sys.stdout.isatty()
    try:
        if shutil.which("arp-scan"):
            output(colore("Scan avec arp-scan…", MUTED_HEX, tty))
            return _scan_arpscan(reseau)
        if shutil.which("nmap") and reseau:
            output(colore("Scan avec nmap…", MUTED_HEX, tty))
            return _scan_nmap(reseau)
        if shutil.which("ip"):
            output(colore("Scan via la table ARP (ip neigh)…", MUTED_HEX, tty))
            return _scan_ipneigh()
    except subprocess.TimeoutExpired:
        output(colore("⚠️ Scan trop long (timeout).", C_DEL, tty))
    except Exception as e:
        output(colore(f"⚠️ Erreur de scan : {e}", C_DEL, tty))
    return []


# ============================================================
# APPAREILS CONNUS (mémoire, fichier JSON)
# ============================================================
def charger_connus():
    if os.path.exists(FICHIER_CONNUS):
        try:
            with open(FICHIER_CONNUS) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def sauver_connus(connus):
    with open(FICHIER_CONNUS, "w") as f:
        json.dump(connus, f, indent=2, ensure_ascii=False)


def ajouter_connu(connus, app, etiquette=""):
    connus[app["mac"]] = {
        "ip": app["ip"],
        "nom": app.get("nom", ""),
        "etiquette": etiquette,
        "premier_vu": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ============================================================
# IA : commenter un appareil inconnu (optionnel)
# ============================================================
def commenter_ia(app, ia):
    from tisseurkit.ia import _ia_generate
    prompt = (
        "Tu es un assistant en cybersécurité défensive. Un appareil INCONNU vient "
        "d'apparaître sur le réseau personnel de l'utilisateur. D'après son adresse "
        "MAC et son nom, dis en 2-3 lignes EN FRANÇAIS quel type d'appareil ou quel "
        "fabricant c'est probablement, et si l'utilisateur devrait s'en inquiéter. "
        "Reste prudent et factuel.\n\n"
        f"IP : {app['ip']}\nMAC : {app['mac']}\nNom/vendor : {app.get('nom','(inconnu)')}\n"
    )
    try:
        return _ia_generate(prompt, ia, timeout=120)
    except Exception:
        return None


# ============================================================
# UN PASSAGE DE SURVEILLANCE
# ============================================================
def un_passage(reseau, connus, ia=None, baseline_ok=False, output=print):
    tty = (output is print) and sys.stdout.isatty()
    appareils = scanner(reseau, output=output)

    if not appareils:
        output(colore("Aucun appareil détecté (droits root nécessaires pour arp-scan/nmap ?).", C_DEL, tty))
        return connus, []

    inconnus = [a for a in appareils if a["mac"] not in connus]

    output(colore(f"{len(appareils)} appareil(s) sur le réseau, {len(inconnus)} inconnu(s).", C_NET, tty))

    # Premier passage sans base connue : on établit la liste de confiance.
    if not connus:
        if baseline_ok:
            # --oui : on fait confiance à tout le monde en silence.
            for a in appareils:
                ajouter_connu(connus, a)
            sauver_connus(connus)
            output(colore(f"✅ Base établie ({len(appareils)} appareils de confiance). "
                          "Je t'avertirai pour tout NOUVEL appareil.", C_OK, tty))
            return connus, []
        output("")
        output(colore("Première fois : voici les appareils actuels.", C_HELP, tty))
        for a in appareils:
            output(f"   {a['ip']:<16} {a['mac']}  {a.get('nom','')}")
        rep = input(colore("\nLes faire confiance comme appareils connus ? (O/n) : ", C_SCAN, tty)).strip().lower()
        if rep in ("", "o", "oui", "y", "yes"):
            for a in appareils:
                ajouter_connu(connus, a)
            sauver_connus(connus)
            output(colore("✅ Base établie. Je t'avertirai pour tout NOUVEL appareil.", C_OK, tty))
        return connus, []

    # Passages suivants : on alerte sur les inconnus.
    if inconnus:
        output("")
        output(colore("=" * 56, BORDURE_HEX, tty))
        output(colore(f"🚨 {len(inconnus)} APPAREIL(S) INCONNU(S) DÉTECTÉ(S)", C_ERR, tty))
        output(colore("=" * 56, BORDURE_HEX, tty))
        for a in inconnus:
            output(colore(f"   {a['ip']:<16} {a['mac']}  {a.get('nom','')}", C_DEL, tty))
            if ia:
                avis = commenter_ia(a, ia)
                if avis:
                    output(colore("   🤖 " + avis.strip().replace("\n", "\n      "), C_GAMER, tty))
        notifier("🛡️ Le Veilleur — appareil inconnu",
                 f"{len(inconnus)} nouvel appareil sur ton réseau")
    else:
        output(colore("✅ Rien de nouveau. Tout le monde est connu.", C_OK, tty))

    return connus, inconnus


# ============================================================
# MODE SURVEILLANCE CONTINUE
# ============================================================
def surveiller(reseau, intervalle, ia=None, output=print):
    tty = (output is print) and sys.stdout.isatty()
    connus = charger_connus()
    output(colore(f"👁️  Surveillance active (scan aux {intervalle}s). Ctrl+C pour arrêter.", C_SCAN, tty))
    # Premier passage pour établir/charger la base.
    connus, _ = un_passage(reseau, connus, ia=ia, output=output)
    try:
        while True:
            time.sleep(intervalle)
            horodatage = datetime.datetime.now().strftime("%H:%M:%S")
            output(colore(f"\n[{horodatage}] passage…", MUTED_HEX, tty))
            connus, inconnus = un_passage(reseau, connus, ia=ia, baseline_ok=True, output=output)
    except KeyboardInterrupt:
        output(colore("\nSurveillance arrêtée. 🫐", MUTED_HEX, tty))


# ============================================================
# ACTIONS SIMPLES
# ============================================================
def montrer_liste():
    tty = sys.stdout.isatty()
    connus = charger_connus()
    if not connus:
        print(colore("Aucun appareil connu pour l'instant. Lance un scan d'abord.", C_DEL, tty))
        return
    print(colore(f"{len(connus)} appareil(s) connu(s) :", C_NET, tty))
    for mac, info in connus.items():
        etiq = f"  [{info['etiquette']}]" if info.get("etiquette") else ""
        print(f"   {info.get('ip',''):<16} {mac}  {info.get('nom','')}{etiq}")


def main():
    parser = argparse.ArgumentParser(description="Le Veilleur — gardien de ton réseau")
    parser.add_argument("--watch", nargs="?", const=60, type=int, default=None,
                         metavar="SECONDES", help="Surveille en continu (défaut: 60s)")
    parser.add_argument("--reseau", default=None, help="Sous-réseau à scanner (ex: 192.168.0.0/24)")
    parser.add_argument("--liste", action="store_true", help="Montre les appareils connus")
    parser.add_argument("--reset", action="store_true", help="Oublie tous les appareils connus")
    parser.add_argument("--oui", action="store_true", help="Fait confiance aux appareils actuels (base)")
    parser.add_argument("--ia", action="store_true", help="L'IA locale commente les appareils inconnus")
    parser.add_argument("--ia-moteur", default="ollama", choices=["ollama", "llamacpp"])
    parser.add_argument("--ia-modele", default=None)
    args = parser.parse_args()

    print_banner()

    if args.reset:
        if os.path.exists(FICHIER_CONNUS):
            os.remove(FICHIER_CONNUS)
        print(colore("🧹 Liste des appareils connus effacée.", C_OK, sys.stdout.isatty()))
        return

    if args.liste:
        montrer_liste()
        return

    ia = None
    if args.ia:
        ia = {"moteur": args.ia_moteur, "modele": args.ia_modele, "url": None}

    reseau = args.reseau or detect_reseau()
    tty = sys.stdout.isatty()
    if reseau:
        print(colore(f"Réseau : {reseau}", MUTED_HEX, tty))
    else:
        print(colore("Réseau non détecté — précise-le avec --reseau 192.168.x.0/24", C_DEL, tty))

    if args.watch is not None:
        surveiller(reseau, args.watch, ia=ia)
        return

    # Un seul passage.
    connus = charger_connus()
    connus, inconnus = un_passage(reseau, connus, ia=ia, baseline_ok=args.oui)
    if args.oui and inconnus:
        for a in inconnus:
            ajouter_connu(connus, a)
        sauver_connus(connus)


if __name__ == "__main__":
    main()
