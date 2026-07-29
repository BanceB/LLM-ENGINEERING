# Chatbot web

Un chatbot qui répond aux questions. Le navigateur parle à ce serveur, et le
serveur parle à l'API Claude — la clé API ne quitte jamais la machine.

## Lancer en local

```powershell
cd web
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."   # si pas déjà défini dans le système
uvicorn serveur:app --reload
```

Puis ouvre <http://localhost:8000>.

`--reload` redémarre le serveur à chaque modification d'un fichier : pratique
pour développer, à retirer en production.

## Les fichiers

| Fichier | Rôle |
|---|---|
| `serveur.py` | Les 3 routes, la mémoire des conversations, l'appel à Claude |
| `static/index.html` | La structure de la page |
| `static/style.css` | L'apparence (thème clair et sombre automatiques) |
| `static/chat.js` | Envoyer, lire le flux, afficher |

## Les réglages

Tout est en haut de `serveur.py` :

| Réglage | Défaut | À quoi ça sert |
|---|---|---|
| `MODELE` | `claude-opus-5` | Le modèle utilisé |
| `EFFORT` | `medium` | Profondeur de réflexion. `low` = plus rapide, `high` = plus fouillé |
| `MAX_MESSAGES` | `20` | Fenêtre glissante : le bot se souvient des 10 derniers échanges |
| `SYSTEM` | — | Le cadrage du bot. **C'est ici qu'on définit son comportement.** |
| `QUOTA_REQUETES` | `20` / min | Garde-fou anti-abus, par session |

## Mettre en ligne

Trois choses à faire le jour où le site sort de ta machine.

**1. La clé API en variable d'environnement de l'hébergeur** — jamais dans le
code, jamais dans un fichier versionné.

**2. Cookies sécurisés.** Une fois en HTTPS, définis `SECURE_COOKIES=1` dans
l'environnement : le cookie de session ne circulera plus qu'en chiffré.

**3. La mémoire des conversations.** C'est le seul vrai point d'attention.
Aujourd'hui l'historique vit dans un dictionnaire Python (classe
`Conversations`). Ça marche parfaitement avec **un seul** processus, mais si
tu lances `uvicorn --workers 4` ou si l'hébergeur met deux machines derrière un
répartiteur de charge, chaque processus aura sa propre copie et les
conversations se perdront au hasard.

La correction est localisée : réécris les méthodes `lire`, `ecrire` et
`effacer` pour taper dans Redis ou SQLite. Le reste du fichier ne bouge pas.
Tant que tu restes à un seul worker, tu peux mettre en ligne tel quel.

**Commande de production** (sans `--reload`) :

```bash
uvicorn serveur:app --host 0.0.0.0 --port $PORT
```
