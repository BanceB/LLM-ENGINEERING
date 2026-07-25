# Expérimentations — prompt caching (Claude Haiku 4.5)

Chaque script mène la même conversation de 10 questions sur un long document
(la Constitution française du 4 octobre 1958, ~20 800 tokens), affiche le
détail du champ `usage` tour par tour, le coût de chaque tour et l'économie
par rapport à la baseline.

## Modules communs (à la racine)

- `tarifs.py`            — prix Haiku 4.5 ($/MTok) + `BASELINE` de référence
- `constitution.txt`     — le texte intégral (source : conseil-constitutionnel.fr)
- `document.py`          — charge la Constitution + `RUN_ID` unique par exécution
  (garantit un cache neuf à chaque lancement, aucune attente entre deux scripts)
- `questions.py`         — les 10 questions du test
- `seuil.py`             — vérification du seuil de cacheabilité (4 096 tokens)
- `afficher_reponse.py`  — bilan des coûts par tour (mode simple ou mélange TTL)

## Scripts

- `01` — baseline sans cache (référence, donne la valeur de `BASELINE`)
- `02` — caching automatique : `cache_control` à la racine de la requête
- `03` / `04` — le piège : suffixe variable après le contenu stable
  (à chaque appel / à chaque minute)
- `05` / `06` / `07` — réparation : breakpoint explicite sur le dernier bloc stable (suffixe très variable / peu variable / stable)
- `08` / `09` / `10` — mélange TTL : 1 h sur le document + 5 min automatique sur la conversation (suffixe très variable / peu variable / stable)
- `11` / `12` — invalidation en cascade : system modifié au tour 4
  (cache simple / mélange TTL)
- `13` / `14` — expiration du TTL 5 min : pause de 5 min 30 avant le tour 4
  (cache simple / mélange TTL)
- `15` — pre-warming : cache 1 h chauffé avec `max_tokens=1` avant le premier utilisateur → le tour 1 démarre directement en LECTURE
