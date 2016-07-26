from bs4 import BeautifulSoup
from urllib2 import urlopen
import argparse


def get_soup_from_url(url, parser="lxml"):
    """
    Short hand for getting the beautiful soup
    object from a given url
    """
    return BeautifulSoup(urlopen(url).read(), parser)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Scraper")
    parser.add_argument('--start-page', dest='START_PAGE',
                         type=int, default=1)
    parser.add_argument('--last-page', dest='END_PAGE',
                         type=int, default=7500)
    parser.add_argument('--dump_every', dest='DUMP_EVERY',
                         type=int, default=10)
    parser.add_argument('--outfile', dest='OUTFILENAME',
                         type=str, default='techcrunch_scraped.json')
    return parser.parse_args()
