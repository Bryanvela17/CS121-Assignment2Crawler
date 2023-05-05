import re
from urllib.parse import urlparse, urldefrag, urljoin # Manually Added https://docs.python.org/3/library/urllib.parse.html#module-urllib.parse 
from bs4 import BeautifulSoup  # Manually Added https://www.crummy.com/software/BeautifulSoup/bs4/doc/
import nltk  # Manually Added 
from nltk.corpus import stopwords  # Manually Added https://pythonspot.com/nltk-stop-words/ 
from collections import defaultdict  # Manually Added
from difflib import SequenceMatcher # Manually Added https://docs.python.org/3/library/difflib.html 
from urllib.robotparser import RobotFileParser # Manually added https://docs.python.org/3/library/urllib.robotparser.html 

nltk.download('stopwords')                    # Downloads a list of stopwords to be used
stop_Words = set(stopwords.words('english'))  # Downloads the english version
count_Words = defaultdict(int)                # Map between words and their frequencies
words_In_Page = {}                            # Map between number of words and a given url
uniqueCounter = []                            # Array of all urls encountered in the crawl
previousListOfStrings = []                    # Array of all words parsed in a given url for comparisson
totalPageCounter = 0                          # Counter for running total pages 

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
    url = urljoin(resp.url,url)     # Converts relative url to abso url, using the base url of the response, using urljoin
    listOfLinks = []  # This is where the list of links will go and be returned
    parsedText = []   # Empty string needed for adding all the words in each url

    if not decideWhetherToExtractInfo(resp, url):   # Decides whether to extract based on 5 if statements
        return []
    soup = BeautifulSoup(resp.raw_response.content, 'lxml')  # Creating a soup object to begin breaking down html and xml
    allText = soup.get_text()   # Gets all the text from the url; everything
    parsedText = checkForContent(allText)                  # Retrieves and removes whitespace and splits the words into a list of strings
    if checkForTrapsAndSimilarity(allText):                # If bool value of resultOfTrap is true, then return and exit function
        print(f'****************___Avoided Trap From URL____******************')
        print(f'***************___Check Url Above Confirm____******************')
        return []
    counter = 0
    counter = all_Count(parsedText, counter)         # This maps all the words with their respective frequency, but first the words are modified and sieved.
    words_In_Page[counter] = url                     # Maps the number of words to a url
    listOfLinks = getAllUrls(soup)                   # Gets all links within a url using soup and defragments
    print(f'-->->->-->->-->->---> This URL --->: {url} has this many words ---> {counter} <-')
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
        for bad_url in BAD_URL:         # Added extra protection, since I kept experiencing some files getting through
            if bad_url in url:
                bad_url_found = True
                break
        if bad_url_found:
            return False
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
    """
        Determines whether a url is to be crawled or not
        Args:
            resp: This is the response given by the caching server for the requested URL
            url: the URL that was used to get the page
        Returns:
            bool: procede to crawl == true, otherwise false
    """
    if resp.status != 200:  # Checks to see if the status code is valid https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        return False
    if resp.raw_response is None:   # If response is empty return
        return False
    checkForType = resp.raw_response.headers.get("Content-Type", "")
    if not re.match(r"text/.*", checkForType) or not "utf-8" in checkForType.lower():   # If header does not specify text or utf-8 skip
        return False
    if not check_URLSize(url, resp, minSize = 500, mbSize = (35 * 1024 * 1024)):       # If page is bigger than 30MB or smaller than 500 bytes skip
        return False
    if not checkRobotFile(url):      # If we aren't allowed to crawl return false
        return False 
    return True


def checkForContent(allText) -> list[str]:
    """
        Retrieves and removes whitespace and splits the words into a list of strings
        Args:
            allText: This contains all the words in the page without modificaiton
        Returns:
            list: list which is of type strings (all the words basically)
    """
    parsedText = allText.strip().split()  # Removes whitespace, and splits into a list of words
    return parsedText


