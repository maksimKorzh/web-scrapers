// Loop over user actions
for (let action of ["status", "create", "remove", "start", "stop", "download"]) {
    // Hook UI button
    document.getElementById(action).onclick = async () => {
        // Get current tab context
        const [tab] = await chrome.tabs.query({
            active: true,
            currentWindow: true
        });

        // Send message to current tab
        chrome.tabs.sendMessage(tab.id, {
            action: action
        });
    };
}