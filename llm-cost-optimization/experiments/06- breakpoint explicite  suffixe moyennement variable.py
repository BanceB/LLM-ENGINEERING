# =============================================================
# 06 — RÉPARATION : BREAKPOINT EXPLICITE (suffixe moyennement variable)
# -------------------------------------------------------------
# Dispositif: même minute SIMULÉE que 04 (avance tous les 2 tours),
#             mais le cache_control est posé DANS le bloc document
#             (dernier bloc STABLE), avant le suffixe variable.
#             Plus de cache_control à la racine de la requête.
# Attendu   : le document est LU du cache à chaque tour, que la
#             minute bouge ou non → comparaison équitable avec 04
#             pour isoler l'effet du breakpoint explicite.
# Comparer  : 04 (le piège non réparé), 05 (variante pire cas).
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
    # Même minute SIMULÉE que le script 04 : elle avance tous les 2 tours,
    # donc la valeur change QUATRE fois pendant le test (tours 3, 5, 7, 9),
    # pour une comparaison équitable avec/sans breakpoint explicite.
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
            "cache_control": {"type": "ephemeral"},   # ← BREAKPOINT EXPLICITE 
            # posé sur le DERNIER BLOC STABLE, avant le contenu variable
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
        # plus de cache_control ici : le breakpoint est DANS le bloc
        system=construire_system(i),           # ← le tour pilote la minute simulée
        messages=MESSAGES,
    )
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)


# --- Bilan ---
TITRE = "BREAKPOINT EXPLICITE (SUFFIXE MOYENEMENT VARIABLE)"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE)