def all_Count(parsedText, counter) -> int:
    """
        This maps all the words with their respective frequency, but first the words are modified and sieved.
        Also keeps a counter variable that counts the number of words and returns it to be attach to the respective
        url, which will also be a map.
        Args:
            parsedText: This contains a list of strings from the url to be sieved.
            counter: This running total will be used to map number of words to a url
        Returns:
            int: Running total of words
    """
    for word in parsedText:             # For every word in the url that we find
        word = word.lower()             # make it lower case for consistency (case-folding, normalization, downcasing)
        sieveTheseWords = re.findall(ALPHANUMERICAL_WORDS, word)    # Sieve these words through the regex 
        for w in sieveTheseWords:
            if len(w) >= 2:               # Lecture 13 @ 1:49 seconds via Professor Martins, sequence of tokens is 2 or more
                if w not in stop_Words:   # If it isn't a word in the stop woirds
                    if w not in count_Words:
                        count_Words[w] = 1   # Incriment the amount of times we've seen this word
                    else:
                        count_Words[w] += 1  # Incriment the amount of times we've seen this word
                    counter += 1             # Return for counter of words in this url
    return counter


runningTotal = 0
def getAllUrls(soup) -> list:
    """
        This function first creates a set to store all the links within a url using beautiful soup.
        We then take a url, check if it has a fragment within the string, if it does we remove it.
        If we have not seen this link before, we add it to an array and increase running total by 1.
        We also add this link to the set (do verify there are no duplicates)
        Finally we return the set, but turn it into a list right before we return.
        Args:
            soup: beautiful soup object to parse html and xml
        Returns:
            list: new list of urls that we will add to our queue
    """
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
            noDuplicateLinks.add(item)      # Add to our set of urls
    return list(noDuplicateLinks)   # Return list of links from set


def checkRobotFile(url) -> bool:
    """
        This function utilizes the Robot File Parser import/library such that we can determine
        whether or not we can crawl a webpage. If no robot.txt file exists return true(continue the crawl),
        otherwise, return whether or not a robot is allowed to crawl.
        Args:
            url: the URL that was used to get the page
        Returns:
            bool: procede to crawl == true, otherwise false
    """
    
    rp = RobotFileParser()                  # Creates a robotFileParser object
    rp.set_url(urljoin(url, "/robots.txt")) # Creates a temporary url with the /robots.txt appened to the end
    try:
        rp.read()                           # Read the file
    except Exception:                       # If no robots.txt file, go ahead and crawl anyway
        return True                     
    return rp.can_fetch("*", url)           # If we are allowed to crawl return true, else false


'''
/*********************************************************************************************
*                                           Citation:
*    Title: Assignment 2 - checkForTrapsAndSimilarity method 
*    Author: Python Software Foundation
*    Date Accessed: 04/28/23
*    Code version: Python
*    Availability: https://docs.python.org/3/library/difflib.html#sequencematcher-examples 
*    Obtained: I used this python resource to determine how to compare two strings and detect
               their similarity. I made sure to create my own implementation of this resource.
**********************************************************************************************/
'''
def checkForTrapsAndSimilarity(currentTextFoundInUrl) -> bool:
    """
        This function takes in the current text from the url we are currently parsing, and comparing it
        to the text from the previous url which is stored in a global variable to be used across function
        calls. We then determine how similar both text from both urls are, and if they are 90% simialar,
        we skip and assume it's too similar to crawl or is a trap.
        Args:
            currentTextFoundInUrl: all the text found in the current url we are considering to crawl.
        Returns:
            bool: procede to crawl == true, otherwise false
    """    
    global previousListOfStrings     # Stores all the text from the previous url
    if previousListOfStrings:        # If there exists text from the prev url continue the logic
        s = SequenceMatcher(lambda x: x == " ", currentTextFoundInUrl, previousListOfStrings) # Does not count whitespaces to hopefully be more precise
        percentageSimilar = s.ratio()   # Opted for ratio, instead of quick_ratio(), and really_quick_ratio() to be more accurate, takes longer however
        if percentageSimilar >= .90:    # If the percentage of similarity is over 90%, true that it's a trap or too similar
            return True
        else:
            previousListOfStrings = currentTextFoundInUrl   # Else, store the current text and place it in prev, to be used for next url
            return False
    else:
        previousListOfStrings = currentTextFoundInUrl       # If there is no prev text, store current text in prev (only used for the first run)
        return False


