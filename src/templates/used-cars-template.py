########################################################
#
#      Script to scrape used cars listings data
#
########################################################

# Packages
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
from pathlib import Path
import datetime
import scrapy
import json
import csv

# Debug mode
DEBUG = True

# Used cars scraper class
class UsedCarsScraper(scrapy.Spider):
    # Scraper name
    name = "used-cars-scraper"
    
    # Entry point
    base_url = "https://example.com"

    # Custom headers
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
    }
    
    # Custom settings
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DOWNLOAD_DELAY": 1
    }
    
    # Redirect custom entry point
    async def start(self):
        for request in self.start_requests():
            yield request

    # Crawler's entry
    def start_requests(self):
        # Create output dir if needed
        BASE_DIR = Path(__file__).resolve().parent
        OUTPUT_DIR = BASE_DIR / "output"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Init filename
        filename = OUTPUT_DIR / f"used-cars-{datetime.datetime.today():%Y-%m-%d-%H-%M}.csv"
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV header
        with open(filename, "w") as f:
            columns = []
            f.write(",".join(columns) + "\n")

        # Current page
        current_page = 1
      
        # Crawl next postcode URL
        yield scrapy.Request(
            url=self.base_url,
            headers=self.headers,
            meta={
                "filename": filename,
                "current_page": current_page
            },
            callback=self.parse_links
        )
    
    # Parse links
    def parse_links(self, response):
        # Extract meta data
        if DEBUG:
            with open("links.html", encoding="utf-8") as f: response = Selector(text=f.read())
        else:
            filename = response.meta.get("filename")
            current_page = response.meta.get("current_page")

        # Extract property links
        links = response.css("a[data-cy='propertyUrl']::attr(href)").getall() # just a placeholder

        # Loop over property card URLs
        for card_url in links:
            print(card_url)
            # Crawl property listing
            #yield response.follow(
            #    url=card_url,
            #    headers=self.headers,
            #    meta={ "filename": filename },
            #    callback=self.parse_listing
            #)
            #break
 
        # Extract total pages
        try: total_pages = 10
        except: total_pages = 1
 
        # Handle pagination within each location URL
        if not DEBUG:
            # Increment current page counter
            current_page += 1
        
            # Check the if current page is within the legal page range
            if current_page <= total_pages:
                # Genrate next page URL
                split_url = response.url.split("?")
                next_page = split_url[0] + "?page=" + str(current_page)
                try:
                    params = split_url[1]
                    if "page" in params: params = "&".join(params.split("&")[1:])
                    if len(split_url[1]): next_page += "&" + params
                except: pass
                if next_page[-1] == "&": next_page = next_page[:-1]
              
                # Print debug information
                print(f"PAGE {current_page} | {total_pages} {next_page}")

                # Crawl next page
                #yield response.follow(
                #    url=next_page,
                #    headers=self.headers,
                #    meta={
                #        "filename": filename,
                #        "current_page": current_page
                #    },
                #    callback=self.parse_links
                #)

    # Parse property card listing
    def parse_listing(self, response):
        # Work with local copy
        if DEBUG:
            with open("listing.html", encoding="utf-8") as f: response = Selector(text=f.read())
            url = "N/A"
        
        # Work with actual response
        else:
            filename = response.meta.get("filename")
            url = response.url

        # CSV entry
        features = {
            "url": url
        }

        # Print extracted data
        if DEBUG:
            print(json.dumps(features, indent=2))
            print(features.keys())
        else:
            # Write features to output file
            with open(filename, "a", encoding="utf-8") as f:
                writer = csv.DictWriter(f, features.keys())
                writer.writerow(features)

# Main driver
if __name__ == "__main__":
    # Run scraper
    if not DEBUG:
        process = CrawlerProcess()
        process.crawl(UsedCarsScraper)
        process.start()
    
    # Debug function
    else:
        UsedCarsScraper.parse_links(UsedCarsScraper, "")