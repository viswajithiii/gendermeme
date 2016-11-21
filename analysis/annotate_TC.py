"""
Scripts to analyze the TechCrunch data.
"""
import os
import json
import argparse
import sys
import time
from datetime import datetime


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
    parser.add_argument('--output_dir',
                        default=os.path.join(
                            get_file_path(),
                            '../annotated/'))
    parser.add_argument('year', type=int)
    parser.add_argument('--month', type=int, default=0,
                        help='Which month? 0 means all.')
    parser.add_argument('port', type=int,
                        help='The port of the CoreNLP server!')
    args = parser.parse_args()

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
    OUT_FN = os.path.join(args.output_dir,
                          'techcrunch_annotated_{}_{}.tsv'.format(
                           args.year, args.month))

    '''
    We write to the TSV file in the format
    URL <tab> JSON loaded of article <tab> JSON of CoreNLP Annotation
    (If we try to write the entire thing as one big JSON, it's just way
    too slow.)
    '''
    loaded_urls = set()
    try:
        with open(OUT_FN, 'r') as out_f:
            for line in out_f:
                loaded_urls.add(line.split('\t')[0])
            print 'Loaded data with {} articles'.format(len(loaded_urls))
    except IOError:
        pass

    i = 0
    for url, data in tc_data.iteritems():
        dt = datetime.strptime(data['timestamp'], '%Y-%m-%d %H:%M:%S')
        if dt.year != args.year:
            continue
        if args.month > 0 and dt.month != args.month:
            continue
        if url in loaded_urls:
            continue
        text_str = data['text'].translate(UNICODE_ASCII_MAP).encode(
            'ascii', 'ignore')
        ann = annotate_corenlp(text_str, annotators=['pos', 'lemma', 'parse',
                                                     'depparse', 'ner',
                                                     'dcoref', 'quote'],
                               port=args.port)
        with open(OUT_FN, 'a') as out_f:
            out_f.write('{}\t{}\t{}\n'.format(
                url, json.dumps(data), json.dumps(ann)))
        i += 1
        if i % PRINT_EVERY == 0:
            print 'Article no', i, 'at', time.ctime()
