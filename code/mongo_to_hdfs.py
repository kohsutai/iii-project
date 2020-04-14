from pymongo import MongoClient
import json
from bson.json_util import dumps

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client['iii-project']
collection = db['judicial']

# Export raw data from mongodb
output = []
for i in collection.find():
    output.append(i)

with open("/home/data/raw_data.json",'w',encoding='utf-8') as f:
  f.write(dumps(output, ensure_ascii=False))

