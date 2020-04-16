from pyspark import SparkContext
from pyspark.sql import SQLContext

if __name__ == "__main__":
    sc = SparkContext()
    sqlContext = SQLContext(sc)
    df = sqlContext.read.json("hdfs://localhost/user/cloudera/data/clean_data.json")

    df.show()   # 顯示DataFrame
    df.select(df['judge_content']).show()   # 顯示"judge_content"的內容
