import re
from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup  ## This is a library for web crawling html or xlm documents
import nltk  # Manually Added
from nltk.corpus import stopwords  # Manually Added https://pythonspot.com/nltk-stop-words/ 
from collections import defaultdict  # Manually Added
from difflib import SequenceMatcher # Manually Added https://docs.python.org/3/library/difflib.html 
from urllib.robotparser import RobotFileParser # Manually added https://docs.python.org/3/library/urllib.robotparser.html 

nltk.download('stopwords')  # Downloads a list of stopwords to be used
stop_Words = set(stopwords.words('english'))  # Downloads the english version
count_Words = defaultdict(int)
words_In_Page = {}
uniqueCounter = []
previousListOfStrings = []
totalPageCounter = 0
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
    url = urljoin(resp.url,url)     # Convert rel to abs
    listOfLinks = []  # This is where the list of hyperlinks will go
    parsedText = []  # Empty string needed for adding all the words in each url
    
    if not decideWhetherToExtractInfo(resp, url):
        return []
    
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')  # Creating a soup object to begin breaking down
    allText = soup.get_text()
    parsedText = checkForContent(allText)
    if checkForTrapsAndSimilarity(allText):                # If bool value of resultOfTrap is true, then return and exit function
        print(f'****************___Avoided Trap From URL____******************')
        print(f'***************___Check Url Above Confirm____******************')
        return []
    counter = 0
    #print(f'\t\tURL Text ---> : {parsedText}\t\t')  # Prints all valid text which can later be used to tuple url with wordset https://www.crummy.com/software/BeautifulSoup/bs4/doc/#get-text
    counter = all_Count(parsedText, counter)            # Gets the number of words per page, and starts tallying all total words
    words_In_Page[counter] = url                            # Assigns and maps the number of words per page to each specific url
    listOfLinks = getAllUrls(soup)                   # Gets all links within a url (recurrsive/inception like behavior)
    #checkForRedirection(listOfLinks, url, resp)
    print(f'-->->->-->->-->->---> This URL --->: {url} has this many words ---> {counter} <-')
    #for token, freq in count_Words.items():
    #    print(f"{token} -> {freq}")
    return listOfLinks


ALLOWED_URLS = [r'^.+\.ics\.uci\.edu(/.*)?$', r'^.+\.cs\.uci\.edu(/.*)?$', r'^.+\.informatics\.uci\.edu(/.*)?$', r'^.+\.stat\.uci\.edu(/.*)?$']
ALLOWED_URL_REGEXES = [re.compile(regex) for regex in ALLOWED_URLS]
ALPHANUMERICAL_WORDS = re.compile('[a-zA-Z]+')
BAD_URL = ["pdf", "ppt", "pptx", "png", "zip", "jpeg", "jpg", "ppsx", "war", "img", "apk"] # maybe add war, img, apk

def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    global totalPageCounter
    try:
        bad_url_found = False
        parsed = urlparse(url)
        if parsed is None:  # If parsed object is empty, exit and return false
            return False
        if parsed.scheme not in set(["http", "https"]):  # These are the only allowed URLS (domains)
            return False
        if not any(regex.match(parsed.netloc) for regex in
                   ALLOWED_URL_REGEXES):  # This returns false for a incompatibe url
            return False
        for bad_url in BAD_URL:
            if bad_url in url:
                bad_url_found = True
                break
        if bad_url_found:
            return False
        if not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|jpeg|jpg|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            totalPageCounter += 1
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|jpeg|jpg|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


def decideWhetherToExtractInfo(resp, url) -> bool:
    if resp.status != 200:  # Checks to see if the status code is valid https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        return False

    if resp.raw_response is None:   # If response is empty return
        return False

    checkForType = resp.raw_response.headers.get("Content-Type", "")
    if not re.match(r"text/.*", checkForType) or not "utf-8" in checkForType.lower():   # If header does not specify test or utf-8 skip
        return False

    if not check_URLSize(url, resp, minSize = 500, mbSize = (35 * 1024 * 1024)):       # If page is bigger than 30MB Skip
        return False

    if not checkRobotFile(url):      # If we aren't allowed to crawl return
        return False 
    
    return True


def checkForContent(allText) -> list[str]:
    parsedText = allText.strip().split()  # Removes whitespace, and splits into a list of words
    return parsedText


def all_Count(parsedText, counter) -> int:
    for word in parsedText:             # For every word in the url that we find
        word = word.lower()             # make it lower case for consistency
        sieveTheseWords = re.findall(ALPHANUMERICAL_WORDS, word)    # Sieve these words through the regex
        for w in sieveTheseWords:
            if len(w) >= 2:               # if it isn't just one letter
                if w not in stop_Words:  # If it isn't a word in the stop woirds
                    count_Words[w] += 1  # incriment the amount of times we've seen this word
                    counter += 1            # Return for counter of words in this url
    return counter
    
runningTotal = 0
def getAllUrls(soup) -> list:
    noDuplicateLinks = set()        # Create a set to get rid of duplicate urls
    global runningTotal
    for item in soup.findAll('a'):  # Use soup to iterate over a given url 
        item = item.get('href')     # Get the url (item)
        if item:                    # If there exists a url
            fragment = urlparse(item).fragment  # If there exists a frag
            if fragment:
                item = item.split("#")[0]   # Remove frag
            global uniqueCounter
            if item not in uniqueCounter:   # If url was not seen before, add to uniqueUrlCounter
                uniqueCounter.append(item)
                runningTotal += 1
                #print(f"-->->->-->->-->->--->Found {runningTotal} unique URLs")
            noDuplicateLinks.add(item)      
    return list(noDuplicateLinks)   # Return list of links from set


