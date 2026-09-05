chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "truthlens-verify-selection",
    title: "Verify with TruthLens",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "truthlens-verify-selection" && info.selectionText) {
    const selectedText = info.selectionText.trim();
    if (!selectedText || !tab.id) return;

    try {
      // Send message to content script to display loading badge
      chrome.tabs.sendMessage(tab.id, {
        action: "TRUTHLENS_LOADING",
        text: selectedText
      });

      const response = await fetch("http://localhost:8000/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: selectedText })
      });

      if (response.ok) {
        const data = await response.json();
        chrome.tabs.sendMessage(tab.id, {
          action: "TRUTHLENS_RESULT",
          result: data
        });
      } else {
        chrome.tabs.sendMessage(tab.id, {
          action: "TRUTHLENS_ERROR",
          error: "Verification failed."
        });
      }
    } catch (e) {
      chrome.tabs.sendMessage(tab.id, {
        action: "TRUTHLENS_ERROR",
        error: "Cannot connect to TruthLens backend at http://localhost:8000."
      });
    }
  }
});
