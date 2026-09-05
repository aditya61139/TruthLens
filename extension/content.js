chrome.runtime.onMessage.addListener((request) => {
  if (request.action === "TRUTHLENS_LOADING") {
    showTruthLensBadge("Verifying with TruthLens...", "loading", request.text);
  } else if (request.action === "TRUTHLENS_RESULT") {
    const res = request.result;
    showTruthLensResult(res);
  } else if (request.action === "TRUTHLENS_ERROR") {
    showTruthLensBadge(request.error, "error", "");
  }
});

function getOrCreateOverlay() {
  let overlay = document.getElementById("truthlens-injected-overlay");
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.id = "truthlens-injected-overlay";
    document.body.appendChild(overlay);
  }
  return overlay;
}

function showTruthLensBadge(message, status, claim) {
  const overlay = getOrCreateOverlay();
  overlay.innerHTML = `
    <div class="truthlens-card">
      <div class="truthlens-header">
        <span class="truthlens-title">🔍 TruthLens Quick Check</span>
        <button class="truthlens-close" id="truthlens-close-btn">&times;</button>
      </div>
      <div class="truthlens-body">
        <p class="truthlens-msg">${message}</p>
      </div>
    </div>
  `;
  document.getElementById("truthlens-close-btn").onclick = () => overlay.remove();
}

function showTruthLensResult(result) {
  const overlay = getOrCreateOverlay();
  const verdictColors = {
    False: "#f43f5e",
    True: "#10b981",
    Misleading: "#f59e0b",
    Satire: "#8b5cf6",
    Unverified: "#94a3b8"
  };
  const color = verdictColors[result.verdict] || "#94a3b8";

  overlay.innerHTML = `
    <div class="truthlens-card">
      <div class="truthlens-header">
        <span class="truthlens-title">🔍 TruthLens Fact Check</span>
        <button class="truthlens-close" id="truthlens-close-btn">&times;</button>
      </div>
      <div class="truthlens-body">
        <div class="truthlens-badge" style="background:${color}20; color:${color}; border:1px solid ${color};">
          ${result.verdict.toUpperCase()} (${Math.round(result.confidence)}% CONFIDENCE)
        </div>
        <p class="truthlens-claim">"${result.extracted_claim}"</p>
        <p class="truthlens-summary">${result.summary}</p>
        <div class="truthlens-footer">
          <a href="http://localhost:5173" target="_blank">Open Full Evidence Trail →</a>
        </div>
      </div>
    </div>
  `;
  document.getElementById("truthlens-close-btn").onclick = () => overlay.remove();
}
