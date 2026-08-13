/*

    A Chrome extension to scrape data from
      https://www.oddsportal.com/

*/

// Request delay constant
const DELAY = 5000;

// UI message handler
chrome.runtime.onMessage.addListener((message) => {
    // Get scraper status
    if (message.action == "status") {
        // Load scraper storage if available
        let scraperStorage = JSON.parse(localStorage.getItem("scraper"));
        
        // Scraper storage doesn't exist
        if (scraperStorage == null) alert("Scraper storage doesn't exist");
        
        // Show current scraper status
        else alert("Scraper " + (scraperStorage.running ? "is" : "is not") + " running");
    }
    
    // Create scraper storage
    else if (message.action == "create") {
        // Load scraper storage if available
        let scraperStorage = JSON.parse(localStorage.getItem("scraper"));

        // Create scraper storage instance if needed
        if (scraperStorage == null) {
            localStorage.setItem("scraper", JSON.stringify({
                "running": false,
                "currentPage": "",
                "listingUrls": [],
                "listingUrlIndex": -1,
                "data": []
            }));
            alert("Scraper storage has been created");
        }
        
        // Scraper storage exists
        else alert("Scraper storage already exists");
    }
    
    // Clear scraper storage
    else if (message.action == "remove") {
        // Load scraper storage if available
        let scraperStorage = JSON.parse(localStorage.getItem("scraper"));

        // Scraper storage doesn't exist
        if (scraperStorage == null) alert("Scraper storage doesn't exist");
        
        // Remove scraper storage
        else {
            localStorage.removeItem("scraper");
            alert("Scraper storage has been removed");
        }
    }
    
    // Start scraper
    else if (message.action == "start") {
        // Load scraper storage if available
        let scraperStorage = JSON.parse(localStorage.getItem("scraper"));
        
        // Scraper storage doesn't exist
        if (scraperStorage == null) alert("Scraper storage doesn't exist");
        
        // Start scraper
        else {
            scraperStorage.running = true;
            localStorage.setItem("scraper", JSON.stringify(scraperStorage));
            alert("Scraper has been started");
            location.reload();
        }
    }
    
    // Stop scraper
    else if (message.action == "stop") {
        // Load scraper storage if available
        let scraperStorage = JSON.parse(localStorage.getItem("scraper"));
        
        // Scraper storage doesn't exist
        if (scraperStorage == null) alert("Scraper storage doesn't exist");
        
        // Start scraper
        else {
            scraperStorage.running = false;
            localStorage.setItem("scraper", JSON.stringify(scraperStorage));
            alert("Scraper has been stopped");
        }
    }
    
    // Download scraped data
    else if (message.action == "download") {
        // Load scraper storage if available
        let scraperStorage = JSON.parse(localStorage.getItem("scraper"));
        
        // Scraper storage doesn't exist
        if (scraperStorage == null) alert("Scraper storage doesn't exist");
        
        // Extract scraped data from local browser storage
        else {
            let data = JSON.parse(localStorage.getItem("scraper")).data;
            
            // Create data blob
            const blob = new Blob(
                [JSON.stringify(data, null, 2)],
                { type: "text/json;charset=utf-8" }
            );
            
            // Create URL
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const link = document.createElement("a");
            link.href = url;
            link.download = "data_" + Date().toString().split(" ").slice(0, 5) + ".json";
            
            // "Click" download URL
            link.click();
            
            // Clear download URL
            URL.revokeObjectURL(url);
        }
    }
});

// Extract useful data from target HTML page
function parseLinks(scraperStorage) {
    let linkSelectors = document.getElementsByClassName("min-w-0 flex-1 items-center border-black-borders md:border-r-0 max-md:border-r max-md:py-2 max-md:pl-2 max-md:pr-1 flex max-mt:items-center max-mt:gap-0 min-mt:grid min-mt:grid-cols-[72px_1fr] min-mt:items-center min-mt:gap-x-2");
    for (let link of linkSelectors) scraperStorage.listingUrls.push(link.href);
}

