#!/data/data/com.termux/files/usr/bin/bash
#
# Tisseur — installation LexOS (Android)
#
# LexOS tourne par-dessus Termux : on réutilise donc le même
# installateur. Ce fichier existe juste pour que tu retrouves ton
# système par son nom.
#
# USAGE :
#   bash install-lexos.sh
#
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "🧵 LexOS tourne sur Termux — on utilise l'installateur Termux."
echo
exec bash "$DIR/install-termux.sh" "$@"
