from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from scrapy_scraper.spiders.iras_spider import IRAS_Spider 
from scrapy_scraper.spiders.mas_spider import MAS_Spider 
from scrapy_scraper.spiders.mlaw_spider import MLAW_Spider 
from scrapy_scraper.spiders.mof_spider import MOF_Spider 

settings = get_project_settings()
process = CrawlerProcess(settings)

process.crawl(IRAS_Spider)
process.crawl(MAS_Spider)
process.crawl(MLAW_Spider)
process.crawl(MOF_Spider)

process.start()
