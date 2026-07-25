"""
Analyse des mesures de prompt caching (Claude Haiku 4.5).
Corpus : Constitution française 1958 (~20 800 tokens), 10 tours par config.
Génère les 4 figures et robustesse.csv.
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).parent
FIG = BASE / "figures"

# --- Tarifs Haiku 4.5, $/MTok (à revérifier sur la page officielle) ----
PRICE = {"input": 1.00, "read": 0.10, "w5": 1.25, "w1": 2.00, "out": 5.00}

m = pd.read_csv(BASE / "results" / "measures.csv", dtype={"config_id": str})
s = pd.read_csv(BASE / "results" / "summary.csv", dtype={"config_id": str})

# Coût par tour (recalcul indépendant, validation croisée avec summary)
m["cost"] = (
    m.input_tokens * PRICE["input"]
    + m.cache_read_tokens * PRICE["read"]
    + m.cache_write_5m_tokens * PRICE["w5"]
    + m.cache_write_1h_tokens * PRICE["w1"]
    + m.output_tokens * PRICE["out"]
) / 1_000_000

sv = s.set_index("config_id").savings_pct
name = s.set_index("config_id").config_name

# Palette
NAVY, GREEN, RED, GOLD, BLUE = "#1F3A5F", "#2E7D46", "#C0392B", "#B8860B", "#2E5C8A"

# =====================================================================
# FIGURE 1 — Effet dose-réponse de la variabilité du suffixe
# =====================================================================
doses = [("03", "Extrême\n(chaque appel)"), ("04", "Moyenne\n(~chaque minute)"),
         ("02", "Stable\n(aucune variation)")]
vals = [sv[c] for c, _ in doses]
labels = [l for _, l in doses]
colors = [RED if v < 0 else GREEN for v in vals]

fig, ax = plt.subplots(figsize=(7.5, 4.2))
bars = ax.bar(labels, vals, color=colors, width=0.6)
ax.axhline(0, color="#333", lw=1)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + (2 if v > 0 else -4),
            f"{v:+.1f} %", ha="center", fontweight="bold",
            va="bottom" if v > 0 else "top")
ax.set_ylabel("Économie vs baseline (%)")
ax.set_title("Facteur 1 — La variabilité du préfixe : un effet dose-réponse\n"
             "(mode automatique, mêmes 10 tours)", fontweight="bold", fontsize=11)
ax.set_ylim(-35, 90)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(FIG / "fig1_dose_reponse.png", dpi=160)
plt.close()

# =====================================================================
# FIGURE 2 — Grille de robustesse : performance vs sensibilité
# =====================================================================
grille = {
    "Automatique":  ["03", "04", "02"],
    "Breakpoint\nexplicite": ["05", "06", "07"],
    "Mélange TTL":  ["08", "09", "10"],
}
niveaux = ["Suffixe extrême", "Suffixe moyen", "Suffixe stable"]
fig, (axL, axR) = plt.subplots(1, 2, figsize=(12, 4.6),
                               gridspec_kw={"width_ratios": [2, 1]})

x = range(3)
markers = ["o", "s", "^"]
palette = [RED, BLUE, GREEN]
for (strat, ids), col, mk in zip(grille.items(), palette, markers):
    ys = [sv[c] for c in ids]
    axL.plot(x, ys, marker=mk, ms=9, lw=2, color=col,
             label=strat.replace("\n", " "))
    for xi, yi in zip(x, ys):
        axL.text(xi, yi + 3, f"{yi:.0f}", ha="center", fontsize=8, color=col)
axL.axhline(0, color="#999", lw=0.8, ls="--")
axL.set_xticks(list(x))
axL.set_xticklabels(niveaux)
axL.set_ylabel("Économie vs baseline (%)")
axL.set_title("Performance selon la variabilité du suffixe", fontweight="bold")
axL.legend(loc="lower right", fontsize=9)
axL.set_ylim(-35, 90)
axL.spines[["top", "right"]].set_visible(False)

# Panneau droit : étendue (robustesse)
etendues = {strat.replace("\n", " "): max(sv[c] for c in ids) - min(sv[c] for c in ids)
            for strat, ids in grille.items()}
noms = list(etendues.keys())
ets = list(etendues.values())
barcols = [RED, BLUE, GREEN]
b = axR.barh(noms, ets, color=barcols)
for bar, v in zip(b, ets):
    axR.text(v + 1.5, bar.get_y() + bar.get_height() / 2,
             f"{v:.1f} pts", va="center", fontweight="bold")
axR.set_xlabel("Étendue des économies (pts)")
axR.set_title("Sensibilité aux conditions\n(plus court = plus robuste)",
              fontweight="bold")
axR.invert_yaxis()
axR.set_xlim(0, 110)
axR.spines[["top", "right"]].set_visible(False)
fig.suptitle("Facteur 2 — Performance vs robustesse : le breakpoint explicite domine",
             fontweight="bold", fontsize=12)
plt.tight_layout()
plt.savefig(FIG / "fig2_robustesse.png", dpi=160)
plt.close()

# =====================================================================
# FIGURE 3 — L'assurance asymétrique du TTL 1 h (signatures de coût)
# =====================================================================
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
paires = [
    (axes[0], "Invalidation (system modifié au tour 4)", "11", "12"),
    (axes[1], "Expiration (pause de 5 min avant le tour 4)", "13", "14"),
]
for ax, titre, simple, mixte in paires:
    for cid, lab, col in [(simple, "Cache simple (5 min)", BLUE),
                          (mixte, "Mélange TTL (1 h + 5 min)", GOLD)]:
        d = m[m.config_id == cid].sort_values("turn")
        d = d[d.turn >= 1]
        ax.plot(d.turn, d.cost * 1000, marker="o", ms=5, lw=1.8,
                label=lab, color=col)
    ax.set_title(titre, fontsize=10, fontweight="bold")
    ax.set_xlabel("Tour")
    ax.axvspan(3.5, 4.5, color="#FDE9E7", zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=8)
axes[0].set_ylabel("Coût du tour (millièmes de $)")
fig.suptitle("Facteur 3 — Le TTL 1 h : une assurance asymétrique\n"
             "aide contre l'expiration (droite), aggrave contre l'invalidation (gauche)",
             fontweight="bold", fontsize=11)
plt.tight_layout()
plt.savefig(FIG / "fig3_assurance_asymetrique.png", dpi=160)
plt.close()

# =====================================================================
# FIGURE 4 — Prévisibilité : ce que le pre-warming achète vraiment
# =====================================================================
fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 4.4))

# Gauche : coût par tour, 15 (prewarm) vs 10 (mélange TTL stable équivalent)
for cid, lab, col in [("10", "Sans pré-chauffage (config 10)", BLUE),
                      ("15", "Avec pré-chauffage (config 15)", GREEN)]:
    d = m[m.config_id == cid].sort_values("turn")
    d = d[d.turn >= 1]   # on masque le tour 0 (pré-chauffage) pour l'échelle
    axA.plot(d.turn, d.cost * 1000, marker="o", ms=5, lw=1.8, label=lab, color=col)
axA.set_xlabel("Tour (hors requête de pré-chauffage)")
axA.set_ylabel("Coût du tour (millièmes de $)")
axA.set_title("Le pic du tour 1 disparaît avec le pré-chauffage", fontweight="bold")
axA.annotate("pic d'écriture\nabsorbé en amont", xy=(1, m[(m.config_id=='10')&(m.turn==1)].cost.iloc[0]*1000),
             xytext=(3, 30), fontsize=8, color=NAVY,
             arrowprops=dict(arrowstyle="->", color=NAVY))
axA.legend(fontsize=8)
axA.spines[["top", "right"]].set_visible(False)

# Droite : amplitude (volatilité intra-config) comparée
amp = s.set_index("config_id").amplitude
comp = [("02", "Auto"), ("10", "Mélange TTL"), ("15", "Pré-chauffage")]
noms = [n for _, n in comp]
amps = [amp[c] * 1000 for c, _ in comp]
bcol = [BLUE, GOLD, GREEN]
bb = axB.bar(noms, amps, color=bcol, width=0.6)
for bar, v in zip(bb, amps):
    axB.text(bar.get_x() + bar.get_width() / 2, v + 0.5,
             f"{v:.1f}", ha="center", fontweight="bold")
axB.set_ylabel("Amplitude coût max−min entre tours (millièmes de $)")
axB.set_title("Volatilité du coût par tour\n(plus bas = plus prévisible)",
              fontweight="bold")
axB.spines[["top", "right"]].set_visible(False)
fig.suptitle("Facteur 4 — Le pré-chauffage optimise la variance, pas le coût",
             fontweight="bold", fontsize=12)
plt.tight_layout()
plt.savefig(FIG / "fig4_previsibilite.png", dpi=160)
plt.close()

# =====================================================================
# robustesse.csv — la métrique dérivée (étendue inter-conditions)
# =====================================================================
rob = pd.DataFrame([
    {"strategie": strat.replace("\n", " "),
     "perf_min": min(sv[c] for c in ids),
     "perf_max": max(sv[c] for c in ids),
     "etendue_pts": max(sv[c] for c in ids) - min(sv[c] for c in ids)}
    for strat, ids in grille.items()
])
rob.to_csv(BASE / "results" / "robustesse.csv", index=False)

print("Figures générées :", [p.name for p in sorted(FIG.glob("*.png"))])
print("\nRobustesse par stratégie :")
print(rob.to_string(index=False))
print("\nAssurance asymétrique :")
print(f"  Expiration : simple {sv['13']:.1f}% -> mixte {sv['14']:.1f}%  ({sv['14']-sv['13']:+.1f} pts)")
print(f"  Invalidation: simple {sv['11']:.1f}% -> mixte {sv['12']:.1f}%  ({sv['12']-sv['11']:+.1f} pts)")
print(f"\nPré-chauffage : amplitude {amp['15']*1000:.1f} vs {amp['10']*1000:.1f} (config 10) "
      f"=> facteur {amp['10']/amp['15']:.0f}x")
