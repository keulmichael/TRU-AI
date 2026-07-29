# TRU-AI

**Version active : 1.0.0 - Scientific Workbench**

TRU-AI est un moteur scientifique local concu pour analyser des questions,
theories, predictions et observations a travers un pipeline deterministe.

Le produit 1.0 expose le moteur scientifique generique sous forme d'API REST et
d'interface Web utilisable localement. Le demonstrateur historique reste
disponible pour compatibilite.

## Capacites Utilisateur

TRU-AI permet aujourd'hui de :

- saisir une question scientifique ;
- fournir une theorie et des claims ;
- fournir une prediction, une observation attendue et une condition de
  falsification ;
- fournir une observation reelle et un score de compatibilite ;
- executer le pipeline scientifique complet ;
- consulter un resume, une explication lisible, les cartes d'etapes, la trace
  operateur et le JSON de resultat ;
- tester rapidement des cas confirmatif, contradictoire et incomplet.

## Pipeline Scientifique

Le pipeline actuellement implemente est :

Observation
-> Theory Evolution
-> Prediction
-> Verification
-> Falsification
-> Scientific Gaps

Les explications lisibles sont derivees des resultats reels du pipeline. Les
recommandations de revision restent des recommandations : aucune mutation de
theorie et aucune persistance implicite ne sont effectuees.

## Routes Disponibles

- `GET /` : interface cognitive historique ;
- `GET /scientific` : interface generique du moteur scientifique ;
- `GET /scientific-demo` : demonstrateur scientifique historique ;
- `GET /scientific/health` : etat du moteur scientifique ;
- `POST /scientific/analyze` : API generique d'analyse scientifique ;
- `POST /reasoning/scientific-demo` : route de compatibilite du demonstrateur ;
- `GET /docs` : documentation OpenAPI.

## Limites 1.0

TRU-AI 1.0 ne fournit pas :

- de sessions scientifiques persistantes ;
- d'historique stocke des analyses ;
- d'ingestion dynamique de corpus ;
- de validation scientifique externe ;
- d'export PDF ou Markdown ;
- d'authentification ;
- d'administration ;
- d'apprentissage autonome.

## Installation

Depuis la racine du depot :

```bash
python -m venv .venv
```

Activation Windows :

```bash
.venv\Scripts\activate
```

Activation Linux / macOS :

```bash
source .venv/bin/activate
```

Installation des dependances :

```bash
python -m pip install -e "backend[dev]"
```

## Lancement Local

Depuis la racine du depot :

```bash
cd backend
python -m uvicorn tru_ai.api.main:app --host 127.0.0.1 --port 8000
```

URLs locales :

- API : `http://127.0.0.1:8000`
- OpenAPI : `http://127.0.0.1:8000/docs`
- Interface scientifique : `http://127.0.0.1:8000/scientific`
- Sante scientifique : `http://127.0.0.1:8000/scientific/health`
- Demonstrateur : `http://127.0.0.1:8000/scientific-demo`

Variables d'environnement strictement necessaires :

```text
Aucune pour le moteur scientifique local 1.0.0.
```

## Exemple API Minimal

```bash
curl -X POST http://127.0.0.1:8000/scientific/analyze \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Analyze this scientific observation.\"}"
```

## Validation

Commande officielle :

```bash
python -m pytest
python -m ruff check backend/tru_ai backend/tests backend/scripts
python -m mypy backend/tru_ai
git diff --check
```

Etat attendu pour 1.0.0 : suite complete verte, Ruff vert, mypy vert.

## Documentation Centrale

- `CODEX.md` : regles permanentes de developpement ;
- `AI_WORKFLOW.md` : processus operationnel ;
- `ARCHITECTURE.md` : architecture existante ;
- `SCIENTIFIC_CAPABILITIES.md` : capacites scientifiques implementees ;
- `PROJECT_STATUS.md` : etat court du projet ;
- `ROADMAP.md` et `RESEARCH_ROADMAP.md` : trajectoire produit et recherche ;
- `CHANGELOG.md` : historique des versions.

## Licence

Voir `LICENSE`.
