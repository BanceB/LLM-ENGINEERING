# =============================================================
# 07 — RÉPARATION : BREAKPOINT EXPLICITE (suffixe stable)
# -------------------------------------------------------------
# Dispositif: même breakpoint explicite que 05/06 (cache_control
#             DANS le bloc document), mais AUCUN bloc variable
#             après lui : cas idéal de la série des breakpoints.
#             Plus de cache_control à la racine de la requête.
# Attendu   : le document est LU du cache à chaque tour, rien n'est
#             réécrit inutilement → meilleur score de la série
#             05-07, équivalent de 02 avec breakpoint manuel.
# Comparer  : 05/06 (suffixe perturbateur), 02 (caching automatique).
# =============================================================

# Importations des tarifs, fonctions,du questionnaire et des bibliotheques
import anthropic
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
            "cache_control": {"type": "ephemeral"},   # ← BREAKPOINT EXPLICITE 
            # posé sur le bloc document, dernier bloc de la requête
        }
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
    MESSAGES.append({"role": "user", "content": q})

    response = client.messages.create(
        model=MODELE,
        max_tokens=MAX_TOKENS,
        # plus de cache_control ici : le breakpoint est DANS le bloc
        system=construire_system(),           # ← system identique à chaque tour
        messages=MESSAGES,
    )
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)


# --- Bilan ---
TITRE = "BREAKPOINT EXPLICITE (SUFFIXE STABLE)"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE)
