const form = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const statusBox = document.querySelector("#status");
const answerBox = document.querySelector("#answer");
const proofsBox = document.querySelector("#proofs");
const processBox = document.querySelector("#process");

async function loadHealth() {
  try {
    const response = await fetch("/cognitive/health");
    const data = await response.json();
    statusBox.textContent = `Mémoire chargée : ${data.memory_element_count} éléments, ${data.source_count} source(s), ${data.production_source_count} source(s) de production.`;
  } catch (error) {
    statusBox.textContent = "Mémoire cognitive indisponible.";
  }
}

function renderClaims(title, claims) {
  if (!claims || claims.length === 0) {
    return "";
  }
  return `<h3>${title}</h3>${claims.map((claim) => `
    <div class="claim">
      <strong>${claim.classification}</strong>
      <span>${claim.text}</span>
      <small>Confiance : ${claim.confidence}</small>
    </div>
  `).join("")}`;
}

function renderAnswer(data) {
  const answer = data.answer;
  answerBox.classList.remove("empty");
  answerBox.innerHTML = `
    <h2>Réponse</h2>
    <p>${answer.summary}</p>
    <p><strong>Niveau de confiance :</strong> ${data.confidence}</p>
    ${renderClaims("Explicite", data.classifications.EXPLICITE)}
    ${renderClaims("Déductions", data.classifications["DÉDUCTION"])}
    ${renderClaims("Hypothèses", data.classifications["HYPOTHÈSE"])}
    ${renderClaims("Inconnu", data.classifications.INCONNU)}
    <h3>Opérateurs appliqués</h3>
    <ul>${((data.cognitive_execution || {}).applied_operators || []).map((item) => `<li>${item.operator_id} : ${item.applied ? "appliqué" : "refusé"}${item.refusal_reason ? " — " + item.refusal_reason : ""}</li>`).join("") || "<li>Aucun opérateur appliqué.</li>"}</ul>
    <h3>Contradictions</h3>
    <ul>${((data.cognitive_execution || {}).contradictions || []).map((item) => `<li>${item}</li>`).join("") || "<li>Aucune contradiction détectée.</li>"}</ul>
    <h3>Connaissances manquantes</h3>
    <ul>${data.missing_knowledge.map((item) => `<li>${item}</li>`).join("") || "<li>Aucune lacune critique signalée.</li>"}</ul>
    <h3>Avertissements</h3>
    <ul>${data.warnings.map((item) => `<li>${item}</li>`).join("") || "<li>Aucun avertissement.</li>"}</ul>
  `;
  proofsBox.textContent = JSON.stringify({
    request_id: data.request_id,
    sources: data.sources,
    evidence: data.evidence || [],
  }, null, 2);
  processBox.textContent = JSON.stringify(data.cognitive_execution || {}, null, 2);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value) {
    return;
  }
  answerBox.textContent = "TRU-AI construit une réponse raisonnée...";
  try {
    const response = await fetch("/cognitive/ask", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: value, include_evidence: true}),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Erreur cognitive");
    }
    renderAnswer(data);
  } catch (error) {
    answerBox.textContent = `Erreur : ${error.message}`;
  }
});

loadHealth();
