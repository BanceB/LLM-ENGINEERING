from tarifs import (PRIX_INPUT, PRIX_ECRIT, PRIX_ECRIT_1H, PRIX_LU,
                    PRIX_SORTIE, mettre_a_jour_baseline)
from exporter_csv import exporter_csv


def afficher_reponse(BASELINE=None, BILANS=None, TITRE="", Melange_TTL=False, cout_warmup=None):

        # --- Bilan ---
        print("=" * 72)
        print(TITRE)
        print("=" * 72)
        cout_total = 0.0
        LOAD_1H = 0 # nombre de token pour le chargement de la doc
        MESURES = []  # une entrée par tour, exportée vers results/*.csv à la fin

        # --- Pré-chauffage éventuel (pre-warming) : on compte son coût
        #     et on récupère la taille du document déjà écrit en cache 1h ---
        if cout_warmup is not None:
                LOAD_1H = cout_warmup.cache_creation_input_tokens
                cout_w = (cout_warmup.input_tokens * PRIX_INPUT
                          + cout_warmup.cache_read_input_tokens * PRIX_LU
                          + cout_warmup.cache_creation.ephemeral_5m_input_tokens * PRIX_ECRIT
                          + cout_warmup.cache_creation.ephemeral_1h_input_tokens * PRIX_ECRIT_1H
                          + cout_warmup.output_tokens * PRIX_SORTIE) / 1_000_000
                cout_total += cout_w
                MESURES.append({"turn": 0,  # tour 0 = warmup, avant le premier utilisateur
                                "input": cout_warmup.input_tokens,
                                "lu": cout_warmup.cache_read_input_tokens,
                                "ecrit_5m": cout_warmup.cache_creation.ephemeral_5m_input_tokens,
                                "ecrit_1h": cout_warmup.cache_creation.ephemeral_1h_input_tokens,
                                "sortie": cout_warmup.output_tokens,
                                "cout": cout_w})

        if Melange_TTL :

                for t, u in enumerate(BILANS, 1):
                        e5m = u.cache_creation.ephemeral_5m_input_tokens
                        e1h = u.cache_creation.ephemeral_1h_input_tokens
                        lus = u.cache_read_input_tokens

                        cout = (u.input_tokens * PRIX_INPUT
                                + lus * PRIX_LU
                                + e5m * PRIX_ECRIT
                                + e1h * PRIX_ECRIT_1H
                                + u.output_tokens * PRIX_SORTIE) / 1_000_000
                        cout_total += cout
                        MESURES.append({"turn": t, "input": u.input_tokens,
                                        "lu": lus, "ecrit_5m": e5m,
                                        "ecrit_1h": e1h, "sortie": u.output_tokens,
                                        "cout": cout})

                        # --- Étiquette d'état, version mélange de TTL ---
                        if lus == 0 :
                                etat = "MIXTE (grosse écriture)"
                                LOAD_1H = e1h  # recuperation du nombre de token de la doc
                        elif lus == LOAD_1H  :
                                etat = "ÉCRITURE 5min"      # régime de croisière : on lit, petit ajout
                        elif lus > LOAD_1H  :
                                etat = "LECTURE (+incrément)"
                        else:
                                etat = "SANS CACHE"

                        print(f"Tour {t} | input: {u.input_tokens:>4} | lu: {lus:>6} | "
                                f"écrit 1h: {e1h:>5} | écrit 5m: {e5m:>5} | "
                                f"sortie: {u.output_tokens:>4} | {cout:.6f} $ | {etat}")

        else :

                for t, u in enumerate(BILANS, 1):
                        cout = (u.input_tokens * PRIX_INPUT
                                + u.cache_read_input_tokens * PRIX_LU
                                + u.cache_creation_input_tokens * PRIX_ECRIT
                                + u.output_tokens * PRIX_SORTIE) / 1_000_000
                        cout_total += cout
                        # répartition 5m/1h si l'API la fournit (sinon tout en 5m)
                        cc = getattr(u, "cache_creation", None)
                        e5m = cc.ephemeral_5m_input_tokens if cc else u.cache_creation_input_tokens
                        e1h = cc.ephemeral_1h_input_tokens if cc else 0
                        MESURES.append({"turn": t, "input": u.input_tokens,
                                        "lu": u.cache_read_input_tokens,
                                        "ecrit_5m": e5m, "ecrit_1h": e1h,
                                        "sortie": u.output_tokens,
                                        "cout": cout})

                        # --- Étiquette d'état : 0 écrit + 0 lu = aucun cache en jeu ---
                        if u.cache_creation_input_tokens == 0 and u.cache_read_input_tokens == 0:
                                etat = "SANS CACHE"
                        elif u.cache_creation_input_tokens > u.cache_read_input_tokens:
                                etat = "ÉCRITURE"
                        else:
                                etat = "LECTURE"

                        print(f"Tour {t} | input: {u.input_tokens:>6} | cache lu: "
                                f"{u.cache_read_input_tokens:>5} | cache écrit: "
                                f"{u.cache_creation_input_tokens:>5} | sortie: "
                                f"{u.output_tokens:>4} | {cout:.6f} $ | {etat}")


        print("-" * 72)
        if BASELINE is None:
                print(f"COÛT TOTAL BASELINE : {cout_total:.3f} $ ")
                # le script 01 vient de tourner : on synchronise tarifs.BASELINE
                if mettre_a_jour_baseline(cout_total):
                        print(f"BASELINE mise à jour dans tarifs.py : {cout_total:.3f} $")
        else:
                print(f"COÛT AVEC CACHE : {cout_total:.3f} $")
                print(f"BASELINE        : {BASELINE:.3f} $")
                economie = BASELINE - cout_total
                print(f"ÉCONOMIE        : {economie:.3f} $  ({economie/BASELINE*100:.1f} %)")

        # --- Mise à jour de results/measures.csv et results/summary.csv ---
        exporter_csv(config_name=TITRE, mesures=MESURES,
                     cout_total=cout_total, baseline=BASELINE)
