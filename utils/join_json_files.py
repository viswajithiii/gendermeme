import sys
import json

filenames = sys.argv[1:]
combined_dict = {}
for filename in filenames:
    with open(filename, 'r') as f:
        curr_dict = json.load(f)
        print len(curr_dict)
        combined_dict.update(curr_dict)

print len(combined_dict)
with open('techcrunch_everything.json', 'w') as out_f:
    json.dump(combined_dict, out_f)
print combined_dict[combined_dict.keys()[-1]]
