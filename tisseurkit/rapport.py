import os
import glob
import html

from .theme import (ACCENT_HEX, NOIR_HEX, NOIR_SIDE_HEX, TEXTE_HEX, TEXTE2_HEX,
                    MUTED_HEX, BORDURE_HEX, C_SCAN, C_GAMER, MODULE_COULEURS, SIGNATURE)

# ============================================================
# RAPPORT HTML (thème néon LEXOS)
# ============================================================
def generer_html(target, timestamp, results, analyse=None):
    """Construit un rapport HTML stylé à partir des résultats structurés."""
    def esc(s):
        return html.escape(s or "")

    sections = []
    for r in results:
        coul = MODULE_COULEURS.get(r["module"], ACCENT_HEX)
        sections.append(f"""
      <section class="etape">
        <h2 style="color:{coul}">[{esc(r['module'])}] {esc(r['name'])}</h2>
        <div class="cmd">$ {esc(r['cmd'])}</div>
        <pre>{esc(r['output']) or '(aucune sortie)'}</pre>
      </section>""")

    bloc_ia = ""
    if analyse:
        bloc_ia = f"""
      <section class="etape ia">
        <h2 style="color:{C_GAMER}">🤖 Analyse IA</h2>
        <pre>{esc(analyse)}</pre>
      </section>"""

    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rapport Tisseur — {esc(target)}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background:{NOIR_HEX}; color:{TEXTE_HEX};
         font-family:ui-monospace,Consolas,monospace; margin:0; padding:24px; }}
  header {{ border-bottom:1px solid {BORDURE_HEX}; padding-bottom:16px; margin-bottom:16px; }}
  h1 {{ color:{ACCENT_HEX}; margin:0 0 4px; }}
  .sign {{ color:{MUTED_HEX}; font-size:.9em; }}
  .meta {{ color:{C_SCAN}; font-size:.9em; }}
  .etape {{ background:{NOIR_SIDE_HEX}; border:1px solid {BORDURE_HEX};
            border-radius:8px; padding:12px 16px; margin:14px 0; }}
  .etape h2 {{ margin:0 0 8px; font-size:1.05em; }}
  .cmd {{ color:{MUTED_HEX}; margin-bottom:8px; }}
  pre {{ background:#070707; color:{TEXTE2_HEX}; padding:12px; border-radius:6px;
         overflow-x:auto; white-space:pre-wrap; word-break:break-word; margin:0; }}
  .ia pre {{ border-left:3px solid {C_GAMER}; }}
  footer {{ color:{MUTED_HEX}; font-size:.85em; margin-top:24px;
            border-top:1px solid {BORDURE_HEX}; padding-top:12px; }}
</style>
</head>
<body>
  <header>
    <h1>🧵 Rapport Tisseur</h1>
    <div class="meta">Cible : {esc(target)} · Généré le {esc(timestamp)}</div>
    <div class="sign">{esc(SIGNATURE)}</div>
  </header>
  {''.join(sections)}
  {bloc_ia}
  <footer>⚠️ À utiliser seulement sur des machines que tu possèdes ou que t'as le droit de tester.</footer>
</body>
</html>"""


def dernier_rapport():
    """Renvoie le chemin du rapport .md le plus récent (ou None)."""
    fichiers = sorted(glob.glob("tisseur_rapport_*.md"), key=os.path.getmtime, reverse=True)
    return fichiers[0] if fichiers else None
