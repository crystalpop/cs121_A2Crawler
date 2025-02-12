import re
from urllib.parse import urlparse, urldefrag, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup


# TODO: check for similarity & duplicates in extract_next_links
# TODO: webpage content similarity repetition over a certain amount of chained pages (the threshold definition is up to you!
# TODO: maybe have a prev variable & a similarity counter. compare current page vs prev page & if similarity is over 80?% don't crawl it. if similarity not over threshold, update prev to curr and curr to next

"""
How many unique pages did you find? Uniqueness for the purposes of this assignment is ONLY established by the URL, but discarding the fragment part. So, for example, http://www.ics.uci.edu#aaa and http://www.ics.uci.edu#bbb are the same URL. Even if you implement additional methods for textual similarity detection, please keep considering the above definition of unique pages for the purposes of counting the unique pages in this assignment.
What is the longest page in terms of the number of words? (HTML markup doesn’t count as words)
What are the 50 most common words in the entire set of pages crawled under these domains ? (Ignore English stop words, which can be found, for example, hereLinks to an external site.) Submit the list of common words ordered by frequency.
How many subdomains did you find in the ics.uci.edu domain? Submit the list of subdomains ordered alphabetically and the number of unique pages detected in each subdomain. The content of this list should be lines containing URL, number, for example:
http://vision.ics.uci.edu, 10 (not the actual number here)


"""
ICS_RFP = RobotFileParser()
CS_RFP = RobotFileParser()
# INF_RFP = RobotFileParser()
STAT_RFP = RobotFileParser()
print("setting robot parser urls")
ICS_RFP.set_url("https://www.ics.uci.edu/robots.txt")
CS_RFP.set_url("https://www.cs.uci.edu/robots.txt")
# INF_RFP.set_url("https://www.informatics.uci.edu/robots.txt")
STAT_RFP.set_url("https://www.stat.uci.edu/robots.txt")
print("reading ics robot files")
ICS_RFP.read()
print("reading cs robot files")
CS_RFP.read()
# print("reading inf robot files")
# INF_RFP.read()
print("reading stat robot files")
STAT_RFP.read()

USER_AGENT = "IR UW25 93481481"

ROBOT_FILES = [
    "https://ics.uci.edu/robots.txt",
    "https://cs.uci.edu/robots.txt",
    "https://informatics.uci.edu/robots.txt",
    "https://stat.uci.edu/robots.txt"
]



ALLOWED_DOMAINS = [
    r'.*\.ics\.uci\.edu',
    r'.*\.cs\.uci\.edu',
    r'.*\.informatics\.uci\.edu',
    r'.*\.stat\.uci\.edu'
]

url_dict = {}   # key: url , value: dict of words with counts 

url_word_count_dict = {} # key: url, value is # of words in it 

all_word_dict = {} # key is word, count is value

subdomain_dict = {} # key: subdomain , value: set of unique urls within it 

stopwords = [
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves"
]


def scraper(url, resp):
    links = extract_next_links(url, resp)
    valid_links = set()
    for link in links:
        if is_valid(link):
            valid_links.add(link)
    if is_valid(url):
        process_info(url, resp)
            
    return list(valid_links)


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
            
            if "Content-Length" in resp.raw_response.headers:
                file_bytes = int(resp.raw_response.headers["Content-Length"])
                if file_bytes > 3000000 and len(text) < 300: #TODO: adjust threshold
                    return []
                
            if len(text) > 300: # TODO: what should be the threshold? if not enough text, skip it
                for a in soup.find_all('a'):
                    href = a.get('href')
                    abs_url = urljoin(url, href) # resolve possible relative url to absolute url
                    result.add(urldefrag(abs_url)[0]) # defragment and add to result

    elif resp.status >= 600 and resp.status <= 606:
        print(f"***********\nERROR: {resp.error}\n*************")

    return list(result)

#TODO: update this, missed points
def tokenize(file_name):
    token_list = []
    with open(file_name, 'r') as file:
        # read line by line to save memory
        for line in file:
            content = line.lower()
            # get only alphanumeric characters
            token_list.extend(re.findall(r"[0-9a-zA-Z]+", content))
    return token_list

#TODO: update this, missed points
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

    #STRIP these just to be safe 
 
    clean_url = urldefrag(resp.url)[0].strip()   # the unique url w/o the fragement 
    
    parsed = urlparse(clean_url)   # Parse the URL
    url_subdomain = parsed.netloc.lower().strip()  # the subdomain.domain 


    if resp.raw_response:
        try:
            soup = BeautifulSoup(resp.raw_response.content, "lxml")
            text = soup.get_text()  # Removes all HTML tags, scripts, etc.

            # Clean text: Remove multiple spaces, newlines, and special characters
            clean_text = re.sub(r'\s+', ' ', text).strip()

            with open("content.txt", "w") as file:
                file.write(clean_text) 
        except Exception as e:
            print(f"Error saving content from {url} to file...")



    # TOKENIZING 
    token_list = tokenize("content.txt")
    word_count_dict = computeWordFrequencies(token_list)

    # ADD to url_dict 
    if clean_url not in url_dict.keys():
        url_dict[clean_url] = word_count_dict

    url_word_count_dict[clean_url] = sum(url_dict[clean_url].values()) # sum of words in that unique url 

    for key, val in word_count_dict.items():  # adds words to an all word dict to maintain sum of all words 
        if key in all_word_dict.keys():
            all_word_dict[key] = all_word_dict[key] + val
        else:
            all_word_dict[key] = val 


    # HANDLING SUBDOMAIN PART 
    subdomain_parts = url_subdomain.split('.')
    if len(subdomain_parts) > 3:    # https://vision.ics.uci.edu/about 
        main_domain = ".".join(subdomain_parts[-3:])  # Last three parts (ics.uci.edu)
        # subdomain = ".".join(subdomain_parts[:-3])  # the part except (ics.uci.edu) --> vision

        if main_domain == "ics.uci.edu":
            # add url to dict set 
            if url_subdomain not in subdomain_dict:
                subdomain_dict[url_subdomain] = set()
            subdomain_dict[url_subdomain].add(clean_url)
    


