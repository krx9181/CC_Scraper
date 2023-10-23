import scrapy
import re
import json
from scrapy.utils.project import get_project_settings
from scrapy_scraper.items import ArticleItem
from scrapy.exceptions import DropItem
from bs4 import BeautifulSoup
from urllib.parse import urljoin
 
import time
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# customise headers
HEADERS = {
    'Connection': 'close',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
}


#scrapy spider
class MAS_Spider(scrapy.Spider):
    name = 'mas_spider'
    start_url = [
        'https://www.mas.gov.sg/news?page=1',
        'https://www.mas.gov.sg/publications?page=1'
    ]

    def start_requests(self):
        # Create a Chrome options object
        # chrome_options = Options()
        # chrome_options.add_argument("--headless")  # This enables headless mode

        #driver = webdriver.Chrome(options=chrome_options)
        driver = webdriver.Chrome()

        #find date to start scraping from
        curr_datetime = datetime.now()
        self.start_date =  curr_datetime - timedelta(weeks=1)
        
        for url in self.start_url:
            driver.get(url)  

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'mas-search-card')))
            #get article links within one week range before today's date
            parent_elements = driver.find_elements(By.XPATH, '//li[@class="mas-search-page__result"]') 
            article_links = []

            if parent_elements:
                for parent in parent_elements:
                    date = parent.find_element(By.XPATH, './/div[@class="ts:xs"]').text.split(': ')[1]
                    publish_date= datetime.strptime(date, "%d %B %Y")

                    if publish_date > self.start_date:
                        link = parent.find_element(By.XPATH, './/a[@class="ola-btn ola-link mas-link mas-link--no-underline"]') 
                        article_links.append(link.get_attribute('href'))
                            
                #follow links and parse articles
                if article_links:
                    for link in article_links:
                        yield scrapy.Request(link, callback=self.parse)

        driver.quit()
    


    def parse(self, response):
        item = ArticleItem()
        item ['domain'] = 'mas'
        url = response.url 
        item['url'] = url
        item['datetime_scraped'] = datetime.now().isoformat()

        soup = BeautifulSoup(response.body,"lxml")

        #BeautifulSoup to get headline
        element = soup.find('h1', class_='mas-text-h1 c:grey-1 fw:semibold m-b:m')
        headline = element.text.strip('\"').strip().strip('\"')
        item['scraped_headline'] = headline

        #BeautifulSoup to get published_date
        date_span = soup.find('div', class_='mas-ancillaries')
        date_text = date_span.text

        parts = date_text.split(': ')[1]
        published_date = parts.replace('\xa0', ' ')
        item['published_date'] = published_date.strip('\n')

        #BeautifulSoup to get text
        div = soup.find('div', class_='_mas-typeset contain m-t:l m-b:3xl mas-rte-content')
        body = div.get_text(separator=' ') 
        item['scraped_content']= body
        #item['related_links'] = ' '

        yield item






