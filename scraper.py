import re
from urllib.parse import urlparse, urldefrag, urlunparse, parse_qs
import hashlib  # Checksum
import logging
from bs4 import BeautifulSoup  # Parse HTML

import atexit
from tokenize_functions import tokenize, compute_word_frequencies, stopwords
from collections import defaultdict

"""
1. checksum for detecting duplicate pages - JEREMY
2. How many unique pages did ou find? - RITHWIK
3. What is the longest page in terms of the number of words? - RITHWIK
4. What are the 50 most common words in the entire set of pages crawled under these domains ? - Assignment 1 - RITHWIK
5. How many subdomains did you find in the ics.uci.edu domain ex: hpi.ics.uci.edu - RITHWIK
6. Detect redirects and if the page redirects your crawler, index the redirected content - JEREMY
7. Detect and avoid dead URLs that return a 200 status but no data - JEREMY
8. Detect and avoid crawling very large files, especially if they have low information value (avoid pages that are
    too long and pages too short - threshold) - RITHWIK
9. You should write simple automatic trap detection systems based on repeated URL patterns and/or (ideally) webpage content similarity repetition over a certain amount of chained pages (the threshold definition is up to you!).
10. Finish relative URLs - RITHWIK.
11. redirects - 300, follow the redirect and index that

"""


class Statistics:
    def __init__(self):
        self.unique_urls = set()
        self.longest_page = {
            "words": 0,
            "url": ""
        }
        self.ics_subdomains = defaultdict(int)
        self.frequent_50_words = dict()

    def get_num_unique_urls(self):
        return len(self.unique_urls)

    def get_unique_urls(self):
        return self.unique_urls

    def update_longest_page(self, num_words, url):
        if num_words > self.longest_page["words"]:
            self.longest_page["words"] = num_words
            self.longest_page["url"] = url

    def update_unique_urls(self, url):
        self.unique_urls.add(url)

    def check_and_update_ics_domain(self, url):
        parsed = urlparse(url)
        if parsed.netloc.endswith("ics.uci.edu"):
            self.ics_subdomains[parsed.netloc] += 1

    def update_frequent_words(self, tokens):
        word_frequencies = compute_word_frequencies(tokens)
        for key, value in word_frequencies.items():
            if key not in stopwords:
                self.frequent_50_words[key] = self.frequent_50_words.get(key, 0) + value

    def get_top_50_frequent_words(self):
        sorted_words = sorted(self.frequent_50_words, key=lambda k: self.frequent_50_words[k], reverse=True)
        if len(sorted_words) >= 50:
            return sorted_words[:50]
        else:
            return sorted_words

    def get_final_statistics(self):
        return {
            "num_unique_urls": len(self.unique_urls),
            "longest_page": self.longest_page["url"],
            "ics_subdomain_count": sorted(self.ics_subdomains.items()),
            "top_50_words": self.get_top_50_frequent_words()
        }


# URL stats to answer all questions
url_stats = Statistics()

# Configure logging to write to a file
logging.basicConfig(filename="output.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CHECKSUMS = set()


def on_exit():
    logging.info(url_stats.get_final_statistics())
    logging.info("PROGRAM END")


atexit.register(on_exit)


def remove_trailing_slash(url: str) -> str:
    parsed = urlparse(url)
    new_parsed = (parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), parsed.params, parsed.query, parsed.fragment)
    return urlunparse(new_parsed)


def get_md5_checksum(text: str):
    return hashlib.md5(text.encode()).hexdigest()


# https://wics.ics.uci.edu/events/category/social-gathering/2020-09/
# Also need to skip ical
# https://ics.uci.edu/event/state-of-the-informatics-department?ical=1

# To detect loops in calenders.
def is_close_path(url: str) -> bool:
    date_pattern = re.compile(r'(\b\d{4}-\d{2}-\d{2}\b)')
    date_pattern2 = re.compile(r'(\b\d{4}-\d{2}\b)')
    match = date_pattern.search(url) or date_pattern2.search(url)
    if match:
        base_url = url.replace(match.group(0), "DATE")  # Normalize by replacing the date
        if base_url in url_stats.get_unique_urls():
            logging.info(f"SIMILAR URL: {url}")
            return True
        url_stats.update_unique_urls(base_url)
    return False


