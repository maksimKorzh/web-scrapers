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
import sys

# Debug mode
DEBUG = False

# RealEstateScraper scraper class
class RealEstateScraper(scrapy.Spider):
    # Scraper name
    name = 'realting'
    
    # Entry point
    base_url = 'https://realting.com/lithuania/apartments'

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
        columns = [
          'url', 'title', 'country', 'state', 'region', 'city', 'address',
          'latitude', 'longitude', 'price', 'price_per_meter', 'floor',
          'floors', 'area', 'rooms', 'year', 'details', 'description'
        ]
        f.write(','.join(columns) + '\n')

      # Current page
      current_page = 1
      
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
      links = response.css('a[class="flex-grow-1"]::attr(href)').getall()

      # Loop over property card URLs
      for card_url in links:
        # Crawl property listing
        yield response.follow(
          url=card_url,
          headers=self.headers,
          meta={ 'filename': filename },
          callback=self.parse_listing
        )
        #break
 
      # Extract total pages
      try:
        total_pages = max([int(i) for i in response.css('div[class="pages"]').css('a::attr(data-page)').getall()])
        print('total', total_pages)
      except: total_pages = 1
 
      # Handle pagination within each location URL
      if not DEBUG:
        # Increment current page counter
        current_page += 1
        
        # Check the if current page is within the legal page range
        if current_page <= total_pages:
          # Genrate next page URL
          split_url = response.url.split('?')
          next_page = split_url[0] + '?page=' + str(current_page)
          try:
            params = split_url[1]
            if 'page' in params: params = '&'.join(params.split('&')[1:])
            if len(split_url[1]): next_page += '&' + params
          except: pass
          if next_page[-1] == '&': next_page = next_page[:-1]
          
          # Print debug information
          print('PAGE %s | %s' % (current_page, total_pages), next_page)

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
      else:
        filename = response.meta.get('filename')
        url = response.url
      
      # Extract location
      try:
        location = ' '.join([i.replace('\n', '|').strip() for i in response.css('section[id="blockAddress"]').css('div[class="lh-small"] *::text').getall()])
        country = location.split('Country |')[-1].split('|')[0].strip()
        state = location.split('State |')[-1].split('|')[0].strip()
        region = location.split('Region |')[-1].split('|')[0].strip()
        city = location.split('City |')[-1].split('|')[0].strip()
        if city == '': city =  location.split('Town |')[-1].split('|')[0].strip()
        if city == '': city =  location.split('Village |')[-1].split('|')[0].strip()
        address = location.split('Address |')[-1].split('|')[0].strip()
      except:
        country = 'N/A'
        state = 'N/A'
        region = 'N/A'
        city = 'N/A'
        address = 'N/A'
      
      # Extract property characteristics
      try:
        characteristics = ' '.join([i.replace('\n', '|').strip() for i in response.css('section[id="blockParams"]').css('div[class="lh-small"] *::text').getall()])
        price = response.css('div[class="price-item"]::attr(data-price-eur)').get()
        price_per_meter = characteristics.split('Price per m² | | | |')[-1].split('|')[0].strip()
        floor = characteristics.split('Floor |')[-1].split('|')[0].strip()
        floors = characteristics.split('Number of floors |')[-1].split('|')[0].strip()
        area = characteristics.split('Total area |')[-1].split('|')[0].strip()
        rooms = characteristics.split('Rooms |')[-1].split('|')[0].strip()
        year = characteristics.split('The year of construction |')[-1].split('|')[0].strip()
        description = response.css('div[class="readmore word-break"]::text').get().strip().replace('\n', ' ').replace('\r', ' ')
        image_urls = [i.split("background-image: url('")[-1].split("')")[0] for i in response.css('div[class="image-item"]::attr(style)').getall()]
      except:
        price = 'N/A'
        price_per_meter = 'N/A'
        floor = 'N/A'
        floors = 'N/A'
        area = 'N/A'
        rooms = 'N/A'
        year = 'N/A'
        description = 'N/A'
        image_urls = 'N/A'

      # Extract extra details
      try:
        details = {}
        details_raw =  ''.join([i.replace('\n', '|').strip() for i in response.css('div[class="tags-block-content"] *::text').getall()])
        details_raw = details_raw.replace(':||', ':')
        details_raw = list(filter(None, details_raw.split('|')))
        for feature in details_raw: details[feature.split(':')[0]] = feature.split(':')[1]
      except: details = 'N/A'
      
      # Extract coordinates
      try:
        if DEBUG:
          latitude = response._text.split('"latitude":')[-1].split(',')[0]
          longitude = response._text.split('"longitude":')[-1].split('}')[0]
        else:
          latitude = response.text.split('"latitude":')[-1].split(',')[0]
          longitude = response.text.split('"longitude":')[-1].split('}')[0]
      except:
        latitude = 'N/A'
        longitude = 'N/A'

      # CSV entry
      features = {
        'url': url,
        'title': response.css('h1[class="h4 color-black mb-10"]::text').get().strip(),
        'country': country,
        'state': state,
        'region': region,
        'city': city,
        'address': address,
        'latitude': latitude,
        'longitude': longitude,
        'price': price,
        'price_per_meter': price_per_meter,
        'floor': floor,
        'floors': floors,
        'area': area,
        'rooms': rooms,
        'year': year,
        'details': details,
        'description': description,
        'image_urls': image_urls
      }

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
