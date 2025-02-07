import re
from urllib.parse import urlparse, urldefrag, urlunparse
import hashlib  # Checksum
import logging
from bs4 import BeautifulSoup  # Parse HTML


# Configure logging to write to a file
logging.basicConfig(filename="output.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

CHECKSUMS = set()
URLS = set()


def remove_trailing_slash(url: str) -> str:
    parsed = urlparse(url)
    new_parsed = (parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), parsed.params, parsed.query, parsed.fragment)
    return urlunparse(new_parsed)


def get_md5_checksum(text: str):
    return hashlib.md5(text.encode()).hexdigest()



# https://wics.ics.uci.edu/events/category/social-gathering/2020-09/
def is_close_path(url: str) -> bool:
    date_pattern = re.compile(r'(\b\d{4}-\d{2}-\d{2}\b)')
    date_pattern2 = re.compile(r'(\b\d{4}-\d{2}\b)')
    match = date_pattern.search(url) or date_pattern2.search(url)
    if match:
        base_url = url.replace(match.group(0), "DATE")  # Normalize by replacing the date
        if base_url in URLS:
            logging.info(f"SIMILAR URL: {url}")
            return True
        URLS.add(base_url)
    return False


def scraper(url: str, resp) -> list:
    if resp is None or resp.raw_response is None:
        logging.info(f"RESPONSE IS NONE, URL: {url}")
        return list()

    # Need to check robots.txt

    # Redirects
    if resp.status == 300:
        print(f"REDIRECT: {url}")
        logging.info(f"REDIRECT: {url}")
        return list()

    # Errors
    if resp.status != 200:
        logging.info(f"ERROR, Status:{resp.status} URL:{url}")
        return list()

    # Parse html, get text, and calculate checksum
    soup = BeautifulSoup(resp.raw_response.content, "html.parser")
    text = soup.get_text()
    checksum = get_md5_checksum(text)

    # Don't scrape pages with duplicate checksum
    if checksum in CHECKSUMS:
        print(f"DUPLICATE, Checksum: {checksum}, URL: {url}")
        logging.info(f"DUPLICATE, Checksum: {checksum}, URL: {url}")
        return list()
    CHECKSUMS.add(checksum)

    links = extract_next_links(url, resp)
    valid_links = []
    for link in links:
        if is_valid(link) and not is_close_path(link):
            valid_links.append(link)
            # print(f"Valid link: {link}")
            logging.info(f"Valid link: {link}")
    # print(f"HERE ARE THE URLS: {urls}")
    # print(f"THESE ARE THE CHECKSUMS: {checksums}")
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
        # De-frag the url
        # clean_url, fragment = urldefrag(a)

        # Avoid the same exact url
        # if clean_url != url:
        # Add only urls, not triggers
        hyperlink_url = a["href"]
        parsed_url = urlparse(hyperlink_url)  # These two lines might be unnecessary
        if parsed_url.scheme in {"http", "https"}:  # ^^
            hyperlinks.append(remove_trailing_slash(hyperlink_url))
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
        if remove_trailing_slash(url) in URLS:
            return False
        URLS.add(remove_trailing_slash(url))

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
        print("TypeError for ", parsed)
        raise
