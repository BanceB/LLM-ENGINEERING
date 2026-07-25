# =============================================================
# 15 — PRE-WARMING : CACHE 1 H CHAUFFÉ AVANT LE PREMIER UTILISATEUR
# -------------------------------------------------------------
# Dispositif: avant la conversation, un appel « warmup » avec
#             max_tokens=1 écrit le document dans le cache (breakpoint
#             TTL "1h" DANS le bloc). La boucle garde ensuite le
#             cache automatique 5 min pour la conversation.
# Attendu   : le tour 1 démarre directement en LECTURE — la pénalité
#             d'écriture initiale est sortie du parcours utilisateur
#             (c'est le warmup qui la paie, cf. cout_warmup au bilan).
# Comparer  : 10 (même mélange TTL, mais tour 1 en écriture).
# =============================================================

# Importations des tarifs, fonctions,du questionnaire et des bibliotheques
import anthropic
from document import DOCUMENT
from questions import QUESTIONS
from afficher_reponse import afficher_reponse
from tarifs import BASELINE


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
                "dis-le clairement. \n\n" + DOCUMENT
            ),
            "cache_control": {"type": "ephemeral", "ttl": "1h"},   # ← TTL 1 HEURE
        },
    ]

# MESSAGES: stockage memoire | BILANS: retour tokens)
MESSAGES = []
BILANS = [] 

# --- Vérification du seuil (rappel : 4 096 tokens pour Haiku 4.5) ---
nb = client.messages.count_tokens(
    model=MODELE, system=construire_system(),
    messages=[{"role": "user", "content": "x"}],
).input_tokens
print(f"Taille du préfixe : {nb} tokens (seuil Haiku 4.5 = 4096)")
print("→ cacheable" if nb >= 4096 else "→ TROP COURT, augmentez le nombre d'articles")
print()

# ------------------------------------------------------------------
# PRE-WARMING : on charge le document dans le cache AVANT le premier
# utilisateur. max_tokens=1 → un seul token de sortie, coût négligeable.
# ------------------------------------------------------------------
print(">>> PRÉCHAUFFAGE DU CACHE (max_tokens=1)...")
warmup = client.messages.create(
    model=MODELE,
    max_tokens=1,                     # ← minimum accepté par l'API : quasi aucune génération
    system=construire_system(),       # le breakpoint explicite est DANS le bloc doc
    messages=[{"role": "user", "content": "warmup"}],  # placeholder quelconque
)
u = warmup.usage
LOAD_1H = u.cache_creation_input_tokens  # recuperation du nombre de token de la doc
print(f"    cache écrit : {LOAD_1H} tokens")
print(f"    cache LU    : {u.cache_read_input_tokens}")
print(f"    stop_reason : {warmup.stop_reason}")
print(f"    contenu     : {warmup.content}   ← 1 token à peine, c'est normal")
print(">>> Cache chaud. Arrivée du premier utilisateur...\n")


# CHAT BOUCLE
for i, q in enumerate(QUESTIONS, 1):
    print("Q :", q)
    MESSAGES.append({"role": "user", "content": q})
    
    response = client.messages.create(
        model=MODELE,
        max_tokens=MAX_TOKENS,
        cache_control={"type": "ephemeral"},   # automatique = 5 min, pour la conversation
        system=construire_system(),
        messages=MESSAGES,
    )

    # ... le reste inchangé
    texte = response.content[0].text
    print("R :", texte[:120], "...\n")

    MESSAGES.append({"role": "assistant", "content": texte})
    BILANS.append(response.usage)


# --- Bilan ---
TITRE = "PRE-WARMING : CACHE 1H CHAUFFÉ AVANT LE PREMIER UTILISATEUR"
afficher_reponse(BASELINE=BASELINE, BILANS=BILANS, TITRE=TITRE,
                 Melange_TTL=True, cout_warmup=warmup.usage)
