import re
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup

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

def scraper(url, resp):
    links = extract_next_links(url, resp)
    valid_links = [link for link in links if is_valid(link)]
    print(valid_links)
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

    parsed_content = BeautifulSoup(resp.raw_response.content, 'html.parser')
    res = [link.get('href') for link in parsed_content.find_all('a')]

    # de-fragment the urls
    for i in range(len(res)):
        defragmented_url, fragment = urldefrag(res[i])
        res[i] = defragmented_url

    return res


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    allowed_domains = {"ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"}
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        valid_domain = False
        for domain in allowed_domains:
            if parsed.hostname.endswith(domain):
                valid_domain = True
                break

        return valid_domain and not re.match(
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


# TEST FUNCTION - DELETE LATER
def test_urls():
    test_cases = [
        "https://www.ics.uci.edu/path",
        "http://faculty.cs.uci.edu/profile",
        "https://www.informatics.uci.edu/",
        "https://www.stat.uci.edu/research",
        "https://invalid-domain.com",
        "malformed-url",
        "https://www.ics.uci.edu/~eppstein/163/",
        "https://cs.ics.uci.edu/research-areas/"
    ]

    for url in test_cases:
        print(f"{url}: {is_valid(url)}")




















if __name__ == '__main__':
    test_urls()
