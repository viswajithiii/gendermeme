from bs4 import BeautifulSoup
from urllib2 import urlopen


def get_author_links():
    page_url = "https://techcrunch.com/about/"
    html = urlopen(page_url).read()
    soup = BeautifulSoup(html, "lxml")
    authors = soup.findAll("div", "profile text")
    author_links = [auth.a["href"] for auth in authors]
    return author_links


def get_author_info(author_link):

    html = urlopen("https://techcrunch.com"+author_link).read()
    soup = BeautifulSoup(html, "lxml")
    social_tag = soup.find("div", "profile cf")
    social_links = [a["href"] for a in social_tag.findAll("a")]

    tweets, foll, foller, likes, join_date = None, None, None, None, None
    for social_link in social_links:
        if 'twitter.com' in social_link:
            twitter_html = urlopen(social_link).read()
            twitter_soup = BeautifulSoup(twitter_html, "lxml")
            profile_nav = twitter_soup.find("div", "ProfileNav")
            tweets = profile_nav.find(attrs={"data-nav": "tweets"})["title"]
            foll = profile_nav.find(attrs={"data-nav": "following"})["title"]
            foller = profile_nav.find(attrs={"data-nav": "followers"})["title"]
            likes = profile_nav.find(attrs={"data-nav": "favorites"})["title"]
            join_date = twitter_soup.find(
                "span", "ProfileHeaderCard-joinDateText")["title"]

    profile_text = social_tag.find("div", "profile-text").get_text()
    name_position = soup.title.string.split("-")
    name = name_position[0]
    position = name_position[1]
    return name, position, tweets, foll, foller, likes, join_date

author_links = get_author_links()
i = 0
print author_links
with open('techcrunch_authors_hash.tsv', 'w') as out_f:
    for author_link in author_links:
        try:
            print author_link
            author_info = get_author_info(author_link)
            out_f.write('\t'.join([s.encode('utf-8') for s in
                                   author_info]) + '\n')
            i += 1
        except:
            pass
