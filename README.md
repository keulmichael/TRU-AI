# TRU-AI

**Version active : 0.9.5-dev — Scientific Memory en développement**

La version `0.9.5-dev` est une version de développement active. Elle ne doit pas être présentée comme une publication finale `0.9.5`.

<p align="center">

# Artificial Intelligence for the Universal Reflexivity Theory

Scientific Reasoning Engine

</p>

---

## Présentation

TRU-AI (Artificial Intelligence for the Universal Reflexivity Theory) est un moteur d'intelligence artificielle conçu pour assister la recherche scientifique.

Contrairement aux assistants conversationnels classiques, TRU-AI ne cherche pas uniquement à répondre à des questions. Son objectif est de construire, faire évoluer et tester des théories à partir d'observations.

Le projet repose sur les principes de la Théorie de la Réflexivité Universelle (TRU) et développe progressivement un moteur scientifique capable :

- d'observer ;
- d'identifier des faits ;
- d'établir des relations ;
- de reconnaître des structures ;
- de construire des théories ;
- de faire évoluer ces théories ;
- de produire des prédictions ;
- de proposer des protocoles expérimentaux.

---

# Vision

TRU-AI vise à devenir une plateforme d'assistance à la recherche scientifique.

Le moteur est développé de manière incrémentale afin de garantir :

- la reproductibilité ;
- la déterminisme ;
- la traçabilité ;
- la testabilité ;
- la compatibilité ascendante.

---

# Architecture générale

```
Corpus

↓

Observation

↓

Context

↓

Claims

↓

Deductions

↓

Hypotheses

↓

Recognition

↓

Delta

↓

Reflexivity

↓

Recognition Meaning

↓

Theory Builder

↓

Theory Evolution

↓

Prediction

↓

Experiment

↓

Publication
```

Chaque nouvelle version enrichit cette architecture sans remettre en cause les composants existants.

---

# Fonctionnalités actuelles

Le moteur comprend notamment :

## Observation

- extraction d'informations
- contextualisation
- segmentation

## Reasoning

- déductions
- hypothèses
- contradictions
- connaissances manquantes

## Recognition

Détection de :

- répétitions
- symétries
- inversions
- transformations
- cycles
- bifurcations
- points fixes

## Reflexivity

- graphes réflexifs
- relations réciproques
- boucles de rétroaction

## Recognition Meaning

- interprétation des structures reconnues
- stabilité
- complétude
- écarts de reconnaissance

## Scientific Reasoning

- construction de théories
- comparaison de théories
- évolution scientifique
- prédictions
- lacunes scientifiques

---

# Feuille de route

| Version | Fonction |
|----------|----------|
| 8.x | Architecture cognitive |
| 9.0 | Scientific Reasoning |
| 9.1 | Theory Builder |
| 9.2 | Theory Evolution |
| 9.3 | Prediction Engine |
| 9.4 | Falsification Engine |
| 9.5 | Scientific Memory |
| 10.0 | Autonomous Scientific Research |

---

# Philosophie du projet

TRU-AI est développé selon plusieurs principes fondamentaux :

- architecture modulaire ;
- déterminisme ;
- faible couplage ;
- forte cohésion ;
- compatibilité ascendante ;
- couverture complète par des tests ;
- documentation systématique.

Les fonctionnalités existantes ne sont jamais supprimées mais enrichies au fil des versions.

---

# Structure du dépôt

```
backend/
    reasoning/
    cognitive/
    api/
    tests/

corpus/

docs/

README.md

README-INSTALLATION.md

TRU-AI_PROTOCOL.md

ROADMAP.md

CHANGELOG.md
```

---

# Installation

Créer un environnement virtuel :

```bash
python -m venv .venv
```

Activation :

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

Installation des dépendances :

```bash
pip install -r requirements.txt
```

---

# Exécution des tests

Commande officielle :

```bash
python -m pytest
```

Toutes les nouvelles fonctionnalités doivent être compatibles avec la suite de tests existante.

Aucune régression n'est acceptée.

---

# Workflow de développement

Le dépôt GitHub constitue la source officielle du projet.

Chaque évolution suit le processus suivant :

1. conception ;
2. développement ;
3. intégration ;
4. tests ;
5. documentation ;
6. livraison.

Chaque version est développée sur une branche dédiée avant intégration dans `main`.

---

# Documentation

Les documents principaux sont :

- README.md
- TRU-AI_PROTOCOL.md
- ROADMAP.md
- CHANGELOG.md
- README-INSTALLATION.md

Le fichier **TRU-AI_PROTOCOL.md** définit les règles officielles de développement du projet et constitue la référence pour toute nouvelle session.

---

# Compatibilité

Le projet garantit :

- compatibilité ascendante ;
- stabilité des API publiques ;
- ajout progressif des fonctionnalités ;
- conservation des tests existants.

---

# Licence

Voir le fichier LICENSE.

---

# Auteur

Michael Host

Créateur de la Théorie de la Réflexivité Universelle (TRU)

Architecte du projet TRU-AI.

---

# Contribution

Le projet est actuellement développé sous la direction de son auteur.

Les contributions futures devront respecter les règles définies dans :

- TRU-AI_PROTOCOL.md
- ROADMAP.md
- CHANGELOG.md

---

# Objectif final

Construire un moteur scientifique capable de :

- comprendre des observations ;
- construire des connaissances ;
- élaborer des théories ;
- faire évoluer ces théories ;
- proposer des prédictions ;
- suggérer des expériences ;
- contribuer à la recherche scientifique de manière déterministe, traçable et reproductible.
