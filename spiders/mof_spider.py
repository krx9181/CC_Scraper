import scrapy
from scrapy.utils.project import get_project_settings
from scrapy_scraper.items import ArticleItem
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json

import time
from datetime import datetime, timedelta

from selenium import webdriver
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options


# customise headers
HEADERS = {
    'Connection': 'close',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
}


#scrapy spider
class MOF_Spider(scrapy.Spider):
    name = 'mof_spider'
    start_urls = [
        'https://www.mof.gov.sg/news-publications/press-releases',
        'https://www.mof.gov.sg/news-publications/public-consultations',
        'https://www.mof.gov.sg/news-publications/speeches'
    ]

    def start_requests(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # This enables headless mode

        driver = webdriver.Chrome(options=chrome_options)

        #find date to start scraping from
        curr_datetime = datetime.now()
        self.start_date =  curr_datetime - timedelta(weeks=8)
       #self.stopper_date =  curr_datetime - timedelta(weeks=2) ##to scrape past news
        
        for url in self.start_urls:
            driver.get(url)  
            count = 1

            while count!=5:
                ignored_exceptions=(NoSuchElementException,StaleElementReferenceException)
                WebDriverWait(driver, 10, ignored_exceptions=ignored_exceptions).until(EC.presence_of_element_located((By.CLASS_NAME, 'article-item')))

                #get article links within one week range before today's date
                dates = driver.find_elements(By.CLASS_NAME,'article-label')

                article_links = []

                for element in dates:
                    date = element.text
                    publish_date= datetime.strptime(date, "%d %b %Y")
                    if publish_date > self.start_date:
                        parent_element = element.find_element(By.XPATH, "..")
                        article_links.append(parent_element.get_attribute('href'))

                #follow links and parse articles
                if article_links:
                    for link in article_links:
                        yield scrapy.Request(link, callback=self.parse)

                # Check for and navigate to the next page
                next_page_script = 'document.querySelector("li[data-page=\'next\']").click()'
                
                try:
                    driver.execute_script(next_page_script)
                    time.sleep(3)
                    counter+=1

                except:
                    break 

        driver.quit()
    


    def parse(self, response):
        item = ArticleItem()
        item ['domain'] = 'mof'
        url = response.url
        item['url'] = url 
        item['datetime_scraped'] = datetime.now().isoformat()
        item['published_date'] = response.css('small.red-text.d-block.mb-2::text').get()

        headline = response.css('h3::text').get()
        item['scraped_headline'] = headline

        #BeautifulSoup to get text
        soup = BeautifulSoup(response.body,"lxml")

        div = soup.find('div', class_='mt-4')
        body = div.get_text(separator=' ') 
        item['scraped_content']= body

        #get hrefs
        link_data = []
        
        links = div.find_all('a')
        for link in links:
            title = link.text
            if not re.search (r'\[\d+\]', title): #exclude footnotes 
                href = link.get('href')
                link_data.append({'title': title, 'href': href})

        # Serialize link_data to JSON
        json_data = json.dumps(link_data)

        item['related_links'] = json_data
        
        #get links in text
        # patterns = [
        #     r'https?://\S+',  # Pattern 1: Matches http:// or https:// followed by non-whitespace characters
        #     r'www\.\S+',      # Pattern 2: Matches URLs starting with "www." followed by non-whitespace characters
        #     r'\S+\.sg'        # Pattern 3: Matches URLs ending with ".sg"
        # ]

        # text_links = []
        # for pattern in patterns:
        #     match = re.search(pattern, body)
        #     if match:
        #         text_links.append(match.group(0))

        # text_links = set(text_links) #remove duplicates

        # for link in text_links:
        #     title = link
        #     href = link
        #     link_data.append({'title': title, 'href': href})        

        yield item





