from collections import defaultdict
from gender import gender, gender_special
from pprint import pprint
import numpy as np

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
    mentions_dictionary = {}
    # We've assumed that all sentences end with full stops.
    # If this assumption breaks, we might be in trouble: notice that we flush
    # the current mention at the end of every sentence, and if a full stop is
    # removed between two sentences that both start with mentions, for example,
    # then we  don't distinguish between the fact that they're in
    # different sentences.
    for sent_i, sentence in enumerate(sentences):
        tokens = sentence['tokens']
        current_mention = ''
        for token in tokens:
            if token['ner'] == 'PERSON':
                if len(current_mention) > 0:
                    current_mention += ' '
                else:
                    start_pos = (sent_i + 1, token['index'])
                current_mention += token['originalText']
                curr_pos = token['index']
            else:
                if len(current_mention) > 0:
                    key = (start_pos[0], start_pos[1], curr_pos)
                    mentions_dictionary[key] = \
                        {'text': current_mention,
                         'mention_num': 1 + len(mentions_dictionary)}
                    if key[1] > 1:
                        preceding_word = tokens[key[1]-2]['originalText']
                        if preceding_word in HONORIFICS:
                            mentions_dictionary[key]['hon_gender'] = \
                                                    HONORIFICS[preceding_word]
                            mentions_dictionary[key]['hon'] = preceding_word
                current_mention = ""

    # Add coreference information
    add_corefs_info(mentions_dictionary, corefs)

    # Add consensus gender
    add_consensus_gender(mentions_dictionary)

    # Add a flag: Is this the first time we are seeing this name,
    # and is this a single name?
    add_flag_last_name_to_be_inferred(mentions_dictionary)

    disjoint_sets_of_mentions, id_to_info, mention_key_to_id = \
        merge_mentions(mentions_dictionary)

    add_quotes(sentences, corefs, mentions_dictionary, mention_key_to_id,
               id_to_info)

    print 'MENTIONS DICTIONARY:'
    pprint(mentions_dictionary)
    print 'DISJOINT SET OF MENTIONS:'
    pprint(disjoint_sets_of_mentions)
    print 'ID TO INFO:'
    pprint(id_to_info)
    '''
    print 'SENTENCES'
    pprint([s['tokens'] for s in sentences])
    '''
    print 'COREFS'
    pprint(corefs)
    return id_to_info


def add_quotes(sentences, corefs, mentions_dictionary,
               mention_key_to_id, id_to_info):

    for entity_id in id_to_info:
        id_to_info[entity_id]['quotes'] = []

    coref_mention_id_to_entity_id = {}
    for mention_key, mention_dict in mentions_dictionary.iteritems():
        coref_mention_id = mention_dict.get('coref_mention_id', None)
        if coref_mention_id:
            coref_mention_id_to_entity_id[coref_mention_id] = \
                    mention_key_to_id[mention_key]

    for sentence in sentences:
        for token in sentence['tokens']:
            if token.get('speaker', '').isdigit():
                speaker_id = int(token['speaker'])
                if VERBOSE:
                    print 'FOUND QUOTE'
                    print speaker_id
                if speaker_id in coref_mention_id_to_entity_id:
                    entity_id = coref_mention_id_to_entity_id[speaker_id]

                id_to_info[entity_id]['quotes'].append(token)


def is_gender_matched(new_mention, set_of_mentions,
                      mentions_dictionary):
    new_mention_gender = new_mention.get('consensus_gender', None)
    if not new_mention_gender:
        return True
    conf_keys = {'high_conf': 2,
                 'med_conf': 1,
                 'low_conf': 0}
    agree_counts_matrix = np.zeros((3, 3))
    disagree_counts_matrix = np.zeros((3, 3))
    row = conf_keys[new_mention_gender[1]]
    # Check that the gender matches.
    for key_m in set_of_mentions:
        curr_mention = mentions_dictionary[key_m]
        curr_mention_gender = \
            curr_mention.get('consensus_gender', None)
        if not curr_mention_gender:
            continue
        col = conf_keys[new_mention_gender[1]]
        if curr_mention_gender[0] == new_mention_gender[0]:
            agree_counts_matrix[row][col] += 1
        else:
            disagree_counts_matrix[row][col] += 1
    if np.sum(disagree_counts_matrix) > 0:
        return False
    else:
        return True


