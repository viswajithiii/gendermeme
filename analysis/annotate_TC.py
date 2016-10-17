"""
Scripts to analyze the TechCrunch data.
"""
import os
import json
import argparse
import sys
import time


def get_file_path():
    return os.path.dirname(os.path.realpath(__file__))

sys.path.append(os.path.join(get_file_path(), '../'))
from nlp.utils import annotate_corenlp

# techcrunch_data =
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze TechCrunch")
    parser.add_argument('--path',
                        default=os.path.join(
                            get_file_path(),
                            '../data/techcrunch_everything.json'))
    args = parser.parse_args()
    with open(args.path, 'r') as tc_f:
        print time.ctime(), "Loading data ..."
        tc_data = json.load(tc_f)
        print time.ctime(), "Loaded data ..."
    print type(tc_data)
