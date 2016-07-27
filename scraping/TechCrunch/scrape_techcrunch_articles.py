import sys
import json
sys.path.append('../../')
from scraping import common


def parse_swiftype_meta(soup, field, only_one=False):
    """
    Get metadata from tags in TechCrunch which are of the form
    <meta class="swiftype" name="title" content="This is the title">
    """
    query_dict = {"class": "swiftype", "name": field}
    if only_one:
        return soup.find("meta", query_dict)["content"]
    return [e["content"] for e in soup.find_all("meta", query_dict)]


def get_webpage_links(page_no):
    """
    Gets all the links of articles from techcrunch.com/page/<page_no>/
    Uses the fact that links to the articles are stored in an
    <a href="link" class="read-more">
    """
    page_url = 'http://techcrunch.com/page/' + unicode(page_no) + '/'
    soup = common.get_soup_from_url(page_url)
    readmores = soup.findAll("a", "read-more")
    links = [readmore["href"] for readmore in readmores]
    return links


def extract_page_contents(page_url):
    """
    Extract article text and metadata from the techcrunch
    article at page_url.
    """
    soup = common.get_soup_from_url(page_url)
    page_data = {"link": page_url}

    single_fields = ["title", "author", "excerpt", "timestamp"]
    for field in single_fields:
        page_data[field] = parse_swiftype_meta(soup, field, only_one=True)

    multiple_fields = ["category", "tag"]
    for field in multiple_fields:
        page_data[field] = parse_swiftype_meta(soup, field)

    p_tags_with_text = soup.find("div", "article-entry").find_all("p")
    page_data["text"] = "\n".join([p.get_text() for p in p_tags_with_text])
    return page_data

if __name__ == "__main__":
    data = {}
    args = common.parse_arguments()

    total_count = 0
    failed_count = 0
    for page_no in range(args.START_PAGE, args.END_PAGE):
        print 'Page no:', page_no, '. Getting links ...'
        links = get_webpage_links(page_no)
        total_count += len(links)
        for link in links:
            try:
                data[link] = extract_page_contents(link)
            except KeyboardInterrupt:
                raise
            except:
                failed_count += 1
                continue
        if page_no % args.DUMP_EVERY == 0:
            print 'Total count:', total_count
            print 'Failed count:', failed_count
            print 'Dumping to file ...'
            with open(args.OUTFILENAME, 'w') as outfile:
                json.dump(data, outfile)
