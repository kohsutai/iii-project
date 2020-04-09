from pymongo import MongoClient
from hdfs import *

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client["judicial_test"]
collect = db["judi"]

for record in collect.find():
    pprint.pprint(record)

# client = Client("https://172.28.0.3:50070")
# client.status("/")
