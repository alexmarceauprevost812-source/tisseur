import sys
import subprocess
import datetime

from .theme import colore, ACCENT_HEX, MUTED_HEX, BORDURE_HEX, C_NET, C_OK, C_DL, MODULE_COULEURS
from .etapes import STEPS
from .ia import analyse_ia, chat_ia
from .outils import verifier_outils, confirmer_autorisation, notifier
from .rapport import generer_html

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
