const API_ENDPOINT = 'http://localhost:8000/api/verify';

document.getElementById('verifyBtn').addEventListener('click', async () => {
  const input = document.getElementById('claimInput').value.trim();
  if (!input) return;

  const btn = document.getElementById('verifyBtn');
  const resultCard = document.getElementById('resultCard');
  const verdictBadge = document.getElementById('verdictBadge');
  const claimQuote = document.getElementById('claimQuote');
  const summaryText = document.getElementById('summaryText');

  btn.textContent = 'Verifying...';
  btn.disabled = true;

  try {
    const res = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: input })
    });

    if (!res.ok) throw new Error('API Error');

    const data = await res.json();
    resultCard.style.display = 'block';

    verdictBadge.textContent = `${data.verdict} (${Math.round(data.confidence)}% Confidence)`;
    verdictBadge.className = `verdict-badge v-${data.verdict}`;
    claimQuote.textContent = `"${data.extracted_claim}"`;
    summaryText.textContent = data.summary;
  } catch (err) {
    resultCard.style.display = 'block';
    verdictBadge.textContent = 'Error';
    verdictBadge.className = 'verdict-badge v-Unverified';
    summaryText.textContent = 'Could not connect to TruthLens backend at http://localhost:8000. Please ensure the backend is running.';
  } finally {
    btn.textContent = 'Verify Claim';
    btn.disabled = false;
  }
});
