########################################################
#
# Script to scrape real estate property listings data
#
########################################################

# Packages
import sys
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.selector import Selector
import json, csv
import datetime
import urllib
import json
import sys

# Debug mode
DEBUG = False

# RealEstateScraper scraper class
class RealEstateScraper(scrapy.Spider):
    # Scraper name
    name = 'airbnb'
    
    # Entry point
    base_url = 'https://www.airbnb.com/s/Prague--Czechia/homes?refinement_paths%5B%5D=%2Fhomes&place_id=ChIJi3lwCZyTC0cRIKgUZg-vAAE&date_picker_type=calendar&query=Prague%2C%20Czechia&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2026-06-01&monthly_length=3&monthly_end_date=2026-09-01&price_filter_input_type=2&channel=EXPLORE&pagination_search=true'

    # Custom headers
    headers = {
      'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    
    # Custom settings
    custom_settings = {
      'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
      'DOWNLOAD_DELAY': 1
    }
    
    # Crawler's entry
    def start_requests(self):
      # Init filename
      is_rent = 'Rent' if 'rent' in self.base_url else 'Sale'
      filename = './output/Residential_' + is_rent + '_Flats_' + datetime.datetime.today().strftime('%Y-%m-%d-%H-%M') + '.csv'
      with open(filename, 'w') as f:
        columns = ['url', 'price', 'title', 'description', 'overview', 'items', 'amenities', 'ratings']
        f.write(','.join(columns) + '\n')

      # Current page
      current_page = 0
      
      # Crawl next postcode URL
      yield scrapy.Request(
        url=self.base_url,
        headers=self.headers,
        meta={
          'filename': filename,
          'current_page': current_page
        },
        callback=self.parse_links
      )
    
    # Parse links
    def parse_links(self, response):
      # Extract meta data
      if DEBUG:
        with open('links.html') as f: response = Selector(text=f.read())
      else:
        filename = response.meta.get('filename')
        current_page = response.meta.get('current_page')

      # Extract property links
      data = json.loads(response.css('script[id="data-deferred-state-0"]::text').get())['niobeClientData'][0][1]['data']['presentation']['staysSearch']
      ids = data['results']['searchResults']

      # Loop over property card URLs
      for id in ids:
        card_id = id['contextualPictures'][0]['picture'].split('Hosting-')[-1].split('/')[0]
        card_url = 'https://www.airbnb.com/rooms/' + str(card_id)
        price = id['structuredDisplayPrice']['primaryLine']['accessibilityLabel']
        
        # Crawl property listing
        yield response.follow(
          url=card_url,
          headers=self.headers,
          meta={
            'filename': filename,
            'price': price
          },
          callback=self.parse_listing
        )
        #break

      # Extract total pages
      try: total_pages = len(data['results']['paginationInfo']['pageCursors'])
      except: total_pages = 1
 
      # Handle pagination within each location URL
      if not DEBUG:
        # Increment current page counter
        current_page += 1
        
        # Check the if current page is within the legal page range
        if current_page <= total_pages:
          # Genrate next page URL
          next_page = response.url.split('pagination_search=true')[0] + 'pagination_search=true&cursor=' + data['results']['paginationInfo']['pageCursors'][current_page]
          
          # Print debug information
          print('PAGE %s | %s' % (current_page+1, total_pages), next_page)

          # Crawl next page
          yield response.follow(
            url=next_page,
            headers=self.headers,
            meta={
              'filename': filename,
              'current_page': current_page
            },
            callback=self.parse_links
          )

    # Parse property card listing
    def parse_listing(self, response):
      # Work with local copy
      if DEBUG:
        with open('listing.html') as f: response = Selector(text=f.read())
        url = 'N/A'
        price = 'N/A'
      else:
        filename = response.meta.get('filename')
        price = response.meta.get('price')
        url = response.url

      # CSV entry
      features = {
        'url': url,
        'price': price
      }

      # Extract JSON data container
      json_data = json.loads([i for i in response.css('script[type="application/json"]::text').getall() if '"niobeClientData"' in i][0])
      data = json_data['niobeClientData'][0][1]['data']['presentation']['stayProductDetailPage']['sections']['sections']
      data1 = json_data['niobeClientData'][0][1]['data']['presentation']['stayProductDetailPage']['sections']['sbuiData']['sectionConfiguration']['root']['sections']
      
      # Extract title
      for section in data:
        if section['sectionId'] == 'AVAILABILITY_CALENDAR_INLINE':
          features['title'] = section['section']['listingTitle']
            
      # Extract description
      for section in data:
        if section['sectionId'] == 'DESCRIPTION_DEFAULT':
          features['description'] = section['section']['htmlDescription']['htmlText']

      # Extract overview      
      for section in data1:
        if section['sectionId'] == 'OVERVIEW_DEFAULT_V2':
          features['overview'] = section['sectionData']['title']
      
      # Extract overview items
      for section in data1:
        if section['sectionId'] == 'OVERVIEW_DEFAULT_V2':
          features['items'] = [i['title'] for i in section['sectionData']['overviewItems']]
      
      # Extract amenities
      amenities_groups = json_data['niobeClientData'][0][1]['data']['node']['pdpPresentation']['amenities']['seeAllAmenitiesGroups']
      amenities = []
      for group in amenities_groups: [amenities.append(i['title']) for i in group['amenities'] if i['available'] == True]
      features['amenities'] = amenities
      
      # Extract ratings
      ratings = []
      try:
        for section in data:
          if section['sectionId'] == 'REVIEWS_DEFAULT':
            [ratings.append(i['accessibilityLabel']) for i in section['section']['ratings']]
      except: ratings = 'N/A'
      features['ratings'] = ratings

      # Print extracted data
      if DEBUG:
        print(json.dumps(features, indent=2))
        print(features.keys())
      else:
        # Write features to output file
        with open(filename, 'a', encoding='utf-8') as f:
          writer = csv.DictWriter(f, features.keys())
          writer.writerow(features)

# Main driver
if __name__ == '__main__':
  if not DEBUG:
    # Run scraper
    process = CrawlerProcess()
    process.crawl(RealEstateScraper)
    process.start()
  else: RealEstateScraper.parse_listing(RealEstateScraper, '')
