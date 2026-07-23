from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
)

from tru_ai.query.engine import (
    GraphQueryEngine,
)
from tru_ai.query.graph_index import GraphIndex
from tru_ai.query.pathfinder import (
    GraphPathfinder,
)
from tru_ai.query.repository import (
    GraphRepository,
)


router = APIRouter(
    prefix="/query",
    tags=["Knowledge graph query"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]

GRAPH_DIRECTORY = (
    PROJECT_ROOT / "corpus" / "graph"
)

NODES_PATH = (
    GRAPH_DIRECTORY / "nodes.jsonl"
)

EDGES_PATH = (
    GRAPH_DIRECTORY / "edges.jsonl"
)


@lru_cache(maxsize=1)
def get_index() -> GraphIndex:
    repository = GraphRepository(
        nodes_path=NODES_PATH,
        edges_path=EDGES_PATH,
    )

    graph = repository.load()

    return GraphIndex(graph)


def get_engine(
    index: GraphIndex | None = None,
) -> GraphQueryEngine:
    return GraphQueryEngine(
        index or get_index()
    )


def get_pathfinder(
    index: GraphIndex | None = None,
) -> GraphPathfinder:
    return GraphPathfinder(
        index or get_index()
    )


@router.get("/health")
def query_health() -> dict:
    try:
        index = get_index()
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "status": "ok",
        "node_count": len(
            index.nodes_by_id
        ),
        "edge_count": len(
            index.edges_by_id
        ),
    }


@router.post("/reload")
def reload_query_graph() -> dict:
    get_index.cache_clear()

    try:
        index = get_index()
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "status": "reloaded",
        "node_count": len(
            index.nodes_by_id
        ),
        "edge_count": len(
            index.edges_by_id
        ),
    }


@router.get("/node/{name}")
def find_node(name: str) -> dict:
    try:
        node = get_engine().find_node(name)
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    if node is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nœud introuvable : {name}"
            ),
        )

    return node.to_dict()


@router.get("/search")
def search_nodes(
    q: str = Query(
        min_length=1,
        description=(
            "Texte recherché dans les "
            "étiquettes et alias."
        ),
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> dict:
    try:
        results = (
            get_engine().search_nodes(
                query=q,
                limit=limit,
            )
        )
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "query": q,
        "count": len(results),
        "results": [
            result.to_dict()
            for result in results
        ],
    }


@router.get("/outgoing/{name}")
def outgoing_relations(
    name: str,
    predicate: str | None = None,
) -> dict:
    try:
        relations = get_engine().outgoing(
            query=name,
            predicate=predicate,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "node": name,
        "direction": "outgoing",
        "predicate": predicate,
        "count": len(relations),
        "relations": [
            relation.to_dict()
            for relation in relations
        ],
    }


@router.get("/incoming/{name}")
def incoming_relations(
    name: str,
    predicate: str | None = None,
) -> dict:
    try:
        relations = get_engine().incoming(
            query=name,
            predicate=predicate,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "node": name,
        "direction": "incoming",
        "predicate": predicate,
        "count": len(relations),
        "relations": [
            relation.to_dict()
            for relation in relations
        ],
    }


@router.get("/neighbors/{name}")
def neighbors(
    name: str,
    direction: str = Query(
        default="both",
        pattern="^(incoming|outgoing|both)$",
    ),
    predicate: str | None = None,
) -> dict:
    try:
        results = get_engine().neighbors(
            query=name,
            direction=direction,
            predicate=predicate,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "node": name,
        "direction": direction,
        "predicate": predicate,
        "count": len(results),
        "neighbors": [
            result.to_dict()
            for result in results
        ],
    }


@router.get("/predicate/{predicate}")
def relations_by_predicate(
    predicate: str,
) -> dict:
    try:
        relations = (
            get_engine()
            .find_by_predicate(predicate)
        )
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "predicate": predicate,
        "count": len(relations),
        "relations": [
            relation.to_dict()
            for relation in relations
        ],
    }


@router.get("/path")
def shortest_path(
    source: str = Query(
        alias="from",
        min_length=1,
    ),
    target: str = Query(
        alias="to",
        min_length=1,
    ),
    directed: bool = False,
    max_depth: int = Query(
        default=10,
        ge=0,
        le=100,
    ),
) -> dict:
    engine = get_engine()

    source_node = engine.find_node(source)
    target_node = engine.find_node(target)

    if source_node is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nœud source introuvable : "
                f"{source}"
            ),
        )

    if target_node is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Nœud cible introuvable : "
                f"{target}"
            ),
        )

    try:
        path = (
            get_pathfinder()
            .shortest_path(
                source_id=source_node.node_id,
                target_id=target_node.node_id,
                directed=directed,
                max_depth=max_depth,
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if path is None:
        return {
            "found": False,
            "from": source,
            "to": target,
            "directed": directed,
            "max_depth": max_depth,
            "path": None,
        }

    return {
        "found": True,
        "from": source,
        "to": target,
        "directed": directed,
        "max_depth": max_depth,
        "path": path.to_dict(),
    }