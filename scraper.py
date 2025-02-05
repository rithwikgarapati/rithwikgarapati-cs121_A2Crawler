import re
from urllib.parse import urlparse, urldefrag

# Parses HTML
from bs4 import BeautifulSoup


def scraper(url, resp):
    print("Extracting starting")
    links = extract_next_links(url, resp)
    print("Extracting done")
    print("Link validation starting")
    valid_links = [link for link in links if is_valid(link)]
    print("Link validation done")
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
        if urlparse(hyperlink_url).scheme in {"http", "https"}:
            hyperlinks.append(hyperlink_url)
            print(f"Hyperlink: {hyperlink_url}")

    return hyperlinks


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        # url must be in uci domain
        if not (parsed.hostname.endswith("ics.uci.edu")
                or parsed.hostname.endswith("cs.uci.edu")
                or parsed.hostname.endswith("informatics.uci.edu")
                or parsed.hostname.endswith("stat.uci.edu")):
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
        print("TypeError for ", parsed)
        raise
