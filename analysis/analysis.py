import sys
sys.path.append('../')
from nlp import utils as nlp_utils
from utils import get_people_mentioned, get_sources


def get_article_info(article_text):
    ann = nlp_utils.annotate_corenlp(article_text,
                                     annotators=['pos', 'lemma', 'ner', 'parse',
                                                 'depparse', 'parse', 'dcoref',
                                                 'quote'])

    sentences, corefs = ann['sentences'], ann['corefs']
    people_mentioned = get_people_mentioned(sentences, corefs,
                                            include_gender=True)
    sources = get_sources(people_mentioned, sentences, corefs)
    return people_mentioned, sources
