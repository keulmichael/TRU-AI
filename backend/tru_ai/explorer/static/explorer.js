const state = { nodes: [], edges: [], center: null, explanations: [] };
const svg = document.getElementById("graph");
const details = document.getElementById("details");
const stats = document.getElementById("stats");

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function edgeKey(edge) {
  return `${edge.subject_id} ${edge.predicate} ${edge.object_id}`;
}

function render() {
  svg.innerHTML = "";
  if (!state.nodes.length) {
    stats.textContent = "Graph is empty or no node is selected.";
    return;
  }
  const width = svg.clientWidth || 800;
  const height = svg.clientHeight || 520;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.max(120, Math.min(width, height) / 3);
  const positions = new Map();
  state.nodes.forEach((node, index) => {
    const angle = (2 * Math.PI * index) / state.nodes.length;
    positions.set(node.node_id, {
      x: cx + Math.cos(angle) * radius,
      y: cy + Math.sin(angle) * radius
    });
  });
  if (state.center && positions.has(state.center)) positions.set(state.center, { x: cx, y: cy });

  state.edges.forEach(edge => {
    const a = positions.get(edge.subject_id);
    const b = positions.get(edge.object_id);
    if (!a || !b) return;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", a.x);
    line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x);
    line.setAttribute("y2", b.y);
    line.setAttribute("class", edge.inferred ? "inferred-edge" : "source-edge");
    line.addEventListener("click", () => showEdge(edge));
    svg.appendChild(line);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", (a.x + b.x) / 2);
    label.setAttribute("y", (a.y + b.y) / 2 - 6);
    label.setAttribute("class", "edge-label");
    label.textContent = edge.predicate;
    svg.appendChild(label);
  });

  state.nodes.forEach(node => {
    const p = positions.get(node.node_id);
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", p.x);
    circle.setAttribute("cy", p.y);
    circle.setAttribute("r", 22);
    circle.setAttribute("class", "node");
    circle.addEventListener("click", () => loadNeighborhood(node.node_id));
    svg.appendChild(circle);
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", p.x);
    label.setAttribute("y", p.y + 38);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("class", "label");
    label.textContent = node.label || node.node_id;
    svg.appendChild(label);
  });
  const inferredCount = state.edges.filter(edge => edge.inferred).length;
  stats.textContent = `Nodes: ${state.nodes.length} | Edges: ${state.edges.length} | Depth: ${document.getElementById("depth").value} | Inferred edges: ${inferredCount} | Explanations: ${state.explanations.length}`;
}

function showEdge(edge) {
  const explanation = state.explanations.find(item => item.inferred_edge_id === edge.edge_id);
  details.textContent = `${edgeKey(edge)}\nConfidence: ${edge.confidence_average}\nStatus: ${edge.inferred ? "inferred" : "source"}\n${explanation ? explanation.deterministic_text : "No explanation available."}`;
}

async function loadNeighborhood(nodeId) {
  state.center = nodeId;
  const depth = document.getElementById("depth").value;
  const direction = document.getElementById("direction").value;
  const predicate = document.getElementById("predicate").value.trim();
  const suffix = predicate ? `&predicate=${encodeURIComponent(predicate)}` : "";
  const result = await api(`/exploration/neighborhood/${encodeURIComponent(nodeId)}?depth=${depth}&direction=${direction}${suffix}`);
  const query = await api("/exploration/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start_node_id: nodeId, maximum_depth: Number(depth), direction })
  });
  state.nodes = query.nodes;
  state.edges = query.edges;
  state.explanations = query.explanations;
  if (!state.nodes.length && result.node_ids.length) {
    state.nodes = result.node_ids.map(id => ({ node_id: id, label: id }));
  }
  render();
}

async function loadFirstNode() {
  const search = document.getElementById("search").value.trim();
  const result = await api(`/exploration/nodes?limit=20&search=${encodeURIComponent(search)}`);
  if (!result.nodes.length) {
    state.nodes = [];
    state.edges = [];
    state.explanations = [];
    render();
    return;
  }
  await loadNeighborhood(result.nodes[0].node_id);
}

async function findPath() {
  const start = document.getElementById("pathStart").value.trim();
  const end = document.getElementById("pathEnd").value.trim();
  const pathResult = document.getElementById("pathResult");
  if (!start || !end) {
    pathResult.textContent = "Enter start and end node IDs.";
    return;
  }
  const result = await api(`/exploration/paths?start_node_id=${encodeURIComponent(start)}&end_node_id=${encodeURIComponent(end)}&maximum_depth=4`);
  pathResult.textContent = result.count ? `Paths: ${result.count}` : "No path found.";
}

document.getElementById("load").addEventListener("click", loadFirstNode);
document.getElementById("findPath").addEventListener("click", findPath);
loadFirstNode().catch(error => { details.textContent = error.message; render(); });
