import json
import sys
import time
from analysis import get_article_info
from utils import get_gender


def load_nyt_data(year, month, folder='../annotated/NYT/'):
    nyt_data = {}
    with open('{}nyt_annotated_{}_{}.tsv'.format(
            folder, year, month), 'r') as nyt_f:
        for line in nyt_f:
            link, data, corenlp = line.strip().split('\t')
            nyt_data[link] = {
                'data': json.loads(data),
                'corenlp': json.loads(corenlp)
            }

    return nyt_data


def get_mentions_quotes(nyt_data, out_fn):

    for link, values in nyt_data.iteritems():
        data = values['data']
        corenlp = values['corenlp']
        if not type(corenlp) is dict:  # This happens when CoreNLP timed out
            continue
        pm, quotes, _, _, _ = get_article_info('', ann=corenlp)
        num_mentions = {'MALE': 0, 'FEMALE': 0}
        num_distinct_mentions = {'MALE': 0, 'FEMALE': 0}
        num_quoted_words = {'MALE': 0, 'FEMALE': 0}
        num_quoted_people = {'MALE': 0, 'FEMALE': 0}
        for person, info in pm.iteritems():
            count = info[0]
            gender = info[1][0]
            if not type(gender) is str:
                continue
            if gender.lower() not in ['male', 'female']:
                continue
            num_mentions[gender.upper()] += count
            num_distinct_mentions[gender.upper()] += 1
            if person in quotes:
                quote_length = len(quotes[person])
                num_quoted_people[gender.upper()] += int(quote_length > 0)
                num_quoted_words[gender.upper()] += quote_length

        author_gender = 'UNKNOWN'
        if 'print_byline' in data:
            pb = data['print_byline']
            if pb.startswith('By'):
                pb = pb[3:]
            if len(pb) > 0:
                author_gender = get_gender(pb)
        elif 'norm_byline' in data:
            author_gender = get_gender(
                data['norm_byline'][data['norm_byline'].find(',') + 1:])
        if not type(author_gender) is str:
            author_gender = 'UNKNOWN'
        else:
            author_gender = author_gender.upper()
        '''
        print author_gender
        print data['id']
        print data.keys()
        print data['print_byline']
        print data['norm_byline']
        '''
        year, month = data['id'].split('_')[:2]
        with open(out_fn, 'a') as out_f:
            try:
                out_f.write('\t'.join(
                    [unicode(a) for a in [
                     link, author_gender, year, month, data.get('section', ''),
                     ','.join([unicode(d) for d in data.get('descriptors',
                                                            [])]),
                     num_distinct_mentions['MALE'],
                     num_distinct_mentions['FEMALE'],
                     num_mentions['MALE'], num_mentions['FEMALE'],
                     num_quoted_people['MALE'], num_quoted_people['FEMALE'],
                     num_quoted_words['MALE'], num_quoted_words['FEMALE'],
                     ]]))
                out_f.write('\n')
            except UnicodeEncodeError:
                pass
            except:
                print link
                print author_gender
                print year
                print month
                print data.get('section', '')
                print data.get('descriptors')
                print ','.join(data.get('descriptors', []))
                print num_distinct_mentions
                print num_mentions
                print [
                            link, author_gender, year, month,
                            data.get('section', ''),
                            ','.join(data.get('descriptors', [])),
                            num_distinct_mentions['MALE'],
                            num_distinct_mentions['FEMALE'],
                            num_mentions['MALE'], num_mentions['FEMALE'],
                        ]
                return


if __name__ == "__main__":

    start_year = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_year = int(sys.argv[2])
    else:
        end_year = start_year

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            print time.ctime(), "Loading data for {}/{}".format(year, month)
            try:
                nyt_data = load_nyt_data(year, month)
            except:
                print "Exception Occurred"
                continue
            print time.ctime(), "Analyzing data ..."
            get_mentions_quotes(
                nyt_data,
                '../nyt_data_counts_0702_{}_{}.tsv'.format(year, month))
