"""
Scripts to analyze the TechCrunch data.
"""
import os
import json
import argparse
import sys
import time
from copy import deepcopy
import re

def get_file_path():
    return os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(get_file_path(), '../'))
from nlp.utils import annotate_corenlp

# techcrunch_data =
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze TechCrunch")
    parser.add_argument('--path',
                        default=os.path.join(
                            get_file_path(),
                            '../data/techcrunch_everything.json'))
    parser.add_argument('year', type=int)
    parser.add_argument('port', type=int, help='The port of the CoreNLP server!')
    args = parser.parse_args()

    # Test for whether URL is from this year
    pattern = re.compile(r'.*techcrunch\.com/%d/.*' % (args.year))
    with open(args.path, 'r') as tc_f:
        print time.ctime(), "Loading data ..."
        tc_data = json.load(tc_f)
        print time.ctime(), "Loaded data ..."

    UNICODE_ASCII_MAP = {
        0x2018: u'\'',
        0x2019: u'\'',
        0x201c: u'\"',
        0x201d: u'\"'
    }

    PRINT_EVERY = 10
    DUMP_EVERY = 1000
    OUT_FN = 'techcrunch_annotated_{}.json'.format(args.year)
    i = 0
    try:
        with open(OUT_FN, 'r') as out_f:
            annotated_tc_data = json.load(out_f)
            print 'Loaded data with {} articles'.format(len(annotated_tc_data))
    except IOError:
        annotated_tc_data = {}
    for url, data in tc_data.iteritems():
        if not pattern.match(url):
            continue
        if url in annotated_tc_data:
            continue
        annotated_tc_data[url] = deepcopy(data)
        text_str = data['text'].translate(UNICODE_ASCII_MAP).encode('ascii', 'ignore')
        ann = annotate_corenlp(text_str, annotators=['pos', 'lemma', 'parse',
                                                     'depparse', 'ner',
                                                     'dcoref', 'quote'],
                               port=args.port)
        annotated_tc_data[url]['corenlp'] = ann
        i += 1
        if i % PRINT_EVERY == 0:
            print 'Article no', i, 'at', time.ctime()
        if i % DUMP_EVERY == 0:
            print 'Dumping ...'
            with open('techcrunch_annotated_{}.json'.format(args.year), 'w') as out_f:
                json.dump(annotated_tc_data, out_f)
            print 'Dumped.'

    print 'Done with all the articles. Now finally dumping ...'
    with open('techcrunch_annotated_{}.json'.format(args.year), 'w') as out_f:
        json.dump(annotated_tc_data, out_f)
    print 'Dumped.'
