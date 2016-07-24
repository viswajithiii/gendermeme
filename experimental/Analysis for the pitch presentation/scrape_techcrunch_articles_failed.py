from bs4 import BeautifulSoup
from urllib2 import urlopen
import sys
import pprint
import subprocess

import signal
def handler(signum, frame):
    print "Function took too long ..."
    raise Exception("Function timeout")




if __name__ == "__main__":
    """
    categories = ['startups', 'mobile', 'gadget', 'enterprise', 'europe', 'asia', 'social']
    for category in categories:
        url = 'http://techcrunch.com/' + category
    """

    signal.signal(signal.SIGALRM, handler)
    links = []
    with open('techcrunch_articles_failed_poorna.txt','r') as in_f:
        links = [a[:-1] for a in in_f.readlines()]

    for i in range(len(links)):
        print i, 'out of', len(links),':',links[i]
        signal.alarm(60)
        try:
            subprocess.call([sys.executable, 'scrape_techcrunch_articles_aux.py', links[i]])
            #data[link] = get_article_info(link, r)
        except:
            continue
            #print data[link]
        #pprint.pprint(data)
