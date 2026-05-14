chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "neovault-scan",
        title: "Scan link with NeoVault",
        contexts: ["link"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "neovault-scan") {
        const linkUrl = info.linkUrl;
        
        // Notify content script
        chrome.tabs.sendMessage(tab.id, { action: "scan_start", url: linkUrl });

        fetch("http://127.0.0.1:5000/api/vault/scan-url", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url: linkUrl })
        })
        .then(response => response.json())
        .then(data => {
            // Send back to content script
            chrome.tabs.sendMessage(tab.id, { action: "scan_result", data: data, url: linkUrl });
        })
        .catch(error => {
            console.error("Scanner Error:", error);
            chrome.tabs.sendMessage(tab.id, { action: "scan_error", url: linkUrl, error: "Connection to local NeoVault failed." });
        });
    }
});
