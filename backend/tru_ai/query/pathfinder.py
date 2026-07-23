from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from tru_ai.query.graph_index import GraphIndex
from tru_ai.query.models import (
    GraphPath,
    PathStep,
)


@dataclass(frozen=True)
class TraversalStep:
    previous_node_id: str
    edge_id: str
    forward: bool


class GraphPathfinder:
    """
    Recherche le plus court chemin par parcours
    en largeur, ou Breadth First Search.
    """

    def __init__(
        self,
        index: GraphIndex,
    ) -> None:
        self.index = index

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        directed: bool = False,
        max_depth: int = 10,
    ) -> GraphPath | None:
        source_node = self.index.get_node(
            source_id
        )

        target_node = self.index.get_node(
            target_id
        )

        if source_node is None:
            raise KeyError(
                f"Nœud source introuvable : "
                f"{source_id}"
            )

        if target_node is None:
            raise KeyError(
                f"Nœud cible introuvable : "
                f"{target_id}"
            )

        if max_depth < 0:
            raise ValueError(
                "max_depth doit être positif "
                "ou nul."
            )

        if source_id == target_id:
            return GraphPath(
                source_id=source_node.node_id,
                source_label=source_node.label,
                target_id=target_node.node_id,
                target_label=target_node.label,
                directed=directed,
                length=0,
                node_ids=(source_id,),
                node_labels=(
                    source_node.label,
                ),
                steps=(),
            )

        queue = deque(
            [(source_id, 0)]
        )

        visited = {source_id}

        previous: dict[
            str,
            TraversalStep,
        ] = {}

        found = False

        while queue:
            current_node_id, depth = (
                queue.popleft()
            )

            if depth >= max_depth:
                continue

            for (
                neighbor_id,
                edge_id,
                forward,
            ) in self.iter_neighbors(
                current_node_id,
                directed=directed,
            ):
                if neighbor_id in visited:
                    continue

                visited.add(neighbor_id)

                previous[neighbor_id] = (
                    TraversalStep(
                        previous_node_id=(
                            current_node_id
                        ),
                        edge_id=edge_id,
                        forward=forward,
                    )
                )

                if neighbor_id == target_id:
                    found = True
                    break

                queue.append(
                    (
                        neighbor_id,
                        depth + 1,
                    )
                )

            if found:
                break

        if not found:
            return None

        return self.reconstruct_path(
            source_id=source_id,
            target_id=target_id,
            directed=directed,
            previous=previous,
        )

    def iter_neighbors(
        self,
        node_id: str,
        directed: bool,
    ) -> list[tuple[str, str, bool]]:
        neighbors = []

        for edge in (
            self.index.get_outgoing_edges(
                node_id
            )
        ):
            neighbors.append(
                (
                    edge.object_id,
                    edge.edge_id,
                    True,
                )
            )

        if not directed:
            for edge in (
                self.index.get_incoming_edges(
                    node_id
                )
            ):
                neighbors.append(
                    (
                        edge.subject_id,
                        edge.edge_id,
                        False,
                    )
                )

        neighbors.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            )
        )

        return neighbors

    def reconstruct_path(
        self,
        source_id: str,
        target_id: str,
        directed: bool,
        previous: dict[
            str,
            TraversalStep,
        ],
    ) -> GraphPath:
        traversal = []

        current_id = target_id

        while current_id != source_id:
            step = previous[current_id]

            traversal.append(
                (
                    step.previous_node_id,
                    current_id,
                    step.edge_id,
                    step.forward,
                )
            )

            current_id = (
                step.previous_node_id
            )

        traversal.reverse()

        node_ids = [source_id]
        path_steps = []

        for (
            from_node_id,
            to_node_id,
            edge_id,
            forward,
        ) in traversal:
            edge = self.index.get_edge(
                edge_id
            )

            if edge is None:
                raise RuntimeError(
                    f"Arête absente : {edge_id}"
                )

            if forward:
                subject_id = edge.subject_id
                object_id = edge.object_id
            else:
                subject_id = from_node_id
                object_id = to_node_id

            subject_node = (
                self.index.get_node(subject_id)
            )

            object_node = (
                self.index.get_node(object_id)
            )

            if (
                subject_node is None
                or object_node is None
            ):
                raise RuntimeError(
                    "Le chemin contient un "
                    "nœud absent."
                )

            path_steps.append(
                PathStep(
                    edge_id=edge.edge_id,
                    subject_id=subject_id,
                    subject_label=(
                        subject_node.label
                    ),
                    predicate=edge.predicate,
                    object_id=object_id,
                    object_label=(
                        object_node.label
                    ),
                )
            )

            node_ids.append(to_node_id)

        source_node = self.index.get_node(
            source_id
        )

        target_node = self.index.get_node(
            target_id
        )

        if (
            source_node is None
            or target_node is None
        ):
            raise RuntimeError(
                "La source ou la cible "
                "du chemin est absente."
            )

        node_labels = tuple(
            self.index.nodes_by_id[
                node_id
            ].label
            for node_id in node_ids
        )

        return GraphPath(
            source_id=source_id,
            source_label=source_node.label,
            target_id=target_id,
            target_label=target_node.label,
            directed=directed,
            length=len(path_steps),
            node_ids=tuple(node_ids),
            node_labels=node_labels,
            steps=tuple(path_steps),
        )