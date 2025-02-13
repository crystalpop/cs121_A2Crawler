from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

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
                # split the content into lines for the RobotFileParser to parse
                lines = resp.raw_response.content.decode("utf-8").splitlines()
                robot_parser.parse(lines)

    def run(self):
        # download the robots.txt files for each domain
        ics_resp = download("https://www.ics.uci.edu/robots.txt", self.config)
        cs_resp = download("https://www.cs.uci.edu/robots.txt", self.config)
        inf_resp = download("https://www.informatics.uci.edu/robots.txt", self.config)
        stat_resp = download("https://www.stat.uci.edu/robots.txt", self.config)

        robot_responses = [ics_resp, cs_resp, inf_resp, stat_resp]

        # create a robot file parser for each robots.txt file
        ICS_RP = RobotFileParser()
        CS_RP = RobotFileParser()
        INF_RP = RobotFileParser()
        STAT_RP = RobotFileParser()

        robot_parsers = [ICS_RP, CS_RP, INF_RP, STAT_RP]

        # parse each robots.txt file, if there are sitemaps, remove the seed and replace with sitemap
        # TODO: is this the right idea? do i add the sitemap to the seed urls instead?
        for i in range(0,4):
            self.parse_robot_file(robot_responses[i], robot_parsers[i])
        
            # sitemaps = robot_parsers[i].site_maps()
            # if sitemaps:
            #     # print(f"REMOVING {robot_responses[i].url[:-11]}")
            #     self.config.seed_urls.remove(robot_responses[i].url[:-11])
            #     for map in sitemaps:
            #         self.frontier.add_url(map)
        # print(f"++++++SEEDS: {[seed for seed in self.config.seed_urls]}")


        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            # pass the robot parsers to scraper
            scraped_urls = scraper.scraper(tbd_url, resp, robot_parsers)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
