# Installation de TRU-AI 0.9.5-dev

Cette documentation concerne la version active de développement `0.9.5-dev`. Elle ne correspond pas à une publication finale `0.9.5`.

## Méthode rapide sous Windows

Décompressez la livraison dans :

```text
C:\Sites\Projects\TRU-AI
```

Fermez VS Code et les processus utilisant le projet, puis exécutez dans CMD :

```cmd
cd /d C:\Sites\Projects\TRU-AI
```

Utilisez le dépôt Git comme source de vérité. N'utilisez pas d'ancienne archive ZIP comme référence si le dépôt est disponible.

## Validation

Dans le dépôt complet :

```cmd
cd /d C:\Sites\Projects\TRU-AI
python -m pytest
```

Résultat attendu dans l'état de préparation `0.9.5-dev` :

```text
461 passed
```
