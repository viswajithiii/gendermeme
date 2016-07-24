from bs4 import BeautifulSoup
from urllib2 import urlopen
import pickle

url_begin = "http://indianexpress.com/page/"
url_end = "/?s=archive"


def get_webpage_links(page_no):
    """
    The Indian express archive exists in pages with urls:
    http://indianexpress.com/page/<page_no>/?s=archive
    This function visits the archive page, and gets the
    links from all the pictures (since each picture corresponds
    to an article) and returns it as a list.
    """
    page_url = url_begin + unicode(page_no) + url_end
    html = urlopen(page_url).read()
    soup = BeautifulSoup(html, "lxml")
    pictures = soup.findAll("div", "picture")
    category_links = [pic.a["href"] for pic in pictures]
    return category_links


def get_article_content(article_url):
    """
    This function goes to the particular article URL, gets the
    article page, and returns a tuple consisting of the
    article text, author name, location and date/time of publishing.

    The implementation itself may seem confusing -- it's just hacking
    through the html source of the (badly formatted) Indian express page
    to get the information we need.
    """
    print article_url
    html = urlopen(article_url).read()
    soup = BeautifulSoup(html, "lxml")
    author = soup.find("div", "author")
    author_name = author.find("div", "editor")
    location = author_name.find("strong").get_text().split()
    date = author_name.find("span").get("content")
    spl_name = author_name.get_text().split()
    author_name = ''
    if spl_name[0] == 'Written' and spl_name[1] == 'by':
        i = 2
        while spl_name[i] != location[0]:
            author_name += spl_name[i] + ' '
            i += 1
    else:
        print 'First two words not written by'
        author_name = ' '.join(spl_name)
    p_tags = soup.findAll("p")
    article_text = ' '.join([p.get_text() for p in p_tags
                             if p.get_text()[-9:] != 'read more'])
    return article_text, author_name, ' '.join(location), date

data = {}

fail_count = 0
# For each page number, get the webpage links, and add it to our
# data hash table.
for page_no in range(1, 271):
    print 'Page number:', page_no, 'Fail count:', fail_count
    links = get_webpage_links(page_no)
    for link in links:
        # This try-except ensures that if we ever get an error (say,
        # some page can't be parsed the same way as the others), the
        # program just silently fails and goes to the next page instead
        # of stopping. Also increases fail_count so we can see how often this
        # is happening.
        try:
            article_text, author_name, location, date = get_article_content(
                link)
            data[link] = (article_text, author_name, location, date)
        except:
            fail_count += 1

    # Dump the data into the pickle file. Doing this inside the loop
    # so I can quit the program at any time and still have the data.
    outfile = open('indianexpress_scraped.pickle', 'w')
    pickle.dump(data, outfile)