// Extract odds data
async function parseOdds(scraperStorage) {
    let allOdds = [];
    let rows = null;
    let ready = false;
    while (ready == false) {
        console.log("Waiting for odds data to be loaded...");
        await sleep(1000);
        rows = document.getElementsByClassName("h-9 ");
        for (let row of rows) {
            try {
                if (row.children[col].children[0].children[0].children[0].children[0].children[1]) ready = true;
            } catch(e) {}
        }
    }
    
    for (let row of rows) {
        if (row.tagName == "TR") {
            let oddsData = {
                "current": [
                    row.children[0].textContent.split("claim bonus")[0],
                    row.children[1].textContent,
                    row.children[2].textContent,
                    row.children[3].textContent,
                    row.children[4].textContent
                ],
    
                "movements": [[], [], []]
            }
            console.log("Extracted basic info...");
            try {
                for (let col = 1; col <= 3; col++) {
                    console.log("Extracting odd movements...");
                    // Click odd to get movements
                    try {
                        document.getElementsByClassName("ml-auto h-6 w-6 cursor-pointer bg-close-X-black bg-center bg-no-repeat text-transparent")[0].click();
                    } catch(e) {}
                        
                    row.children[col].children[0].children[0].children[0].children[0].children[1].click();
    
                    let ready = false;
                    let movementsSelector = null;
                    let attempts = 60;
                    while (ready == false) {
                        await sleep(1000);
                        movementsSelector = document.getElementsByClassName("flex flex-col gap-1 text-xs");
                        if (movementsSelector.length == 3) ready = true;
                        else {
                            attempts--;
                            if (attempts == 0) break;
                        }
                    }
                    
                    let movements = [];
                    let dates = [];
                    let odds = [];
                    let diffs = [];
                    
                    for (let date of movementsSelector[0].children) dates.push(date.textContent);
                    for (let odd of movementsSelector[1].children) odds.push(odd.textContent);
                    for (let diff of movementsSelector[2].children) diffs.push(diff.textContent);
                        
                    for (let i = 0; i < dates.length; i++) {
                        movements.push({
                            "date": dates[i],
                            "odd": odds[i],
                            "diff": diffs[i],
                        });
                    }
                    oddsData.movements[col-1] = movements;
                }
            } catch(e) { console.log("Failed extracting movements", e);
                try {
                    document.getElementsByClassName("ml-auto h-6 w-6 cursor-pointer bg-close-X-black bg-center bg-no-repeat text-transparent")[0].click();
                } catch(e) {}
            }
            console.log(JSON.stringify(oddsData, null, 2));
            allOdds.push(oddsData);
        }
    }
    
    scraperStorage.data.push({
        "date": Date().toString().split(" ").slice(0, 5).join(),
        "odds": allOdds
    })
}

// Wait before going to the next page
async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Crawl through URLs
(async () => {
    // Load scraper storage if available
    let scraperStorage = JSON.parse(localStorage.getItem("scraper"));
    
    // Do nothing if no scrape storage available
    if (scraperStorage == null) return;
    
    else if (scraperStorage.running) {
        // We just landed on a page
        if (scraperStorage.listingUrls.length == 0) {
            // Get the list of listing URLs
            parseLinks(scraperStorage);
            
            // Store current page to back to it later
            scraperStorage.currentPage = location.href;
            
            // Update scraper storage state in local browser storage
            localStorage.setItem("scraper", JSON.stringify(scraperStorage));
        }
        
        // We are crawling through listing URLs within the current page
        else parseOdds(scraperStorage);
        
        // Update URL index
        scraperStorage.listingUrlIndex++;
        
        // Update scraper storage state in local browser storage
        localStorage.setItem("scraper", JSON.stringify(scraperStorage));
        
        // If no more URLs to crawl
        if (scraperStorage.listingUrlIndex == scraperStorage.listingUrls.length) {
            // Reset listing URL list
            scraperStorage.listingUrls = [];
            scraperStorage.listingUrlIndex = -1;

            // Update scraper storage state in local browser storage
            localStorage.setItem("scraper", JSON.stringify(scraperStorage));
            
            // Wait for a while
            await sleep(DELAY);
            
            // Go to the next page
            location.href = scraperStorage.currentPage;
        }
        
        // Otherwise we crawl through listings on current page
        else {
            // Wait for a while
            await sleep(DELAY);
            
            // Navigate to listing URL
            location.href = scraperStorage.listingUrls[scraperStorage.listingUrlIndex]
        }
    }
})();