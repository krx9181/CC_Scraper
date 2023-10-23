from bs4 import BeautifulSoup
import scrapy
from scrapy.utils.project import get_project_settings
from scrapy_scraper.items import ArticleItem
import json
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin

class IRAS_Spider(scrapy.Spider):
    name = 'iras_spider'
    start_url = 'https://www.iras.gov.sg/news-events/newsroom/1?Year=all&type=media-release'

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse)

    def parse(self, response):

        #check if published_date is within 1 week
        curr_datetime = datetime.now()
        self.start_date =  curr_datetime - timedelta(weeks=8)

        dates = response.css('.eyd-article-item__meta--date') 

        article_links = []

        for element in dates:
            date = element.css('::text').get()
            publish_date= datetime.strptime(date, "%d %b %Y")
            if publish_date > self.start_date:
                parent_element = element.xpath('../..')

                article_links.append(parent_element.css('a::attr(href)').get())

        #follow links
        if article_links:
            for link in article_links:
                yield scrapy.Request(link, callback=self.parse_articles)


    def parse_articles(self, response):
        item = ArticleItem()
        item ['domain'] = 'iras'
        url = response.url
        item['url'] = url
        item['datetime_scraped'] = datetime.now().isoformat()
        item['published_date'] = response.css('span.eyd-event-details__date::text').get()   #edit

        headline = response.xpath('//header[@class="eyd-page-header eyd-page-header--share"]/h1/text()').get()
        item['scraped_headline'] = headline    #edit
        
        #BeautifulSoup to get text
        soup = BeautifulSoup(response.body,"lxml")

        div = soup.find('section', class_='eyd-rte')
        body = div.get_text(separator=' ') 
        item['scraped_content']= body

        #get hrefs
        link_data = []
        
        links = div.find_all('a')
        base_url = "https://www.iras.gov.sg/"

        for link in links:
            href = link.get('href')
            title = link.text
            if not re.search (r'#\w+', href) and title != '': #exclude footnotes 
                complete_url = urljoin(base_url, href) 
                link_data.append({'title': title, 'href': complete_url})

        # Serialize link_data to JSON
        json_data = json.dumps(link_data)

        item['related_links'] = json_data

        yield item

