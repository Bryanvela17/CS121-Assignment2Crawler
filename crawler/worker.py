from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
from scraper import printCrawlerSummary




class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)

    def run(self):
        tbd_urlManualCount = []
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            print(f'-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            if tbd_url not in tbd_urlManualCount: # check if link has been seen already
                tbd_urlManualCount.append(tbd_url)
            print(f'-->->->-->->-->->--->tbd_urlManualCount: {len(tbd_urlManualCount)}')
            #printCrawlerSummary()
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
        
        printCrawlerSummary()
        print(f'-->->->-->->-->->--->tbd_urlManualCount: {len(tbd_urlManualCount)}')
