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

#nlp = StanfordNLP()
"""
result = nlp.parse("Hello world!  It is so beautiful.")
pprint(result)
"""

"""
from nltk.tree import Tree
tree = Tree.parse(result['sentences'][0]['parsetree'])
pprint(tree)
"""

#root_dir = '/media/sf_kickstarter/Brown/data/LDC2008T19_The-New-York-Times-Annotated-Corpus/data'

root_dir ='lfs/local/0/viswa/LDC2008T19_The-New-York-Times-Annotated-Corpus/data/data2'
info_d = {}
info_d['male'] = {}
info_d['female'] = {}
for year in range(1987, 2008):
    info_d['male'][year] = 0
    info_d['female'][year] = 0
    root_dir += '/'+str(year)
    for root, subfolders, files in os.walk(root_dir):
        #print root, subfolders, files
        if len(files) > 0:
            if files[0][-1] != 'l':
                continue
        else:
            continue


        print root
        for file_i in files:
            try:
                filepath = os.path.join(root, file_i)
                with open(filepath, 'r') as xml_f:
                    xml = xml_f.read()
                    soup = BeautifulSoup(xml, "lxml")
                    author = soup.find("byline", "print_byline")
                    auth_text = author.get_text().split()
                    if auth_text[0] == 'By':
                        gend = get_gender(auth_text[1])
                        if gend is not None:
                            info_d[gend][year] = info_d[gend][year] + 1

            except:
                continue

        #pickle.dump(info_d, open('nyt_info.pickle','w'))
        print info_d
