#!/data/data/com.termux/files/usr/bin/bash
#
# Tisseur — installation Termux / LexOS (Android)
#
# Installe les dépendances, puis crée la commande « tisseur » pour que
# tu puisses lancer l'outil de n'importe où juste en tapant : tisseur
#
# USAGE :
#   bash install-termux.sh
#
set -e

echo "🧵 Installation de Tisseur (Termux / LexOS)..."
echo

# 1. Dépendances — python et git sont requis, nmap pour le module Scanning.
#    -y répond "oui" tout seul (pas de question [Y/n] qui bloque).
echo "📦 Installation de python, git, nmap..."
pkg install -y python git nmap

# 2. Trouver où est ce script (donc où est tisseur.py), peu importe le
#    dossier où tu l'as cloné. Fini les erreurs de chemin.
DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$DIR/tisseur.py" ]; then
    echo "❌ tisseur.py introuvable dans $DIR"
    echo "   Lance ce script depuis le dossier du projet (celui qui contient tisseur.py)."
    exit 1
fi

# 3. Créer la commande « tisseur » dans le dossier des commandes de Termux.
echo "🔗 Création de la commande 'tisseur'..."
cat > "$PREFIX/bin/tisseur" <<FIN
#!$PREFIX/bin/bash
exec python "$DIR/tisseur.py" "\$@"
FIN
chmod +x "$PREFIX/bin/tisseur"

echo
echo "✅ Terminé !"
echo
echo "Tu peux maintenant lancer Tisseur de n'importe où :"
echo "    tisseur                           # menu interactif"
echo "    tisseur --target 192.168.56.102   # lancer sur une cible"
echo "    tisseur --guide                   # afficher le guide"
echo
echo "⚠️  Sur Android, l'interface graphique (--gui) ne marche pas (pas d'écran)."
echo "    Reste en mode terminal/menu."
