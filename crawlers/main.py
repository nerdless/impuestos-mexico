from crawlers.spiders.prestadero import PrestaderoCrawler

crawler = PrestaderoCrawler()
data = crawler.crawl()
crawler.save_data(data)

crawler.close_connection()