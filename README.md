# 🧵 Tisseur

**Tisseur** tisse ensemble les outils de pentest du cours **Hacking 101** en un
seul pipeline. Il les exécute **un par un** — en attendant que chaque étape soit
complètement terminée avant de passer à la suivante — puis tisse tous les
résultats en un seul **rapport final Markdown** (`.md`).

> ⚠️ **À utiliser seulement sur des machines que tu possèdes ou que t'as le
> droit explicite de tester** (ton lab Metasploitable2, etc.). Scanner ou
> attaquer un système sans autorisation est illégal.

---

## Les modules

Les étapes sont regroupées en 5 modules, exécutés dans l'ordre :

| Module | Outils |
|---|---|
| **Reconnaissance** | `ping`, `whois` |
| **Scanning** | `nmap` (scan complet), `masscan` (scan rapide) |
| **Énumération** | `enum4linux`, `gobuster`, `nikto`, `snmpwalk` |
| **Exploitation** | `hydra` (brute force SSH), `sqlmap` (injection SQL) |
| **Outils avancés** | `tcpdump` (capture réseau) |

D'autres étapes sont présentes **mais commentées** dans le code (theHarvester,
Legion, Metasploit, Burp Suite, linPEAS, netcat, John the Ripper, Hashcat,
Aircrack-ng, Wifite). Elles ont besoin d'un setup différent d'une simple IP
(un fichier de hash, une interface wifi, un resource script…). Ouvre
`tisseur.py`, section `STEPS`, pour l'explication de chacune et comment
l'activer.

---

## Installation

### 1. Télécharger l'outil

```bash
git clone https://github.com/alexmarceauprevost812-source/tisseur.git
cd tisseur
git checkout claude/nice-goldberg-saufsc
```

> ⚠️ Le `git checkout` est important : le code vit sur la branche
> `claude/nice-goldberg-saufsc`. Sans cette ligne, tu te retrouves sur une
> branche sans le script.

Pour mettre à jour un dossier déjà cloné :

```bash
cd tisseur
git pull origin claude/nice-goldberg-saufsc
```

### 2. Kit d'installation (un script par plateforme)

Une fois le dossier téléchargé, lance le script qui correspond à ton système.
Il installe les dépendances **et** crée la commande `tisseur` (qui trouve le
dossier toute seule — plus besoin de taper le chemin complet).

| Système | Commande |
|---|---|
| **Linux** (Kali, Debian, Ubuntu…) | `bash install-linux.sh` |
| **Termux** (Android) | `bash install-termux.sh` |
| **LexOS** (Android) | `bash install-lexos.sh` |
| **Windows** (PowerShell) | `powershell -ExecutionPolicy Bypass -File install-windows.ps1` |

Après, tu lances l'outil de n'importe où :

```bash
tisseur                           # menu interactif
tisseur --target 192.168.56.102   # lancer sur une cible
tisseur --guide                   # afficher le guide
```

> 💡 Les scripts sont **idempotents** : tu peux les relancer sans danger (par
> exemple si tu déplaces le dossier, relance le script pour corriger le
> raccourci).

### 3. Dépendances (si tu installes à la main)

- **Python 3** — déjà présent sur Kali/Linux ; aucun paquet externe pour les
  modes terminal.
- **Tkinter** — seulement pour l'interface graphique (`--gui`). Sur Kali/Debian :
  ```bash
  sudo apt install python3-tk
  ```
  ⚠️ L'interface graphique **ne marche pas sur Termux/LexOS** (Android n'a pas
  d'écran graphique X11) : reste en mode terminal.
- **Les outils de pentest** (`nmap`, `masscan`, `hydra`, `nikto`, `enum4linux`,
  `gobuster`, `sqlmap`, `snmpwalk`, `tcpdump`…) — préinstallés sur **Kali
  Linux**. Tisseur ne fait que les lancer, il ne les installe pas. Sur Termux et
  Windows, surtout `nmap` est disponible ; pour le kit complet, Kali reste le
  meilleur choix.

---

