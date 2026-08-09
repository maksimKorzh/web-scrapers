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
DEBUG = False

# Used cars scraper scraper class
class UsedCarsScraper(scrapy.Spider):
    # Scraper name
    name = "used-cars-scraper"
    
    # Entry point
    base_url = "https://carvago.com/cars"

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
            columns = ['url', 'title', 'general', 'details', 'features']
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
        links = response.css("a[class='gtm-element-visibility-impressions-list css-1jlwndo']::attr(href)").getall()

        # Loop over property card URLs
        for card_url in links:
            # Crawl property listing
            yield response.follow(
                url=card_url,
                headers=self.headers,
                meta={ "filename": filename },
                callback=self.parse_listing
            )
 
        # Extract total pages
        try: total_pages = max([int(i) for i in response.css("a[class='Pagination-link']::text").getall() if i[0].isdigit()])
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
                print("PAGE %s | %s" % (current_page, total_pages), next_page)

                # Crawl next page
                yield response.follow(
                    url=next_page,
                    headers=self.headers,
                    meta={
                        "filename": filename,
                        "current_page": current_page
                    },
                    callback=self.parse_links
                )

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

        # Extract general info
        try:
            general = {}
            for item in response.css("div[class='css-hh37mb']"):
                feature = [i.strip() for i in item.css(" *::text").getall()]
                if "css" not in "".join(feature):
                    general[feature[0]] = "".join(feature[1:])
        except:
            general = "N/A"
        
        # Extract details
        try:
            details = {}
            for item in response.css("div[class='css-1sxi7eb']"):
                feature = [i.strip() for i in item.css(" *::text").getall()]
                if "css" not in "".join(feature):
                    details[feature[0]] = "".join(feature[1:])
        except:
            details = "N/A"
        
        # Extract new electric motor specs
        try: features = [i for i in response.css("ul[class='css-13odobh'] *::text").getall() if "css" not in i]
        except: features = "N/A"
        
        # CSV entry
        features = {
            "url": url,
            "title": response.css("h1[role='heading']::text").get(),
            "general": general,
            "details": details,
            "features": features,
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
        UsedCarsScraper.parse_listing(UsedCarsScraper, "")