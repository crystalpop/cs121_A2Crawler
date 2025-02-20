from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time

from urllib.robotparser import RobotFileParser
import re
from urllib.parse import urlparse


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
    
    # For parsing robots.txt files after downloading
    def parse_robot_file(self, resp, robot_parser):
        if resp.status == 200:
            if resp.raw_response:
                # split the content into lines for the RobotFileParser to parse
                lines = resp.raw_response.content.decode("utf-8").splitlines()
                robot_parser.parse(lines)

    # Checks each domain, returns True if the robot_parser.can_fetch, False if not. 
    def robot_allowed(self, robot_parsers, url):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if re.match(scraper.ALLOWED_DOMAINS[0], domain):
            if not robot_parsers[0].can_fetch(self.config.user_agent, url):
                # print(f"{url} *****DISALLOWED IN ROBOTS*****")
                return False
        elif re.match(scraper.ALLOWED_DOMAINS[1], domain):
            if not robot_parsers[1].can_fetch(self.config.user_agent, url):
                # print(f"{url} *****DISALLOWED IN ROBOTS*****")
                return False
        elif re.match(scraper.ALLOWED_DOMAINS[2], domain):
            if not robot_parsers[2].can_fetch(self.config.user_agent, url):
                # print(f"{url} *****DISALLOWED IN ROBOTS*****")
                return False
        elif re.match(scraper.ALLOWED_DOMAINS[3], domain):
            if not robot_parsers[3].can_fetch(self.config.user_agent, url):
                # print(f"{url} *****DISALLOWED IN ROBOTS*****")
                return False
        return True

    def run(self):
        # Download the robots.txt files for each domain
        ics_resp = download("https://www.ics.uci.edu/robots.txt", self.config)
        cs_resp = download("https://www.cs.uci.edu/robots.txt", self.config)
        inf_resp = download("https://www.informatics.uci.edu/robots.txt", self.config)
        stat_resp = download("https://www.stat.uci.edu/robots.txt", self.config)
        robot_responses = [ics_resp, cs_resp, inf_resp, stat_resp]

        # Create a robot file parser for each robots.txt file
        ICS_RP = RobotFileParser()
        CS_RP = RobotFileParser()
        INF_RP = RobotFileParser()
        STAT_RP = RobotFileParser()
        robot_parsers = [ICS_RP, CS_RP, INF_RP, STAT_RP]

        # Parse each robots.txt file 
        for i in range(0,4):
            self.parse_robot_file(robot_responses[i], robot_parsers[i])
            
            """Attempt at checking sitemaps: 
                If there are sitemaps for this domain, remove the original domain from 
                frontier and replace with the sitemap."""
            # sitemaps = robot_parsers[i].site_maps()
            # if sitemaps:
            #     print(f"REMOVING {robot_responses[i].url[:-11]}")
            #     self.frontier.to_be_downloaded.remove(robot_responses[i].url[:-11])
            #     for map in sitemaps:
            #         print(f"REPLACING WITH {map}")
            #         self.frontier.add_url(map)


        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            # Only download url if allowed in robots.txt
            if self.robot_allowed(robot_parsers, tbd_url):
                resp = download(tbd_url, self.config, self.logger)
                self.logger.info(
                    f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")
                
                scraped_urls = scraper.scraper(tbd_url, resp)
                for scraped_url in scraped_urls:
                    self.frontier.add_url(scraped_url)
                self.frontier.mark_url_complete(tbd_url)
                time.sleep(self.config.time_delay)
