document.getElementById("autofill-btn").addEventListener("click", async () => {
    const btn = document.getElementById("autofill-btn");
    const originalText = btn.innerText;
    btn.innerText = "Injecting AI...";
    btn.disabled = true;

    try {
        let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        
        // Execute the content script
        await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ["content.js"]
        });
        
        document.getElementById("status-msg").innerText = "Execution initiated. Watch the page!";
        document.getElementById("status-msg").style.color = "#10b981";
    } catch(err) {
        document.getElementById("status-msg").innerText = "Error: " + err.message;
        document.getElementById("status-msg").style.color = "#ef4444";
    } finally {
        setTimeout(() => {
            btn.innerText = originalText;
            btn.disabled = false;
        }, 2000);
    }
});
