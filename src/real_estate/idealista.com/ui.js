// Scraper Status
document.getElementById("status").onclick = async () => {
    // Get current tab context
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    // Send message to current tab
    chrome.tabs.sendMessage(tab.id, {
        action: "scraperStatus"
    });
};

// Create Scraper Storage
document.getElementById("create").onclick = async () => {
    // Get current tab context
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    // Send message to current tab
    chrome.tabs.sendMessage(tab.id, {
        action: "createScraper"
    });
};

// Remove Scraper Storage
document.getElementById("remove").onclick = async () => {
    // Get current tab context
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    // Send message to current tab
    chrome.tabs.sendMessage(tab.id, {
        action: "removeScraper"
    });
};

// Start Scraper
document.getElementById("start").onclick = async () => {
    // Get current tab context
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    // Send message to current tab
    chrome.tabs.sendMessage(tab.id, {
        action: "startScraper"
    });
};

// Stop Scraper
document.getElementById("stop").onclick = async () => {
    // Get current tab context
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    // Send message to current tab
    chrome.tabs.sendMessage(tab.id, {
        action: "stopScraper"
    });
};

// Download scraped data
document.getElementById("download").onclick = async () => {
    // Get current tab context
    const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true
    });

    // Send message to current tab
    chrome.tabs.sendMessage(tab.id, {
        action: "downloadData"
    });
}