def add_corefs_info(mentions_dictionary, corefs):

    # COREFERENCE-BASED GENDER EXTRACTION
    # print "COREFERENCE CHAINS"
    # pprint(corefs)
    for coref_chain_id, coref_chain in corefs.iteritems():
        mentions_pos = []
        male_pronoun_count = 0
        female_pronoun_count = 0
        it_pronoun_count = 0
        for mention_dict in coref_chain:
            pos = (mention_dict['sentNum'],
                   mention_dict['startIndex'],
                   mention_dict['endIndex'] - 1)
            # If pos matches one of our mentions
            if pos in mentions_dictionary:
                mentions_pos.append(pos)
                mentions_dictionary[pos]['coref_mention_id'] = \
                    mention_dict['id']

            # Otherwise, if pos contains one of our mentions
            elif mention_dict['number'] == 'SINGULAR' and \
                    mention_dict['animacy'] == 'ANIMATE' and \
                    mention_dict['type'] == 'PROPER':
                for (sent_num, start_index, end_index) in \
                        mentions_dictionary:
                    if sent_num == pos[0]:
                        if start_index >= pos[1] and \
                                end_index <= pos[2]:
                            mentions_pos.append(
                                    (sent_num, start_index, end_index))
                            mentions_dictionary[
                                    (sent_num, start_index, end_index)][
                                    'coref_mention_id'] =\
                                mention_dict['id']

            if mention_dict['type'] == 'PRONOMINAL':
                if mention_dict['gender'] == 'MALE':
                    male_pronoun_count += 1
                if mention_dict['gender'] == 'FEMALE':
                    female_pronoun_count += 1
                if mention_dict['animacy'] == 'INANIMATE' and \
                        mention_dict['number'] == 'SINGULAR':
                    it_pronoun_count += 1
        if len(mentions_pos) > 0:
            for pos_i, pos in enumerate(mentions_pos):
                if 'coref_gender' in mentions_dictionary[pos]:
                    print "THIS MENTION IS IN TWO COREFERENCE CHAINS"
                    print pos
                mentions_dictionary[pos]['coref_gender'] = \
                    {"MALE": male_pronoun_count,
                     "FEMALE": female_pronoun_count,
                     "NON-LIVING": it_pronoun_count}
                mentions_dictionary[pos]['coreferent_mentions'] = \
                    mentions_pos[:pos_i] + mentions_pos[pos_i + 1:]


def add_consensus_gender(mentions_dictionary):
    high_conf_thres_coref = 3
    for mention in mentions_dictionary.values():
        hon_gender = None
        coref_gender = None
        num_nonzero_conf_counts = 0
        if mention.get('hon_gender', None):
            hon_gender = mention['hon_gender']
        if mention.get('coref_gender', None):
            # get (gender, count) as a list of tuples.
            coref_counts = \
                       sorted(mention['coref_gender'].items(),
                              key=lambda tup: tup[1],
                              reverse=True)
            # find number of nonzero gender counts
            num_nonzero_coref_counts = \
                len([tup[1] for tup in coref_counts
                     if tup[1] != 0])
            coref_gender = coref_counts[0][0]
            coref_gender_count = coref_counts[0][1]
        if hon_gender:
            mention['consensus_gender'] = (hon_gender,
                                           'high_conf',
                                           'hon')
        elif coref_gender and num_nonzero_coref_counts == 1:
            if coref_gender_count >= high_conf_thres_coref:
                mention['consensus_gender'] = (coref_gender,
                                               'high_conf',
                                               'coref')
            elif coref_gender_count < high_conf_thres_coref:
                mention['consensus_gender'] = (coref_gender,
                                               'med_conf',
                                               'coref')
        elif coref_gender and num_nonzero_coref_counts > 1:
            mention['consensus_gender'] = (coref_gender,
                                           'low_conf',
                                           'coref')
        if num_nonzero_conf_counts > 1:
            mention['coref_gender_conflict'] = True
        # Haven't included name-based gender detection here
        # because that would ideally only be necessitated in
        # a later step (if no gender is found during merging)
        # In this step, it is likely to fail a lot
        # because many people could be referred to by
        # surname.


def add_flag_last_name_to_be_inferred(mentions_dictionary):
    """
    Add a flag: Is this the first time we are seeing this name,
    and is this a single name?
    If yes, we are on the alert for a person who is related to another person,
    and whose last name is to be inferred from the text.
    For example, in the sentence "President Barack Obama and his wife Michelle
    spoke at the gathering," we have that Michelle's last name is to be
    inferred from her relationship with her husband. Then, a "Ms. Obama" in the
    text refers to Michelle, but this connection is not made explicit.
    This is, of course, just a rough heuristic. There are cases (e.g. Lorde)
    where a person is referred to exclusively by just one name.
    """
    set_of_mentions = set()
    for key in sorted(mentions_dictionary):
        mention = mentions_dictionary[key]['text']
        if len(mention.split()) == 1:
            first_time = True
            for el in set_of_mentions:
                if mention in el:
                    first_time = False
            if first_time:
                mentions_dictionary[key]['flag_last_name_to_infer'] = True
        set_of_mentions.add(mention)


