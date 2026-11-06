import sys
import json
import urllib.request
import urllib.error

from .theme import colore, MUTED_HEX, BORDURE_HEX, C_DEL, C_SCAN, C_GAMER

# ============================================================
# ANALYSE IA LOCALE (Ollama ou llama.cpp)
# ------------------------------------------------------------
# L'IA tourne EN LOCAL sur ta machine (aucune donnée envoyée sur
# Internet). Elle LIT le rapport et te CONSEILLE — elle n'exécute
# jamais de commande elle-même.
#
#   Ollama     : https://ollama.com  ->  ollama run llama3
#                API : http://localhost:11434
#   llama.cpp  : serveur ./llama-server -m modele.gguf
#                API : http://localhost:8080
# ============================================================
IA_DEFAUTS = {
    "ollama":   {"url": "http://localhost:11434", "modele": "llama3"},
    "llamacpp": {"url": "http://localhost:8080",  "modele": ""},
}

PROMPT_IA = """Tu es un mentor en cybersécurité pour le cours « Hacking 101 ».
On te donne le rapport d'un scan de pentest effectué sur un LAB D'ENTRAÎNEMENT
AUTORISÉ (une machine Metasploitable2 ou équivalente que l'étudiant possède et a
le droit de tester).
{mission}
Analyse ce rapport et réponds EN FRANÇAIS, de façon claire et pédagogique :

1. RÉSUMÉ — les hôtes, ports ouverts, services et versions détectés.
2. FAILLES POTENTIELLES — les vulnérabilités probables, de la plus à la moins
   prioritaire, avec une courte explication de chacune.
3. PROCHAINES ÉTAPES — quoi explorer ensuite pour apprendre, en restant dans le
   cadre d'un lab autorisé.

Reste factuel : base-toi sur ce qui est RÉELLEMENT dans le rapport. Ne donne pas
d'instructions pour attaquer des systèmes non autorisés.

===== RAPPORT =====
{rapport}
===== FIN DU RAPPORT =====
"""


def _bloc_mission(mission):
    """Bloc 'rapport de mission' injecté dans les prompts pour diriger l'IA."""
    if mission and mission.strip():
        return ("\nRAPPORT DE MISSION (objectif fixé par l'étudiant — oriente tes "
                "réponses en fonction) :\n" + mission.strip() + "\n")
    return ""


def _ia_config(ia):
    """Normalise le dict `ia` -> (moteur, url, modele)."""
    moteur = ia.get("moteur", "ollama")
    defauts = IA_DEFAUTS.get(moteur, IA_DEFAUTS["ollama"])
    url = (ia.get("url") or defauts["url"]).rstrip("/")
    modele = ia.get("modele") or defauts["modele"]
    return moteur, url, modele


def _ia_generate(prompt, ia, timeout=300):
    """Envoie un prompt à l'IA locale et renvoie le texte. Lève en cas d'échec.

    Partagé par l'analyse automatique et le chat.
    """
    moteur, url, modele = _ia_config(ia)
    if moteur == "ollama":
        endpoint = f"{url}/api/generate"
        payload = {"model": modele, "prompt": prompt, "stream": False}
    else:  # llamacpp
        endpoint = f"{url}/completion"
        payload = {"prompt": prompt, "n_predict": 768, "stream": False}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    # Ollama -> "response" ; llama.cpp -> "content"
    return (body.get("response") or body.get("content") or "").strip()


def _ia_message_erreur(moteur, modele, raison, output, tty):
    """Message d'aide commun quand l'IA locale ne répond pas."""
    output(colore(f"⚠️ Impossible de joindre l'IA locale ({moteur}) : {raison}", C_DEL, tty))
    if moteur == "ollama":
        output("   Démarre Ollama d'abord :  ollama run " + (modele or "llama3"))
        output("   (installe-le sur https://ollama.com si ce n'est pas fait)")
    else:
        output("   Démarre le serveur llama.cpp d'abord :")
        output("   ./llama-server -m ton_modele.gguf  (écoute sur le port 8080)")


def analyse_ia(rapport, ia, output=print, mission=""):
    """Envoie le rapport à une IA locale et renvoie son analyse (texte).

    `ia` est un dict : {"moteur": "ollama"|"llamacpp", "modele": str, "url": str}.
    `mission` : objectif optionnel pour orienter l'IA.
    Renvoie None en cas d'échec (après avoir affiché une explication).
    """
    moteur, url, modele = _ia_config(ia)
    tty = (output is print) and sys.stdout.isatty()
    output("")
    output(colore(f"🤖 Analyse IA locale ({moteur}) en cours…", C_GAMER, tty))

    # On tronque le rapport pour ne pas dépasser le contexte du modèle.
    prompt = PROMPT_IA.format(mission=_bloc_mission(mission), rapport=rapport[:12000])

    try:
        texte = _ia_generate(prompt, ia)
        if not texte:
            output(colore("⚠️ L'IA a répondu, mais sans texte exploitable.", C_DEL, tty))
            return None

        output(colore("=" * 60, BORDURE_HEX, tty))
        output(colore("🤖 ANALYSE IA", C_GAMER, tty))
        output(colore("=" * 60, BORDURE_HEX, tty))
        output(texte)
        return texte

    except urllib.error.URLError as e:
        _ia_message_erreur(moteur, modele, e.reason, output, tty)
        return None
    except Exception as e:
        output(colore(f"⚠️ Erreur pendant l'analyse IA : {e}", C_DEL, tty))
        return None


# ============================================================
# CHAT IA — commande /chat (terminal)
# ------------------------------------------------------------
# Poser des questions à l'IA locale sur un rapport. Tape /quit
# (ou q) pour sortir.
# ============================================================
PROMPT_CHAT = """Tu es un mentor en cybersécurité du cours « Hacking 101 ». Tu
réponds aux questions d'un étudiant à propos d'un scan fait sur son LAB
D'ENTRAÎNEMENT AUTORISÉ. Réponds EN FRANÇAIS, bref et pédagogique, en te basant
sur le rapport ci-dessous. Ne donne pas d'instructions pour attaquer des
systèmes non autorisés.
{mission}
===== RAPPORT =====
{rapport}
===== FIN DU RAPPORT =====

Question de l'étudiant : {question}
Réponse :"""


def chat_ia(rapport, ia, mission=""):
    """Boucle de chat (terminal) : pose des questions à l'IA sur le rapport."""
    moteur, url, modele = _ia_config(ia)
    tty = sys.stdout.isatty()

    print(colore("=" * 60, BORDURE_HEX, tty))
    print(colore(f"💬 Chat IA ({moteur}) — pose tes questions sur le rapport.", C_GAMER, tty))
    print(colore("   Tape /quit (ou q) pour sortir.", MUTED_HEX, tty))
    print(colore("=" * 60, BORDURE_HEX, tty))

    rapport_court = rapport[:12000]
    bloc_mission = _bloc_mission(mission)
    while True:
        try:
            question = input(colore("\n💬 toi > ", C_SCAN, tty)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in ("/quit", "/exit", "q", "quit", "exit"):
            print(colore("Fin du chat. 🫐", MUTED_HEX, tty))
            break

        prompt = PROMPT_CHAT.format(mission=bloc_mission, rapport=rapport_court, question=question)
        try:
            reponse = _ia_generate(prompt, ia)
            print(colore("\n🤖 ia  > ", C_GAMER, tty) + (reponse or "(pas de réponse)"))
        except urllib.error.URLError as e:
            _ia_message_erreur(moteur, modele, e.reason, print, tty)
            break
        except Exception as e:
            print(colore(f"⚠️ Erreur : {e}", C_DEL, tty))
