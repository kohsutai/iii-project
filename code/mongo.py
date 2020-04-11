import json
from pymongo import MongoClient
import re
from hdfs import *
from bson.json_util import dumps

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client['iii-project']
collection = db['judicial']

output = []
for i in collection.find():
    i['_id']=re.findall("'(.*)'",i.get('_id').__repr__())[0]
    output.append(i)

with open('/home/data/mongo_data.json','w',encoding='utf-8') as f:
  f.write(dumps(output, ensure_ascii=False))

# client = Client("http://172.28.0.3:50070")
# client.status("/")
