from pymongo import MongoClient
import json
from bson.json_util import dumps
from hdfs import Client

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client['iii-project']
collection = db['judicial']
hdfs_client = Client("http://172.28.0.3:50070",root="/")

# Export raw data from mongodb
output = []
for i in collection.find({},{'_id':False}):
    output.append(i)

with open("/home/data/raw_data.json",'w',encoding='utf-8') as f:
  f.write(dumps(output, ensure_ascii=False))

# Send raw data from mongodb to hdfs
hdfs_client.makedirs("/user/cloudera/iii-project", permission=777)
hdfs_client.upload("/user/cloudera/iii-project","/home/cloudera/iii-project/data")
