# Installation de TRU-AI 0.9.6

Cette documentation concerne la version `0.9.6`.

## Méthode rapide sous Windows

Placez-vous à la racine du dépôt :

```cmd
cd <repo>
```

Utilisez le dépôt Git comme source de vérité. N'utilisez pas d'ancienne archive ZIP comme référence si le dépôt est disponible.

## Dépendances de développement

Installez le paquet et les outils qualité depuis la racine du dépôt :

```cmd
python -m pip install -e "backend[dev]"
```

## Validation

Dans le dépôt complet :

```cmd
cd <repo>
python -m pytest
```

Résultat attendu dans l'état de préparation `0.9.6` :

```text
514 passed
```
