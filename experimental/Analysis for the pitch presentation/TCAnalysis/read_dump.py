from datetime import datetime
from pprint import pprint
from gender import gender, gender_special
import numpy as np
import matplotlib.pyplot as plt

PRINT_COUNT = 20
verbose = False
AT_LEAST = False # Global setting for at least argument for filter_by_gender


def pprint_list(list_to_print):
    pprint(list_to_print[:20])


def get_gender(name):

    first_name = name.split()[0].upper()
    if first_name == 'DR.':
        first_name = name.split()[1].upper()
    found = gender.get(first_name, None)
    if not found:
        special_found = gender_special.get(name.upper(), None)
        if special_found:
            return special_found
        if verbose:
            print 'Gender not found:', name
    if type(found) is tuple:
        special_found = gender_special.get(name.upper(), None)
        if special_found:
            return special_found
        if verbose:
            print 'Ambiguous gender:', name, found
    return found


def load_articles_data(filename='final_article_info.txt'):
    data = {}
    with open(filename, 'r') as text_dump_f:
        for line in text_dump_f:
            line_dict = eval(line)
            data[line_dict["url"]] = {
                            'shares': line_dict["shares"],
                            "authors": line_dict["authors"],
                            "tags": line_dict["tags"],
                            "channels": line_dict["channels"],
                            "date": datetime.strptime(line_dict["date"],
                                                      "%Y-%m-%d %H:%M:%S")}
    return data


def load_authors_data(filename='techcrunch_authors_hash.tsv'):

    def get_first_int(the_str):
        """
        Helper function to convert
        "5, 124 followers" to 5124
        """

        first_token = the_str.split()[0]
        offset = 1 if first_token[0] == '\"' else 0

        return int(first_token[offset:].replace(',', ''))

    data = {}
    with open(filename, 'r') as authors_dump_f:
        for line in authors_dump_f:
            sp_line = line.split('\t')
            name = sp_line[0][:-1]
            gend = get_gender(name)
            position = sp_line[1]
            tweets = get_first_int(sp_line[2])
            following = get_first_int(sp_line[3])
            followers = get_first_int(sp_line[4])
            likes = get_first_int(sp_line[5])
            date = datetime.strptime(sp_line[6][:-2], "%d-%m-%Y %H:%M")

            data[name] = {'position': position, 'tweets': tweets, 'following':
                          following, 'followers': followers, 'likes': likes,
                          'date_joined_twitter': date, 'gender': gend}

    # pprint(data)


def get_most_seen_tags(articles_data):

    tags_to_count = {}
    for article in articles_data:
        tags = articles_data[article]["tags"]

        for tag in tags:
            if tag in tags_to_count:
                tags_to_count[tag] = tags_to_count[tag] + 1
            else:
                tags_to_count[tag] = 1
    sorted_tags = sorted(tags_to_count, key=tags_to_count.get, reverse=True)
    return [(t, tags_to_count[t]) for t in sorted_tags]


def get_most_seen_channels(articles_data):

    chan_to_count = {}
    for article in articles_data:
        chans = articles_data[article]["channels"]

        for chan in chans:
            if chan in chan_to_count:
                chan_to_count[chan] = chan_to_count[chan] + 1
            else:
                chan_to_count[chan] = 1
    sorted_chans = sorted(chan_to_count, key=chan_to_count.get, reverse=True)
    return [(c, chan_to_count[c]) for c in sorted_chans[:PRINT_COUNT]]


def get_most_shared_tags(articles_data):

    tags_to_shares = {}
    for article in articles_data:
        tags = articles_data[article]["tags"]
        shares = articles_data[article]["shares"]

        for tag in tags:
            if tag in tags_to_shares:
                tags_to_shares[tag] = tags_to_shares[tag] + shares
            else:
                tags_to_shares[tag] = shares
    sorted_tags = sorted(tags_to_shares, key=tags_to_shares.get, reverse=True)
    return [(t, tags_to_shares[t]) for t in sorted_tags[:PRINT_COUNT]]


def get_most_shared_channels(articles_data):

    chan_to_shares = {}
    for article in articles_data:
        chans = articles_data[article]["channels"]

        for chan in chans:
            if chan in chan_to_shares:
                chan_to_shares[chan] = chan_to_shares[chan] + 1
            else:
                chan_to_shares[chan] = 1
    sorted_chans = sorted(chan_to_shares, key=chan_to_shares.get, reverse=True)
    return [(c, chan_to_shares[c]) for c in sorted_chans[:PRINT_COUNT]]


