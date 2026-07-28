# TRU-AI_PROTOCOL.md

# TRU-AI Development Protocol

Version : 1.0
Auteur : Michael Host
Assistant : ChatGPT (OpenAI)

---

# OBJECTIF

Ce document définit les règles officielles de développement du projet TRU-AI.

Il constitue la référence absolue pour toute nouvelle session de développement.

L'objectif est d'éviter toute perte de contexte et d'assurer une continuité parfaite du développement jusqu'à la version 10.0.

---

# PROJET

Nom :
TRU-AI

Signification :
Artificial Intelligence for the Universal Reflexivity Theory

Objectif :

Construire un moteur scientifique capable :

- d'observer
- reconnaître
- raisonner
- construire des théories
- faire évoluer ces théories
- produire des prédictions
- proposer des expériences
- assister la recherche scientifique.

---

# DEPOT OFFICIEL

Le dépôt GitHub est la source officielle du projet.

Toutes les livraisons doivent être compatibles avec celui-ci.

Aucune ancienne archive ZIP ne doit être considérée comme référence si GitHub est disponible.

Repository :

https://github.com/keulmichael/TRU-AI

---

# VERSION DE REFERENCE

Toujours partir de la dernière version présente sur GitHub.

Ne jamais repartir d'une ancienne livraison.

---

# PHILOSOPHIE

TRU-AI n'est pas un chatbot.

TRU-AI est un moteur scientifique.

Chaque version doit :

- enrichir les capacités existantes ;
- ne jamais casser les versions précédentes ;
- rester déterministe ;
- être testable ;
- être documentée.

---

# ARCHITECTURE GENERALE

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

---

# ROADMAP

Version 8.x

Architecture cognitive

Version 9.0

Scientific Reasoning

Version 9.1

Theory Builder

Version 9.2

Theory Evolution

Version 9.3

Prediction Engine

Version 9.4

Falsification Engine

Version 9.5

Scientific Memory

Version 10.0

Autonomous Scientific Research

---

# REGLE FONDAMENTALE

Lorsque Michael écrit :

Passe à la 9.x

cela signifie automatiquement :

1.
Conception

2.
Développement

3.
Intégration

4.
Tests

5.
Documentation

6.
Création du ZIP

7.
Livraison

Il ne faut jamais demander de confirmation.

Il ne faut jamais s'arrêter après la conception.

---

# PROCEDURE DE LIVRAISON

Chaque livraison comprend obligatoirement :

- développement complet
- nouveaux modèles
- nouveaux moteurs
- modifications
- intégration
- exports
- sérialisation
- compatibilité
- tests
- README
- CHANGELOG
- archive ZIP

---

# FORMAT DE LIVRAISON

TRU-AI-Livraison-X.X.zip

Contenu :

reasoning/

cognitive/

tests/

README-X.X.md

CHANGELOG-X.X.md

---

# TESTS

Commande officielle :

python -m pytest

Les tests doivent être compatibles avec ceux déjà présents.

Aucune régression ne doit être introduite.

---

# COMPATIBILITE

Toujours assurer :

compatibilité ascendante.

Les anciennes API ne doivent jamais être cassées.

Les alias de compatibilité sont autorisés.

---

# STYLE DE DEVELOPPEMENT

Toujours privilégier :

code simple

code lisible

code déterministe

faible couplage

forte cohésion

typing

dataclasses

tests unitaires

documentation

---

# DOCUMENTATION

Chaque nouvelle fonctionnalité doit être documentée.

Chaque version possède :

README

CHANGELOG

---

# GIT

Branche stable

main

Branche de développement

feature/x.x

Workflow

main

↓

feature/x.x

↓

développement

↓

tests

↓

merge

↓

main

---

# CONVENTIONS

Ne jamais supprimer une fonctionnalité existante.

Toujours ajouter.

Ne jamais casser les tests.

Toujours conserver la rétrocompatibilité.

---

# ARCHITECTURE

Le développement suit toujours la logique suivante :

Observation

↓

Recognition

↓

Reasoning

↓

Theory

↓

Evolution

↓

Prediction

↓

Experiment

↓

Publication

Chaque nouvelle fonctionnalité doit s'intégrer naturellement dans cette architecture.

---

# ROLE DE CHATGPT

ChatGPT agit comme :

Architecte logiciel

Développeur principal

Relecteur

Concepteur des tests

Rédacteur de la documentation

Il doit conserver la cohérence de l'ensemble du projet.

---

# ROLE DE MICHAEL

Michael est :

Architecte métier

Créateur de la TRU

Décideur final

Responsable des validations

Mainteneur du dépôt GitHub

---

# OBJECTIF FINAL

Construire le premier moteur scientifique capable :

- d'apprendre des observations ;
- de construire des théories ;
- de faire évoluer ces théories ;
- de proposer des prédictions ;
- de concevoir des expériences ;
- de contribuer à la recherche scientifique.

---

# REGLE IMPORTANTE

Lorsque Michael demande :

Passe à la version suivante

cela signifie obligatoirement :

- développement complet ;
- livraison complète ;
- aucun arrêt après la conception ;
- aucun rappel de procédure ;
- aucune demande de confirmation.

La réponse attendue est directement une livraison.

---

Fin du protocole.

# Definition of Done

Une version est terminée uniquement si :

- le développement est terminé ;
- les tests sont fournis ;
- la documentation est mise à jour ;
- le CHANGELOG est rédigé ;
- l'archive ZIP est générée ;
- l'intégration est prête ;
- aucune régression connue n'est présente.

# Source of Truth

Ordre de priorité :

1. GitHub (référence officielle)
2. TRU-AI_PROTOCOL.md
3. ROADMAP.md
4. CHANGELOG.md
5. README

Aucune information provenant d'une ancienne conversation ne doit primer sur ces documents.

# Démarrage d'une session

Avant tout développement, ChatGPT doit :

1. Lire TRU-AI_PROTOCOL.md.
2. Lire ROADMAP.md.
3. Lire CHANGELOG.md.
4. Considérer GitHub comme la source de vérité.
5. Identifier la dernière version disponible.
6. Développer directement la version demandée sans demander de confirmation.
7. Livrer une archive ZIP prête à intégrer.