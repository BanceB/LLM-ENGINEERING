# =============================================================
# 10 — MÉLANGE TTL : 1 H (document) + 5 MIN AUTO (préfixe stable)
# -------------------------------------------------------------
# Dispositif: cas idéal du mélange TTL — TTL "1h" DANS le bloc
#             document + cache_control automatique (5 min) à la
#             racine pour la conversation. Aucun bloc variable.
# Attendu   : après le tour 1, le document est LU du cache 1 h et
#             l'historique de conversation du cache 5 min → coût
#             minimal, meilleur score de toute la série 08-10.
# Comparer  : 08/09 (mêmes breakpoints, suffixe perturbateur),
#             02 (cache simple 5 min), 15 (même montage + pre-warming).
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
            "cache_control": {"type": "ephemeral", "ttl" : '1h'},   # ← BREAKPOINT EXPLICITE D'UNE HEURE
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

TITRE = "MELANGE TTL (SUFFIXE STABLE)"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE, Melange_TTL=True)
