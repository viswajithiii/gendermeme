import json
from jsonrpc import ServerProxy, JsonRpc20, TransportTcpIp
from pprint import pprint
import os
from bs4 import BeautifulSoup
import pickle
from gender import gender, gender_special
import traceback
import numpy as np

verbose=False
NUM_PER_DAY=10 # Number of articles to randomly sample per day.

class StanfordNLP:
    def __init__(self):
        self.server = ServerProxy(JsonRpc20(),
                                  TransportTcpIp(addr=("127.0.0.1", 9900)))

    def parse(self, text):
        s = self.server.parse(text)
        return json.loads(s)

def get_gender(name):

    first_name = name.split()[0].upper()
    """
    if first_name == 'DR.':
        first_name = name.split()[1].upper()
    """
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

def word_is_proper_noun(word):
    return word[1]['PartOfSpeech'] == 'NNP'

def word_is_pronoun(word):
    return word[1]['PartOfSpeech'] in ['PRP' ,'PRP$']

nlp = StanfordNLP()
"""
result = nlp.parse("Hello world!  It is so beautiful.")
pprint(result)
"""

"""
from nltk.tree import Tree
tree = Tree.parse(result['sentences'][0]['parsetree'])
pprint(tree)
"""

root_dir = '/media/sf_kickstarter/Brown/data/LDC2008T19_The-New-York-Times-Annotated-Corpus/data'
info_d = {}
info_d['male'] = {}
info_d['female'] = {}
for year in range(1987, 1988):
    root_dir += '/'+str(year)
    for root, subfolders, files in os.walk(root_dir):
        #print root, subfolders, files
        if len(files) > 0:
            if files[0][-1] != 'l':
                continue
        else:
            continue


        chosen_file_idxs = np.random.choice(len(files), NUM_PER_DAY, replace=False)
        for i in chosen_file_idxs:
            print i
            try:
                filepath = os.path.join(root, files[i])
                print filepath
                with open(filepath, 'r') as xml_f:
                    xml = xml_f.read()
                    soup = BeautifulSoup(xml, "lxml")
                    full_text = soup.find("block", "full_text")
                    text = full_text.get_text()
                    lines = text.split('\n')
                    #text = full_text.get_text().replace('\n', ' ')

                    for line in lines[1:]:
                        parse = nlp.parse(line)
                        for sentence in parse['sentences']:
                            # print sentence['text']
                            used_deps = set()
                            for word in sentence['words']:
                                gend = None
                                if word_is_pronoun(word):
                                    if word[1]['Lemma'] == 'he':
                                        gend = 'male'
                                    elif word[1]['Lemma'] == 'she':
                                        gend = 'female'
                                if word_is_proper_noun(word):
                                    gend = get_gender(word[0])

                                if gend is not None:
                                    for (dep_i, dep) in enumerate(sentence['dependencies']):
                                        if dep_i in used_deps:
                                            continue
                                        if dep[2] == word[0]:
                                            used_deps.add(dep_i)
                                            if dep[0] not in info_d[gend]:
                                                info_d[gend][dep[0]] = {}
                                            temp_d = info_d[gend][dep[0]]
                                            #print dep, gend
                                            if dep[1] in temp_d:
                                                temp_d[dep[1]] = temp_d[dep[1]] + 1
                                            else:
                                                temp_d[dep[1]] = 1
                                            break
            except:
                traceback.print_exc()
                continue
        for gend in ['male', 'female']:
            for key in info_d[gend]:
                temp_d = info_d[gend][key]
                sorted_d = sorted(temp_d, key=temp_d.get, reverse=True)
                print gend, key, sorted_d[:10]

        pickle.dump(info_d, open('nyt_info.pickle','w'))
