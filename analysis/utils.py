from gender import gender, gender_special


def get_gender(name, verbose=False):
    """
    Get the gender from a name.
    Works with full names by extracting
    """

    first_name = name.split()[0].upper()
    if first_name == 'DR.':
        first_name = name.split()[1].upper()
    found = gender.get(first_name, None)
    if not found:
        special_found = gender_special.get(name.upper(), None)
        if special_found:
            return special_found
        if verbose:
            print 'Gender not found:', name
    if type(found) is tuple:
        special_found = gender_special.get(name.upper(), None)
        if special_found:
            return special_found
        if verbose:
            print 'Ambiguous gender:', name, found
    return found


def get_people_mentioned(sentences):
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

    people_mentioned = set()

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
                    # We see if this mention existed before.
                    # If it has any words in common with another mentioned name,
                    # then we keep only the largest of each mention.
                    sp_cm = tuple(curr_mention.split())
                    intersected = False
                    to_remove = []
                    for pm in people_mentioned:
                        if len(set(pm).intersection(set(sp_cm))) > 0:
                            intersected = True
                            if len(sp_cm) > len(pm):
                                to_remove.append(pm)
                    if not intersected:
                        people_mentioned[sp_cm] = 1
                    else:
                        total = 1
                        for elem in to_remove:
                            total += people_mentioned.pop(elem)
                        people_mentioned[sp_cm] = total
                    curr_mention = ''

    return people_mentioned
