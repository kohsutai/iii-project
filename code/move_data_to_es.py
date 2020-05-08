from elasticsearch import Elasticsearch
import json

clean_data_path = "/home/data/clean_data.json"
es = Elasticsearch('172.28.0.7:9200')

# 測試用
# raw_data_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/final_raw_data.json"
# clean_data_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/clean_data.json"
# es = Elasticsearch('192.168.234.134:9200')

body = {
    'mappings': {
        'properties': {
            'location': {
                'type': 'geo_point'
            },
            'judge_date': {
                'type': 'date'
            }
        }
    }
}

a = es.indices.create(index='judicial_test', ignore=400, body=body)
# a = es.indices.delete(index='judicial_test', ignore=400)
print(a)

with open(clean_data_path, encoding='utf-8') as r:
    clean_data = json.load(r)

k = 1
for i in clean_data:
    es.index(index='judicial_test', body=i)
    print(k)
    k+=1

print('Complete')
