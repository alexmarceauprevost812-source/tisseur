#!/usr/bin/env bash
#
# Tisseur — installation Linux (Kali, Debian, Ubuntu...)
#
# Installe les dépendances, puis crée la commande « tisseur » pour que
# tu puisses lancer l'outil de n'importe où juste en tapant : tisseur
#
# USAGE :
#   bash install-linux.sh
#
set -e

echo "🧵 Installation de Tisseur (Linux)..."
echo

# On a besoin de sudo seulement si on n'est pas déjà root.
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    SUDO="sudo"
fi

# 1. Dépendances de base — python3 et git sont requis, nmap pour le
#    module Scanning. Sur Kali, tout est déjà là.
echo "📦 Installation de python3, git, nmap..."
$SUDO apt-get update
$SUDO apt-get install -y python3 git nmap

# Outils de pentest optionnels : déjà présents sur Kali. Sur Debian/
# Ubuntu, certains peuvent manquer des dépôts — on n'arrête pas
# l'installation s'ils ne sont pas trouvés (|| true).
echo "📦 Outils de pentest (optionnels)..."
$SUDO apt-get install -y hydra nikto gobuster sqlmap snmp enum4linux tcpdump masscan whois arp-scan || true

# 2. Trouver où est ce script (donc où est tisseur.py), peu importe le
#    dossier où tu l'as cloné.
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$DIR/tisseur.py" ]; then
    echo "❌ tisseur.py introuvable dans $DIR"
    echo "   Lance ce script depuis le dossier du projet (celui qui contient tisseur.py)."
    exit 1
fi

# 3. Créer la commande « tisseur » dans /usr/local/bin (sur le PATH).
echo "🔗 Création de la commande 'tisseur'..."
$SUDO tee /usr/local/bin/tisseur >/dev/null <<FIN
#!/usr/bin/env bash
exec python3 "$DIR/tisseur.py" "\$@"
FIN
$SUDO chmod +x /usr/local/bin/tisseur

# Commande 'veilleur' (gardien de ton réseau)
$SUDO tee /usr/local/bin/veilleur >/dev/null <<FIN
#!/usr/bin/env bash
exec python3 "$DIR/veilleur.py" "\$@"
FIN
$SUDO chmod +x /usr/local/bin/veilleur

echo
echo "✅ Terminé !"
echo
echo "Tu peux maintenant lancer Tisseur de n'importe où :"
echo "    tisseur                           # menu interactif"
echo "    tisseur --gui                     # interface graphique"
echo "    tisseur --target 192.168.56.102   # lancer sur une cible"
echo "    tisseur --guide                   # afficher le guide"
echo
echo "💡 Pour l'interface graphique (--gui), il faut Tkinter :"
echo "    sudo apt install python3-tk"
