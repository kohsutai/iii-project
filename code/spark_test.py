#!/usr/bin/python
# -*- coding: utf-8 -*-
from pyspark import SparkContext
from pyspark.sql import SQLContext
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == "__main__":
    sc = SparkContext()
    sqlContext = SQLContext(sc)
    df = sqlContext.read.json("hdfs://localhost/user/cloudera/data/clean_data.json")

    df.show()
    df.select(df['judge_content']).show()
