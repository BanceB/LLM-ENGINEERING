# =============================================================
# 13 — EXPIRATION DU TTL 5 MIN (cache simple)
# -------------------------------------------------------------
# Dispositif: caching automatique (5 min) ; pause de 5 min 30 avant
#             le tour 4, volontairement au-delà du TTL de 5 minutes.
# Attendu   : tours 1-3 en LECTURE ; au tour 4 l'entrée a expiré →
#             RÉÉCRITURE complète du préfixe (document + historique) ;
#             tours 5+ repartent en LECTURE.
# Comparer  : 14 (même pause avec un TTL 1 h sur le document).
# =============================================================

# Importations des tarifs, fonctions,du questionnaire et des bibliotheques
import anthropic
import time
from afficher_reponse import afficher_reponse
from document import DOCUMENT
from questions import QUESTIONS
from tarifs import BASELINE
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
for i, q in enumerate(QUESTIONS, 1):

    print("Q :", q)

    # ⚠️ AVANT le tour 4 : on laisse le cache expirer (TTL 5 min)
    if i == 4:
        print(">>> PAUSE DE 5 MIN 30 : on laisse le cache expirer... <<<")
        time.sleep(330)   # 5 min 30, marge au-delà du TTL de 5 min

    MESSAGES.append({"role": "user", "content": q})
    # ... le reste strictement identique à 3B


    response = client.messages.create(
        model=MODELE,
        max_tokens=MAX_TOKENS,
        cache_control = {"type": "ephemeral"},  # CACHE AUTOMATIQUE
        system=construire_system(),
        messages=MESSAGES,
    )

    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)


# --- Bilan ---
TITRE = "EXPIRATION DU TTL 5 MINUTES"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE)