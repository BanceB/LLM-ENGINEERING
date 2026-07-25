# -------------------------------------------------------------
# LE DOCUMENT LONG : le "gros préfixe stable" du projet.
# La Constitution française du 4 octobre 1958 (texte officiel,
# domaine public), chargée depuis constitution.txt.
# Elle dépasse largement le seuil de cacheabilité de 4 096 tokens.
# -------------------------------------------------------------
import uuid
from pathlib import Path

# Référence unique par EXÉCUTION : garantit un cache neuf à chaque lancement
# de script (aucune attente entre deux expériences). Le cache reste partagé
# normalement entre les tours d'une même exécution.
RUN_ID = uuid.uuid4().hex[:8]

CHEMIN = Path(__file__).parent / "constitution.txt"

DOCUMENT = f"CONSTITUTION DU 4 OCTOBRE 1958 (réf. interne {RUN_ID})\n\n"
DOCUMENT += CHEMIN.read_text(encoding="utf-8")
