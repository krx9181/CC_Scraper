from bs4 import BeautifulSoup
import requests
import scrapy
import re
import json
from scrapy.utils.project import get_project_settings
from scrapy_scraper.items import ArticleItem
from urllib.parse import urljoin
 
import time
from datetime import datetime, timedelta


class MLAW_Spider(scrapy.Spider):
    name = 'mlaw_spider'
    start_url = [
        'https://www.mlaw.gov.sg/news/press-releases/',
        'https://www.mlaw.gov.sg/news/announcements/',
        'https://www.mlaw.gov.sg/news/public-consultations/',
        'https://www.mlaw.gov.sg/news/parliamentary-speeches/',
        'https://www.mlaw.gov.sg/news/speeches/'
    ]


    def start_requests(self):
        for url in self.start_url:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        #check if published_date is within 1 week
        curr_datetime = datetime.now()
        self.start_date =  curr_datetime - timedelta(weeks=8)
        #self.stopper_date =  curr_datetime - timedelta(weeks=0) ###to scrape past news

        dates = response.xpath('//a/div/div[2]/small')   #edit

        article_links = []

        for element in dates:
            date = element.css('::text').get()
            publish_date= datetime.strptime(date, "%d %b %Y")
            if publish_date > self.start_date:        
                parent_element = element.xpath('../../..')
                link = parent_element.css('a::attr(href)').get()
                absolute_link = urljoin(response.url, link)
                article_links.append(absolute_link)

        #follow links
        if article_links:
            for link in article_links:
                yield scrapy.Request(link, callback=self.parse_articles)
        

    def parse_articles(self, response):
        item = ArticleItem()
        item ['domain'] = 'mlaw'
        url = response.url 
        item['url'] = url
        item['datetime_scraped'] = datetime.now().isoformat()
        item['published_date'] = response.css('small.has-text-white::text').get()  

        headline = response.css('b::text').get()
        item['scraped_headline'] = headline   

        #BeautifulSoup to get text
        soup = BeautifulSoup(response.body,"lxml")

        div = soup.find('div', class_='col is-8 is-offset-2 print-content')
        body = div.get_text(separator=' ') 
        item['scraped_content']= body

        #get hrefs
        link_data = []
        
        links = div.find_all('a')
        exclude_titles = ['Press releases', 'Parliamentary speeches and responses', 'Speeches', 'Announcements']
        exclude_links = ['https://go.gov.sg/contactminlaw']

        for link in links:
            href = link.get('href')
            title = link.text
            if not re.search (r'#\w+', href) and title not in exclude_titles and href not in exclude_links: #exclude footnotes 
                link_data.append({'title': title, 'href': href})

        json_data = json.dumps(link_data)
        #print(url, json_data)
        item['related_links'] = json_data

        yield item