def filter_by_gender(articles_data, gend='female', atleast=True):
    """
    Returns a filtered dict with articles with
    at least one article by an author whose gender is gend.
    atleast=True means at least one article is sufficient
    atleast=False means all the authors should be of gend
    """
    filtered = {}
    for article in articles_data:
        authors = articles_data[article]["authors"]
        if atleast:
            for author in authors:
                if get_gender(author) == gend:
                    filtered[article] = articles_data[article]
                    break
        else:
            select = True
            for author in authors:
                if not get_gender(author) == gend:
                    select = False
            if select:
                filtered[article] = articles_data[article]

    return filtered


def filter_by_tag(articles_data, tag):

    filtered = {}
    for article in articles_data:
        tags = articles_data[article]["tags"]
        if tag in tags:
            filtered[article] = articles_data[article]

    return filtered


def get_unique_male_female_count(articles_data):

    male = set()
    female = set()
    for article in articles_data:
        authors = articles_data[article]["authors"]
        for author in authors:
            gend = get_gender(author)
            if gend == 'male':
                male.add(author)
            elif gend == 'female':
                female.add(author)

    return len(male), len(female)


def get_shares_ndarray(articles_data):
    return np.array([float(a["shares"]) for a in articles_data.values()])


def get_cnt_sum_mean_median_shares(articles_data):
    s = get_shares_ndarray(articles_data)
    return len(s), np.sum(s), np.mean(s), np.median(s)

if __name__ == "__main__":
    """
    get_most_seen_tags(articles_data)
    get_most_seen_channels(articles_data)
    get_most_shared_tags(articles_data)
    get_most_shared_channels(articles_data)
    """

    # Load data from articles
    articles_data = load_articles_data()

    # Load data from authors
    authors_data = load_authors_data()

    female_written_articles = filter_by_gender(articles_data, 'female', AT_LEAST)
    male_written_articles = filter_by_gender(articles_data, 'male', AT_LEAST)
    print 'Total number of articles:', len(articles_data)
    print 'Articles with at least one male author:', len(male_written_articles)
    print 'Articles with at least one female author:', len(
        female_written_articles)

    male_shares = get_shares_ndarray(male_written_articles)
    female_shares = get_shares_ndarray(female_written_articles)

    """
    n1 = len(male_shares)
    n2 = len(female_shares)
    m1 = np.mean(male_shares)
    m2 = np.mean(female_shares)
    s1 = np.var(male_shares, ddof=1)
    s2 = np.var(female_shares, ddof=1)
    print 's1 s2', s1, s2
    snew = ((n1 - 1)*s1 + (n2 - 1)*s2)/(n1+n2-2)
    print snew
    out = np.sqrt(snew)*np.sqrt(1.0/n1 + 1.0/n2)
    print out
    tstat = (m1-m2)/out
    print tstat
    assert False
    """

    print 'Tot, avg, median shares of articles with at least one male author:',
    print np.sum(male_shares), np.mean(male_shares), np.median(male_shares)
    male_shares = np.sort(male_shares)
    plt.hist(male_shares[:-1], bins=np.linspace(0, 10000, 20))
    print 'Tot, avg, median shares of articles with at least one female author:',
    print np.sum(female_shares), np.mean(female_shares), np.median(
        female_shares)

    plt.hist(female_shares, bins=np.linspace(0, 10000, 20))
    plt.show()

    most_seen_tags = get_most_seen_tags(articles_data)
    for (tag, count) in most_seen_tags[:20]:
        print tag
        filtered_by_tag = filter_by_tag(articles_data, tag)
        male = filter_by_gender(filtered_by_tag, 'male', AT_LEAST)
        female = filter_by_gender(filtered_by_tag, 'female', AT_LEAST)
        print 'Total:', get_cnt_sum_mean_median_shares(filtered_by_tag)
        print 'Male:', get_cnt_sum_mean_median_shares(male)
        print 'Female:', get_cnt_sum_mean_median_shares(female)
        print 'Unique male and female authors:', get_unique_male_female_count(
            filtered_by_tag)
        print

    print 'Most seen tags by men'
    pprint_list(get_most_seen_tags(male_written_articles))
    print 'Most seen tags by women'
    pprint_list(get_most_seen_tags(female_written_articles))
