"""
Analyze errors, given a file of CoreNLP annotations, and
a directory with manual annotations
"""
import argparse
import os
import json
import time
from analysis import get_article_info


MANUAL_HEADERS = ['Full Name', 'Gender', 'Mentions count', 'Say something?',
                  'Number of words quoted', 'Source/subject', 'Adjectives',
                  'Expert/non-expert', 'Profession/Role(s)', 'Quotes']


def get_file_path():
    return os.path.dirname(os.path.realpath(__file__))


def load_manual_ann(manual_path, art_id, annotator):

    filename = os.path.join(manual_path, '{}{}.tsv'.format(art_id, annotator))
    print filename

    with open(filename, 'r') as f:
        lines = f.readlines()

    # Skip header row (if exists)
    if lines[0].startswith('Full Name'):
        lines = lines[1:]

    info_dict = {}
    for line in lines:
        sp_line = line.strip('\n').split('\t')
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
    all_errors = {}
    try:
        with open(corenlp_fn, 'r') as corenlp_f:
            for line in corenlp_f:
                art_id, art_data, ann = line.strip().split('\t')
                art_data = json.loads(art_data)
                ann = json.loads(ann)

                # print 'Analyzing art_id {}'.format(art_id)

                # Load Manual
                try:
                    manual_ann = load_manual_ann(
                            manual_path, art_id, annotator)
                except IOError:
                    continue

                # Load Automated
                people_mentioned, quotes, verbs, sources, adjectives = \
                    get_article_info(art_data['text'], ann=ann)

                errors = {
                    'mention_not_found': 0,
                    'extra_mention': 0,
                    'mismatch_mention_count': 0,
                    'mean_diff_mention_count': 0,
                    'mismatch_quote_count': 0,
                    'mean_diff_quote_count': 0,
                    'gender_mismatch': 0,
                    'gender_not_found': 0,
                    'total_m_count': 0,
                    'total_m_quotes': 0
                }
                print art_id
                # print manual_ann.keys()
                # print people_mentioned.keys()

                errors['extra_mention'] = len(
                        [n for n in people_mentioned if n not in manual_ann])
                print 'Extra mentions'
                print [n for n in people_mentioned if n not in manual_ann]
                print 'Missing mentions'
                print [n for n in manual_ann if n not in people_mentioned]
                for name in manual_ann:
                    if name not in people_mentioned:
                        print name, 'is missing from automated list ...'
                        errors['mention_not_found'] += 1
                        continue

                    a_count, (a_gender, _) = people_mentioned[name]
                    m_gender, m_count, m_quotes = manual_ann[name]
                    a_quotes = len(quotes[name])

                    # print name
                    m_count = int(m_count)
                    m_quotes = 0 if len(m_quotes) == 0 else int(m_quotes)

                    # print name
                    if a_gender is None:
                        errors['gender_not_found'] += 1
                    elif a_gender.lower() != m_gender.lower():
                        errors['gender_mismatch'] += 1
                    if a_count != m_count:
                        errors['mismatch_mention_count'] += 1
                        errors['mean_diff_mention_count'] += \
                            float(abs(a_count - m_count))
                    if a_quotes != m_quotes:
                        if m_quotes > 0:
                            errors['mean_diff_quote_count'] += \
                                float(abs(a_quotes - m_quotes))
                        errors['mismatch_quote_count'] += 1

                    errors['total_m_count'] += m_count
                    errors['total_m_quotes'] += m_quotes

                # print art_id, len(manual_ann), errors
                all_errors[art_id] = (len(manual_ann), errors)
    except IOError:
        pass

    # keys = all_errors['a001'][1].keys()
    total_ments = sum([all_errors[_id][0] for _id in all_errors])
    total_found_ments = total_ments - \
        sum([all_errors[_id][1]['mention_not_found'] for _id in all_errors])

    for key in ['mention_not_found', 'extra_mention']:
        print key, float(sum(
            [all_errors[_id][1][key] for _id in all_errors]))/total_ments

    for key in ['gender_mismatch', 'gender_not_found',
                'mismatch_quote_count', 'mismatch_mention_count']:
        print key, float(sum(
            [all_errors[_id][1][key] for _id in all_errors]))/total_found_ments

    print 'Total mentions (true)', float(
            sum([all_errors[_id][1]['total_m_count'] for _id in all_errors]))
    print 'Total mention_diff', float(
            sum([all_errors[_id][1]['mean_diff_mention_count']
                for _id in all_errors]))

    print 'Total quotes (true)', float(
            sum([all_errors[_id][1]['total_m_quotes'] for _id in all_errors]))
    print 'Total quotes_diff', float(
            sum([all_errors[_id][1]['mean_diff_quote_count']
                for _id in all_errors]))

    # print
    # for key in keys:
    #    print key, float(sum(
    #        [all_errors[_id][1][key] for _id in all_errors]))/len(all_errors)
    # print all_errors


