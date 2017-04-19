from collections import defaultdict
from gender import gender, gender_special
from pprint import pprint

VERBOSE = False

HONORIFICS = {
    'Mr': 'MALE',
    'Ms': 'FEMALE',
    'Mrs': 'FEMALE',
    'Sir': 'MALE',
    'Dr': None,
    'Dr.': None,
    'Mr.': 'MALE',
    'Mrs.': 'FEMALE',
    'Ms.': 'FEMALE'
}

RELATIVES = {
    'Wife',
    'Husband',
    'Daughter',
    'Son'
}


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


def get_gender_with_context(name, corefs, honorifics):
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

    If we have an honorific, that's great, because it's perfect information
    about the gender.
    Else, we use coreference with a gendered pronoun as the preferred approach
    for determining gender.
    TODO: Does not handle the case of conflicting information.
    Else, we fall back on getting the gender based on the first name.


    We return both the gender ('MALE', 'FEMALE' or None) and the method
    ('HONORIFIC', 'COREF', 'NAME_ONLY' or None).
    """

    name_words = set(name.split())

    for honorific, names in honorifics.iteritems():
        for h_name in names:
            if len(set(h_name.split()).intersection(name_words)) > 0:
                # Honorofics is none for things like doctor, which
                # are gender neutral.
                if HONORIFICS[honorific] is not None:
                    return HONORIFICS[honorific], 'HONORIFIC'

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
        if type(gender) is tuple:
            gender = 'Ambiguous; most likely {}'.format(gender[0])
    else:
        method = None
    return gender, method


def identify_sources(people, sentences=None, corefs=None,
                     people_to_quotes=None, people_to_verbs=None):
    """
    Given the people mentioned, identify which of them are sources.
    Sources is defined as people who we have identified as quoting,
    as well as people who are the subject of a verb that corresponds to saying
    something.

    For flexibility, we can pass it either sentences and corefs, in which
    case it will call get_quotes and get_associated_verbs to get
    people_to_quotes and people_to_verbs, or directly pass in those if you've
    computed them already.
    """
    SPEAKING_LEMMAS = {'say', 'tell', 'speak', 'ask', 'mention', 'suggest',
                       'claim', 'question', 'tweet', 'write'}

    assert (sentences is not None and corefs is not None) or (
        people_to_quotes is not None and people_to_verbs is not None)
    if people_to_quotes is None:
        people_to_quotes = get_quotes(people, sentences, corefs)
    if people_to_verbs is None:
        people_to_verbs = get_associated_verbs(people, sentences, corefs)

    # Sources is a dictionary which contains only people who are sources,
    # and has, for each of them, a list of reasons why we classified them
    # as sources.
    sources = defaultdict(list)
    for p, quotes in people_to_quotes.iteritems():
        if len(quotes) > 0:
            sources[p].append('Quoted saying {} words'.format(len(quotes)))

    for p, verbs in people_to_verbs.iteritems():
        # Verbs is a list of (actual verb from text, lemma). For example,
        # [(said, say), (say, say), (spoke, speak)]
        verb_lemma_set = set([v[1] for v in verbs])
        speaking_verbs_used = verb_lemma_set.intersection(SPEAKING_LEMMAS)
        if len(speaking_verbs_used) > 0:
            sources[p].append('Subject of {}'.format(
                ', '.join(speaking_verbs_used)))

    return sources


def get_quotes(people_mentioned, sentences, corefs):
    """
    Given the people_mentioned (as a list, set or keys of a dictionary),
    this function returns a dictionary from people mentioned to the list of
    words that they are quoted as saying. This directly uses CoreNLP's system
    for quote identification -- each token has a 'speaker' key, which has the
    value 'PER0' if the token is not in a quote, and an integer corresponding
    to the id in the coreference chain of the entity who CoreNLP thinks is
    saying this quote.

    The first part of this function is just logic for matching the names of
    people mentioned to the chains of coreference they are contained in.
    """

    people_to_quotes = {p: [] for p in people_mentioned}

    part_to_full_name = _build_index_with_part_names(people_mentioned)

    corefs_to_people = {}
    mention_to_coref_chain = {}

    for coref_id, coref_chain in corefs.iteritems():
        for mention in coref_chain:
            mention_to_coref_chain[int(mention['id'])] = coref_id
            full_name = None

            text = mention['text']
            for honorific in HONORIFICS:
                if text.startswith(honorific):
                    text = ' '.join(text.split()[1:])

            if text.endswith("'s"):
                text = text[:-2]

            if text in people_mentioned:
                full_name = text
            elif text in part_to_full_name:
                if len(part_to_full_name[text]) == 1:
                    full_name = next(iter(part_to_full_name[text]))

            if full_name:
                corefs_to_people[coref_id] = full_name

    if VERBOSE:
        pprint(corefs)

    for sentence in sentences:
        for token in sentence['tokens']:
            if token.get('speaker', '').isdigit():
                speaker_id = int(token['speaker'])
                if VERBOSE:
                    print 'FOUND QUOTE'
                    print speaker_id
                root_coref_id = mention_to_coref_chain[speaker_id]
                if root_coref_id in corefs_to_people:
                    people_to_quotes[corefs_to_people[root_coref_id]].append(
                        token)

                # This else block is for situations like
                # 'President Xi Jinping of China', or
                # "If it is real, we will learn new physics," said Wendy
                # Freedman of the University of Chicago, who has spent most of
                # her career charting the size and growth of the universe.

                # In this case, the mention identified by CoreNLP is
                # 'Wendy Freedman of the University of Chicago, who ...'
                # And the speaker id is set to this mention.
                # We use a simple heuristic: scan this mention from
                # left to right, and look for the name of someone
                # who is in our people mentioned.
                else:
                    for candidate_mention in corefs[
                            mention_to_coref_chain[speaker_id]]:
                        if candidate_mention['id'] == speaker_id:
                            mention = candidate_mention

                    assert mention
                    if mention['animacy'] != 'ANIMATE':
                        continue
                    if mention['number'] != 'SINGULAR':
                        continue

                    sp_text = mention['text'].split()
                    if len(sp_text) < 3:
                        continue

                    for word in sp_text:
                        if word in part_to_full_name:
                            full_names = part_to_full_name[word]
                            if len(full_names) == 1:
                                full_name = next(iter(full_names))

                        # We've found a full name!
                        if full_name:
                            people_to_quotes[full_name].append(token)
                            break

    return people_to_quotes


def get_associated_adjectives(people, sentences, corefs):
    """
    Given a list of verbs, get the adjectives associated with them, using
    CoreNLP dependency parse information.
    """
    people_to_adjs = {p: [] for p in people}

    people_to_ment_locs = _get_locations_of_mentions(people, sentences,
                                                     corefs)

    ment_locs_to_people = {}
    for person, ment_locs in people_to_ment_locs.iteritems():
        for ment_loc in ment_locs:
            ment_locs_to_people[ment_loc] = person

    for i, sentence in enumerate(sentences):

        curr_sent_idx = i + 1  # Since CoreNLP uses 1-based indexing
        tokens = sentence['tokens']
        deps = sentence['collapsed-ccprocessed-dependencies']

        for dep in deps:
            curr_dep_loc = (curr_sent_idx, dep['dependent'])
            if curr_dep_loc in ment_locs_to_people:
                curr_person = ment_locs_to_people[curr_dep_loc]

                # This captures things like "She is clever"
                # which has a subject relationship from she to clever
                # since 'is' is a copular verb.
                if dep['dep'] in ['nsubj', 'nsubjpass']:
                    gov_token = tokens[dep['governor'] - 1]
                    if gov_token['pos'] == 'JJ':
                        people_to_adjs[curr_person].append(
                            (gov_token['originalText'], gov_token['lemma']))

            # TODO: Is this else necessary?
            # It basically ensures that if the dependent corresponds to one
            # of our persons, then we ignore the governor.
            # Helps in some weird cases: given a phrase
            # 'many other Republicans, like XYZ', it coreferences
            # XYZ and many other Republicans, and so we start seeing links
            # from many to other as a link characterizing XYZ.
            else:
                curr_gov_loc = (curr_sent_idx, dep['governor'])
                if curr_gov_loc in ment_locs_to_people:
                    curr_person = ment_locs_to_people[curr_gov_loc]

                    dep_token = tokens[dep['dependent'] - 1]

                    if dep_token['pos'] == 'JJ':
                        people_to_adjs[curr_person].append(
                            (dep_token['originalText'], dep_token['lemma']))

    return people_to_adjs


def get_associated_verbs(people, sentences, corefs):
    """
    Given a list of people, get the verbs associated with them using CoreNLP
    annotations.

    Assumes that sentences have dependency parse information.
    """
    people_to_verbs = {p: [] for p in people}

    people_to_ment_locs = _get_locations_of_mentions(people, sentences,
                                                     corefs)

    ment_locs_to_people = {}
    for person, ment_locs in people_to_ment_locs.iteritems():
        for ment_loc in ment_locs:
            ment_locs_to_people[ment_loc] = person

    for i, sentence in enumerate(sentences):

        curr_sent_idx = i + 1  # Since CoreNLP uses 1-based indexing
        tokens = sentence['tokens']
        deps = sentence['collapsed-ccprocessed-dependencies']

        for dep in deps:
            curr_loc = (curr_sent_idx, dep['dependent'])
            if curr_loc not in ment_locs_to_people:
                continue

            curr_person = ment_locs_to_people[curr_loc]

            if dep['dep'] in ['nsubj', 'nsubjpass']:
                gov_token = tokens[dep['governor'] - 1]
                if gov_token['pos'].startswith('VB'):
                    people_to_verbs[curr_person].append(
                        (gov_token['originalText'], gov_token['lemma']))

    return people_to_verbs


def which_people_are_companies(people, sentences, corefs):

    companies = set()
    COMPOUND_INDICATORS = ['executive', 'employee', 'attorney', 'chairman',
                           'executives', 'employees', 'attorneys',
                           'CEO', 'CTO', 'CXO']
    POSS_INDICATORS = ['CEO', 'CTO', 'CXO']

    people_to_ment_locs = _get_locations_of_mentions(people, sentences,
                                                     corefs)

    ment_locs_to_people = {}
    for person, ment_locs in people_to_ment_locs.iteritems():
        for ment_loc in ment_locs:
            ment_locs_to_people[ment_loc] = person

    for i, sentence in enumerate(sentences):

        curr_sent_idx = i + 1  # Since CoreNLP uses 1-based indexing
        deps = sentence['collapsed-ccprocessed-dependencies']

        for dep in deps:
            curr_loc = (curr_sent_idx, dep['dependent'])
            if curr_loc not in ment_locs_to_people:
                continue

            curr_person = ment_locs_to_people[curr_loc]

            if dep['dep'] == 'compound':
                governor = dep['governorGloss']
                if governor in COMPOUND_INDICATORS:
                    companies.add(curr_person)

            if 'poss' in dep['dep']:
                governor = dep['governorGloss']
                if governor in POSS_INDICATORS:
                    companies.add(curr_person)

    # Coreference with it
    for name in people:
        if name in companies:
            continue

        name_words = name.split()
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
                if mention['type'] == 'PRONOMINAL' and \
                        mention['animacy'] == 'INANIMATE' and \
                        mention['number'] == 'SINGULAR':
                    companies.add(name)

    return list(companies)


def get_people_mentioned(sentences, corefs=None, include_gender=False,
                         exclude_companies=True):
    """
    Process the 'sentences' object returned by CoreNLP's annotation
    to get a set of people mentioned.
    It is a list of dictionaries -- one per sentence.
    If exclude_companies is True, then run our heuristics to
        get rid of company names.
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
    honorifics = _get_honorifics(sentences)

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
                # The current token is not a person.
                # If curr_mention is not empty, that means that the words just
                # preceding this token correspond to a completed mention.
                # We add it to the set of people mentioned.

                if len(curr_mention) > 0:
                    _add_mention_to_dict(curr_mention, people_mentioned)
                    curr_mention = ''

    people_mentioned = {' '.join(key): value for
                        key, value in people_mentioned.iteritems()}

    if exclude_companies:
        companies = which_people_are_companies(people_mentioned,
                                               sentences, corefs)
        for company in companies:
            del people_mentioned[company]

    if include_gender:
        honorifics = _get_honorifics(sentences)
        people_mentioned = {k: (v, get_gender_with_context(k, corefs,
                                                           honorifics))
                            for k, v in people_mentioned.iteritems()}
    return people_mentioned


