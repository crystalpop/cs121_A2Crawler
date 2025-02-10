import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status != 200 or resp.raw_response is None:
        return []

    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    links = set()  # Use set to avoid duplicate URLs

    for tag in soup.find_all("a", href=True):
        absolute_url = urljoin(url, tag["href"])
        absolute_url = absolute_url.split("#")[0]  # Remove fragments
        links.add(absolute_url)

    return list(links)  # Convert set to list

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]) or not parsed.netloc:
            return False

        if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
            return False

        if re.search(r"[?&]page=\d+", parsed.query):    #ignore pagination links
            return False  

        if re.search(r"session|sid|track|utm_", parsed.query, re.IGNORECASE):   # ignore tracking params
            return False  

        if re.search(r"\d{4}-\d{2}-\d{2}", parsed.path) or re.search(r"date=\d{4}-\d{2}-\d{2}", parsed.query)::  # calendar pages
            return False 

        if "do=media" in parsed.query or "image=" in parsed.query:  # ignore media-related URLs
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
