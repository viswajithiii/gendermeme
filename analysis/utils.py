from collections import defaultdict
from gender import gender, gender_special


def get_gender(name, verbose=False):
    """
    Get the gender from a name.
    Works with full names by extracting the first name out.
    """
    name = name.upper()

    first_name = name.split()[0]
    if first_name == 'DR.':
        first_name = name.split()[1]
    found = gender.get(first_name, None)
    if not found:
        special_found = gender_special.get(name, None)
        if special_found:
            return special_found
        if verbose:
            print 'Gender not found:', name
    if type(found) is tuple:
        special_found = gender_special.get(name, None)
        if special_found:
            return special_found
        if verbose:
            print 'Ambiguous gender:', name, found
    return found


def get_gender_with_coref_chain(name, corefs):
    """
    Gets the gender of a full name that we've extracted from a body of text,
    given the coref chain output from CoreNLP. The coref chain is a dictionary
    where each key is an id, and the value is a list of mentions which CoreNLP
    thinks are coreferent. For example:
    u'35': [{u'animacy': u'ANIMATE',
            u'endIndex': 11,
            u'gender': u'FEMALE',
            u'id': 35,
            u'isRepresentativeMention': True,
            u'number': u'SINGULAR',
            u'position': [6, 2],
            u'sentNum': 6,
            u'startIndex': 9,
            u'text': u'Amanda Bradford',
            u'type': u'PROPER'},
            {u'animacy': u'ANIMATE',
            u'endIndex': 17,
            u'gender': u'MALE',
            u'id': 46,
            u'isRepresentativeMention': False,
            u'number': u'SINGULAR',
            u'position': [7, 5],
            u'sentNum': 7,
            u'startIndex': 15,
            u'text': u"Bradford's",
            u'type': u'PROPER'},
            {u'animacy': u'ANIMATE',
            u'endIndex': 11,
            u'gender': u'FEMALE',
            u'id': 58,
            u'isRepresentativeMention': False,
            u'number': u'SINGULAR',
            u'position': [8, 3],
            u'sentNum': 8,
            u'startIndex': 10,
            u'text': u'she',
            u'type': u'PRONOMINAL'},

    As is evident, the 'gender' attribute CoreNLP supplies is completely
    unreliable (it doesn't seem to use the coreference information at all).

    We use coreference with a gendered pronoun as the gold standard for
    determining gender.
    TODO: Does not handle the case of conflicting information.
    Else, we fall back on getting the gender based on the first name.


    We return both the gender ('MALE', 'FEMALE' or None) and the method
    ('COREF', 'NAME_ONLY' or None).
    """

    name_words = set(name.split())
    for coref_chain in corefs.values():
        chain_contains_name = False
        for mention in coref_chain:
            if mention['animacy'] == 'ANIMATE' and \
                    len(set(mention['text'].split()).intersection(
                        name_words)) > 0:
                chain_contains_name = True
                break

        if not chain_contains_name:
            continue

        for mention in coref_chain:
            if mention['type'] == 'PRONOMINAL' and mention['gender'] in [
                    'MALE', 'FEMALE']:
                return mention['gender'], 'COREF'

    gender = get_gender(name)
    if gender:
        method = 'NAME_ONLY'
    else:
        method = None
    return gender, method


def get_sources(people_mentioned, sentences, corefs):

    people_to_quotes = {p: [] for p in people_mentioned}

    part_to_full_name = _build_index_with_part_names(people_mentioned)

    corefs_to_people = {}
    mention_to_coref_chain = {}

    for coref_id, coref_chain in corefs.iteritems():
        for mention in coref_chain:
            mention_to_coref_chain[int(mention['id'])] = coref_id
            full_name = None
            if mention['text'] in people_mentioned:
                full_name = mention['text']
            elif mention['text'] in part_to_full_name:
                if len(part_to_full_name) == 1:
                    full_name = next(iter(part_to_full_name[mention['text']]))

            if full_name:
                corefs_to_people[coref_id] = full_name

    for sentence in sentences:
        for token in sentence['tokens']:
            if token.get('speaker', '').isdigit():
                speaker_id = int(token['speaker'])
                root_coref_id = mention_to_coref_chain[speaker_id]
                if root_coref_id in corefs_to_people:
                    people_to_quotes[corefs_to_people[root_coref_id]].append(
                        token)

    return people_to_quotes


def get_people_mentioned(sentences, corefs=None, include_gender=False):
    """
    Process the 'sentences' object returned by CoreNLP's annotation
    to get a set of people mentioned.
    It is a list of dictionaries -- one per sentence.
    The key we're most concerned about in the dictionary is the tokens one,
    which contains elements like this for each token in the text.
    u'tokens': [{u'after': u'',
                u'before': u'',
                u'characterOffsetBegin': 0,
                u'characterOffsetEnd': 6,
                u'index': 1,
                u'lemma': u'Google',
                u'ner': u'ORGANIZATION',
                u'originalText': u'Google',
                u'pos': u'NNP',
                u'speaker': u'PER0',
                u'word': u'Google'},
                ...
                ]
    """

    people_mentioned = {}

    for sentence in sentences:

        # List of words in the sentence, with extra information tagged
        # by CoreNLP
        tokens = sentence['tokens']

        # Current mention is the person currently being mentioned
        # (Relevant for when the full name is being written down.)
        curr_mention = ''
        for token in tokens:

            if token['ner'] == 'PERSON':

                # Add space between names.
                if len(curr_mention) > 0:
                    curr_mention += ' '
                curr_mention += token['originalText']

            else:
                # This token is not a person. If curr_mention is not empty, that
                # means that we have just seen a completed mention. We add it to
                # the set of people mentioned.

                if len(curr_mention) > 0:
                    _add_mention_to_dict(curr_mention, people_mentioned)
                    curr_mention = ''

    people_mentioned = {' '.join(key): value for
                        key, value in people_mentioned.iteritems()}
    if include_gender:
        people_mentioned = {k: (v, get_gender_with_coref_chain(k, corefs))
                            for k, v in people_mentioned.iteritems()}
    return people_mentioned


def _build_index_with_part_names(full_names):
    """
    Given a list, set or dict with full_names, (say ['Viswajith Venugopal',
    'Poorna Kumar']), return a dict which goes from each part of the name to
    the full names that contain it ('Viswajith' -> ['Viswajith Venugopal']) etc.
    """

    index_dict = defaultdict(set)
    for full_name in full_names:
        for part_name in full_name.split():
            index_dict[part_name].add(full_name)

    return index_dict


def _add_mention_to_dict(mention, people_mentioned):
    """
    Helps the get_people_mentioned function by adding this mention to the
    dictionary. Sees if the mention already existed. If it is a sub/super-string
    of another mention, then we fold the two together to keep the largest
    mention.
    """

    sp_mention = tuple(mention.split())
    # We find if this entity already exists in our dict of
    # people mentioned. We find out whether we should overwrite
    # that element, or just add one to its tally (our policy
    # is to keep the longest mention only.)
    existing_elem = None
    overwrite = False
    for pm in people_mentioned:
        if pm == sp_mention:
            existing_elem = pm
            break
        if len(set(pm).intersection(set(sp_mention))) > 0:
            existing_elem = pm
            if len(sp_mention) > len(pm):
                overwrite = True

    if existing_elem:
        if overwrite:
            people_mentioned[sp_mention] = 1 + \
                people_mentioned.pop(pm)
        else:
            people_mentioned[pm] += 1
    else:
        people_mentioned[sp_mention] = 1
