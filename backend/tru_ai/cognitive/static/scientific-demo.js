const contradictoryExample = {
  observation: "La reconnaissance répétée ne stabilise pas cette relation.",
  claims: [
    "La reconnaissance répétée stabilise une relation.",
    "Une relation stabilisée rend les prédictions plus robustes."
  ],
  prediction_rule: {
    id: "rule-stability",
    statement: "La répétition de la reconnaissance augmente la stabilité.",
    condition: "la reconnaissance est répétée",
    consequence: "la stabilité mesurée augmente",
    confidence: 0.85,
    expected_observation: "Hausse mesurable de la stabilité.",
    falsification_condition: "La stabilité diminue malgré la répétition.",
    horizon: "trois cycles"
  },
  compatibility_score: 0.12,
  matches_falsification_condition: true
};

const confirmatoryExample = {
  ...contradictoryExample,
  observation: "La reconnaissance répétée stabilise cette relation.",
  compatibility_score: 0.9,
  matches_falsification_condition: false
};

let currentExample = contradictoryExample;

const form = document.querySelector("#demo-form");
const observation = document.querySelector("#observation");
const claims = document.querySelector("#claims");
const ruleId = document.querySelector("#rule-id");
const statement = document.querySelector("#statement");
const confidence = document.querySelector("#confidence");
const statusBox = document.querySelector("#status");
const summary = document.querySelector("#summary");
const conclusion = document.querySelector("#conclusion");
const reflexiveView = document.querySelector("#reflexive-view");
const cards = document.querySelector("#stage-cards");
const trace = document.querySelector("#trace");
const rawJson = document.querySelector("#raw-json");
const resetButton = document.querySelector("#reset-button");
const contradictoryButton = document.querySelector("#contradictory-button");
const confirmatoryButton = document.querySelector("#confirmatory-button");

function loadExample(example) {
  currentExample = example;
  observation.value = example.observation;
  claims.value = example.claims.join("\n");
  ruleId.value = example.prediction_rule.id;
  statement.value = example.prediction_rule.statement;
  confidence.value = example.prediction_rule.confidence;
}

function resetOutput() {
  summary.innerHTML = "";
  conclusion.innerHTML = "";
  reflexiveView.innerHTML = "";
  cards.innerHTML = "";
  trace.innerHTML = "";
  rawJson.textContent = "";
}

function payloadFromForm() {
  return {
    observation: observation.value,
    claims: claims.value.split("\n").map((item) => item.trim()).filter(Boolean),
    prediction_rule: {
      ...currentExample.prediction_rule,
      id: ruleId.value,
      statement: statement.value,
      confidence: Number(confidence.value)
    },
    compatibility_score: currentExample.compatibility_score,
    matches_falsification_condition: currentExample.matches_falsification_condition
  };
}

