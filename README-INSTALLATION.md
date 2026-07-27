# TRU-AI — Livraison 7.4

## Objet

Cette livraison ajoute l'analyse déterministe des contradictions réflexives.
Elle conserve les contradictions déjà déclarées dans le contexte et examine
uniquement des métadonnées explicites du graphe de reconnaissance.

## Métadonnées reconnues

### Référence de contradiction explicite

```python
"attributes": {"contradicts_relation_id": "r2"}
```

### Polarité explicite

```python
"attributes": {"polarity": "positive"}
"attributes": {"polarity": "negative"}
```

Deux polarités opposées portant sur la même paire orientée de nœuds produisent
une contradiction réflexive explicite.

### Tension potentielle

```python
"attributes": {"tension": True}
"attributes": {"tension": "potential"}
```

Une tension potentielle est signalée séparément et n'est pas présentée comme
une contradiction établie.

## Principe de sûreté épistémique

Le moteur ne déduit rien à partir de mots tels que `nie`, `refuse`, `accepte`
ou `reconnaît`. En l'absence de métadonnées explicites, aucune contradiction
réflexive n'est créée.

## Fichiers

```text
backend/tru_ai/cognitive/reasoning/engines/contradictions.py
backend/tru_ai/cognitive/reasoning/engines/synthesis.py
backend/tests/cognitive/test_reasoning_engines.py
backend/tests/cognitive/test_reasoning_executor.py
backend/tests/cognitive/test_reflexive_contradictions.py
```

## Installation

Copier le dossier `backend` de l'archive dans la racine du dépôt TRU-AI et
accepter le remplacement des fichiers présents dans cette livraison.

## Tests

Depuis `C:\Sites\Projects\TRU-AI\backend` :

```cmd
python -m py_compile tru_ai\cognitiveeasoning\engines\contradictions.py
python -m py_compile tru_ai\cognitiveeasoning\engines\synthesis.py
python -m pytest tests\cognitive	est_reflexive_contradictions.py -v
python -m pytest tests\cognitive	est_reasoning_engines.py -v
python -m pytest tests\cognitive	est_reasoning_executor.py -v
python -m pytest
```

## Résultat attendu

La base validée contient 420 tests. Cette livraison ajoute 10 tests, soit un
total attendu de 430 tests si aucun autre test n'a été ajouté localement.
