# =============================================================
# 05 — RÉPARATION : BREAKPOINT EXPLICITE (suffixe extrêmement variable)
# -------------------------------------------------------------
# Dispositif: le cache_control est posé DANS le bloc document
#             (dernier bloc STABLE), AVANT le bloc datetime qui
#             change à chaque appel. Plus de cache_control à la
#             racine de la requête.
# Attendu   : le document est LU du cache à chaque tour ; seuls le
#             suffixe variable et l'historique restent au tarif
#             plein → l'essentiel de l'économie de 02 est retrouvé
#             malgré le suffixe.
# Comparer  : 03 (le piège non réparé), 02 (référence cache sain).
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
            "cache_control": {"type": "ephemeral"},   # ← BREAKPOINT EXPLICITE 
            # posé sur le DERNIER BLOC STABLE, avant le contenu variable
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
        # plus de cache_control ici : le breakpoint est DANS le bloc
        system=construire_system(),         
        messages=MESSAGES,
    )
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)


# --- Bilan ---
TITRE = "BREAKPOINT EXPLICITE (SUFFIXE EXTREMEMENT VARIABLE)"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE)