function escapeHtml(value) {
  return valueOrDash(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function valueOrDash(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "oui" : "non";
  }
  return String(value);
}

function formatScore(value) {
  if (typeof value !== "number") {
    return valueOrDash(value);
  }
  if (value >= 0 && value <= 1) {
    return `${(value * 100).toFixed(1).replace(".", ",")} %`;
  }
  return String(value);
}

function statusClass(value) {
  if (value === true || value === "falsified") return "is-falsified";
  if (value === "contradicted") return "is-contradicted";
  if (value === "revise") return "is-revise";
  if (value === "success" || value === "confirmed") return "is-success";
  return "";
}

function renderSummary(data) {
  const s = data.summary;
  const metrics = [
    ["Maturité", s.theory_maturity?.score, true],
    ["Confiance", s.prediction_confidence, true],
    ["Niveau", s.prediction_confidence_level, false],
    ["Vérification", s.verification_status, false],
    ["Cohérence", s.verification_consistency_score, true],
    ["Preuve", s.verification_evidence_score, true],
    ["Falsifié", s.falsified, false],
    ["Révision", s.revision_required, false],
    ["Action finale", s.final_action, false]
  ];
  summary.innerHTML = metrics.map(([label, value, score]) => `
    <article class="metric ${statusClass(value)}">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(score ? formatScore(value) : valueOrDash(value))}</strong>
    </article>
  `).join("");
}

function renderConclusion(data) {
  const human = data.human_readable;
  conclusion.innerHTML = `
    <h2>Conclusion du moteur</h2>
    <div class="human-text">${human.conclusion.split("\n\n").map((line) => `<p>${escapeHtml(line)}</p>`).join("")}</div>
  `;
}

function renderReflexiveView(data) {
  const view = data.human_readable.reflexive_view;
  const rows = [
    ["Qu’est-ce qui est observé ?", view.observed],
    ["Qu’est-ce qui est reconnu ?", view.recognized],
    ["Qu’est-ce qui est prédit ?", view.predicted],
    ["Qu’est-ce qui confirme ou infirme la prédiction ?", view.confirmed_or_refuted_by],
    ["Que doit apprendre ou réviser le système ?", view.learning]
  ];
  reflexiveView.innerHTML = `
    <h2>Lecture réflexive</h2>
    <div class="reflexive-grid">
      ${rows.map(([question, answer]) => `
        <article>
          <span>${escapeHtml(question)}</span>
          <strong>${escapeHtml(answer)}</strong>
        </article>
      `).join("")}
    </div>
  `;
}

function renderCards(data) {
  cards.innerHTML = data.stage_cards.map((card) => `
    <article class="stage-card ${statusClass(card.decision)} ${statusClass(card.status)}">
      <header>
        <h3>${escapeHtml(card.stage)}</h3>
        <span class="badge">${escapeHtml(card.status || "unknown")}</span>
      </header>
      <p class="explanation">${escapeHtml(card.explanation)}</p>
      <div class="stage-grid">
        <div class="cell"><span>Opérateur</span>${escapeHtml(card.operator)}</div>
        <div class="cell"><span>Ce que le moteur reçoit</span>${escapeHtml(card.inputs.join(", ") || "—")}</div>
        <div class="cell"><span>Ce qu’il produit</span>${escapeHtml(card.outputs.join(", ") || "—")}</div>
        <div class="cell"><span>Score principal</span>${escapeHtml(formatScore(card.score))}</div>
      </div>
      <div class="cell decision"><span>Décision prise</span>${escapeHtml(card.decision)}</div>
      <details>
        <summary>Données JSON</summary>
        <pre>${escapeHtml(JSON.stringify(card.data, null, 2))}</pre>
      </details>
    </article>
  `).join("");
}

function renderTrace(data) {
  trace.innerHTML = data.operator_trace.map((item) => `
    <div class="trace-row ${statusClass(item.status)}">
      <strong>${escapeHtml(item.position)}</strong>
      <span>${escapeHtml(item.operator)} · ${escapeHtml(item.stage)}</span>
      <span>${escapeHtml(item.status)}</span>
    </div>
  `).join("");
}

async function runDemo(event) {
  event.preventDefault();
  statusBox.className = "status";
  statusBox.textContent = "Exécution du pipeline...";
  form.querySelectorAll("button").forEach((button) => {
    button.disabled = true;
  });

  try {
    const response = await fetch("/reasoning/scientific-demo", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payloadFromForm())
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Erreur API");
    }
    renderSummary(data);
    renderConclusion(data);
    renderReflexiveView(data);
    renderCards(data);
    renderTrace(data);
    rawJson.textContent = JSON.stringify(data, null, 2);
    statusBox.textContent = "Pipeline exécuté.";
  } catch (error) {
    statusBox.className = "status error";
    statusBox.textContent = error.message;
  } finally {
    form.querySelectorAll("button").forEach((button) => {
      button.disabled = false;
    });
  }
}

resetButton.addEventListener("click", () => {
  loadExample(contradictoryExample);
  resetOutput();
  statusBox.className = "status idle";
  statusBox.textContent = "Prêt.";
});

contradictoryButton.addEventListener("click", () => {
  loadExample(contradictoryExample);
  resetOutput();
  statusBox.className = "status idle";
  statusBox.textContent = "Cas contradictoire chargé.";
});

confirmatoryButton.addEventListener("click", () => {
  loadExample(confirmatoryExample);
  resetOutput();
  statusBox.className = "status idle";
  statusBox.textContent = "Cas confirmatif chargé.";
});

form.addEventListener("submit", runDemo);
loadExample(contradictoryExample);
