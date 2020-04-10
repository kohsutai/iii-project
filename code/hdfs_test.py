from pymongo import MongoClient
from hdfs import *

mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client["judicial"]
collect = db["judi"]

data = collect.find()
print(data)


# client = Client("http://172.28.0.3:50070")
# client.status("/")
