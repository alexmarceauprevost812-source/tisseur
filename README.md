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
| `--gui` | Ouvre directement l'interface graphique |
| `--guide` | Affiche le guide puis quitte |

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

<p align="center"><em>Alex Marceau Prévost · Produit au Lac-Saint-Jean 🫐</em></p>
