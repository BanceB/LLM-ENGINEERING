# =============================================================
# 09 — MÉLANGE TTL : 1 H (document) + 5 MIN AUTO (suffixe peu variable)
# -------------------------------------------------------------
# Dispositif: mêmes deux breakpoints que 08 (TTL "1h" sur le
#             document + cache auto 5 min), mais la minute SIMULÉE
#             n'avance que tous les 2 tours ((tour - 1) // 2) :
#             changements aux tours 3, 5, 7 et 9 seulement.
# Attendu   : document toujours LU du cache 1 h ; la partie 5 min
#             est LUE tant que la minute ne bouge pas et réécrite
#             aux tours 3, 5, 7, 9 → économie intermédiaire entre 08 et 10.
# Comparer  : 08 (pire cas), 10 (cas idéal sans suffixe).
# =============================================================

# Importations des tarifs, fonctions,du questionnaire et des bibliotheques
import anthropic
from afficher_reponse import afficher_reponse
from document import DOCUMENT
from questions import QUESTIONS
from tarifs import BASELINE
from datetime import datetime, timedelta
from seuil import seuil

client = anthropic.Anthropic()

# parametres systeme
MODELE = "claude-haiku-4-5"
MAX_TOKENS = 300
HEURE_DEBUT = datetime.now()   # figée au lancement : le "temps" avance avec les tours

def construire_system(tour=1):
    # Minute SIMULÉE : elle avance d'un cran tous les 2 tours, donc la
    # valeur change QUATRE fois pendant le test (aux tours 3, 5, 7
    # et 9), quelle que soit la vitesse réelle des réponses.
    minute_simulee = HEURE_DEBUT + timedelta(minutes=(tour - 1) // 2)
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
            "text": f"Date et heure actuelles : {minute_simulee.isoformat(timespec='minutes')}",
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

    response = client.messages.create(
        model=MODELE,
        max_tokens=MAX_TOKENS,
        cache_control={"type": "ephemeral"},   # CACHE AUTOMATIQUE
        system=construire_system(i),           # ← le tour pilote la minute simulée
        messages=MESSAGES,
    )
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)



# --- Bilan ---
TITRE = "MELANGE TTL (SUFFIXE MOYENEMENT VARIABLE)"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE, Melange_TTL=True)
