# -------------------------------------------------------------
# EXPORT CSV : appelé automatiquement par afficher_reponse() à la
# fin de chaque script. Met à jour :
#   - results/measures.csv : le détail tour par tour
#   - results/summary.csv  : totaux + économie vs baseline
# Les lignes du script relancé sont REMPLACÉES (pas dupliquées),
# celles des autres scripts sont conservées.
# Le config_id est déduit du nom du fichier exécuté
# (« 05- breakpoint explicite ....py » → « 05 »).
# -------------------------------------------------------------
import csv
import re
import sys
from pathlib import Path

DOSSIER_RESULTS = Path(__file__).resolve().parent.parent / "results"
FICHIER_MESURES = DOSSIER_RESULTS / "measures.csv"
FICHIER_RESUME  = DOSSIER_RESULTS / "summary.csv"

COLONNES_MESURES = ["config_id", "config_name", "turn", "input_tokens",
                    "cache_read_tokens", "cache_write_5m_tokens",
                    "cache_write_1h_tokens", "output_tokens"]
COLONNES_RESUME  = ["config_id", "config_name", "total_cost_usd", "total_read",
                    "total_write_5m", "total_write_1h", "total_input",
                    "total_output", "savings_pct", "amplitude"]


def _config_id():
    """Numéro du script en cours (« 01- Baseline sans cache.py » → « 01 »)."""
    nom = Path(sys.argv[0]).stem
    m = re.match(r"\s*(\d+)", nom)
    return m.group(1) if m else nom


def _remplacer(fichier, colonnes, config_id, nouvelles_lignes):
    """Réécrit le CSV : anciennes lignes du config_id remplacées, le reste conservé."""
    lignes = []
    if fichier.exists():
        with open(fichier, newline="", encoding="utf-8") as f:
            lignes = [l for l in csv.DictReader(f) if l["config_id"] != config_id]
    lignes.extend(nouvelles_lignes)
    DOSSIER_RESULTS.mkdir(exist_ok=True)
    with open(fichier, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colonnes)
        w.writeheader()
        w.writerows(lignes)


def exporter_csv(config_name, mesures, cout_total, baseline=None):
    """mesures : liste de dicts {turn, input, lu, ecrit_5m, ecrit_1h, sortie}
    (turn 0 = warmup éventuel). baseline=None pour le script 01 lui-même."""
    cid = _config_id()

    lignes_mesures = [
        {"config_id": cid, "config_name": config_name, "turn": m["turn"],
         "input_tokens": m["input"], "cache_read_tokens": m["lu"],
         "cache_write_5m_tokens": m["ecrit_5m"],
         "cache_write_1h_tokens": m["ecrit_1h"],
         "output_tokens": m["sortie"]}
        for m in mesures
    ]
    _remplacer(FICHIER_MESURES, COLONNES_MESURES, cid, lignes_mesures)

    economie_pct = 0.0 if not baseline else (baseline - cout_total) / baseline * 100

    # amplitude : écart en $ entre le tour le plus cher et le moins cher
    # (warmup exclu) — mesure les « pics » d'écriture / d'invalidation.
    couts_tours = [m["cout"] for m in mesures if m["turn"] >= 1]
    amplitude = max(couts_tours) - min(couts_tours) if couts_tours else 0.0
    amplitude = f"{amplitude:.8f}"  # décimal fixe (évite le « 1.79e-05 » dans le tableur)

    resume = {"config_id": cid, "config_name": config_name,
              "total_cost_usd": round(cout_total, 8),
              "total_read": sum(m["lu"] for m in mesures),
              "total_write_5m": sum(m["ecrit_5m"] for m in mesures),
              "total_write_1h": sum(m["ecrit_1h"] for m in mesures),
              "total_input": sum(m["input"] for m in mesures),
              "total_output": sum(m["sortie"] for m in mesures),
              "savings_pct": round(economie_pct, 2),
              "amplitude": amplitude}
    _remplacer(FICHIER_RESUME, COLONNES_RESUME, cid, [resume])

    print(f"CSV mis à jour : {FICHIER_MESURES.name} / {FICHIER_RESUME.name} (config {cid})")
