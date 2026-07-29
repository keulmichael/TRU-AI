## [0.9.6]

- added public scientific analysis models for generic scientific requests and
  results;
- added `ScientificInputAdapter` to isolate mapping from public inputs to
  reasoning context;
- added `ScientificService` as the application facade over `ReasoningPlanner`
  and `ReasoningExecutor`;
- added `ScientificExplanationService` for reusable summaries, stage cards, and
  human-readable projections derived from real results;
- exposed `GET /scientific/health` and `POST /scientific/analyze`;
- migrated `POST /reasoning/scientific-demo` to the generic scientific service
  while preserving the historical response contract;
- preserved compatibility with `GET /scientific-demo`;
- kept scientific revisions as recommendations, not applied mutations;
- kept persistence disabled and absent from the scientific API.

## [0.9.5-dev] - Historical development line

- préparation de l'ancienne ligne de développement `0.9.5-dev` ;
- ajout d'une source Python unique de version pour le package, la CLI et les métadonnées FastAPI ;
- nettoyage du suivi Git des artefacts générés (`__pycache__`, fichiers `.pyc`, métadonnées `.egg-info`, archives et verrous temporaires).

## 0.9.4 — Falsification Engine

- ajout de `ScientificObservation`, `VerificationReport` et `FalsificationReport` ;
- ajout de `VerificationOperator` et `FalsificationOperator` au pipeline cognitif ;
- comparaison explicite des prédictions aux observations ;
- calcul déterministe des scores de cohérence et de preuve ;
- falsification formelle uniquement lorsqu’une condition explicite existe et est satisfaite ;
- production de révisions scientifiques (`retain`, `review`, `revise`) ;
- sérialisation complète et traçabilité opératorielle ;
- ajout de cinq tests dédiés à la version 9.4 ;
- passage de la version du paquet à `0.9.4`.

# Changelog

## 0.9.3 — Prediction Engine

- ajout du calcul déterministe de confiance des prédictions ;
- ajout des niveaux normalisés de confiance ;
- prise en charge des observations attendues, horizons et hypothèses ;
- génération de prédictions depuis des règles conditionnelles explicites ;
- ajout des scénarios scientifiques ;
- ajout de la simulation croisée prédictions/scénarios ;
- sérialisation des scénarios et simulations ;
- ajout de cinq tests dédiés à la version 9.3 ;
- passage de la version du paquet à `0.9.3`.

9.0
✓ Scientific Reasoning

447 tests

--------------------------------

9.1
✓ Theory Builder

447 tests

--------------------------------

9.2

✓ Theory Evolution
✓ Versionnement déterministe des théories
✓ Historique et snapshots immuables
✓ Filiation entre snapshots
✓ Résumé des ajouts, retraits, renforcements et affaiblissements
✓ Trace des opérateurs TRU
✓ Sérialisation et compatibilité ascendante
✓ 4 nouveaux tests dédiés à la 9.2

Validation de l’export léger : 447 tests réussis sur 451.
Les 4 tests restants requièrent les corpus et ressources statiques exclus de l’export.
