from crawlers.spiders.prestadero import PrestaderoCrawler
from crawlers.spiders.afluenta import AfluentaCrawler

crawler = PrestaderoCrawler()
data = crawler.crawl()
crawler.save_data(data)
crawler.close_connection()

crawler = AfluentaCrawler()
data = crawler.crawl()
crawler.save_data(data)
crawler.close_connection()
