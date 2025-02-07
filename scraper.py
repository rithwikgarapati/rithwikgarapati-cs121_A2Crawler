import re
from urllib.parse import urlparse, urldefrag, urlunparse
import hashlib  # Checksum
import logging
from bs4 import BeautifulSoup  # Parse HTML

"""
1. checksum for detecting duplicate pages - JEREMY
2. How many unique pages did you find? - RITHWIK
3. What is the longest page in terms of the number of words? - RITHWIK
4. What are the 50 most common words in the entire set of pages crawled under these domains ? - Assignment 1 - RITHWIK
5. How many subdomains did you find in the ics.uci.edu domain ex: hpi.ics.uci.edu - RITHWIK
6. Detect redirects and if the page redirects your crawler, index the redirected content - JEREMY
7. Detect and avoid dead URLs that return a 200 status but no data - JEREMY
8. Detect and avoid crawling very large files, especially if they have low information value (avoid pages that are
    too long and pages too short - threshold) - RITHWIK
9. You should write simple automatic trap detection systems based on repeated URL patterns and/or (ideally) webpage content similarity repetition over a certain amount of chained pages (the threshold definition is up to you!).
"""


class Statistics:
    def __init__(self):
        self.unique_urls = set()
        self.longest_page = {
            "words": 0,
            "url": ""
        }

    def update_longest_page(self, num_words, urls):
        if num_words > self.longest_page["words"]:
            self.longest_page["words"] = num_words
            self.longest_page["urls"] = urls

    def update_unique_urls(self, url):
        self.unique_urls.add(url)

    def get_num_unique_urls(self):
        return len(self.unique_urls)

    def get_unique_urls(self):
        return self.unique_urls


# URL stats to answer all questions
url_stats = Statistics()

# Configure logging to write to a file
logging.basicConfig(filename="output.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CHECKSUMS = set()


def remove_trailing_slash(url: str) -> str:
    parsed = urlparse(url)
    new_parsed = (parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), parsed.params, parsed.query, parsed.fragment)
    return urlunparse(new_parsed)


def get_md5_checksum(text: str):
    return hashlib.md5(text.encode()).hexdigest()


# To detect loops in calenders.
def is_close_path(url: str) -> bool:
    date_pattern = re.compile(r'(\b\d{4}-\d{2}-\d{2}\b)')
    match = date_pattern.search(url)
    if match:
        base_url = url.replace(match.group(0), "DATE")  # Normalize by replacing the date
        if base_url in url_stats.get_unique_urls():
            logging.info(f"SIMILAR URL: {url}")
            return True
        url_stats.update_unique_urls(base_url)
    return False


def scraper(url: str, resp) -> list:
    if resp is None or resp.raw_response is None:
        return list()

    # Need to check robots.txt

    # Need to check for close path
    # if is_close_path(url):
    #     logging.info(f"PATH TOO SIMILAR: {url}")
    #     return list()

    # Redirects
    if resp.status == 300:
        print(f"REDIRECT: {url}")
        logging.info(f"REDIRECT: {url}")
        return list()

    # Errors
    if resp.status != 200:
        return list()

    if resp.raw_response is None:
        return list()

    # Parse html, get text, and calculate checksum
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    text = soup.get_text()
    checksum = get_md5_checksum(text)

    # Don't scrape pages with duplicate checksum
    if checksum in CHECKSUMS:
        print(f"Checksum: {checksum}, URL: {url}")
        logging.info(f"Checksum: {checksum}, URL: {url}")
        return list()
    CHECKSUMS.add(checksum)

    links = extract_next_links(url, resp)

    valid_links = []
    for link in links:
        if is_valid(link) and not is_close_path(link):
            valid_links.append(link)
            logging.info(f"Valid link: {link}")

            # to get all unique urls
            url_stats.update_unique_urls(link)

            # to get longest 




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
        
        hyperlink_url = a["href"]
        # De-frag the url
        defragmented_url, fragment = urldefrag(hyperlink_url)
        parsed_url = urlparse(hyperlink_url)
        # Add only urls, not triggers
        if parsed_url.scheme in {"http", "https"}:
            hyperlinks.append(remove_trailing_slash(defragmented_url))
            # print(f"Hyperlink: {hyperlink_url}")

    return hyperlinks


def is_valid(url: str) -> bool:
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # url must be in uci domain
        if (parsed.hostname is None
                or not (parsed.hostname.endswith("ics.uci.edu")
                        or parsed.hostname.endswith("cs.uci.edu")
                        or parsed.hostname.endswith("informatics.uci.edu")
                        or parsed.hostname.endswith("stat.uci.edu"))):
            return False
        # No duplicate urls
        if remove_trailing_slash(url) in url_stats.get_unique_urls():
            return False
        url_stats.update_unique_urls(remove_trailing_slash(url))

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
        print("TypeError for ", url)
        raise