def get_people_mentioned_new(sentences, corefs):
    """

    """
    print 'COREFS BELOW'
    pprint(corefs)
    mentions_dictionary = {}
    for sent_i, sentence in enumerate(sentences):
        tokens = sentence['tokens']
        pprint(tokens)
        current_mention = ''
        for token in tokens:       
            if token['ner'] == 'PERSON':
                if len(current_mention) > 0:
                    current_mention += ' '
                else:
                    start_pos = (sent_i, token['index'])
                current_mention += token['originalText']
            else:
                if len(current_mention) > 0:
                    key = (current_mention, start_pos[0], start_pos[1])
                    mentions_dictionary[key] = \
                            {'mention': current_mention,
                            'mention_num': len(mentions_dictionary)}
                    if key[2] > 1: 
                        preceding_word = tokens[key[2]-1]['originalText']
                        if preceding_word in HONORIFICS:
                            mentions_dictionary[key]['hon_gen'] = \
                                    HONORIFICS[preceding_word] 

                            




# PRIVATE UTILITY FUNCTIONS FOLLOW

def _get_locations_of_mentions(people, sentences, corefs):
    """
    Given a list of full names of people mentioned, get the locations (where
    location is a tuple of (sentence_index, word_index) -- note that these
    are designed to match CoreNLP numbering, which starts at 1 and not 0) where
    they are mentioned. It resolves coreferences fully to return a full list
    per person.

    For example, given the input sentence:
    "Viswajith Venugopal is writing this code. He likes it. That is how
     Viswajith is."
    the ideal output would be:
    {"Viswajith Venugopal": [(1, 1), (1, 2), (2, 1), (3, 4)]} for
    Viswajith, Venugopal, He and the last Viswajith respectively.
    """
    people_to_locations = {p: [] for p in people}

    part_to_full_name = _build_index_with_part_names(people)

    for coref_id, coref_chain in corefs.iteritems():
        # The person (out of our list of people)
        # who this coref chain corresponds to, if any.
        curr_chain_person = None
        for mention in coref_chain:
            if mention['text'] in people:
                curr_chain_person = mention['text']
            # Now, we try splitting the mention text into
            # individual words. Helps with things like "Mr. Obama"
            else:
                for word in mention['text'].split():
                    if word in part_to_full_name:
                        # If there's more than one full name (very unlikely)
                        # we just skip.
                        if len(part_to_full_name[word]) == 1:
                            curr_chain_person = next(
                                iter(part_to_full_name[word]))
                            break

            if curr_chain_person:
                break

        # If this coref chain has one of the people in our list,
        # we add to the locations here.
        if curr_chain_person:
            for mention in coref_chain:
                # If it's a multi-name mention, then we want to add
                # each location of the mention individually.
                length = len(mention['text'].split())
                sent_num = mention['sentNum']
                start_idx = mention['startIndex']
                for idx in range(length):
                    people_to_locations[curr_chain_person].append(
                        (sent_num, start_idx + idx))

    return people_to_locations


