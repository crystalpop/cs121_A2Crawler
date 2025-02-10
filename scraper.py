import re
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup
import PartA as A
import PartB as B

#TODO: relative --> absolute urls
#TODO: traps? no url twice
#TODO: get words & freqeuncies
#TODO: subdomains for ics.uci.edu
#TODO: do we want pdfs, .doc?


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
    unique_count = 0
    valid_links = [link for link in links if is_valid(link)]

    return valid_links

def update_subdomains(sub_dict, parsed):
    # assuming each parsed that comes in is unique
    domain = parsed.netloc.lower()
    if isinstance(domain, bytes):
        domain = domain.decode('utf-8')
    if re.match(r'.*\.ics\.uci\.edu', domain):
        if domain in sub_dict:
            sub_dict[domain] += 1
        else:
            sub_dict[domain] = 1

def extract_next_links(url, resp):
    result = []
    # keys are the subdomains, values are number of unique pages
    ics_subdomains = {}
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    if resp.status == 200 or resp.status >= 300:
        if resp.raw_response:
            html_doc = resp.raw_response.content
            # making sure the doc has data/content
            if len(html_doc) > 0:
                soup = BeautifulSoup(html_doc, "lxml")
                
                for link in soup.find_all('a'):
                    href = link.get('href')
                    parsed = urlparse(href)
                    hyper = urldefrag(href)[0]
                    # make sure don't get the same link twice from one page
                    if hyper not in result:
                        result.append(hyper)
                        update_subdomains(ics_subdomains, parsed)
                        process_info(clean_text, hyper)
        
    with open('report.txt', 'w') as report:
        for sub in ics_subdomains:
            report.write(f"{sub}, {ics_subdomains[sub]}")
    return result

def tokenize(file_name):
    token_list = []
    with open(file_name, 'r') as file:
        # read line by line to save memory
        for line in file:
            content = line.lower()
            # get only alphanumeric characters
            token_list.extend(re.findall(r"[0-9a-zA-Z]+", content))
    return token_list

def computeWordFrequencies(token_list):
    # empty dict
    token_frequencies = {}
    # if dict does not contain token, add it. else, increment value.
    for token in token_list:
        if token not in token_frequencies:
            token_frequencies[token] = 1
        else:
            token_frequencies[token] += 1
    return token_frequencies

def process_info(url, resp):
    url_dict = {}
    if resp.raw_response:
        html_doc = resp.raw_response.content
        # making sure the doc has data/content
        if len(html_doc) > 0:
            soup = BeautifulSoup(html_doc, "lxml")
            soup_text = soup.get_text()
            clean_text = re.sub(r'\s+','', soup_text)


            with open('words.txt', 'w') as words:
                words.write(clean_text)
    tokens = tokenize('words.txt')
    word_frequencies = computeWordFrequencies(tokens)

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            with open('report.txt', 'w') as report:
                report.write(f"{url} NOT VALID")
            return False
        if any(re.match(pattern, parsed.netloc.lower()) for pattern in ALLOWED_DOMAINS) and not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            with open('report.txt', 'w') as report:
                report.write(f"{url} IS VALID")
            return True
        else:
            with open('report.txt', 'w') as report:
                report.write(f"{url} NOT VALID")
            return False

    except TypeError:
        print ("TypeError for ", parsed)
        raise
