# =============================================================
# 01 — BASELINE SANS CACHE (référence)
# -------------------------------------------------------------
# Contexte  : conversation de 10 questions sur la Constitution
#             (~20 800 tokens dans le system), modèle claude-haiku-4-5.
# Dispositif: aucun cache_control — chaque tour renvoie l'intégralité
#             du document + l'historique au tarif input plein (1x).
# Attendu   : coût maximal ; le total obtenu donne la valeur BASELINE
#             (tarifs.py) contre laquelle tous les autres scripts
#             calculent leur économie.
# Comparer  : point de comparaison de toute la suite (02 → 15).
# =============================================================

# Importations des tarifs, fonctions,du questionnaire et des bibliotheques
import anthropic
from afficher_reponse import afficher_reponse
from document import DOCUMENT
from questions import QUESTIONS
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
        system=construire_system(),         
        messages=MESSAGES,
    )
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)



# --- Bilan ---
TITRE = "BASELINE SANS CACHE"
afficher_reponse(BILANS=BILANS, TITRE=TITRE)