def merge_mentions(mentions_dictionary):
    disjoint_sets_of_mentions = {}
    for key in sorted(mentions_dictionary):
        new_mention = mentions_dictionary[key]
        new_mention_text = new_mention['text']
        intersection_idx = []
        for idx, set_of_mentions in disjoint_sets_of_mentions.iteritems():
            for key_m in set_of_mentions:
                mention_text = mentions_dictionary[key_m]['text']
                # Determine whether the new mention is a subset of
                # an old mention.
                if is_mention_subset(new_mention_text, mention_text):
                    intersection_idx.append(idx)
                    break
        # If there is an intersection, we merge the new mention into the
        # intersectiong set.
        # FIXME: Most newsrooms have style guidelines that refer to a person
        # by their full name when they first appear in the text.
        # Subsequently, they are referred to by last name alone.
        # Ideally, if everyone followed this convention, we could only
        # consider last-name overlaps (ie, if Smith would overlap with
        # Jane Smith, which would appear first).
        # However, Jane Smith could later on be referred to in a quotation
        # as Jane, and we would miss this. Also, if they style guideline
        # were not followed, and instead Jane Smith were later referred to
        # as Jane, we would miss this.
        # So, we consider any kind of overlap as a sign of life.
        # This opens the door to potential mistakes:
        # Example: "Barack and Sasha Obama took a weeklong vacation. Jim Smith
        # and his wife Sasha wisely stayed away." --> We would incorrectly
        # classify Sasha Obama and Jim Smith's wife Sasha as the same person.
        gender_match = False
        for idx in intersection_idx:
            set_of_mentions = \
                disjoint_sets_of_mentions[idx]
            gender_match = \
                is_gender_matched(new_mention,
                                  set_of_mentions,
                                  mentions_dictionary)
            if gender_match:
                set_of_mentions.add(key)
                break
        if not gender_match:
            idx = len(disjoint_sets_of_mentions)
            disjoint_sets_of_mentions[idx] = set([key])

    id_to_info = {}
    mention_key_to_id = {}
    for _id, set_of_mentions in disjoint_sets_of_mentions.iteritems():
        longest_mention = ''
        set_gender = None
        for key in set_of_mentions:
            mention_key_to_id[key] = _id
            mention = mentions_dictionary[key]
            if len(mention['text']) > len(longest_mention):
                longest_mention = mention['text']

            curr_gender = mention.get('consensus_gender', None)
            if curr_gender:
                curr_gender = curr_gender[0]
                # If this is the first entry with a gender
                if not set_gender:
                    set_gender = curr_gender

                # If a previous entry had a gender,
                # we check if they match.
                else:
                    if curr_gender != set_gender:
                        # TODO: We need to look at the number of
                        # low confidence and high confidence mentions
                        # for each gender, and conclude about which gender
                        # the entity referred to by the set of mentions is.
                        # This is a temporary workaround where we're marking
                        # the gender as UNKNOWN if there is any conflict at all
                        # Of course, our current code ensures no conflict ...
                        set_gender = 'UNKNOWN'

        id_to_info[_id] = {'name': longest_mention,
                           'gender': set_gender,
                           'count': len(set_of_mentions)}

    return disjoint_sets_of_mentions, id_to_info, mention_key_to_id


def is_mention_subset(small_mention_text, large_mention_text):
    """
    Check if the smaller mention is a "subset" of the larger mention.
    We define "subset" in a very specific way:
    1. Subsequence:
       Example: Barack is a subset of Barack Obama,
                John Kelly is a subset of John Kelly Smith,
                Kelly Smith is a subset of John Kelly Smith, etc.
                And, Barack is a subset of Barack.
    2. The smaller string is equal to the larger string minus the words in the
        middle.
       Example: John Smith is a subset of John Jackson Smith.
    """
    small_mention_tokens = small_mention_text.split()
    large_mention_tokens = large_mention_text.split()
    if small_mention_text in large_mention_text:
        return True
    elif len(large_mention_tokens) > 2:
        if small_mention_tokens == \
                (large_mention_tokens[0] + large_mention_tokens[-1]):
            return True
    return False

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
