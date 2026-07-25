# =============================================================
# 08 — MÉLANGE TTL : 1 H (document) + 5 MIN AUTO (suffixe très variable)
# -------------------------------------------------------------
# Dispositif: deux breakpoints — TTL "1h" DANS le bloc document, et
#             cache_control automatique (5 min) à la racine pour la
#             suite de la requête. Entre les deux, le bloc datetime
#             change à CHAQUE appel.
# Attendu   : le document reste LU du cache 1 h à chaque tour ; la
#             partie 5 min (suffixe + historique) est réécrite à
#             chaque appel à cause du suffixe variable.
# Comparer  : 09 et 10 (suffixe de moins en moins variable),
#             05 (breakpoint explicite sans mélange TTL).
# =============================================================

# Importations des tarifs, fonctions,du questionnaire et des bibliotheques
import anthropic
from afficher_reponse import afficher_reponse
from document import DOCUMENT
from questions import QUESTIONS
from tarifs import BASELINE
from datetime import datetime

from seuil import seuil

client = anthropic.Anthropic()

# parametres systeme
MODELE = "claude-haiku-4-5"
MAX_TOKENS = 300
def construire_system():
    return [
        {
            "type": "text",
            "text": (
                "Tu es un assistant juridique. Tu réponds aux questions des "
                "citoyens en te basant UNIQUEMENT sur la Constitution française "
                "fournie ci-dessous. Si l'information n'y figure pas, "
                "dis-le clairement.\n\n" + DOCUMENT
            ),
            "cache_control": {"type": "ephemeral", "ttl" : '1h'},   # ← BREAKPOINT EXPLICITE D'UNE HEURE

        },
        {
            "type": "text",
            "text": f"Date et heure actuelles : {datetime.now().isoformat()}",
        },
    ]


# MESSAGES: stockage memoire | BILANS: retour tokens)
MESSAGES = []
BILANS = []


# --- Vérification du seuil (rappel : 4 096 tokens pour Haiku 4.5) ---
action = seuil(MODELE, construire_system())
if not action:
    raise SystemExit("Document trop court : augmentez le nombre d'articles.")

# CHAT BOUCLE
for q in QUESTIONS:

    print("Q :", q)
    MESSAGES.append({"role": "user", "content": q})

    response = client.messages.create(
        model=MODELE,
        max_tokens=MAX_TOKENS,
        cache_control={"type": "ephemeral"},   # CACHE AUTOMATIQUE
        system=construire_system(),         
        messages=MESSAGES,
    )
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)

# --- Bilan ---
TITRE = "MELANGE TTL (SUFFIXE EXTREMEMENT VARIABLE)"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE, Melange_TTL=True)