def check_URLSize(url, resp, minSize = 500, mbSize = (35 * 1024 * 1024)):
    """
       This function calcualtes whether or not a url has too much data and is too large to crawl, likewise,
       also calculates whether it is too small to crawl. 500 Bytes is too small, and 35MB is too large.
        Args:
            url: the URL that was used to get the page
            resp: This is the response given by the caching server for the requested URL
            minSize: 500 bytes is considered too small
            mbSize:  35 Megabytes is considered too large
        Returns:
            bool: procede to crawl == true, otherwise false
    """
    # Page is too small in bytes to crawl
    if len(resp.raw_response.content) < minSize:
        print(f'Skipping {url}: page size of: {len(resp.raw_response.content)} bytes is too small!')
        return False
    # Page is too large in bytes to crawl
    if len(resp.raw_response.content) > mbSize:
        print(f'Skipping {url}: page size of: {len(resp.raw_response.content)} bytes is too large!')
        return False

    # Page can be crawled
    return True


'''
/*********************************************************************************************  
*                                 Report Utlity Functions
**********************************************************************************************/
'''
def count_unique_pages(words_In_Page) -> int:
    uni_Links = set()
    for Link in words_In_Page.values(): # go through the links in the words_In_Page dict
        #makes a new link without the fragment
        parse_Link = urlparse(Link)
        uni_Link = parse_Link.scheme + "://" + parse_Link.netloc + parse_Link.path
        uni_Links.add(uni_Link) #puts the new link in the set of unique links
    return len(uni_Links)

def longest_page_words(words_In_Page) -> int:
    numberOfWords = max(words_In_Page.keys())   # Returns the largest number of words in a given url 
    return numberOfWords

def longest_page(numberOfWords, words_In_Page) -> str:
    longestPage = words_In_Page[numberOfWords]  # Finds the url with respect to the it's number of words
    return longestPage


def most_common_words(count_Words) -> dict:
    sortedList = sorted(count_Words.items(), key=lambda x: x[1], reverse=True)  # Sort the map by frequency count in descending order
    mostCommon = {entry[0]: entry[1] for entry in sortedList[:50]} # Create a new map with the 50 most common words and their frequency counts
    return mostCommon
    

def getSubDomains(words_In_Page) -> list[tuple[str, int]]:
    subdomain_counts = defaultdict(int) # This map counts the number of unique pages associated with each subdomain
    subdomain_pages = defaultdict(set)  # This map stores a set of URLs associated with each subdomain

    for url in words_In_Page.values(): # Loop through the URLs in the words_in_Page map and extract subdomains for URLs that belong to the ".ics.uci.edu" domain
        parsed_url = urlparse(url)     # Extract the netloc component, which is the domain and subdomain
        if parsed_url.netloc.endswith('.ics.uci.edu'):      # If it belongs to the ics domain
            subdomain = parsed_url.netloc.split(".")[0]     # Extract subdomain from the netloc by splitting on the "." character
            subdomain_counts[subdomain] += 1                # For each given subdomain increment the count
            subdomain_pages[subdomain].add(url)             # For each given subdomain, add it to the set ,associated with that url

    # Sort the subdomains by the number of unique pages in alphabetically by subdomain name
    sorted_subdomains = sorted(subdomain_counts.items(), key=lambda x: (x[0].lower(), x[1]), reverse=False)
    
    # Return a list of tuples with the url and frequencu
    return [(f'https://{subdomain}.ics.uci.edu', len(subdomain_pages[subdomain])) for subdomain, _ in sorted_subdomains]


def printCrawlerSummary():
    file = open('results.txt', 'w')
    file.write(f'\t\t\t\t\tCrawler Report\t\t\t\t\t\n')
    file.write("Members ID Numbers: 87866641, 18475327, 92844565, 86829976\n\n")
    #file.write(f'\t\t\tTotal Number of Unique Pages: {totalPageCounter} with new counter\n\n')
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
