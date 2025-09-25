#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gpt_ssh_runner.py
Contrôleur central : envoie une requête en français à l'API OpenAI,
extrait la commande proposée, demande confirmation, puis exécute via SSH
sur les hôtes listés dans hosts.txt.

Usage:
  export OPENAI_API_KEY="sk-..."
  export SSH_KEY="~/.ssh/id_rsa"
  python3 gpt_ssh_runner.py "Votre demande en français"

Remarques de sécurité :
- Ne stockez jamais la clé API dans le repo.
- Préférez exécution depuis un poste contrôleur (PC/VPS), pas directement depuis les routeurs.
- Le script demande confirmation avant exécution et utilise une whitelist simple.
"""
import os
import re
import shlex
import subprocess
import sys
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Erreur: définissez la variable d'environnement OPENAI_API_KEY.")
    sys.exit(1)

SSH_KEY = os.path.expanduser(os.getenv("SSH_KEY", "~/.ssh/id_rsa"))
HOSTS_FILE = os.getenv("HOSTS_FILE", "hosts.txt")  # format: user@host[:port] par ligne
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

def ask_gpt(prompt):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": MODEL,
        "messages": [{"role":"user","content": prompt}],
        "max_tokens": 300,
        "temperature": 0.2
    }
    r = requests.post(OPENAI_CHAT_URL, json=data, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def extract_shell(text):
    # Cherche un bloc entre ```sh``` ou ```bash```
    m = re.search(r"```(?:sh|bash)\n(.+?)```", text, re.S)
    if m:
        return m.group(1).strip()
    # Cherche inline `commande`
    m2 = re.search(r"`([^`]+)`", text)
    if m2:
        return m2.group(1).strip()
    # fallback: première ligne utile
    for line in text.splitlines():
        line = line.strip()
        if line and not line.lower().startswith(("note:", "explain")):
            return line
    return None

# Whitelist simple : adapter selon vos besoins
WHITELIST_PREFIXES = [
    "ls","ip","ifconfig","cat","grep","nmap","uname","df","free","ps","netstat",
    "iproute","iwconfig","ping","systemctl","service","sed","awk","hostname"
]

def is_allowed(cmd):
    try:
        first = shlex.split(cmd)[0]
    except Exception:
        return False
    return any(first == p or first.startswith(p) for p in WHITELIST_PREFIXES)

def read_hosts(path):
    hosts = []
    if not os.path.exists(path):
        print(f"Fichier hosts introuvable: {path}")
        sys.exit(1)
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                hosts.append(line)
    return hosts

def run_ssh(host, cmd):
    ssh_cmd = ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", host, cmd]
    proc = subprocess.run(ssh_cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def main():
    if len(sys.argv) < 2:
        print("Usage: gpt_ssh_runner.py \"Votre demande en français\"")
        sys.exit(1)
    prompt = sys.argv[1]
    print("Envoi de la requête au modèle...")
    resp_text = ask_gpt(prompt)
    print("Réponse du modèle:\n", resp_text)
    cmd = extract_shell(resp_text)
    if not cmd:
        print("Aucune commande détectée dans la réponse.")
        sys.exit(0)
    print("\nCommande extraite:\n", cmd)
    if not is_allowed(cmd):
        print("Commande interdite par la whitelist. Abandon.")
        sys.exit(2)
    hosts = read_hosts(HOSTS_FILE)
    if not hosts:
        print("Aucun hôte trouvé dans hosts.txt")
        sys.exit(1)
    confirm = input(f"Exécuter la commande sur {len(hosts)} hôtes ? [y/N] ")
    if confirm.lower() != "y":
        print("Annulé.")
        sys.exit(0)
    for h in hosts:
        print(f"\n=== Exécution sur {h} ===")
        rc, out, err = run_ssh(h, cmd)
        print(f"Return code: {rc}\n--- STDOUT ---\n{out}\n--- STDERR ---\n{err}")

if __name__ == "__main__":
    main()