import os
import glob
import html

from .theme import (ACCENT_HEX, NOIR_HEX, NOIR_SIDE_HEX, TEXTE_HEX, TEXTE2_HEX,
                    MUTED_HEX, BORDURE_HEX, C_SCAN, C_GAMER, MODULE_COULEURS, SIGNATURE)

# ============================================================
# RAPPORT HTML — deux thèmes (néon LEXOS / pro corporatif)
# ------------------------------------------------------------
# PLAFOND DE TAILLE : on tronque les sorties trop longues dans le
# HTML pour éviter un fichier géant (leçon de ti-lex v10). Le
# rapport .md, lui, garde TOUJOURS la sortie complète.
# ============================================================
HTML_MAX_SORTIE = 20000   # caractères max par étape dans le HTML


def _tronquer(texte, limite=HTML_MAX_SORTIE):
    """Coupe une sortie trop longue et ajoute un avis. Renvoie (texte, coupe?)."""
    if texte and len(texte) > limite:
        coupe = len(texte) - limite
        avis = (f"\n\n… [sortie tronquée : {coupe} caractères de plus — "
                f"voir le rapport .md complet]")
        return texte[:limite] + avis, True
    return texte, False


# Styles CSS par thème (on garde {{ }} pour les accolades littérales en f-string)
def _css_neon():
    return f"""
  :root {{ color-scheme: dark; }}
  body {{ background:{NOIR_HEX}; color:{TEXTE_HEX};
         font-family:ui-monospace,Consolas,monospace; margin:0; padding:24px; }}
  header {{ border-bottom:1px solid {BORDURE_HEX}; padding-bottom:16px; margin-bottom:16px; }}
  h1 {{ color:{ACCENT_HEX}; margin:0 0 4px; }}
  .sign {{ color:{MUTED_HEX}; font-size:.9em; }}
  .meta {{ color:{C_SCAN}; font-size:.9em; }}
  .mission {{ color:{C_GAMER}; font-size:.9em; margin-top:6px; }}
  .etape {{ background:{NOIR_SIDE_HEX}; border:1px solid {BORDURE_HEX};
            border-radius:8px; padding:12px 16px; margin:14px 0; }}
  .etape h2 {{ margin:0 0 8px; font-size:1.05em; }}
  .cmd {{ color:{MUTED_HEX}; margin-bottom:8px; }}
  pre {{ background:#070707; color:{TEXTE2_HEX}; padding:12px; border-radius:6px;
         overflow-x:auto; white-space:pre-wrap; word-break:break-word; margin:0; }}
  .ia pre {{ border-left:3px solid {C_GAMER}; }}
  footer {{ color:{MUTED_HEX}; font-size:.85em; margin-top:24px;
            border-top:1px solid {BORDURE_HEX}; padding-top:12px; }}
"""


def _css_pro():
    # Thème sobre/corporatif : fond clair, sans-serif, bleu marine.
    return """
  :root { color-scheme: light; }
  body { background:#f5f6f8; color:#1f2937;
         font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         margin:0; padding:32px; line-height:1.5; }
  .page { max-width:900px; margin:0 auto; }
  header { border-bottom:3px solid #1e3a5f; padding-bottom:18px; margin-bottom:24px; }
  h1 { color:#1e3a5f; margin:0 0 4px; font-size:1.6em; }
  .sign { color:#6b7280; font-size:.85em; }
  .meta { color:#374151; font-size:.95em; }
  .mission { color:#1e3a5f; font-weight:600; font-size:.95em; margin-top:8px;
             background:#eaf0f6; padding:8px 12px; border-radius:6px; }
  .etape { background:#ffffff; border:1px solid #e5e7eb; border-radius:8px;
           padding:16px 20px; margin:16px 0; box-shadow:0 1px 2px rgba(0,0,0,.04); }
  .etape h2 { margin:0 0 10px; font-size:1.05em; color:#1e3a5f;
              border-left:4px solid #1e3a5f; padding-left:10px; }
  .cmd { color:#6b7280; font-family:ui-monospace,Consolas,monospace;
         font-size:.9em; margin-bottom:10px; }
  pre { background:#f3f4f6; color:#111827; padding:14px; border-radius:6px;
        overflow-x:auto; white-space:pre-wrap; word-break:break-word; margin:0;
        font-size:.88em; border:1px solid #e5e7eb; }
  .ia { border-left:4px solid #1e3a5f; }
  .ia h2 { color:#1e3a5f; }
  footer { color:#6b7280; font-size:.82em; margin-top:28px;
           border-top:1px solid #e5e7eb; padding-top:14px; }
"""


def generer_html(target, timestamp, results, analyse=None, theme="neon", mission=""):
    """Construit un rapport HTML. theme = 'neon' (défaut) ou 'pro'."""
    def esc(s):
        return html.escape(s or "")

    coul_titre = "#1e3a5f" if theme == "pro" else ACCENT_HEX
    coul_ia = "#1e3a5f" if theme == "pro" else C_GAMER

    sections = []
    for r in results:
        coul = "#1e3a5f" if theme == "pro" else MODULE_COULEURS.get(r["module"], ACCENT_HEX)
        sortie, _coupe = _tronquer(r["output"])
        sections.append(f"""
      <section class="etape">
        <h2 style="color:{coul}">[{esc(r['module'])}] {esc(r['name'])}</h2>
        <div class="cmd">$ {esc(r['cmd'])}</div>
        <pre>{esc(sortie) or '(aucune sortie)'}</pre>
      </section>""")

    bloc_ia = ""
    if analyse:
        analyse_court, _ = _tronquer(analyse)
        bloc_ia = f"""
      <section class="etape ia">
        <h2 style="color:{coul_ia}">🤖 Analyse IA</h2>
        <pre>{esc(analyse_court)}</pre>
      </section>"""

    bloc_mission = ""
    if mission and mission.strip():
        bloc_mission = f'<div class="mission">🎯 Mission : {esc(mission.strip())}</div>'

    css = _css_pro() if theme == "pro" else _css_neon()
    ouvre_page = '<div class="page">' if theme == "pro" else ""
    ferme_page = "</div>" if theme == "pro" else ""

    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rapport Tisseur — {esc(target)}</title>
<style>{css}</style>
</head>
<body>
{ouvre_page}
  <header>
    <h1>🧵 Rapport Tisseur</h1>
    <div class="meta">Cible : {esc(target)} · Généré le {esc(timestamp)}</div>
    {bloc_mission}
    <div class="sign">{esc(SIGNATURE)}</div>
  </header>
  {''.join(sections)}
  {bloc_ia}
  <footer>⚠️ À utiliser seulement sur des machines que tu possèdes ou que t'as le droit de tester.</footer>
{ferme_page}
</body>
</html>"""


def dernier_rapport():
    """Renvoie le chemin du rapport .md le plus récent (ou None)."""
    fichiers = sorted(glob.glob("tisseur_rapport_*.md"), key=os.path.getmtime, reverse=True)
    return fichiers[0] if fichiers else None
