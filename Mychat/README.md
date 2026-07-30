# Mychat

Un chatbot web minimaliste : une page HTML, un serveur FastAPI, et Claude qui
répond en streaming (mot par mot, comme sur claude.ai).

Le navigateur ne voit jamais la clé API. Il parle au serveur, et c'est le
serveur qui parle à l'API Anthropic.

---

## Fonctionnalités

- **Réponses en streaming** via Server-Sent Events — le texte s'affiche au fur et
  à mesure, sans attendre la fin de la génération.
- **Mémoire de conversation** par session (cookie `sid`, `httponly`), avec une
  fenêtre glissante des 10 derniers échanges.
- **Bouton « Effacer »** pour repartir de zéro.
- **Garde-fous** : limitation de débit par session, longueur de question bornée,
  expiration automatique des sessions inactives.
- **Zéro dépendance côté front** : HTML, CSS et JavaScript natifs.

## Prérequis

- Python 3.10 ou plus
- Une clé API Anthropic ([console.anthropic.com](https://console.anthropic.com))

## Installation

```bash
git clone https://github.com/BanceB/LLM-ENGINEERING.git
cd LLM-ENGINEERING/Mychat
pip install -r requirements.txt
```

Renseigner la clé API dans l'environnement (le SDK `anthropic` la lit
automatiquement) :

```bash
# PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# bash / zsh
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Lancement

```bash
uvicorn serveur:app --reload
```

Puis ouvrir <http://localhost:8000>.

## Utilisation

| Action | Raccourci |
| --- | --- |
| Envoyer la question | `Entrée` |
| Aller à la ligne | `Maj` + `Entrée` |
| Effacer la conversation | bouton **Effacer** |

## Architecture

```
Mychat/
├── serveur.py          le back : routes, mémoire, appel à Claude
├── requirements.txt    dépendances Python
└── static/
    ├── index.html      la page
    ├── style.css       les styles
    └── chat.js         envoi de la question, lecture du flux SSE
```

### Routes

| Méthode | Route | Rôle |
| --- | --- | --- |
| `GET` | `/` | sert la page HTML |
| `POST` | `/api/chat` | reçoit une question, renvoie la réponse en streaming (SSE) |
| `POST` | `/api/reset` | oublie la conversation en cours |

### Le flux, de bout en bout

1. `chat.js` envoie la question en `POST /api/chat`.
2. Le serveur identifie la session via le cookie `sid` (créé s'il est absent),
   vérifie le quota, puis reconstitue l'historique.
3. `client.messages.stream(...)` ouvre le flux vers l'API ; chaque morceau de
   texte est réémis immédiatement sous forme d'événement SSE
   `data: {"genre": "delta", "contenu": "…"}`.
4. Le front lit le corps de la réponse au fur et à mesure, découpe les
   événements sur la ligne vide et les concatène dans la bulle en cours.
5. À la fin (`genre: "fin"`), la réponse complète est écrite dans l'historique.
   En cas d'erreur, rien n'est mémorisé : une question restée sans réponse ne
   doit pas polluer les tours suivants.

Le front écrit toujours via `textContent`, jamais `innerHTML` : aucune injection
possible depuis le texte du modèle.

## Configuration

Les réglages sont en haut de [serveur.py](serveur.py#L33-L41) :

| Constante | Défaut | Rôle |
| --- | --- | --- |
| `MODELE` | `claude-opus-5` | modèle appelé |
| `MAX_TOKENS` | `16000` | longueur maximale d'une réponse |
| `EFFORT` | `medium` | budget de réflexion (`low` → `max`) |
| `MAX_MESSAGES` | `20` | taille de la fenêtre glissante (20 = 10 échanges) |
| `LONGUEUR_MAX_QUESTION` | `4000` | caractères acceptés par question |
| `TTL_SESSION` | `3600` | durée de vie d'une session inactive (secondes) |
| `QUOTA_REQUETES` / `QUOTA_FENETRE` | `20` / `60` | 20 questions par minute et par session |

`SYSTEM` contient le prompt système — c'est là qu'on change la personnalité et
la langue de l'assistant.

Variables d'environnement :

| Variable | Rôle |
| --- | --- |
| `ANTHROPIC_API_KEY` | clé API (obligatoire) |
| `SECURE_COOKIES` | mettre à `1` en production pour n'émettre le cookie qu'en HTTPS |

## Mise en production

Un seul point de bascule : la classe `Conversations` garde les historiques en
mémoire vive. Avec plusieurs workers (`uvicorn --workers 4`) ou plusieurs
machines, chaque processus a sa propre copie et les conversations se perdent au
hasard. Il suffit alors de réécrire `lire`, `ecrire` et `effacer` pour taper
dans Redis ou SQLite — le reste du fichier ne bouge pas.

Le même raisonnement vaut pour `Limiteur`.

Derrière nginx, garder l'en-tête `X-Accel-Buffering: no` (déjà envoyé par le
serveur) : sans lui, le proxy bufferise le flux et le streaming disparaît.

## Licence

MIT — voir [LICENSE](LICENSE).
