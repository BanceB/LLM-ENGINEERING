# =============================================================
# 03 — LE PIÈGE : SUFFIXE VARIABLE À CHAQUE APPEL
# -------------------------------------------------------------
# Dispositif: caching automatique (comme 02) + un bloc « Date et
#             heure : datetime.now() » ajouté APRÈS le document.
#             Il change à CHAQUE appel (secondes incluses) ; or le
#             cache est un match de PRÉFIXE : le breakpoint
#             automatique tombe après ce bloc, jamais réutilisable.
# Attendu   : ÉCRITURE du préfixe complet à chaque tour, aucune
#             LECTURE → plus cher que la baseline (surcoût ~1,25x
#             sans aucune contrepartie).
# Comparer  : 02 (cache sain), 05 (réparation par breakpoint explicite).
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
        },
        {
            "type": "text",
            # ⚠️ LE PIÈGE : ce bloc change à CHAQUE appel (secondes incluses)
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
TITRE = "SUFFIXE EXTREMEMENT VARIABLE"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE)
