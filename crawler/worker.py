from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
    
    def parse_robot_file(self, resp, robot_parser):
        if resp.status == 200:
            if resp.raw_response:
                soup = BeautifulSoup(resp.raw_response.content, "lxml")
                lines = soup.get_text().splitlines()
                # for line in lines:
                #     print(line)
                robot_parser.parse(lines)
        else:
            print(f"NO ROBOT FOR {resp.url}")

    def run(self):
        ics_resp = download("https://www.ics.uci.edu/robots.txt", self.config)
        cs_resp = download("https://www.cs.uci.edu/robots.txt", self.config)
        inf_resp = download("https://www.informatics.uci.edu/robots.txt", self.config)
        stat_resp = download("https://www.stat.uci.edu/robots.txt", self.config)

        robot_responses = [ics_resp, cs_resp, inf_resp, stat_resp]

        ICS_RP = RobotFileParser()
        CS_RP = RobotFileParser()
        INF_RP = RobotFileParser()
        STAT_RP = RobotFileParser()

        robot_parsers = [ICS_RP, CS_RP, INF_RP, STAT_RP]

        for i in range(0,4):
            self.parse_robot_file(robot_responses[i], robot_parsers[i])

        # print(ICS_RP.can_fetch(self.config.user_agent, "https://www.cs.uci.edu/people"))

        # for sitemap in STAT_RP.site_maps():
        #     print(f"SiTEMAP: {sitemap}")

        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp, robot_parsers)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
