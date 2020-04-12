from pymongo import MongoClient
from hdfs import Client
import json
from bson.json_util import dumps

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client['iii-project']
collection = db['judicial']
mongo_path = "/home/data/raw_data.json"

hdfs_client = Client("http://172.28.0.3:50070")
hdfs_path = "/user/cloudera/data"

# Export raw data from mongodb
output = []
for i in collection.find({},{'_id':False}):
    output.append(i)

with open(mongo_path,'w',encoding='utf-8') as f:
  f.write(dumps(output, ensure_ascii=False))

# Send raw data from mongodb to cloudera hdfs
client.makedirs(hdfs_path, permission=777)
client.upload(hdfs_path, mongo_path)
