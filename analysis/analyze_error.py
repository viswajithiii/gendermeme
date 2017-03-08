"""
Analyze errors, given a file of CoreNLP annotations, and
a directory with manual annotations
"""
import argparse
import os
import json
from analysis import get_article_info


MANUAL_HEADERS = ['Full Name', 'Gender', 'Mentions count', 'Say something?',
                  'Number of words quoted', 'Source/subject', 'Adjectives',
                  'Expert/non-expert', 'Profession/Role(s)']


def get_file_path():
    return os.path.dirname(os.path.realpath(__file__))


def load_manual_ann(manual_path, art_id, annotator):

    filename = os.path.join(manual_path, '{}{}.tsv'.format(art_id, annotator))

    with open(filename, 'r') as f:
        lines = f.readlines()

    # Skip header row (if exists)
    if lines[0].startswith('Full Name'):
        lines = lines[1:]

    info_dict = {}
    for line in lines:
        sp_line = line.strip().split('\t')
        name = sp_line[0]
        gender = sp_line[1]
        mentions_count = sp_line[2]
        num_quoted = sp_line[4]
        info_dict[name] = (gender, mentions_count, num_quoted)

    return info_dict


def analyze_error(corenlp_fn, manual_path, annotator):
    """
    Annotator: either 'v' or 'p'
    """
    with open(corenlp_fn, 'r') as corenlp_f:
        for line in corenlp_f:
            art_id, art_data, ann = line.strip().split('\t')
            art_data = json.loads(art_data)
            ann = json.loads(ann)
            print 'Analyzing art_id {}'.format(art_id)

            # Load Manual
            manual_ann = load_manual_ann(manual_path, art_id, annotator)

            # Load Automated
            people_mentioned, quotes, verbs, sources, adjectives = \
                get_article_info(art_data['text'], ann=ann)

            for name in manual_ann:
                if name not in people_mentioned:
                    print name, 'is missing from automated list ...'
                    continue

                a_count, (a_gender, _) = people_mentioned[name]
                m_gender, m_count, m_quotes = manual_ann[name]
                a_quotes = len(quotes[name])

                print name
                print a_gender, m_gender
                print a_count, m_count
                print a_quotes, m_quotes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--manual-path',
            default='/Users/viswa/Desktop/Box Sync/Gendermeme/Annotations')
    parser.add_argument(
            '--corenlp-ann',
            default=os.path.join(get_file_path(),
                                 '../annotated/manual/ann.tsv'))

    args = parser.parse_args()

    analyze_error(args.corenlp_ann, args.manual_path, 'v')