def _build_index_with_part_names(full_names):
    """
    Given a list, set or dict with full_names, (say ['Viswajith Venugopal',
    'Poorna Kumar']), return a dict which goes from each part of the name to
    the full names that contain it ('Viswajith' -> ['Viswajith Venugopal']) etc
    """

    index_dict = defaultdict(set)
    for full_name in full_names:
        for part_name in full_name.split():
            index_dict[part_name].add(full_name)

    return index_dict


def _add_mention_to_dict_v2(mention, people_mentioned):
    """
    Helps the get_people_mentioned function by adding this mention to the
    dictionary. Sees if the mention already existed. If it's a sub/super-string
    of another mention, then we fold the two together to keep the largest
    mention.

    v2: Better disambiguation when multiple people share same component of name
    """

    sp_mention = tuple(mention.split())
    # We find if this entity already exists in our dict of
    # people mentioned. We find out whether we should overwrite
    # that element, or just add one to its tally (our policy
    # is to keep the longest mention only.)
    existing_elem = []
    overwrite = False
    for pm in people_mentioned:
        pm_join = ' '.join(pm)
        if mention in pm_join:
            if type(people_mentioned[pm]) is not list:
                existing_elem.append(pm) # could be one or more matches
        '''
        if len(set(pm).intersection(set(sp_mention))) > 0:
            existing_elem = pm
            if len(sp_mention) > len(pm):
                overwrite = True
            break
        '''
    # If the name has been seen only in part before. 
    # Example: The name is Bond. James Bond.
    if existing_elem == []:
        people_mentioned[sp_mention] = 1
    if len(existing_elem) == 1:
        people_mentioned[existing_elem[0]] += 1
    elif len(existing_elem) > 1:
        people_mentioned[sp_mention] = ["Ambiguous"] + existing_elem