## Trois façons de le lancer

```bash
python3 tisseur.py                          # menu interactif (terminal)
python3 tisseur.py --gui                    # interface graphique (fenêtre)
python3 tisseur.py --target <ip> [options]  # mode direct (scripts/automatisation)
```

### Mode direct — exemples

```bash
# Pipeline complet sur ton lab Metasploitable2
python3 tisseur.py --target 192.168.56.102

# Juste certains modules
python3 tisseur.py --target 192.168.56.102 --modules Reconnaissance,Scanning

# Préciser une URL différente pour les outils web (autre port)
python3 tisseur.py --target 192.168.56.102 --url http://192.168.56.102:8080

# Afficher le guide intégré puis quitter
python3 tisseur.py --guide
```

### Options

| Option | Description |
|---|---|
| `--target <ip>` | IP ou host de la cible (**requis** en mode direct) |
| `--url <url>` | URL pour les outils web (défaut : `http://<target>`) |
| `--modules <liste>` | Modules séparés par virgule (défaut : tous). Ex : `Reconnaissance,Scanning` |
| `--mission "<texte>"` | Rapport de mission / objectif, pour **diriger l'IA** |
| `--html` | Génère aussi un **rapport HTML** néon en plus du `.md` |
| `--html-pro` | Rapport HTML **thème pro** (sobre, pour une compagnie) |
| `--check` | Vérifie seulement quels **outils sont installés**, puis quitte |
| `--oui` | Confirme d'avance l'autorisation de tester (pour scripts) |
| `--ia` | **Analyse IA** locale du rapport à la fin |
| `--chat` | Ouvre le **chat IA** après le scan (implique `--ia`) |
| `--gui` | Ouvre directement l'interface graphique |
| `--guide` | Affiche le guide puis quitte |

### Avant de lancer : vérif des outils + autorisation

- **Vérif des outils** — au démarrage (et avec `--check`), Tisseur liste les
  outils installés (✅) et manquants (❌), avec la commande pour installer ceux
  qui manquent (adaptée à Termux ou apt). Plus de surprise « command not found ».
- **Confirmation d'autorisation** — Tisseur demande « As-tu l'autorisation de
  tester cette cible ? » avant de scanner. Un réflexe éthique ; passe `--oui`
  dans un script si tu es déjà certain d'avoir le droit.

### Notifications

Quand un scan se termine, Tisseur envoie une **notification système**
(best-effort) : `termux-notification` sur Android, `notify-send` sur Linux,
`osascript` sur macOS. Si aucun n'est dispo, rien ne casse.

### Copier-coller dans l'interface graphique

Les champs **Cible / URL** et la zone de résultats supportent le copier-coller :

- **Clic droit** n'importe où → menu **Couper / Copier / Coller / Tout
  sélectionner**.
- **Ctrl+A** pour tout sélectionner (fiable même en clavier français, là où les
  raccourcis Ctrl par défaut de Tkinter sont capricieux).
- Le bouton **« Copier le rapport »** copie toute la sortie affichée dans le
  presse-papier d'un seul coup.

---

## Le rapport

À la fin du pipeline, Tisseur écrit un rapport Markdown dans le dossier courant :

```
tisseur_rapport_<ip>_<AAAAMMJJ_HHMMSS>.md
```

Chaque étape y apparaît avec sa commande exacte et sa sortie complète (stdout +
stderr), dans des blocs de code. Une étape qui dépasse **10 minutes** est
interrompue (timeout) et notée comme telle dans le rapport.

---

## Analyse IA locale (optionnel)

