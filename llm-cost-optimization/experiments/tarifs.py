# --- Tarifs Haiku 4.5 ($ / MTok) ---
PRIX_INPUT  = 1.00
PRIX_ECRIT  = 1.25      # prix écriture cache 5min  
PRIX_ECRIT_1H = 2.00   # prix écriture cache 1 h 
PRIX_LU     = 0.10
PRIX_SORTIE = 5.00

# --- Coût de référence mesuré à l'étape 01 (baseline sans cache) ---
# Mise à jour AUTOMATIQUE à chaque exécution du script 01 si le coût
# mesuré change (voir mettre_a_jour_baseline ci-dessous).
BASELINE = 0.229


def mettre_a_jour_baseline(nouveau_cout):
    """Réécrit la ligne « BASELINE = ... » de ce fichier si le coût mesuré
    par le script 01 diffère de la valeur actuelle (au millième près).
    Retourne True si le fichier a été modifié."""
    import re
    from pathlib import Path

    if f"{nouveau_cout:.3f}" == f"{BASELINE:.3f}":
        return False

    chemin = Path(__file__)
    texte = chemin.read_text(encoding="utf-8")
    texte = re.sub(r"^BASELINE\s*=\s*[0-9.]+",
                   f"BASELINE = {nouveau_cout:.3f}",
                   texte, count=1, flags=re.M)
    chemin.write_text(texte, encoding="utf-8")
    return True

