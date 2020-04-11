import json
from pymongo import MongoClient
from hdfs import *

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client.judicial
collection = db.judi

mongo_output = json.dumps(collection)
print(mongo_output)

# client = Client("http://172.28.0.3:50070")
# client.status("/")
