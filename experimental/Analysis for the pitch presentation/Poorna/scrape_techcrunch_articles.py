from bs4 import BeautifulSoup
from urllib2 import urlopen
import sys
import pprint
import subprocess

import signal
def handler(signum, frame):
    print "Function took too long ..."
    raise Exception("Function timeout")



def get_webpage_links(page_no):
    """
    Gets all the links of articles from techcrunch.com/page/<page_no>/
    Uses the fact that links to the articles are stored in an
    <a href="link" class="read-more">
    """
    page_url = 'http://techcrunch.com/page/' + unicode(page_no) + '/'
    html = urlopen(page_url).read()
    soup = BeautifulSoup(html, "lxml")
    readmores = soup.findAll("a", "read-more")
    links = [readmore["href"] for readmore in readmores]
    return links

if __name__ == "__main__":
    """
    categories = ['startups', 'mobile', 'gadget', 'enterprise', 'europe', 'asia', 'social']
    for category in categories:
        url = 'http://techcrunch.com/' + category
    """
    data = {}

    signal.signal(signal.SIGALRM, handler)

    START_PAGE = 150
    MAX_PAGES = 7500
    for page_no in range(START_PAGE, MAX_PAGES):
        print 'Page no:', page_no, '. Getting links ...'
        links = get_webpage_links(page_no)

        i = 0
        for i in range(len(links)):
            print links[i]
            signal.alarm(60)
            try:
                subprocess.call([sys.executable, 'scrape_techcrunch_articles_aux.py', links[i]])
                #data[link] = get_article_info(link, r)
            except:
                continue
            #print data[link]
        #pprint.pprint(data)
