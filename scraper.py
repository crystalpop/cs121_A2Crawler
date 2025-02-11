import re
from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup

"""
 Implement the scraper function in scraper.py. The scraper function receives a URL
and corresponding Web response (for example, the first one will be 
"http://www.ics.uci.edu" and the Web response will contain the page itself). 
Your task is to parse the Web response, extract enough information from the page 
(if it's a valid page) so as to be able to answer the questions for the report, 
and finally, return the list of URLs "scrapped" from that page. Some important notes:

Make sure to return only URLs that are within the domains and paths mentioned above! (see is_valid function in scraper.py -- you need to change it)
Make sure to defragment the URLs, i.e. remove the fragment part.
You can use whatever libraries make your life easier to parse things. Optional dependencies you might want to look at: BeautifulSoup, lxml (nudge, nudge, wink, wink!)
Optionally, in the scraper function, you can also save the URL and the web page on your local disk.
"""

ALLOWED_DOMAINS = [
    r'.*\.ics\.uci\.edu',
    r'.*\.cs\.uci\.edu',
    r'.*\.informatics\.uci\.edu',
    r'.*\.stat\.uci\.edu'
]

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


"""
source for absolute path resolution : https://blog.finxter.com/scraping-the-absolute-url-of-instead-of-the-relative-path-using-beautifulsoup/

"""
def extract_next_links(url, resp):
    result = set()
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if (resp.status == 200 or (resp.status >= 300 and resp.status < 400)) and resp.raw_response:
        html_doc = resp.raw_response.content
        # make sure page has content
        if len(html_doc) > 0:
            soup = BeautifulSoup(html_doc, "lxml")
            text = soup.get_text()
            if len(text) > 250: # TODO: what should be the threshold? if not enough text, skip it
                for a in soup.find_all('a'):
                    href = a.get('href')
                    abs_url = urljoin(url, href) # resolve possible relative url to absolute url
                    result.add(urldefrag(abs_url)[0]) # defragment and add to result
    return list(result)


def repeated_segments(path):
            # Split the path into non-empty segments
        segments = [seg for seg in path.split('/') if seg]

        # Check for excessive consecutive repetition
        max_allowed_reps = 3 
        current_rep = 1  # count current consecutive repetition
        for i in range(1, len(segments)):
            if segments[i] == segments[i - 1]:
                current_rep += 1
            else:
                current_rep = 1  # reset count if segment changes
            if current_rep > max_allowed_reps:
                return True

        return False

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        query = parsed.query.lower()
        if parsed.scheme not in set(["http", "https"]):
            # print(f"{url} bad scheme NOT VALID")
            return False
        
        if not any(re.match(pattern, domain) for pattern in ALLOWED_DOMAINS):
            # print(f"{url} bad domain NOT VALID")
            return False
        
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            # print(f'{url} has bad extension NOT VALID')
            return False
        
        if re.search(r"\d{4}-\d{2}-\d{2}", path) or re.search(r"date=\d{4}-\d{2}-\d{2}", query):  # calendar pages
            # print(f'{url} contains calendar NOT VALID')
            return False 
        
        if re.search(r"(tab_files=|do=media|image=|do=diff)", query): # media/dynamic/diff pages
            return False 
        
        if re.search(r"[?&]page=\d+", parsed.query):    #ignore pagination links
            return False  

        if re.search(r"session|sid|track|utm_", parsed.query, re.IGNORECASE):   # ignore tracking params
            return False
        # /people and /happening not allowed from robots.txt
        if repeated_segments(path):
            return False

        if any(re.match(pattern, domain) for pattern in ALLOWED_DOMAINS[0:1]) and re.match(r'^/(?:people|happening)', path):
            # print(f'{url} contains happening or people NOT VALID')
            return False
        # /wp-admin/ disallowed for stat.uci.edu
        if re.match(ALLOWED_DOMAINS[3], domain) and re.match(r'^/wp-admin/', path):
            # print(f'{url} wp-admin disallowed NOT VALID')
            return False
        
        if re.match(ALLOWED_DOMAINS[2], domain) and re.match(r'^/(?:wp-admin|research)/', path):
            # print(f'{url} wp-admin or research disallowed NOT VALID')
            return False

        return True


    except TypeError:
        print ("TypeError for ", parsed)
        raise
