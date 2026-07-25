# =============================================================
# 02 — CACHING AUTOMATIQUE : UNE SEULE LIGNE
# -------------------------------------------------------------
# Dispositif: une seule ligne ajoutée par rapport à 01 —
#             cache_control={"type": "ephemeral"} à la racine de la
#             requête. L'API pose le breakpoint sur le DERNIER bloc
#             cacheable (TTL 5 min par défaut).
# Attendu   : tour 1 = ÉCRITURE du préfixe (~1,25x), tours suivants =
#             LECTURE (~0,1x) → ~90 % d'économie sur la partie cachée.
# Comparer  : 01 (baseline sans cache).
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
        cache_control={"type": "ephemeral"},   # ← AJOUT DU CACHE AUTOMATIQUE
        system=construire_system(),         
        messages=MESSAGES,
    )
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)

# --- Bilan ---
TITRE = "CACHING AUTOMATIQUE"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE)
