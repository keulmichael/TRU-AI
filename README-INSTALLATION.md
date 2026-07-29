# Installation de TRU-AI 1.0.0

Cette documentation concerne la version `1.0.0`.

## Methode rapide

Placez-vous a la racine du depot :

```cmd
cd <repo>
```

Utilisez le depot Git comme source de verite. N'utilisez pas d'ancienne archive
ZIP comme reference si le depot est disponible.

## Dependances de developpement

Installez le paquet et les outils qualite depuis la racine du depot :

```cmd
python -m pip install -e "backend[dev]"
```

## Lancement local

```cmd
cd backend
python -m uvicorn tru_ai.api.main:app --host 127.0.0.1 --port 8000
```

URLs utiles :

- `http://127.0.0.1:8000/scientific`
- `http://127.0.0.1:8000/scientific/health`
- `http://127.0.0.1:8000/scientific-demo`
- `http://127.0.0.1:8000/docs`

## Validation

Dans le depot complet :

```cmd
python -m pytest
python -m ruff check backend/tru_ai backend/tests backend/scripts
python -m mypy backend/tru_ai
git diff --check
```

Resultat attendu dans l'etat 1.0.0 : suite complete verte, Ruff vert, mypy
vert et diff sans erreur d'espaces.