def _add_mention_to_dict(mention, people_mentioned):
    """
    Helps the get_people_mentioned function by adding this mention to the
    dictionary. Sees if the mention already existed. If it's a sub/super-string
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
            break

    if existing_elem:
        if overwrite:
            people_mentioned[sp_mention] = 1 + \
                people_mentioned.pop(existing_elem)
        else:
            people_mentioned[existing_elem] += 1
    else:
        people_mentioned[sp_mention] = 1


def _get_honorifics(sentences):
    '''
    Extract gender cues from annotated sentences: Mrs., Ms., Mr.
    For each of these gender cues, we have a list of associated names.
    For example, if our content was: 'Mr. Barack Obama was the President.
    His wife Mrs. Michelle was the First Lady. Their daughter Ms. Sasha is
    in high school. Mr. Biden is the Vice President.', then
    honorofics should be:
    {'Mr.': set(['Barack Obama', 'Biden']),
    'Mrs.': set(['Michelle']),
    'Ms.': set(['Sasha'])}
    '''

    honorifics = {h: set() for h in HONORIFICS}

    for sentence in sentences:
        tokens = sentence['tokens']
        for token_i, token in enumerate(tokens):
            if token_i == 0:
                person_name = ''

                # saveAs is a flag of sorts: tells you whether
                # to be on the lookout for a name
                saveAs = ''
            if token['originalText'] in HONORIFICS:
                '''
                After seeing a gender cue ('Mr.'/'Mrs.'/'Ms.'), get ready to:
                1. store a person's name (which would logically follow this
                token as person_name (initialized to an empty string).
                2. save the gender cue we have just seen as saveAs.
                '''
                saveAs = token['originalText']
                person_name = ''
                continue
            if saveAs != '':
                if token['ner'] == 'PERSON':
                    if person_name == '':
                        person_name = token['originalText']
                    else:
                        person_name += ' ' + token['originalText']
                else:
                    if person_name != '':
                        honorifics[saveAs].add(person_name)
                        person_name = ''
                    saveAs = ''
    return honorifics
