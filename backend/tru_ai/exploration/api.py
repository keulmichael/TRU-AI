from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from tru_ai.exploration.engine import ExplorationEngine
from tru_ai.exploration.models import (
    GraphPattern,
    GraphQuery,
    PatternConstraint,
)
from tru_ai.exploration.pattern_matcher import (
    ExplorationPatternMatcher,
)
from tru_ai.exploration.repository import (
    ExplorationRepository,
)


router = APIRouter(
    prefix="/exploration",
    tags=["Advanced graph exploration"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
GRAPH_INFERRED_DIRECTORY = PROJECT_ROOT / "corpus" / "graph_inferred"
REASONING_DIRECTORY = PROJECT_ROOT / "corpus" / "reasoning"
EXPLORATION_DIRECTORY = PROJECT_ROOT / "corpus" / "exploration"


@lru_cache(maxsize=1)
def get_indexes():
    return ExplorationRepository(
        GRAPH_INFERRED_DIRECTORY,
        REASONING_DIRECTORY,
        EXPLORATION_DIRECTORY,
    ).load_indexes()


def get_engine() -> ExplorationEngine:
    return ExplorationEngine(get_indexes())


@router.get("/health")
def exploration_health() -> dict:
    try:
        indexes = get_indexes()
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(503, str(error)) from error
    return {
        "status": "ok",
        "loaded": True,
        "node_count": len(indexes.nodes_by_id),
        "edge_count": len(indexes.edges_by_id),
        "explanation_count": len(indexes.explanations_by_edge_id),
    }


@router.get("/nodes")
def list_nodes(
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    indexes = get_indexes()
    nodes = indexes.search_nodes(search, limit, offset)
    return {"count": len(nodes), "nodes": list(nodes)}


@router.get("/nodes/{node_id}")
def get_node(node_id: str) -> dict:
    indexes = get_indexes()
    if node_id not in indexes.nodes_by_id:
        raise HTTPException(404, f"Nœud absent : {node_id}")
    return indexes.node_to_dict(node_id)


@router.get("/neighborhood/{node_id}")
def neighborhood(
    node_id: str,
    depth: int = Query(default=2, ge=0, le=6),
    direction: str = Query(default="both", pattern="^(incoming|outgoing|both)$"),
    predicate: str | None = None,
    minimum_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    include_source: bool = True,
    include_inferred: bool = True,
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    try:
        result = get_engine().get_neighborhood(
            node_id=node_id,
            maximum_depth=depth,
            direction=direction,
            predicates=(predicate,) if predicate else (),
            minimum_confidence=minimum_confidence,
            limit=limit,
            include_source_edges=include_source,
            include_inferred_edges=include_inferred,
        )
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    return result.to_dict()


@router.get("/paths")
def paths(
    start_node_id: str,
    end_node_id: str,
    maximum_depth: int = Query(default=4, ge=0, le=8),
    predicate: str | None = None,
    minimum_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=500),
) -> dict:
    try:
        result = get_engine().find_paths(
            start_node_id,
            end_node_id,
            (predicate,) if predicate else (),
            maximum_depth,
            minimum_confidence,
            True,
            True,
            limit,
        )
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    return {"count": len(result), "paths": [path.to_dict() for path in result]}


@router.post("/query")
def query_graph(payload: dict) -> dict:
    query = GraphQuery(
        start_node_id=payload.get("start_node_id"),
        end_node_id=payload.get("end_node_id"),
        predicates=tuple(payload.get("predicates", [])),
        direction=payload.get("direction", "both"),
        maximum_depth=payload.get("maximum_depth", 2),
        include_source_edges=payload.get("include_source_edges", True),
        include_inferred_edges=payload.get("include_inferred_edges", True),
        minimum_confidence=payload.get("minimum_confidence", 0.0),
        limit=payload.get("limit", 50),
    )
    return get_engine().execute_query(query).to_dict()


@router.post("/pattern")
def pattern(payload: dict) -> dict:
    constraints = tuple(
        PatternConstraint(
            subject=item["subject"],
            predicate=item.get("predicate"),
            object=item["object"],
        )
        for item in payload.get("constraints", [])
    )
    graph_pattern = GraphPattern(
        variables=tuple(payload.get("variables", [])),
        constraints=constraints,
        maximum_results=payload.get("maximum_results", 100),
    )
    try:
        matches = ExplorationPatternMatcher(get_indexes()).match(graph_pattern)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {
        "count": len(matches),
        "matches": [match.to_dict() for match in matches],
    }


@router.post("/reload")
def reload_exploration() -> dict:
    get_indexes.cache_clear()
    indexes = get_indexes()
    return {
        "status": "reloaded",
        "loaded": True,
        "node_count": len(indexes.nodes_by_id),
        "edge_count": len(indexes.edges_by_id),
    }
