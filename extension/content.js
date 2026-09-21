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
  overlay.textContent = "";

  const card = document.createElement("div");
  card.className = "truthlens-card";

  const header = document.createElement("div");
  header.className = "truthlens-header";

  const title = document.createElement("span");
  title.className = "truthlens-title";
  title.textContent = "🔍 TruthLens Quick Check";

  const closeBtn = document.createElement("button");
  closeBtn.className = "truthlens-close";
  closeBtn.textContent = "×";
  closeBtn.onclick = () => overlay.remove();

  header.appendChild(title);
  header.appendChild(closeBtn);

  const body = document.createElement("div");
  body.className = "truthlens-body";

  const msg = document.createElement("p");
  msg.className = "truthlens-msg";
  msg.textContent = message;

  body.appendChild(msg);
  card.appendChild(header);
  card.appendChild(body);
  overlay.appendChild(card);
}

function showTruthLensResult(result) {
  const overlay = getOrCreateOverlay();
  overlay.textContent = "";

  const verdictColors = {
    False: "#ef4444",
    True: "#10b981",
    Misleading: "#f59e0b",
    Satire: "#8b5cf6",
    Unverified: "#94a3b8"
  };
  const color = verdictColors[result.verdict] || "#94a3b8";

  const card = document.createElement("div");
  card.className = "truthlens-card";

  const header = document.createElement("div");
  header.className = "truthlens-header";

  const title = document.createElement("span");
  title.className = "truthlens-title";
  title.textContent = "🔍 TruthLens Fact Check";

  const closeBtn = document.createElement("button");
  closeBtn.className = "truthlens-close";
  closeBtn.textContent = "×";
  closeBtn.onclick = () => overlay.remove();

  header.appendChild(title);
  header.appendChild(closeBtn);

  const body = document.createElement("div");
  body.className = "truthlens-body";

  const badge = document.createElement("div");
  badge.className = "truthlens-badge";
  badge.style.backgroundColor = `${color}20`;
  badge.style.color = color;
  badge.style.border = `1px solid ${color}`;
  badge.textContent = `${(result.verdict || "UNVERIFIED").toUpperCase()} (${Math.round(result.confidence || 0)}% CONFIDENCE)`;
  body.appendChild(badge);

  const claimPara = document.createElement("p");
  claimPara.className = "truthlens-claim";
  claimPara.textContent = `"${result.extracted_claim || ""}"`;
  body.appendChild(claimPara);

  if (result.plain_english_takeaway) {
    const takeaway = document.createElement("p");
    takeaway.style.fontSize = "11px";
    takeaway.style.fontWeight = "600";
    takeaway.style.color = "#10b981";
    takeaway.style.marginBottom = "8px";
    takeaway.style.lineHeight = "1.4";
    takeaway.textContent = `💡 Takeaway: ${result.plain_english_takeaway}`;
    body.appendChild(takeaway);
  }

  const summaryPara = document.createElement("p");
  summaryPara.className = "truthlens-summary";
  summaryPara.textContent = result.summary || "";
  body.appendChild(summaryPara);

  const footer = document.createElement("div");
  footer.className = "truthlens-footer";
  const link = document.createElement("a");
  link.href = "http://localhost:5173";
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "Open Full Evidence Trail →";
  footer.appendChild(link);
  body.appendChild(footer);

  card.appendChild(header);
  card.appendChild(body);
  overlay.appendChild(card);
}