def write_final_output():

    try:
        with open("finaloutput.txt", "w") as outputfile:
            outputfile.write(f"Answer 1: \n")
            outputfile.write(f"Number of unique pages: {len(url_dict)}\n\n")

            sorted__url_word_count_dict = dict(sorted(url_word_count_dict.items(), key=lambda item: item[1], reverse=True))
            longest_page = next(iter(sorted__url_word_count_dict), None)
            words_in_longest_page = sorted__url_word_count_dict.get(longest_page, 0)

            #longest_page = list(sorted__url_word_count_dict.keys())[0] 
            #words_in_longest_page = list(sorted__url_word_count_dict.values())[0] 

            outputfile.write(f"Answer 2: \n")
            outputfile.write(f"Longest page: {longest_page} with {words_in_longest_page} words\n\n") 


            filtered_all_word_dict = {k: v for k, v in all_word_dict.items() if k not in stopwords}
            sorted_all_word_dict = dict(sorted(filtered_all_word_dict.items(), key=lambda item: item[1], reverse=True))
            first_50_words = list(sorted_all_word_dict.items())[:50]

            outputfile.write(f"Answer 3: \n")
            outputfile.write("List of 50 most common words:\n")
            for word, count in first_50_words:
                outputfile.write(f"{word}: {count}\n")
            outputfile.write("\n")

            unique_subdomain_count = len(subdomain_dict)

            outputfile.write(f"Answer 4: \n")
            outputfile.write(f"Number of subdomains found within ics.uci.edu: {unique_subdomain_count}\n")
            outputfile.write(f"Subdomains with count of unique pages within each: \n")

            for key, val in subdomain_dict.items():
                count = len(val)
                outputfile.write(f"{key}: {count}\n")


    except Exception as e:
        print(e)


def repeated_segments(path):
    # Split the path into non-empty segments
    segments = [seg for seg in path.split('/') if seg]

    n = len(segments)
    # Try different group lengths from min_group_length (2) up to half the segments
    for group_len in range(2, n // 2 + 1):
        # Slide a window over the segments list
        for i in range(n - 2 * group_len + 1):
            group = segments[i:i+group_len]
            next_group = segments[i+group_len:i+2*group_len]
            if group == next_group:
                print(f"Found repeated group {group} in segments: {segments}")
                return True
    return False


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        print(f"checking validity of {url}")
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path
        query = parsed.query

        if parsed.scheme not in set(["http", "https"]):
            print(f"{url} bad scheme NOT VALID")
            return False
        
        if not any(re.match(pattern, domain) for pattern in ALLOWED_DOMAINS):
            print(f"{url} bad domain NOT VALID")
            return False
        

        # robot.txt filters
        if re.match(ALLOWED_DOMAINS[0], domain):
            if not ICS_RFP.can_fetch(USER_AGENT, url):
                print(f"{url} DISALLOWED IN robots")
                return False
        elif re.match(ALLOWED_DOMAINS[1], domain):
            if not CS_RFP.can_fetch(USER_AGENT, url):
                print(f"{url} DISALLOWED IN robots")
                return False
        # elif re.match(ALLOWED_DOMAINS[2], domain):
        #     if not INF_RFP.can_fetch(USER_AGENT, url):
        #         print(f"{url} DISALLOWED IN robots")
        #         return False
        elif re.match(ALLOWED_DOMAINS[3], domain):
            if not STAT_RFP.can_fetch(USER_AGENT, url):
                print(f"{url} DISALLOWED IN robots")
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
            print(f'{url} has bad extension NOT VALID')
            return False
        
        if re.search(r"\d{4}-\d{2}-\d{2}", path) or re.search(r"date=\d{4}-\d{2}-\d{2}", query):  # calendar pages
            print(f'{url} contains calendar NOT VALID')
            return False 
        
        if re.search(r"(tab_files=|do=media|image=|do=diff)", query): # media/dynamic/diff pages
            return False 
        
        if re.search(r"[?&]page=\d+", parsed.query):    #ignore pagination links
            return False  

        if re.search(r"session|sid|track|utm_", parsed.query, re.IGNORECASE):   # ignore tracking params
            return False
        
        if repeated_segments(path):
            return False

        return True


    except TypeError:
        print ("TypeError for ", parsed)
        raise
