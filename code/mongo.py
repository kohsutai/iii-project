from pymongo import MongoClient
from hdfs import *

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client.judicial
collect = db.judi

data = list(collect.find())
mongo_export = data.to_json()
print(mongo_export)

# client = Client("http://172.28.0.3:50070")
# client.status("/")
