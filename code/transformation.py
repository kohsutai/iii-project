import csv
import json
import jieba
import os
from pymongo import MongoClient
from bson.json_util import dumps

raw_data_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/final_raw_data.json"
clean_data_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/clean_data.json"
tags_0_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/tags_0.csv"
tags_1_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/tags_1.csv"

# 建立Mongodb連線
# mongodb_client = MongoClient('172.28.0.2:27017')
# db = mongodb_client['iii-project']
# collection = db['judicial']
#
# # 將資料從Mongodb取出
# output = []
# for i in collection.find():
#     output.append(i)
#
# with open(raw_data_path,'w',encoding='utf-8') as f:
#     f.write(dumps(output, ensure_ascii=False))

if os.path.isfile(clean_data_path):
    os.remove(clean_data_path)
    print('File deleted')

def transform(raw_data):
    result = []
    for item in raw_data:
        # 將"judge_date"民國時間轉換成西元時間
        dates = list(jieba.cut(item['judge_date'].replace(' ','')))
        print(dates)
        if len(dates) > 5:
            date_time = str(int(dates[1])+1911)+'-'+dates[3]+'-'+dates[5]
            print(date_time)
            content = item['judge_content'].replace(' ', '').replace('　', '').split(',')
            result.append(find_tags(item, date_time, content))

    return result

def find_tags(item, date_time, content):
    data = {
        'judge_title': item['judge_id'],
        'judge_date': date_time,
        'judge_reason': item['judge_reason'],
        'judge_content': content,
        'judgment_list': item['judgment_list'],
        'law_list': item['law_list']
    }
    print(data)
    reason_type_list = []

    # 開啟tags_1檔案(特徵清單)
    with open(tags_1_path, newline='') as c1:
        tags_0_list = csv.reader(c1)
        for tag in tags_0_list:
            keyword = tag[0]
            reason_type = tag[1]
            reason_name = tag[2]

            # 判斷是否含有關鍵字，有就寫1，沒有忽略
            if keyword in str(content):
                reason_type_list.append(reason_type)
                data[reason_name] = 1

    # 開啟tags_0檔案
    with open(tags_0_path, newline='') as c0:
        tags_0_list = csv.reader(c0)
        for tag in tags_0_list:
            keyword = tag[0]
            reason_type = tag[1]
            reason_name = tag[2]

            # 判斷是否含有關鍵字，有就寫0，沒有忽略
            if keyword in str(content):
                reason_type_list.append(reason_type)
                data[reason_name] = 0

    data['reason_type'] = sorted(set(reason_type_list), key=reason_type_list.index)
    return data

def main():
    # 載入Raw data
    with open(raw_data_path, encoding='utf-8') as r:
        raw_data = json.load(r)
    trans_data = transform(raw_data)
    print(len(trans_data))

    # 輸出檔案
    final_data = []
    for i in trans_data:
        # if len(i['reason_type']) >= 2:
        if 'win_lose' in dict.keys(i):
            final_data.append(i)

    print(len(final_data))
    json.dump(final_data, open(clean_data_path, 'w',encoding='utf-8'), ensure_ascii=False)
    print('檔案輸出成功')

if __name__ == '__main__':
    main()