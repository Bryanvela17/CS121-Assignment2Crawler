import re
from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup  ## This is a library for web crawling html or xlm documents
import nltk  # Manually Added
from nltk.corpus import stopwords  # Manually Added
from collections import defaultdict  # Manually Added
from urllib.robotparser import RobotFileParser # Manually added

nltk.download('stopwords')  # Downloads a list of stopwords to be used
stop_Words = set(stopwords.words('english'))  # Downloads the english version
count_Words = defaultdict(int)
words_In_Page = {}
# Extra stop words that aren't in the download
add_These_Words = {"a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
                   "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
                   "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
                   "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't",
                   "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his",
                   "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its",
                   "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
                   "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
                   "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
                   "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
                   "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
                   "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who",
                   "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
                   "yours", "yourself", "yourselves"}
stop_Words = stop_Words.union(add_These_Words)



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

    if resp.status != 200:  # Checks to see if the status code is valid https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        return []

    if resp.raw_response is None:   # If response is empty return
        return []
    
    if not checkRobotFile(url):      # If we aren't allowed to crawl return
        return [] 
    


    listOfLinkText = checkForContent(resp)
    counter = 0
    all_Count(listOfLinkText, counter)
    print(f'\t\tURL Text ---> : {listOfLinkText}\t\t')  # Prints all valid text which can later be used to tuple url with wordset https://www.crummy.com/software/BeautifulSoup/bs4/doc/#get-text

    counter = all_Count(listOfLinkText, counter)            # Gets the number of words per page, and starts tallying all total words
    words_In_Page[counter] = url                            # Assigns and maps the number of words per page to each specific url
    listOfLinks = getAllUrls(listOfLinks)                   # Gets all links within a url (recurrsive/inception like behavior)
    listOfLinks = convertToAbsolute(url, listOfLinks)       # Converts all urls to absolute
    print(f'\t\tThis URL: {url} has this many words ---> len{listOfLinkText}\t\t')
    

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


def checkForContent(resp) -> list[str]:
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')  # Creating a soup object to begin breaking down
    # the url
    listOfLinkText = soup.get_text()  # Gets all the legit text from the website
    listOfLinkText = listOfLinkText.strip().split()  # Removes whitespace, and splits into a list of words
    return listOfLinkText


def all_Count(listofLinkText, counter) -> int:
    for word in listofLinkText:
        word = word.lower()
        if word not in stop_Words:
            count_Words[word] += 1
            counter += 1
    return counter

def getAllUrls(listOfLinks) -> list:
    for everyLink in soup.findAll('a')
        listOfLinks.append(everyLink.get('href'))
    return listOfLinks

def convertToAbsolute(url, urlList) -> list[str]:
    completeUrls = []
    for link in urlList:
        complete_link = urljoin(url, link)  # Combines the link with the regular url to get abso link
        parsedLink = urlparse(complete_link) # Parse the abso link to verify that it's abosulte
        if parsedLink.scheme:
            completeUrls.append(complete_link)  # If it's complete just add
        elif parsedLink.netloc:
            completeUrls.append(f"http{complete_link}") # If it's partial, just add http
        else:
            completeUrls.append(f"{url.rstrip('/')}/{complete_link}")   # If it's relative, strip thisLink and add currLink to the end
    completeUrls = [urldefrag(u).url for u in completeUrls]
    completeUrls = list(set(completeUrls))
    return completeUrls

def checkRobotFile(url):
    rp = RobotFileParser()
    rp.set_url(urljoin(url, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        return True
    return rp.can_fetch("*", url)