/*

    A Chrome extension to scrape data from
      https://www.immobilienscout24.de/

*/

// Request delay constant
const DELAY = 5000;

// UI message handler
chrome.runtime.onMessage.addListener((message) => {
    // Get scraper status
    if (message.action == "scraperStatus") {
        // Load scraper storage if available
        let scraperStorage = JSON.parse(localStorage.getItem("scraper"));
        
        // Scraper storage doesn't exist
        if (scraperStorage == null) alert("Scraper storage doesn't exist");
        
        // Show current scraper status
        else alert("Scraper " + (scraperStorage.running ? "is" : "is not") + " running");
    }
    
    // Create scraper storage
    else if (message.action == "createScraper") {
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
    else if (message.action == "removeScraper") {
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
    else if (message.action == "startScraper") {
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
    else if (message.action == "stopScraper") {
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
    else if (message.action == "downloadData") {
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
    let linkSelectors = document.getElementsByClassName("item-link");
    for (let link of linkSelectors) scraperStorage.listingUrls.push(link.href);
}

// Navigate to the next listing URL
function parseListing(scraperStorage) {
    try {
        // Extract features
        let features = [];
        let featureSelector = document.getElementsByClassName("details-property_features");

        // Loop over features
        for (let div of featureSelector) {
            for (let ul of div.children) {
                for (let li of ul.children) {
                    // Collect features
                    features.push(li.textContent.trim().replace("\n", ""));
                }
            }
        }

        // Extract listing data
        let data = {
            "url": location.href,
            "title": document.getElementsByClassName("main-info__title-main")[0].innerHTML,
            "price": document.getElementsByClassName("info-data-price")[0].children[0].innerHTML,
            "features": features,
            "description": document.getElementsByClassName("comment")[0].textContent.trim().replaceAll("\n", ""),
        }

        // Log extracted data to console
        console.log(JSON.stringify(data, null, 2))
        console.log("\nCurrent page:", scraperStorage.currentPage);

        // Save listing to the browser local storage
        scraperStorage.data.push(data)
    } catch(e) {}
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
        // We are done crawling all listings on this page
        if (scraperStorage.currentPage == location.href) {
            // Go to the next page
            scraperStorage.currentPage = "";
            location.href = document.getElementsByClassName("icon-arrow-right-after")[0].href
            return;
        }
        
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
        else parseListing(scraperStorage);
        
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