Avec l'option **`--ia`**, Tisseur fait lire le rapport à une **IA qui tourne sur
ta propre machine** (rien n'est envoyé sur Internet). Elle **résume les failles
trouvées et conseille les prochaines étapes** — elle n'exécute **jamais** de
commande elle-même. L'analyse s'affiche à l'écran et s'ajoute au bas du rapport
`.md`.

Deux moteurs supportés (aucune dépendance Python à installer, juste le moteur) :

| Moteur | Démarrer | Port API |
|---|---|---|
| **Ollama** | `ollama run llama3` ([ollama.com](https://ollama.com)) | `11434` |
| **llama.cpp** | `./llama-server -m modele.gguf` | `8080` |

### Exemples

```bash
# Pipeline + analyse par Ollama (modèle llama3 par défaut)
tisseur --target 192.168.56.102 --ia

# Choisir le modèle Ollama
tisseur --target 192.168.56.102 --ia --ia-modele mistral

# Utiliser llama.cpp au lieu d'Ollama
tisseur --target 192.168.56.102 --ia --ia-moteur llamacpp
```

Options IA : `--ia` (active), `--ia-moteur ollama|llamacpp`, `--ia-modele <nom>`,
`--ia-url <url>` (si ton moteur n'est pas sur le port par défaut).

Dans le **menu interactif** et l'**interface graphique**, une case « IA locale »
te laisse activer l'analyse et choisir le moteur/modèle sans taper d'options.

> 💡 Si l'IA n'est pas démarrée, Tisseur te le dit poliment et te donne la
> commande pour la lancer — le pipeline, lui, a déjà fait son travail.

### 🎯 Rapport de mission (diriger l'IA)

Avec **`--mission`**, tu donnes un objectif à l'IA pour orienter ses réponses :

```bash
tisseur --target 192.168.56.102 --ia --mission "CTF : trouver le chemin vers le flag"
tisseur --target 192.168.56.102 --ia --mission "Focus sur les failles web"
```

La mission est injectée dans l'analyse **et** dans le chat, et notée en haut du
rapport. Le menu et la GUI ont aussi un champ « Mission ».

### 💬 Chat IA — commande `/chat`

Au lieu d'une seule analyse, tu peux **discuter** avec l'IA à propos du rapport :

```bash
# Ouvrir le chat tout de suite après le scan
tisseur --target 192.168.56.102 --chat

# Rouvrir le chat plus tard sur le DERNIER rapport, sans rescanner
tisseur /chat
tisseur /chat --ia-modele llama3.2:1b
```

Dans le chat, pose tes questions (« c'est quoi le port 3306 ? », « par où je
commence ? ») ; tape **`/quit`** (ou `q`) pour sortir. Le menu interactif a aussi
l'option **3) Chat IA** (ou tape `/chat` directement au menu).

### 📄 Rapport HTML

Avec **`--html`**, Tisseur écrit aussi un rapport `.html` stylé (thème néon) à
côté du `.md`, ouvrable dans un navigateur et facile à partager. Avec
**`--html-pro`**, c'est un thème **sobre/corporatif** (fond clair, bleu marine),
parfait pour présenter à une compagnie.

```bash
tisseur --target 192.168.56.102 --html       # thème néon
tisseur --target 192.168.56.102 --html-pro    # thème pro (fichier *_pro.html)
```

> 🛡️ **Plafond de taille** : les sorties très longues sont tronquées dans le
> HTML (20 000 caractères par étape) avec un avis, pour éviter un fichier géant.
> Le rapport `.md`, lui, garde **toujours** la sortie complète.

### 📱 Sur téléphone (Termux / LexOS) : petits modèles

Ollama tourne sur Android, mais la RAM d'un téléphone est limitée : le modèle
`llama3` (8 milliards de paramètres) est souvent **trop gros** et plante. Utilise
un **petit modèle** à la place :

```bash
ollama run llama3.2:1b      # léger, bon compromis
ollama run qwen2.5:0.5b     # encore plus petit, pour les appareils serrés
```

Puis lance Tisseur en pointant vers ce modèle :

```bash
tisseur --target 192.168.56.102 --ia --ia-modele llama3.2:1b
```

> Règle du pouce : vise un modèle **plus petit que la moitié de ta RAM libre**.
> Un petit modèle répond moins finement qu'un gros, mais pour résumer un rapport
> et suggérer des pistes, ça fait très bien la job.

---

## Prérequis

- **Python 3** (aucune dépendance externe pour les modes terminal).
- **Tkinter** pour l'interface graphique. Sur Kali/Debian, s'il n'est pas déjà
  installé :
  ```bash
  sudo apt install python3-tk
  ```
- Les **outils de pentest** eux-mêmes (`nmap`, `masscan`, `hydra`, `nikto`…).
  Ils sont préinstallés sur **Kali Linux**. Une étape dont l'outil est absent
  l'indiquera dans sa sortie et le pipeline continuera avec la suivante.

---

## Comment ça marche

Tisseur utilise `subprocess.run()`, qui **bloque** jusqu'à ce que chaque
commande soit complètement terminée — c'est ce qui garantit que les étapes se
font **une à la fois, en ordre**. Le moteur (`run_pipeline()`) accepte un
« puits de sortie » (`output`) interchangeable, ce qui permet au terminal et à
l'interface graphique de partager exactement le même code : la GUI roule le
pipeline sur un thread en arrière-plan et affiche la sortie au fur et à mesure.

---

## 🛡️ Le Veilleur — gardien de ton réseau

Si Tisseur **audite une cible**, **Le Veilleur protège ton propre réseau**. Il
regarde qui est connecté chez toi et t'**avertit dès qu'un appareil inconnu
apparaît**. 100 % défensif — à utiliser sur **ton** réseau seulement.

```bash
python3 veilleur.py                 # un scan ; la 1re fois, établit la base
python3 veilleur.py --watch         # surveille en continu (scan aux 60 s)
python3 veilleur.py --watch 30      # ... aux 30 secondes
python3 veilleur.py --liste         # montre les appareils connus
python3 veilleur.py --ia            # l'IA locale commente les inconnus
python3 veilleur.py --reseau 192.168.0.0/24   # préciser le réseau
```

Comment ça marche :
1. Il scanne ton réseau local (`arp-scan`, sinon `nmap -sn`, sinon la table ARP).
2. La **première fois**, il mémorise les appareils actuels comme « de confiance »
   (dans `veilleur_connus.json`).
3. Ensuite, dès qu'un **appareil inconnu** (nouvelle adresse MAC) apparaît →
   🚨 alerte + **notification système** (la même que Tisseur).
4. Avec `--ia`, l'IA locale te dit à quoi ressemble l'inconnu (fabricant probable)
   pour t'aider à décider s'il est louche.

> Le Veilleur **réutilise les pièces de Tisseur** : thème néon, notifications et
> IA locale. Les installateurs créent aussi une commande **`veilleur`** à côté de
> `tisseur`. `arp-scan`/`nmap` demandent souvent les droits root (`sudo`).

---

## Structure du code

Le code est découpé en **modules** (une pièce par fichier) dans le dossier
`tisseurkit/`. Tu n'as rien à monter : `tisseur.py` est juste le point d'entrée,
et Python assemble les pièces tout seul au lancement.

| Fichier | Rôle |
|---|---|
| `tisseur.py` | Point d'entrée (la « clé de contact ») |
| `tisseurkit/theme.py` | Couleurs, palette néon, bannière |
| `tisseurkit/etapes.py` | La liste des étapes (`STEPS`) |
| `tisseurkit/pipeline.py` | Le moteur : exécute les étapes, écrit le rapport |
| `tisseurkit/ia.py` | Analyse IA + chat `/chat` (Ollama / llama.cpp) |
| `tisseurkit/outils.py` | Vérif des outils, autorisation, notifications |
| `tisseurkit/rapport.py` | Rapport HTML |
| `tisseurkit/guide.py` | Guide / aide |
| `tisseurkit/menu.py` | Menu interactif (terminal) |
| `tisseurkit/gui.py` | Interface graphique (Tkinter) |
| `tisseurkit/cli.py` | Options en ligne de commande (`--target`, `--ia`…) |

> Ça ne change **rien** à l'installation ni au lancement : toujours
> `python3 tisseur.py` ou la commande `tisseur`.

---

<p align="center"><em>Alex Marceau Prévost · Produit au Lac-Saint-Jean 🫐</em></p>
