########################################################
#
# Script to scrape real estate property listings data
#
########################################################

# packages
import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
import json, csv
import datetime
import urllib
import sys

# debug mode
DEBUG = True

# RealEstateScraper scraper class
class RealEstateScraper(scrapy.Spider):
    # scraper name
    name = 'real-estate-scraper'
    
    # Entry point
    base_url = ''

    # custom headers
    headers = {
      'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    
    # custom settings
    custom_settings = {
      'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
      'DOWNLOAD_DELAY': 1
    }
    
    # crawler's entry
    def start_requests(self):
      # init filename
      is_rent = 'Rent' if 'rent' in self.base_url else 'Sale'
      filename = './output/Residential_' + is_rent + '_Flats_' + datetime.datetime.today().strftime('%Y-%m-%d-%H-%M') + '.csv'
      with open(filename, 'w') as f:
        columns = []
        f.write(','.join(columns) + '\n')

      # current page
      current_page = 1
      
      # crawl next postcode URL
      yield scrapy.Request(
        url=self.base_url,
        headers=self.headers,
        meta={
          'filename': filename,
          'current_page': current_page
        },
        callback=self.parse_links
      )
    
    # parse links
    def parse_links(self, response):
      # extract meta data
      if DEBUG:
        with open('links.html') as f: response = Selector(text=f.read())
      else:
        filename = response.meta.get('filename')
        current_page = response.meta.get('current_page')

      # Extract property links
      links = response.css('a[data-cy="propertyUrl"]::attr(href)').getall() # just a placeholder

      # loop over property card URLs
      for card_url in links:
        print(card_url)
        # crawl property listing
        #yield response.follow(
        #  url=card_url,
        #  headers=self.headers,
        #  meta={ 'filename': filename },
        #  callback=self.parse_listing
        #)
        #break
 
      # extract total pages
      try: total_pages = 10
      except: total_pages = 1
 
      # handle pagination within each location URL
      if not DEBUG:
        # increment current page counter
        current_page += 1
        
        # check the if current page is within the legal page range
        if current_page <= total_pages:
          # genrate next page URL
          split_url = response.url.split('?')
          next_page = split_url[0] + '?page=' + str(current_page)
          try:
            params = split_url[1]
            if 'page' in params: params = '&'.join(params.split('&')[1:])
            if len(split_url[1]): next_page += '&' + params
          except: pass
          if next_page[-1] == '&': next_page = next_page[:-1]
          
          # print debug information
          print('PAGE %s | %s' % (current_page, total_pages), next_page)

          # crawl next page
          #yield response.follow(
          #  url=next_page,
          #  headers=self.headers,
          #  meta={
          #    'filename': filename,
          #    'current_page': current_page
          #  },
          #  callback=self.parse_links
          #)

    # parse property card listing
    def parse_listing(self, response):
      # Work with local copy
      if DEBUG:
        with open('listing.html') as f: response = Selector(text=f.read())
      else: filename = response.meta.get('filename')
      
      # CSV entry
      features = {}

      if DEBUG: print(json.dumps(features, indent=2))
      else:
        # write features to output file
        with open(filename, 'a', encoding='utf-8') as f:
          writer = csv.DictWriter(f, features.keys())
          writer.writerow(features)

# main driver
if __name__ == '__main__':
  if not DEBUG:
    # run scraper
    process = CrawlerProcess()
    process.crawl(RealEstateScraper)
    process.start()
  else: RealEstateScraper.parse_links(RealEstateScraper, '')
