# Livraison 4 — Finalisation de la refonte conversationnelle

Cette livraison ajoute uniquement des tests de non-régression.

## Fichiers

- `backend/tests/cognitive/test_conversation_service.py`
- `backend/tests/cognitive/test_conversation_pipeline_regressions.py`

## Vérification

Depuis le dossier `backend` :

```cmd
python -m compileall tru_ai
python -m pytest
```

Les nouveaux tests vérifient notamment :

- la délégation du `ConversationService` vers le pipeline ;
- la consultation et la suppression des conversations ;
- la récupération des requêtes et des preuves ;
- la normalisation des données persistées invalides ;
- l'utilisation effective de la question réécrite ;
- la déduplication insensible à la casse des avertissements ;
- la présence de la trace conversationnelle.