def dump_error(corenlp_fn, manual_path, output):

    KEYS = ['art_id', 'url', 'name', 'where', 'm_gender',
            'a_gender', 'm_count', 'a_count',
            'm_quotes', 'a_quotes']

    with open(output, 'w') as output_f:
        output_f.write('{}\n'.format('\t'.join(KEYS)))

    with open(corenlp_fn, 'r') as corenlp_f:
        for line in corenlp_f:
            art_id, art_data, ann = line.strip().split('\t')
            art_data = json.loads(art_data)
            ann = json.loads(ann)
            # print 'Analyzing art_id {}'.format(art_id)

            # Load Manual
            try:
                manual_ann = load_manual_ann(
                        manual_path, art_id, 'v')
            except IOError:
                try:
                    manual_ann = load_manual_ann(
                            manual_path, art_id, 'p')
                except IOError:
                    continue

            # Load Automated
            people_mentioned, quotes, verbs, sources, adjectives = \
                get_article_info(art_data['text'], ann=ann)

            for name in manual_ann:
                to_print = {'art_id': art_id, 'url': art_data['url'],
                            'name': name}
                m_gender, m_count, m_quotes = manual_ann[name]
                if name in people_mentioned:
                    to_print['where'] = 'both'
                    a_count, (a_gender, _) = people_mentioned[name]
                    a_quotes = len(quotes[name])
                    m_count = 0 if len(m_count) == 0 else int(m_count)
                    m_quotes = 0 if len(m_quotes) == 0 else int(m_quotes)
                    to_print['m_gender'] = m_gender.lower()
                    if type(a_gender) is str:
                        to_print['a_gender'] = a_gender.lower()
                    elif type(a_gender) is tuple:
                        to_print['a_gender'] = a_gender[0].lower()
                    else:
                        to_print['a_gender'] = None
                    to_print['m_count'] = m_count
                    to_print['a_count'] = a_count
                    to_print['m_quotes'] = m_quotes
                    to_print['a_quotes'] = a_quotes

                else:
                    to_print['where'] = 'manual_only'
                    to_print['m_gender'] = m_gender

                with open(output, 'a') as output_f:
                    for key in KEYS:
                        output_f.write('{}\t'.format(to_print.get(key, '')))
                    output_f.write('\n')

            for name in people_mentioned:
                if name in manual_ann:
                    continue
                a_count, (a_gender, _) = people_mentioned[name]
                if type(a_gender) is str:
                    a_gender = a_gender.lower()
                elif type(a_gender) is tuple:
                    a_gender = a_gender[0].lower()
                else:
                    a_gender = None

                to_print = {'art_id': art_id, 'url': art_data['url'],
                            'name': name, 'where': 'auto_only',
                            'a_gender': a_gender, 'a_count': a_count}
                with open(output, 'a') as output_f:
                    for key in KEYS:
                        output_f.write('{}\t'.format(to_print.get(key, '')))
                    output_f.write('\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('outputsuffix', nargs='?',
                        default='_'.join(
                            time.ctime().replace(':', '_').split()))

    parser.add_argument(
            '--manual-path',
            default='/Users/viswa/Desktop/Box Sync/Gendermeme/Annotations')
    parser.add_argument(
            '--corenlp-ann',
            default=os.path.join(get_file_path(),
                                 '../annotated/manual/ann.tsv'))

    args = parser.parse_args()
    output_path = os.path.join(get_file_path(),
                               '../annotated/manual/ann_dump_{}.tsv'.format(
                                   args.outputsuffix))

    # analyze_error(args.corenlp_ann, args.manual_path, 'v')
    dump_error(args.corenlp_ann, args.manual_path, output_path)
