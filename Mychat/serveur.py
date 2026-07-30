"""
CHATBOT WEB — le back
=====================
Deux routes seulement :
  GET  /           -> la page HTML
  POST /api/chat   -> reçoit une question, renvoie la réponse en streaming (SSE)
  POST /api/reset  -> oublie la conversation en cours

Le navigateur ne voit jamais la clé API : il parle à ce serveur, et c'est ce
serveur qui parle à Claude.

Lancement :
  pip install -r requirements.txt
  uvicorn serveur:app --reload
  puis http://localhost:8000
"""

from __future__ import annotations

import json
import os
import time
import uuid
from collections import deque
from pathlib import Path

import anthropic
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# --- Réglages ---------------------------------------------------------------
MODELE = "claude-opus-5"
MAX_TOKENS = 16000
EFFORT = "medium"              # low | medium | high | xhigh | max
MAX_MESSAGES = 20              # fenêtre glissante : 20 = 10 derniers échanges
LONGUEUR_MAX_QUESTION = 4000   # caractères
TTL_SESSION = 3600             # une session inactive est oubliée après 1 h
QUOTA_REQUETES = 20            # nb de questions...
QUOTA_FENETRE = 60             # ...par tranche de 60 s

SYSTEM = (
    "Tu es un assistant qui répond aux questions. "
    "Tu réponds de façon claire, concise et directe, en français. "
    "Si la question est ambiguë, tu poses une question de clarification "
    "plutôt que de deviner."
)

COOKIE = "sid"
# En ligne (HTTPS), mets SECURE_COOKIES=1 dans l'environnement.
COOKIE_SECURISE = os.environ.get("SECURE_COOKIES") == "1"

RACINE = Path(__file__).parent
STATIQUE = RACINE / "static"


# --- Mémoire des conversations ---------------------------------------------
class Conversations:
    """Historique par session, gardé en mémoire vive.

    POINT DE BASCULE UNIQUE pour la mise en ligne : dès qu'il y a plus d'un
    worker (`uvicorn --workers 4`) ou plus d'une machine, chaque processus a
    sa propre copie de ce dictionnaire et les conversations se perdent au
    hasard. Il suffit alors de réécrire `lire` et `ecrire` pour taper dans
    Redis ou SQLite — le reste du fichier ne bouge pas.
    """

    def __init__(self, max_messages: int, ttl: int):
        self._max = max_messages
        self._ttl = ttl
        self._data: dict[str, dict] = {}

    def _purger(self) -> None:
        limite = time.time() - self._ttl
        for sid in [s for s, v in self._data.items() if v["vu"] < limite]:
            del self._data[sid]

    def lire(self, sid: str) -> list[dict]:
        self._purger()
        entree = self._data.get(sid)
        return list(entree["messages"]) if entree else []

    def ecrire(self, sid: str, messages: list[dict]) -> None:
        self._data[sid] = {
            "messages": messages[-self._max:],   # fenêtre glissante
            "vu": time.time(),
        }

    def effacer(self, sid: str) -> None:
        self._data.pop(sid, None)


class Limiteur:
    """Garde-fou anti-abus : N requêtes par fenêtre glissante, par session."""

    def __init__(self, maximum: int, fenetre: int):
        self._max = maximum
        self._fenetre = fenetre
        self._hits: dict[str, deque] = {}

    def autorise(self, sid: str) -> bool:
        maintenant = time.time()
        passages = self._hits.setdefault(sid, deque())
        while passages and passages[0] < maintenant - self._fenetre:
            passages.popleft()
        if len(passages) >= self._max:
            return False
        passages.append(maintenant)
        return True


conversations = Conversations(MAX_MESSAGES, TTL_SESSION)
limiteur = Limiteur(QUOTA_REQUETES, QUOTA_FENETRE)
client = anthropic.AsyncAnthropic()

app = FastAPI(title="Chatbot")
app.mount("/static", StaticFiles(directory=STATIQUE), name="static")


# --- Format SSE -------------------------------------------------------------
def sse(genre: str, contenu: str = "") -> str:
    """Un événement Server-Sent Events : une ligne `data:` + une ligne vide.

    `genre` vaut "delta" (un morceau de texte), "fin" ou "erreur".
    """
    charge = json.dumps({"genre": genre, "contenu": contenu}, ensure_ascii=False)
    return f"data: {charge}\n\n"


ENTETES_SSE = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",   # empêche nginx de bufferiser le flux
}


# --- Routes -----------------------------------------------------------------
@app.get("/")
async def page():
    return FileResponse(STATIQUE / "index.html")


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=LONGUEUR_MAX_QUESTION)


@app.post("/api/chat")
async def chat(q: Question, request: Request):
    sid = request.cookies.get(COOKIE) or uuid.uuid4().hex

    if not limiteur.autorise(sid):
        flux = _flux_erreur("Trop de questions d'un coup — attends une minute.")
    else:
        historique = conversations.lire(sid)
        messages = historique + [{"role": "user", "content": q.question.strip()}]
        flux = _flux_reponse(sid, messages)

    reponse = StreamingResponse(flux, media_type="text/event-stream",
                                headers=ENTETES_SSE)
    reponse.set_cookie(COOKIE, sid, httponly=True, samesite="lax",
                       secure=COOKIE_SECURISE, max_age=TTL_SESSION)
    return reponse


@app.post("/api/reset")
async def reset(request: Request):
    sid = request.cookies.get(COOKIE)
    if sid:
        conversations.effacer(sid)
    return {"ok": True}


# --- Le cœur : appel de Claude en streaming ---------------------------------
async def _flux_reponse(sid: str, messages: list[dict]):
    """Générateur asynchrone : chaque `yield` part aussitôt vers le navigateur."""
    morceaux: list[str] = []
    try:
        async with client.messages.stream(
            model=MODELE,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            output_config={"effort": EFFORT},
            messages=messages,
        ) as flux:
            async for texte in flux.text_stream:
                morceaux.append(texte)
                yield sse("delta", texte)

    except anthropic.AuthenticationError:
        yield sse("erreur", "Clé API invalide ou absente côté serveur.")
        return
    except anthropic.RateLimitError:
        yield sse("erreur", "Limite de l'API atteinte — réessaie dans un instant.")
        return
    except anthropic.APIConnectionError:
        yield sse("erreur", "Le serveur n'arrive pas à joindre l'API.")
        return
    except anthropic.APIStatusError as e:
        yield sse("erreur", f"Erreur API ({e.status_code}).")
        return

    # On ne mémorise qu'en cas de succès : une question restée sans réponse
    # ne doit pas polluer les tours suivants.
    complete = "".join(morceaux)
    conversations.ecrire(sid, messages + [{"role": "assistant",
                                           "content": complete}])
    yield sse("fin")


async def _flux_erreur(message: str):
    yield sse("erreur", message)
