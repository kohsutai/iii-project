from hdfs import Client

hdfs_client = Client("http://172.28.0.3:50070")
hdfs_client.makedirs("/user/cloudera/data", permission=777)
hdfs_client.upload("/user/cloudera/data", "/home/cloudera/iii-project/data")
