import sys
from pprint import pprint
import json
import os


def get_file_path():
    return os.path.dirname(os.path.realpath(__file__))


sys.path.append(os.path.join(get_file_path(), '../'))
from nlp import utils as nlp_utils
from utils import get_people_mentioned_new


def get_article_info(article_text, ann=None, verbose=False, make_json=True):
    """
    Given a piece of text, runs it through our entire pipeline.

    Can optionally pass it the CoreNLP annotation if it was precomputed.
    """
    if ann is None:
        ann = nlp_utils.annotate_corenlp(
                article_text,
                annotators=['pos', 'lemma', 'ner', 'parse',
                            'depparse', 'dcoref', 'quote',
                            'openie'])

    sentences, corefs = ann['sentences'], ann['corefs']
    if verbose:
        pprint(sentences)
        pprint(corefs)

    id_to_info = get_people_mentioned_new(sentences, corefs)

    def transform_source(is_source_entry):
        """
        is_source_entry is (True/False, [list_of_reasons])
        """
        if is_source_entry is None:
            is_source_entry = (False, [])

        return (is_source_entry[0], {'Reasons': is_source_entry[1]})

    def transform_mentions(mention_set):

        mention_list = sorted(list(mention_set))

        to_return = []
        for sent_idx, start_pos, end_pos in mention_list:
            to_return.append({
                'sent_num': sent_idx,
                'start': start_pos,
                'end': end_pos
            })

        return to_return

    method_name_map = {
        None: None,
        'hon': 'HONORIFIC',
        'coref': 'COREF',
        'name_only': 'NAME_ONLY'
    }

    json_dict = {}

    for _id, _dict in id_to_info.iteritems():
        new_dict = {
            'associated_verbs': list(_dict.get('associated_verbs', [])),
            'associated_adjs': list(_dict.get('associated_adjs', [])),
            'num_times_mentioned': _dict.get('count', 0),
            'gender': _dict.get('gender'),
            'gender_method': method_name_map[_dict.get('gender_method')],
            'name': _dict.get('name'),
            'quotes': _dict.get('quotes'),
            'is_speaker': transform_source(_dict.get('is_source')),
            'mentions': transform_mentions(_dict.get('mentions'))
        }
        json_dict[_id] = new_dict

    if make_json:
        return json.dumps(json_dict)

    return json_dict
