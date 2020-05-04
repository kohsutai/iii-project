from elasticsearch import Elasticsearch
import json

raw_data_path = '/home/gordon/iii-project/data/raw_data.json'
es = Elasticsearch('172.28.0.7:9200')

es.indices.create(index='judicial', ignore=400)

with open(raw_data_path, encoding='utf-8') as r:
    raw_data = json.load(r)

for i in raw_data:
    result = es.index(index='judicial', doc_type='judgment', body=i)
