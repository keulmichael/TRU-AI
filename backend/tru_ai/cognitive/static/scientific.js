const form = document.querySelector("#scientific-form");
const statusBox = document.querySelector("#status");
const summary = document.querySelector("#summary");
const humanReadable = document.querySelector("#human-readable");
const results = document.querySelector("#results");
const stageCards = document.querySelector("#stage-cards");
const trace = document.querySelector("#trace");
const rawJson = document.querySelector("#raw-json");
const clearButton = document.querySelector("#clear-button");
const confirmatoryButton = document.querySelector("#confirmatory-button");
const contradictoryButton = document.querySelector("#contradictory-button");
const incompleteButton = document.querySelector("#incomplete-button");

const examples = {
  confirmatory: {
    question: "Analyze whether the observation confirms the supplied prediction.",
    theoryId: "stability-theory",
    theoryName: "Relation stability theory",
    claims: ["Repeated recognition stabilizes a relation."],
    prediction: "Relation stability increases.",
    expectedObservation: "Observed stability increases.",
    falsificationCondition: "Observed stability decreases.",
    observation: "Observed stability increases.",
    compatibilityScore: 0.9,
    falsificationHit: false
  },
  contradictory: {
    question: "Analyze whether the observation contradicts the supplied prediction.",
    theoryId: "stability-theory",
    theoryName: "Relation stability theory",
    claims: ["Repeated recognition stabilizes a relation."],
    prediction: "Relation stability increases.",
    expectedObservation: "Observed stability increases.",
    falsificationCondition: "Observed stability decreases.",
    observation: "Observed stability decreases.",
    compatibilityScore: 0.1,
    falsificationHit: true
  },
  incomplete: {
    question: "Analyze the theory with no matching scientific observation.",
    theoryId: "stability-theory",
    theoryName: "Relation stability theory",
    claims: ["Repeated recognition stabilizes a relation."],
    prediction: "Relation stability increases.",
    expectedObservation: "Observed stability increases.",
    falsificationCondition: "Observed stability decreases.",
    observation: "",
    compatibilityScore: 0.5,
    falsificationHit: false
  }
};

function valueOrDash(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "boolean") {
    return value ? "oui" : "non";
  }
  return String(value);
}

