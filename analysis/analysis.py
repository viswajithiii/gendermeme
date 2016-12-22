import sys
from pprint import pprint
sys.path.append('../')
from nlp import utils as nlp_utils
from utils import get_people_mentioned, get_quotes, get_associated_verbs, \
    identify_sources, get_associated_adjectives


def get_article_info(article_text, verbose=False):
    """
    Helper function that applies our techniques on a given piece of text,
    first annotating it with CoreNLP then doing other stuff.

    Primarily used by the web app right now.
    """
    ann = nlp_utils.annotate_corenlp(article_text,
                                     annotators=['pos', 'lemma', 'ner', 'parse',
                                                 'depparse', 'dcoref', 'quote',
                                                 'openie'])

    sentences, corefs = ann['sentences'], ann['corefs']
    if verbose:
        pprint(sentences)
        pprint(corefs)
    people_mentioned = get_people_mentioned(sentences, corefs,
                                            include_gender=True)
    quotes = get_quotes(people_mentioned, sentences, corefs)
    verbs = get_associated_verbs(people_mentioned, sentences, corefs)
    sources = identify_sources(people_mentioned, people_to_quotes=quotes,
                               people_to_verbs=verbs)
    adjectives = get_associated_adjectives(people_mentioned, sentences, corefs)
    return people_mentioned, quotes, verbs, sources, adjectives