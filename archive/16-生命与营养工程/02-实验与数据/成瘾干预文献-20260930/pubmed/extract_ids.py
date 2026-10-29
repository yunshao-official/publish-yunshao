import sys, json
d = json.load(sys.stdin)
print(','.join(d['esearchresult']['idlist']))