function escapeHtml(value) {
  return valueOrDash(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function lines(selector) {
  return document.querySelector(selector).value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function numericValue(selector) {
  const value = Number(document.querySelector(selector).value);
  return Number.isFinite(value) ? value : null;
}

function payloadFromForm() {
  const claims = lines("#claims");
  const predictionText = document.querySelector("#prediction").value.trim();
  const observationText = document.querySelector("#observation").value.trim();
  const compatibilityScore = numericValue("#compatibility-score");
  const request = {
    question: document.querySelector("#question").value.trim(),
    theory_version: "1.0.0",
    options: {
      include_human_readable: true,
      include_raw_result: document.querySelector("#include-raw").checked,
      persist: false
    }
  };

  if (claims.length > 0) {
    request.theory = {
      id: document.querySelector("#theory-id").value.trim() || "user-theory",
      name: document.querySelector("#theory-name").value.trim() || "User theory",
      claims: claims.map((claim, index) => ({
        claim_id: `c${index + 1}`,
        text: claim,
        status: "partial"
      }))
    };
  }

  if (predictionText) {
    request.prediction_rules = [{
      id: "rule-1",
      condition: claims[0] || "provided theory",
      consequence: predictionText,
      source_claim_ids: claims.length > 0 ? ["c1"] : [],
      expected_observation: document.querySelector("#expected-observation").value.trim() || null,
      falsification_condition: document.querySelector("#falsification-condition").value.trim() || null
    }];
  }

  if (observationText) {
    request.scientific_observations = [{
      observation_id: "o1",
      prediction_id: predictionText ? "rule-1" : null,
      text: observationText,
      compatibility_score: compatibilityScore,
      matches_falsification_condition: document.querySelector("#falsification-hit").checked
    }];
  }

  return request;
}

function loadExample(example) {
  document.querySelector("#question").value = example.question;
  document.querySelector("#theory-id").value = example.theoryId;
  document.querySelector("#theory-name").value = example.theoryName;
  document.querySelector("#claims").value = example.claims.join("\n");
  document.querySelector("#prediction").value = example.prediction;
  document.querySelector("#expected-observation").value = example.expectedObservation;
  document.querySelector("#falsification-condition").value = example.falsificationCondition;
  document.querySelector("#observation").value = example.observation;
  document.querySelector("#compatibility-score").value = example.compatibilityScore;
  document.querySelector("#falsification-hit").checked = example.falsificationHit;
  resetOutput();
}

function renderSummary(data) {
  const s = data.summary || {};
  const metrics = [
    ["Claims", s.claim_count],
    ["Prédictions", s.prediction_count],
    ["Observations", s.observation_count],
    ["Vérifications", s.verification_report_count],
    ["Falsifications", s.falsification_report_count],
    ["Gaps", s.scientific_gap_count],
    ["Évolution", s.has_theory_evolution],
    ["Révisions", s.revision_recommendation_count]
  ];
  summary.innerHTML = metrics.map(([label, value]) => `
    <article class="metric">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(valueOrDash(value))}</strong>
    </article>
  `).join("");
}

function listSection(title, items, formatter) {
  if (!items || items.length === 0) {
    return "";
  }
  return `
    <article class="stage-card">
      <header><h3>${escapeHtml(title)}</h3><span class="badge">${items.length}</span></header>
      <div class="human-text">
        ${items.map((item) => `<p>${escapeHtml(formatter(item))}</p>`).join("")}
      </div>
    </article>
  `;
}

function renderHumanReadable(data) {
  const readable = data.human_readable;
  if (!readable) {
    humanReadable.innerHTML = "";
    return;
  }
  const sections = [
    listSection("Observations", readable.observations, (item) => item),
    listSection("Prédictions", readable.predictions, (item) => item),
    listSection("Vérifications", readable.verification_reports, (item) => item),
    listSection("Falsifications", readable.falsification_reports, (item) => item),
    listSection("Recommandations", readable.revision_recommendations, (item) => item),
    listSection("Gaps", readable.scientific_gaps, (item) => item)
  ].join("");
  humanReadable.innerHTML = `
    <h2>Explication lisible</h2>
    <div class="human-text">
      <p>${escapeHtml(readable.overview)}</p>
    </div>
    <div class="cards">${sections}</div>
  `;
}

function renderResults(data) {
  const blocks = [
    listSection("Prédictions", data.scientific_predictions, (item) => item.text),
    listSection("Observations", data.scientific_observations, (item) => item.text),
    listSection("Rapports de vérification", data.verification_reports, (item) => `${item.status}: ${item.rationale || item.prediction_id}`),
    listSection("Rapports de falsification", data.falsification_reports, (item) => `falsified=${item.falsified}; revision_required=${item.revision_required}`),
    listSection("Recommandations de révision", data.scientific_theory_revisions, (item) => `${item.revision.action}; applied=${item.applied}`),
    listSection("Gaps scientifiques", data.scientific_gaps, (item) => item.description)
  ].join("");
  results.innerHTML = blocks || "<p>Aucun résultat scientifique détaillé.</p>";
}

function renderStageCards(data) {
  stageCards.innerHTML = (data.stage_cards || []).map((card) => `
    <article class="stage-card">
      <header>
        <h3>${escapeHtml(card.title || card.stage)}</h3>
        <span class="badge">${escapeHtml(card.status)}</span>
      </header>
      <p class="explanation">${escapeHtml(card.summary)}</p>
      <details>
        <summary>Données JSON</summary>
        <pre>${escapeHtml(JSON.stringify(card.data, null, 2))}</pre>
      </details>
    </article>
  `).join("");
}

function renderTrace(data) {
  trace.innerHTML = (data.operator_trace || []).map((item) => `
    <div class="trace-row">
      <strong>${escapeHtml(item.position)}</strong>
      <span>${escapeHtml(item.operator)} · ${escapeHtml(item.stage)}</span>
      <span>${escapeHtml(item.status)}</span>
    </div>
  `).join("");
}

function resetOutput() {
  summary.innerHTML = "";
  humanReadable.innerHTML = "";
  results.innerHTML = "";
  stageCards.innerHTML = "";
  trace.innerHTML = "";
  rawJson.textContent = "";
  statusBox.className = "status idle";
  statusBox.textContent = "Prêt.";
}

async function runAnalysis(event) {
  event.preventDefault();
  statusBox.className = "status";
  statusBox.textContent = "Analyse en cours...";
  form.querySelectorAll("button, input, textarea").forEach((field) => {
    field.disabled = true;
  });

  try {
    const response = await fetch(form.dataset.endpoint, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payloadFromForm())
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Erreur API");
    }
    renderSummary(data);
    renderHumanReadable(data);
    renderResults(data);
    renderStageCards(data);
    renderTrace(data);
    rawJson.textContent = JSON.stringify(data, null, 2);
    statusBox.textContent = "Analyse terminée.";
  } catch (error) {
    statusBox.className = "status error";
    statusBox.textContent = error.message;
  } finally {
    form.querySelectorAll("button, input, textarea").forEach((field) => {
      field.disabled = false;
    });
  }
}

form.addEventListener("submit", runAnalysis);
clearButton.addEventListener("click", resetOutput);
confirmatoryButton.addEventListener("click", () => loadExample(examples.confirmatory));
contradictoryButton.addEventListener("click", () => loadExample(examples.contradictory));
incompleteButton.addEventListener("click", () => loadExample(examples.incomplete));
