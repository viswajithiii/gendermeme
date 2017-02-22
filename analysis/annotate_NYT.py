"""
Script to annotate the NYT corpus.
"""
import os
import json
import argparse
import sys
import time
import xml.etree.cElementTree as ET
from pprint import pprint


VERBOSE = False


def get_file_path():
    return os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(get_file_path(), '../'))
from nlp.utils import annotate_corenlp


def get_args():
    parser = argparse.ArgumentParser(description="Analyze TechCrunch")
    parser.add_argument(
        '--path',
        default=os.path.join(
            get_file_path(),
            '../data/LDC2008T19_The-New-York-Times-Annotated-Corpus/data'))
    parser.add_argument('--output_dir',
                        default=os.path.join(
                            get_file_path(),
                            '../annotated/NYT/'))
    parser.add_argument('year', type=int)
    parser.add_argument('month', type=int)
    parser.add_argument('--port', type=int, default=9000,
                        help='The port of the CoreNLP server!')
    parser.add_argument('--all_pages', action="store_true",
                        help="Annotate all pages or just the front page?")
    args = parser.parse_args()
    return args


def extract_article_data(article_id, filename, all_pages):
    """
    Extracts data from the NYT article given the filename.
    Returns the article as a dictionary with the following format:
    {
        'id': year_month_day_id (2001_05_25_0001234)
        'headline': Headline (99.95%)
        'lead': The lead paragraph (96.19%)
        'text': Full text of the article (98.68%)
        'print_byline': The print byline ("by Viswajith Venugopal") (60.04%)
        'norm_byline': The normalized byline ("Venugopal, Viswajith") (48.18%)
        'section': A list of 'online' sections this article is in (97.73%)
        'news_desk': Which desk within NYT? Something like a section. (100%)
        'page_number': Which page in the newspaper was this on? (99.94%)
        'descriptors': Some tags for the article (84.84%)
        'general_online_descriptors': More general tags for the article (79.72%)
        'taxonomic_classifiers': Hierarchical section for the article
                                (like Top/News/U.S/Rockies) (99.50%)
        'locations': A list of locations (32.34%)
        'people': A list of people mentioned (71.57%)
        'organizations': A list of organizations (32.17%)
        (THE ABOVE THREE FIELDS ONLY SEEM TO CONTAIN FAMOUS LOCS/PEOPLE/ORGS)
        'online_locations': A list of locations (6.69%)
        'online_people': A list of people mentioned (6.16%)
        'online_organizations': A list of organizations (7.38%)
        (THE ABOVE THREE ARE TAGGED ALGORITHMICALLY BUT VERIFIED MANUALLY
         AND ONLY START APPEARING FROM 2000-2001)
    }
    NOTE: Not all these things exist for all articles. If it doesn't, the dict
    just won't have that key. The percentages in the above format denote what
    percentage of articles (overall) that field is present in.
    This information was pulled from:
    https://catalog.ldc.upenn.edu/docs/LDC2008T19/new_york_times_annotated_corpus.pdf

    If all_pages is False, then we return None unless the article was on page 1.
    """

    # List of XPATHS pulled from the PDF linked above in the comments.
    # SINGLE because these will have only one element.
    SINGLE_XPATHS = {
        'headline': './body[1]/body.head/hedline/hl1',
        'lead': './body/body.content/block[@class="lead_paragraph"]',
        'text': './body/body.content/block[@class="full_text"]',
        'print_byline': './body/body.head/byline[@class="print_byline"]',
        'norm_byline':
            './body/body.head/byline[@class="normalized_byline"]',
    }

    # These are single XPATHS where, instead of the text in the element,
    # we will need to extract the value of the attribute content.
    SINGLE_XPATHS_CONTENT = {
        'section': './head/meta[@name="online_sections"]',
        'news_desk': './head/meta[@name="dsk"]',
    }

    MULTIPLE_XPATHS = {
        'descriptors':
        './head/docdata/identified-content/classifier[@class="indexing_service"][@type="descriptor"]',
        'general_online_descriptors':
        './head/docdata/identified-content/classifier[@class="online_producer"][@type="general_descriptor"]',
        'taxonomic_classifiers':
        './head/docdata/identified-content/classifier[@class="online_producer"][@type="taxonomic_classifier"]',
        'locations':
        './head/docdata/identified-content/location[@class="indexing_service"]',
        'people':
        './head/docdata/identified-content/person[@class="indexing_service"]',
        'organizations':
        './head/docdata/identified-content/org[@class="indexing_service"]',
        'online_locations':
        './head/docdata/identified-content/location[@class="online_producer"]',
        'online_people':
        './head/docdata/identified-content/person[@class="online_producer"]',
        'online_organizations':
        './head/docdata/identified-content/org[@class="online_producer"]',
    }

    xml_root = ET.parse(filename).getroot()

    page_number_node = xml_root.find('./head/meta[@name="print_page_number"]')
    if page_number_node is None:
        return None
    page_number = int(page_number_node.attrib['content'])

    # Return None if we want only first page articles, and this article is not
    # a first page article.
    if not all_pages and page_number != 1:
        return None

    # The dictionary of data for the current article.
    curr_art_data = {'id': article_id, 'page_number': page_number}

    for key, xpath in SINGLE_XPATHS.iteritems():
        node = xml_root.find(xpath)
        if node is not None:
            if key in ['text', 'lead']:
                value = '\n'.join([el.text for el in node])
            else:
                value = node.text
            curr_art_data[key] = value

    for key, xpath in SINGLE_XPATHS_CONTENT.iteritems():
        node = xml_root.find(xpath)
        if node is not None:
            curr_art_data[key] = node.attrib['content']

    for key, xpath in MULTIPLE_XPATHS.iteritems():
        nodes = xml_root.findall(xpath)
        values = []
        for node in nodes:
            values.append(node.text)
        curr_art_data[key] = values

    # Remove the lead paragraph from the article text
    # by stripping off everything up to the first '\n'
    if not 'text' in curr_art_data:
        return None  # Nothing to annotate for articles without text
    if curr_art_data['text'].startswith('LEAD'):
        try:
            lead_end = curr_art_data['text'].index('\n')
            curr_art_data['text'] = curr_art_data['text'][
                lead_end + 1:]
        except ValueError:
             pass
    curr_art_data['text'] = curr_art_data['text'].replace("''", '"')

    return curr_art_data

