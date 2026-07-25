# =============================================================
# 12 — INVALIDATION EN CASCADE AVEC MÉLANGE TTL
# -------------------------------------------------------------
# Question  : modifier le bloc en cache 1 h invalide-t-il aussi le
#             cache 5 min de la conversation ?
# Dispositif: TTL "1h" sur le document + cache auto 5 min ; au tour 4,
#             la consigne RH modifie le TEXTE du bloc document (1 h).
# Attendu   : oui — le cache est un match de préfixe : changer le
#             bloc 1 h invalide tout ce qui suit, cache 5 min
#             compris. Réécriture complète au tour 4 : un TTL long
#             ne protège PAS contre une modification de contenu.
# Comparer  : 11 (cache simple), 10 (mélange TTL sans perturbation).
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
def construire_system(consigne_extra=""):
    return [
        {
            "type": "text",
            "text": (
                "Tu es un assistant juridique. Tu réponds aux questions des "
                "citoyens en te basant UNIQUEMENT sur la Constitution française "
                "fournie ci-dessous. Si l'information n'y figure pas, "
                "dis-le clairement." + consigne_extra + "\n\n" + DOCUMENT
            ),
            "cache_control": {"type": "ephemeral", "ttl" : '1h'},   # ← BREAKPOINT EXPLICITE D'UNE HEURE
            
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
    MESSAGES.append({"role": "user", "content": q})

    # ⚠️ AU TOUR 4 : la RH demande une modification de consigne
    if i >= 4:
        consigne = " Termine toujours ta réponse par « Cordialement, votre service RH »."
        if i == 4:
            print(">>> MODIFICATION DU SYSTEM PROMPT À CE TOUR <<<")
    else:
        consigne = ""

    response = client.messages.create(
        model=MODELE,
        max_tokens=MAX_TOKENS,
        cache_control = {"type": "ephemeral"},  # CACHE AUTOMATIQUE
        system=construire_system(consigne),
        messages=MESSAGES,
    )

    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)


# --- Bilan ---
TITRE ="MELANGE TTL ET INVALIDATION PAR MODIFICATION DU SYSTEM"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE, Melange_TTL=True)