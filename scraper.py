import re
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
<<<<<<< Updated upstream
from urllib.parse import urljoin

=======
import sys
from simhash import Simhash

LOG_FILE = "found_links.log"

found_urls = set()
unique_pages = set()

page_hashes = set()

def log_links(links):
    """ Save links to a log file and print them for real-time monitoring. """
    with open(LOG_FILE, "a") as f:
        for link in links:
            log_entry = f"{link}\n"
            f.write(log_entry)
            sys.stdout.write(log_entry)  # Prints to console immediately
            sys.stdout.flush()

def log_message(message):
    """Log a custom message to the log file and print to console."""
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")
    sys.stdout.write(message + "\n")
    sys.stdout.flush()

'''def get_simhash(content):
    # Generate simhash for the page content
    soup = BeautifulSoup(content, "lxml")
    
    for tag in soup(["nav", "header", "footer", "aside", "script", "style"]):
        tag.extract()  # remove tags
    text = soup.get_text(separator=" ", strip=True)
    return Simhash(text).value'''
>>>>>>> Stashed changes

def scraper(url, resp):
    links = extract_next_links(url, resp)
    valid_links = [link for link in links if is_valid(link, resp)]

    log_links(valid_links)

    return valid_links

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

def is_valid(url, resp=None):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}

    try:
        parsed = urlparse(url)

        if url in found_urls:
            return False  # Skip already found full URL
        found_urls.add(url)

        no_fragment_url = parsed.scheme + "://" + parsed.netloc + parsed.path  # stripped fragment
        unique_pages.add(no_fragment_url)

        if parsed.scheme not in set(["http", "https"]) or not parsed.netloc:
            return False

        if not any(parsed.netloc.endswith(domain) for domain in allowed_domains):
            return False

        if re.search(r"[?&]page=\d+|session|sid|track|utm_", parsed.query, re.IGNORECASE):   # ignore tracking params
            return False  

        if re.search(r"(date|from|to|timestamp|start|end)=\d{4}[-_/]\d{2}[-_/]\d{2}", parsed.query) or \
           re.search(r"/\d{4}[-_/]\d{2}[-_/]\d{2}", parsed.path):
            return False    # ignore links with date-based URLs

<<<<<<< Updated upstream
        if re.search(r"\d{4}-\d{2}-\d{2}", parsed.path) or re.search(r"date=\d{4}-\d{2}-\d{2}", parsed.query)::  # calendar pages
            return False 

        if "do=media" in parsed.query or "image=" in parsed.query:  # ignore media-related URLs
=======
        if re.search(r"(tab_files=|do=media|image=)", parsed.query):
            return False    # skip dynamically generated media pages
        
        if "filter" in parsed.query:
>>>>>>> Stashed changes
            return False

        if re.search(r"doku\.php.*[?&]idx=", parsed.path + parsed.query, re.IGNORECASE):
            log_message(f"[Filtered Out] Skipping potential trap: {url}")
            return False    # doku.php trap


        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            r"|png|tiff?|mid|mp2|mp3|mp4"
            r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            r"|epub|dll|cnf|tgz|sha1"
            r"|thmx|mso|arff|rtf|jar|csv"
            r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            return False  

        '''if resp and resp.status == 200 and resp.raw_response:
            page_simhash = get_simhash(resp.raw_response.content)
            log_message(f"[DEBUG] Simhash for {url}: {page_simhash}")
            if any(abs(page_simhash - h) < 50 for h in page_hashes):
                log_message(f"[Near-Duplicate] Skipping {url}")
                return False  

            page_hashes.add(page_simhash)'''

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def print_report():
    """Print and log the final crawling statistics."""
    summary = (
        f"\n=== CRAWLING REPORT ===\n"
        f"Total Found URLs: {len(found_urls)}\n"
        f"Total Unique Pages: {len(unique_pages)}\n"
        f"Saved log: {LOG_FILE}\n"
    )

    print(summary)  # Print to console
    with open("output.txt", "a") as f:
        f.write(summary)