if __name__ == "__main__":

    args = get_args()

    PRINT_EVERY = 10
    OUT_FN = os.path.join(args.output_dir,
                          'nyt_annotated_{}_{}.tsv'.format(
                           args.year, args.month))

    '''
    We write to the TSV file in the format:
    y_m_d_number <tab> JSON with article info <tab> JSON of CoreNLP Annotation

    (y_m_d_number is just the year, month and day followed by the
    filename (except the .xml part) which use as an id for the article.
    For example, a file named 0001234.xml published on the 5th of November,
    1997, will have id 1997_11_05_001234.
    '''

    # This is for cases where the annotation gets interrupted,
    # so that we can resume without repeating any work.
    loaded_article_ids = set()
    try:
        with open(OUT_FN, 'r') as out_f:
            for line in out_f:
                loaded_article_ids.add(line.split('\t')[0])
            print 'Loaded data with {} articles'.format(len(loaded_article_ids))
    except IOError:
        # The output file doesn't exist, which means that nothing has been
        # written to the file yet.
        pass

    year_str = str(args.year)
    month_str = str(args.month).zfill(2)  # zfill(2) turns '3'->'03' and so on.

    root_dir = os.path.join(args.path, year_str, month_str)

    for root, subfolders, files in os.walk(root_dir):

        # This makes sure we only look at the leaf directories,
        # which actually contain the xml files.
        if len(files) == 0:
            continue

        # The folder name is the day, in two digits, like 01 or 26
        curr_day = root[-2:]

        for file_ in files:
            if not file_.endswith('xml'):
                continue

            curr_art_id = '{}_{}_{}_{}'.format(year_str, month_str, curr_day,
                                            file_.split('.')[0])
            if curr_art_id in loaded_article_ids:
                continue
            curr_art_data = extract_article_data(curr_art_id,
                                                 os.path.join(root, file_),
                                                 args.all_pages)

            if curr_art_data is None:
                continue

            ann = annotate_corenlp(curr_art_data['text'],
                                   annotators=['pos', 'lemma', 'parse',
                                               'depparse', 'ner', 'quote',
                                               'dcoref', 'openie'],
                                   port=args.port)


            with open(OUT_FN, 'a') as out_f:
                out_f.write('{}\t{}\t{}\n'.format(
                    curr_art_id, json.dumps(curr_art_data), json.dumps(ann)))

            if VERBOSE:
                pprint(curr_art_data)

        print time.ctime(), 'Just finished day no: {}.'.format(curr_day)
