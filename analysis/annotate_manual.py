"""
Do the CoreNLP annotation of articles that we manually tagged.
"""
import argparse
import os
import sys
import json


def get_file_path():
    return os.path.dirname(os.path.realpath(__file__))


sys.path.append(os.path.join(get_file_path(), '../'))
from nlp.utils import annotate_corenlp


def extract_article_data(filename):
    """
    For manually annotated articles, the format is simple:
    line 1: article_id
    line 2: url
    line 3: headline
    line 4: byline (';' separated list)
    line 5 onwards: text
    """

    with open(filename, 'r') as f:
        lines = f.readlines()

    lines = [l.strip() for l in lines]
    lines = [l for l in lines if len(l) > 0]

    art_data = {
        'id': lines[0],
        'url': lines[1],
        'headline': lines[2],
        'byline': lines[3]
    }

    art_data['text'] = unicode('\n'.join(lines[4:]), encoding='utf-8')

    return art_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--input-path',
            default='/Users/viswa/Desktop/Box Sync/Gendermeme/Annotations')
    parser.add_argument(
            '--output-file',
            default=os.path.join(get_file_path(),
                                 '../annotated/manual/ann.tsv'))

    args = parser.parse_args()

    # This is for when we want to update the file
    # but not recompute everything in it
    loaded_article_ids = set()
    try:
        with open(args.output_file, 'r') as out_f:
            for line in out_f:
                loaded_article_ids.add(line.split('\t')[0])
    # File doesn't exist yet, nothing to do
    except IOError:
        pass

    print 'Found {} annotated articles'.format(len(loaded_article_ids))

    for filename in os.listdir(args.input_path):
        if not filename.endswith('.txt'):
            continue

        art_id = filename[:filename.index('.')]
        if art_id in loaded_article_ids:
            continue

        art_data = extract_article_data(os.path.join(args.input_path,
                                                     filename))

        ann = annotate_corenlp(
                art_data['text'],
                annotators=['pos', 'lemma', 'parse', 'depparse', 'ner',
                            'quote', 'dcoref', 'openie'])

        with open(args.output_file, 'a') as out_f:
            out_f.write('{}\t{}\t{}\n'.format(art_id, json.dumps(art_data),
                                              json.dumps(ann)))