def checkRobotFile(url) -> bool:
    rp = RobotFileParser()                  # Creates a robotFileParser object
    rp.set_url(urljoin(url, "/robots.txt")) # Creates a temporary url with the /robots.txt appened to the end
    try:
        rp.read()                           # Read the file
    except Exception:                       # If no robots.txt file, go ahead and crawl anyway
        return True                     
    return rp.can_fetch("*", url)           # If we are allowed to crawl return true, else false


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
    #print(completeUrls)
    #global uniqueCounter
    #if url not in uniqueCounter:
    #    uniqueCounter.append(url)
    return completeUrls

'''
/*********************************************************************************************
*                                           Citation:
*    Title: Assignment 2 - checkForTrapsAndSimilarity method 
*    Author: Python Software Foundation
*    Date Accessed: 04/28/23
*    Code version: Python
*    Availability: https://docs.python.org/3/library/difflib.html#sequencematcher-examples 
*    Obtained: TBD Need TO DO 
**********************************************************************************************/
'''
def checkForTrapsAndSimilarity(currentTextFoundInUrl) -> bool:
    global previousListOfStrings
    if previousListOfStrings:
        s = SequenceMatcher(lambda x: x == " ", currentTextFoundInUrl, previousListOfStrings)
        percentageSimilar = s.ratio()
        if percentageSimilar >= .90: # Changed to 0.9 for Deployment Run # 2
            return True
        else:
            previousListOfStrings = currentTextFoundInUrl
            return False
    else:
        previousListOfStrings = currentTextFoundInUrl
        return False

def count_unique_pages(words_In_Page) -> int:
    uni_Links = set()
    for Link in words_In_Page.values(): # go through the links in the words_In_Page dict
        #makes a new link without the fragment
        parse_Link = urlparse(Link)
        uni_Link = parse_Link.scheme + "://" + parse_Link.netloc + parse_Link.path
        uni_Links.add(uni_Link) #puts the new link in the set of unique links
    return len(uni_Links)


def longest_page_words(words_In_Page) -> int:
    numberOfWords = max(words_In_Page.keys())
    return numberOfWords

def longest_page(numberOfWords, words_In_Page) -> str:
    longestPage = words_In_Page[numberOfWords]
    return longestPage


def most_common_words(count_Words):
    sortedList = sorted(count_Words.items(), key=lambda x: x[1], reverse=True)
    mostCommon = {entry[0]: entry[1] for entry in sortedList[:50]}
    return mostCommon
    

def getSubDomains(words_In_Page):
    subdomain_counts = defaultdict(int)
    subdomain_pages = defaultdict(set)

    for url in words_In_Page.values():
        parsed_url = urlparse(url)
        if parsed_url.netloc.endswith('.ics.uci.edu'):
            subdomain = parsed_url.netloc.split(".")[0]
            subdomain_counts[subdomain] += 1
            subdomain_pages[subdomain].add(url)

    # Sort the subdomains by the number of unique pages in descending order
    sorted_subdomains = sorted(subdomain_counts.items(), key=lambda x: (x[0].lower(), x[1]), reverse=False)
    
    # Return a list of tuples with the URL and count for each subdomain
    return [(f'https://{subdomain}.ics.uci.edu', len(subdomain_pages[subdomain])) for subdomain, _ in sorted_subdomains]

def check_URLSize(url, resp, minSize = 500, mbSize = (35 * 1024 * 1024)):
    if len(resp.raw_response.content) < minSize:
        print(f'Skipping {url}: page size of: {len(resp.raw_response.content)} bytes is too small!')
        return False
    #page is too large
    if len(resp.raw_response.content) > mbSize:
        print(f'Skipping {url}: page size of: {len(resp.raw_response.content)} bytes is too large!')
        return False

    #page can be crawled
    return True


def printCrawlerSummary():
    file = open('results.txt', 'w')
    file.write(f'\t\t\t\t\tCrawler Report\t\t\t\t\t\n')
    file.write("Members ID Numbers: 87866641, 18475327, 92844565, 86829976\n\n")
    file.write(f'\t\t\tTotal Number of Unique Pages: {totalPageCounter} with new counter\n\n')
    file.write(f'\t\t\tTotal Number of Unique Pages: {len(uniqueCounter)} No change\n\n')
    longestNumOfWords = longest_page_words(words_In_Page)
    nameOfUrlWithLongestNumOfWords = longest_page(longestNumOfWords, words_In_Page)
    file.write(f'\t\t\tThis url: {nameOfUrlWithLongestNumOfWords} has the most words with: {longestNumOfWords} words\n\n')
    topFiftyMostCommonWords = most_common_words(count_Words)
    for word, count in topFiftyMostCommonWords.items():
        file.write(f'\t\t\t{word} -> {count}\n')
    file.write('\n')
    subDomainsOfICS = getSubDomains(words_In_Page)
    output_lines = [f"\t\t\t{url}, {count}" for url, count in subDomainsOfICS]
    file.write('\n'.join(output_lines))
    file.write(f'\t\t\t\t\tEnd Crawler Report\t\t\t\t\t\n')
    file.close()