# Don't scrape large files and files with low information value
def low_information_or_large_file(resp, text, tokens) -> bool:
    threshold = 1 * 1024 * 1024  # 1MB page is big
    num_words = len(tokens)
    unique_word_ratio = len(set(tokens)) / num_words if num_words > 0 else 0
    print(f"filesize:{len(resp.raw_response.content)}")
    print(f"{resp.url}, {unique_word_ratio}")

    # large page
    if len(resp.raw_response.content) > threshold:
        print(f"here: threshold{len(resp.raw_response.content)}")
        return True

    # low information
    if num_words < 50 or unique_word_ratio < 0.1:
        print(f"second condition")
        return True

    return False


def scraper(url: str, resp) -> list:

    # logging.info(f"Scraped URL: {url}")

    if resp is None or resp.raw_response is None:
        logging.info(f"RESPONSE IS NONE, URL: {url}")
        return list()

    # Redirects
    if 300 <= resp.status <= 399:
        logging.info(f"REDIRECT, Status: {resp.status}, URL: {url}")
        # new_url = resp.raw_response.headers.get("Location")
        # if not new_url:
        #     logging.info(f"REDIRECT WITHOUT LOCATION HEADER, Status: {resp.status}, URL: {url}")
        #     return list()

        # logging.info(f"REDIRECT DETECTED, Status: {resp.status}, Redirecting {url} → {new_url}")

        # # Fetch the new URL's content
        # redirected_resp = requests.get(new_url, allow_redirects=True)  # Follow redirects automatically

        # # Recursively call scraper with new response
        # return scraper(new_url, type("Response", (object,), {"status": redirected_resp.status_code, "raw_response": redirected_resp}))


    # Errors
    if not 200 <= resp.status <= 299:
        logging.info(f"ERROR, Status: {resp.status} URL:{url}")
        return list()

    # Parse html, get text, and calculate checksum
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    text = soup.get_text()
    checksum = get_md5_checksum(text)
    tokens = tokenize(text)

    # Don't scrape pages with duplicate checksum
    if checksum in CHECKSUMS:
        logging.info(f"DUPLICATE PAGE, Checksum: {checksum}, URL: {url}")
        return list()
    CHECKSUMS.add(checksum)

    # Don't scrape large or small files, and files with low information value
    if low_information_or_large_file(resp, text, tokens):
        print(f"low info or large file: {url}")
        logging.info(f"low info or large file: {url}")
        return []

    # COMPUTING STATISTICS TO ANSWER THE QUESTIONS
    url_stats.update_unique_urls(url)
    url_stats.update_longest_page(len(tokens), url)
    url_stats.update_frequent_words(tokens)
    url_stats.check_and_update_ics_domain(url)

    print(f"url:{url}")

    links = extract_next_links(url, resp)

    valid_links = []
    for link in links:
        if is_valid(link) and not is_close_path(link) and link not in url_stats.get_unique_urls():
            url_stats.update_unique_urls(link)
            valid_links.append(link)
            # logging.info(f"Valid link: {link}")

    return valid_links


def extract_next_links(url: str, resp) -> list:
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    if resp.status != 200:
        return list()

    # Parse the response content
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")

    # Extract all hyperlinks
    hyperlinks = []
    for a in soup.find_all('a', href=True):
        # Add only urls, not triggers
        hyperlink_url = a["href"]
        # De-frag the url
        defragmented_url, fragment = urldefrag(hyperlink_url)
        parsed_url = urlparse(defragmented_url)
        # Add only urls, not triggers
        if parsed_url.scheme in {"http", "https"}:
            hyperlinks.append(remove_trailing_slash(defragmented_url))

    return hyperlinks


def is_valid(url: str) -> bool:
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # Check for correct hostname

        # url must be in uci domain
        if (parsed.hostname is None
                or (parsed.hostname.endswith("cecs.uci.edu")
                    or parsed.hostname.endswith("eecs.uci.edu"))
                or not (parsed.hostname.endswith("ics.uci.edu")
                        or parsed.hostname.endswith("cs.uci.edu")
                        or parsed.hostname.endswith("informatics.uci.edu")
                        or parsed.hostname.endswith("stat.uci.edu"))):
            return False

        # Skip ical download links
        query_params = parse_qs(parsed.query)
        if any("ical" in key.lower() for key in query_params):
            return False

        # No duplicate urls
        if remove_trailing_slash(url) in url_stats.get_unique_urls():
            return False

        return not re.match(

            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|ics|ppsx)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", url)
        raise

