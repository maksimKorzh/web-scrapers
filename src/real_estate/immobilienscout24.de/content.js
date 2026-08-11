/*

    A Chrome extension to scrape data from
      https://www.immobilienscout24.de/

*/

// Request delay constant
const DELAY = 5000;

// Extract useful data from target HTML page
function parseLinks(scraperStorage) {
    let linkSelectors = document.getElementsByClassName("cursor-pointer");
    for (let link of linkSelectors) scraperStorage.listingUrls.push(link.href);
}

// Navigate to the next listing URL
function parseListing(scraperStorage) {
    try {
        // Extracted features
        let features = {};

        // Loop over features and extract them one by one
        for (let feature of document.getElementsByClassName("grid")) {
            if (feature.tagName == 'DL' && feature.children[0].innerHTML.trim() && feature.children[1].innerHTML.trim().length < 50)
                features[feature.children[0].innerHTML.trim()] = feature.children[1].innerHTML.trim()
        }

        // Listing description
        let description = "";

        // Extract listing description
        for (let i of document.getElementsByClassName("expose-description-body"))
            description += i.innerHTML;

        // Extract listing data
        let data = {
            "url": location.href,
            "title": document.getElementsByClassName("truncated no_js_expanded")[0].innerHTML,
            "price": document.getElementsByClassName("is24-preis-value")[0].innerHTML,
            "price_per_meter": document.getElementsByClassName("is24qa-maincriteria-baserent-label-main-label is24-label font-s")[0].children[0].innerHTML.split(" \x3C!-- -->")[1],
            "features": features,
            "description": description,
            "address": document.getElementsByClassName("padding-vertical-l palm-padding-vertical-xl")[1].children[1].innerHTML,
            "location": document.getElementsByClassName("padding-vertical-l palm-padding-vertical-xl")[1].children[2].innerHTML
        };

        // Log extracted data to console
        console.log(JSON.stringify(data, null, 2))

        // Save listing to the browser local storage
        scraperStorage.data.push(data)
    } catch(e) {}
}

// Download scraped data
function download(filename="data.json") {
    // Extract scraped data from local browser storage
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
    link.download = filename;
    
    // "Click" download URL
    link.click();
    
    // Clear download URL
    URL.revokeObjectURL(url);
}

// Wait before going to the next page
async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Crawl through URLs
(async () => {
    // Load scraper storage if available
    let scraperStorage = JSON.parse(localStorage.getItem("scraper"));

    // Create scraper storage instance if needed
    if (scraperStorage == null) {
        localStorage.setItem("scraper", JSON.stringify({
            "currentPage": "",
            "listingUrls": [],
            "listingUrlIndex": -1,
            "data": []
        }));
        alert("Reload tab to start scraping or go to 'chrome://extensions' to turn off scraper");
    }
    
    // Scraper storage instance already exists
    else {
        // We are done crawling all listings on this page
        if (scraperStorage.currentPage == location.href) {
            // Go to the next page
            scraperStorage.currentPage = "";
            document.getElementsByClassName("Pagination_pagination-button-next__-x23D")[0].click();
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
            download("data-" + Date().toString().split(" ").slice(0, 5) + ".json");
            
            // Reset listing URL list
            scraperStorage.listingUrls = [];
            scraperStorage.listingUrlIndex = -1;
            scraperStorage.data = [];
            
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