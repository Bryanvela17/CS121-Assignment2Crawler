import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup  ## This is a library for web crawling html or xlm documents


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


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

    listOfLinks = []  # This is where the list of hyperlinks will go
    listOfLinkText = []  # Empty string needed for adding all the words in each url

    print(f'\t\tURL Name ---> : {url}\t\t')  # Should print the url names so that we can see what's going on and to help debug

    if 300 > resp.status >= 200:  # Checks to see if the status code is valid https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        if resp.raw_response is not None:
            listOfLinkText = raw_Response(resp)
            all_Count(listOfLinkText)
            print(f'\t\tURL Text ---> : {listOfLinkText}\t\t')  # Prints all valid text which can later be used to tuple url with wordset https://www.crummy.com/software/BeautifulSoup/bs4/doc/#get-text

    # TODO: Begin to parse for urls contained in each url (inception) and make sure they are valid_urls()

    return listOfLinks


ALLOWED_URLS = [r'^.+\.ics\.uci\.edu(/.*)?$',
                r'^.+\.cs\.uci\.edu(/.*)?$',
                r'^.+\.informatics\.uci\.edu(/.*)?$',
                r'^.+\.stat\.uci\.edu(/.*)?$']
ALLOWED_URL_REGEXES = [re.compile(regex) for regex in ALLOWED_URLS]


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed is None:  # If parsed object is empty, exit and return false
            return False
        if parsed.scheme not in set(["http", "https"]):  # These are the only allowed URLS (domains)
            return False
        if not any(regex.match(parsed.netloc) for regex in
                   ALLOWED_URL_REGEXES):  # This returns false for a incompatibe url
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|jpeg|jpg|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|ps|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


def raw_Response(resp) -> list[str]:
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')  # Creating a soup object to begin breaking down
    # the url
    listOfLinkText = soup.get_text()  # Gets all the legit text from the website
    listOfLinkText = listOfLinkText.strip().split()  # Removes whitespace, and splits into a list of words
    return listOfLinkText


def all_Count(listofLinkText) -> None:
    for word in listofLinkText:
        word = word.lower()
        if word not in stop_Words:
            count_Words[word] += 1

