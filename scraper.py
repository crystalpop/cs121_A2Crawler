import re
from urllib.parse import urlparse, urldefrag, urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import numpy as np


ALLOWED_DOMAINS = [
    r'.*\.ics\.uci\.edu',
    r'.*\.cs\.uci\.edu',
    r'.*\.informatics\.uci\.edu',
    r'.*\.stat\.uci\.edu'
]

SIMHASH_THRESHOLD = 4
simhash_set = set() 

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
    # Ignore any urls that return error codes
    if resp.status >= 400:
        return []
    links = extract_next_links(url, resp)
    valid_links = set()
    # We only want to scrape valid links
    for link in links:
        if is_valid(link):
            valid_links.add(link)
    # Analyzing the url if valid for final output
    if is_valid(url):
        process_info(url, resp)
            
    return list(valid_links)


"""
Source for absolute path resolution : https://blog.finxter.com/scraping-the-absolute-url-of-instead-of-the-relative-path-using-beautifulsoup/
"""
def extract_next_links(url, resp):
    result = set()

    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # Check for valid status codes & existence of raw_response
    if (resp.status >= 200 and resp.status < 400) and resp.raw_response:
        html_doc = resp.raw_response.content
        # Make sure page has content
        if len(html_doc) > 0:
            soup = BeautifulSoup(html_doc, "lxml")
            text = soup.get_text()

            # Checking for large file & low information value
            if "Content-Length" in resp.raw_response.headers:
                file_bytes = int(re.sub(r'\D', '', resp.raw_response.headers["Content-Length"]))
                # Thresholds are 5 MB and 250 characters
                if file_bytes > 3000000 and len(text) < 250:
                    # print("*****LARGE FILE LOW INFO, SKIP*****")
                    return []
                    
            # Checking for duplicates
            simhash = compute_simhash(text)
            if is_near_duplicate(simhash):
                return []
            # Adding to simhash_set for future reference if duplicate not found
            simhash_set.add(tuple(simhash))
            
            # Threshold for low text data is 250 characters (about 50 words)
            if len(text) >= 250:
                for a in soup.find_all('a'):
                    href = a.get('href')
                    # resolve possible relative url to absolute url
                    abs_url = urljoin(url, href) 
                    # defragment and add to result
                    defragged = urldefrag(abs_url)[0]
                    result.add(defragged)

    elif resp.status >= 600 and resp.status <= 606:
        print(f"***********\nERROR: {resp.error}\n*************")

    return list(result)



"""SIMHASH METHODS"""

def compute_simhash(text, bit_length=64):
    try:
        vector = np.zeros(bit_length)
        with open("content.txt", "w") as file:
            file.write(text)
        words = tokenize("content.txt")
        for word in words:
            hash_value = hash(word) & ((1 << bit_length) - 1)
            binary_array = np.array([1 if (hash_value >> i) & 1 else -1 for i in range(bit_length)])
            vector += binary_array

        return np.where(vector >= 0, 1, 0)
    except Exception as e:
        print(f"Error saving content in simhash to file...: {e}")

def hamming_distance(h1, h2):
    return np.sum(h1 != h2)

def is_near_duplicate(simhash):
    for existing_hash in simhash_set:
        if hamming_distance(np.array(existing_hash), simhash) < SIMHASH_THRESHOLD:
            # print(f"--------FOUND NEAR DUPLICATE--------")
            return True
    return False


"""ANALYSIS & FINAL REPORT METHODS"""
    
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
            if len(token) >= 3 and token.isalpha():
                token_frequencies[token] = 1
        else:
            token_frequencies[token] += 1
    return token_frequencies

def process_info(url, resp):

    # STRIP these just to be safe 
 
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
            outputfile.write(f"Number of unique pages: {len(url_dict)}\n")

            sorted__url_word_count_dict = dict(sorted(url_word_count_dict.items(), key=lambda item: item[1], reverse=True))
            longest_page = next(iter(sorted__url_word_count_dict), None)
            words_in_longest_page = sorted__url_word_count_dict.get(longest_page, 0)

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

            for key in sorted(subdomain_dict):
                count = len(subdomain_dict[key])
                outputfile.write(f"{key}: {count}\n")


    except Exception as e:
        print(e)


"""VALIDITY TESTING METHODS"""

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
                # print(f"Found repeated group {group} in segments: {segments}")
                return True
    return False


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        # print(f"checking validity of {url}")
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path
        query = parsed.query

        if parsed.scheme not in set(["http", "https"]):
            return False
        
        if not any(re.match(pattern, domain) for pattern in ALLOWED_DOMAINS):
            # print(f"{url} bad domain NOT VALID")
            return False

        if re.search(
            r"\.(css|js|bam|war|bmp|gif|jpe?g|lif|ico"
            + r"|png|img|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|mpg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|apk|sql|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", 
            parsed.path.lower() + parsed.query.lower()):
            # print(f'{url} has bad extension NOT VALID')
            return False

        # Check for individual commits in gitlab
        if re.search(r"gitlab.ics.uci.edu", domain) and (re.search(r"/(commit|tree)/", path)):
            # print(f'{url} gitlab NOT VALID')
            return False
        
        # Check for calendar pages
        if re.search(r"\d{4}-\d{2}-\d{2}", path) or re.search(r"\d{4}-\d{2}", path) or re.search(r"date=\d{4}-\d{2}-\d{2}", query) or re.search(r"ical=1", query):
            # print(f'{url} contains calendar NOT VALID')
            return False 

        # Try to avoid large datasets
        if re.search(r"/(datasets|dataset|files)/", path):
            # print(f'{url} large data set NOT VALID')
            return False
        
        # Check for media/dynamic/diff/revision pages
        if re.search(r"(tab_files=|do=media|image=|do=diff|action=diff|version=|ver=|do=edit|rev=|do=revisions)", query): 
            return False 
        
        # Avoid pagination links
        if re.search(r"[?&]page=\d+", parsed.query):    
            return False  

        # Avoid tracking params
        if re.search(r"session|sid|track|utm_", parsed.query, re.IGNORECASE):   
            return False
        
        # Avoid repeated patterns in paths
        if repeated_segments(path):
            return False

        return True


    except TypeError:
        print ("TypeError for ", parsed)
        raise
