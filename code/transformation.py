import csv
import json
import jieba
import os
from pymongo import MongoClient
from bson.json_util import dumps

raw_data_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/final_raw_data.json"
clean_data_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/clean_data.json"
reason_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/reason.csv"
win_lose_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/win_lose.csv"
court_path = "C:/Users/Big data/Anaconda3/envs/Project/ETL/court.txt"
jieba.load_userdict('C:/Users/Big data/Anaconda3/envs/Project/ETL/userdict.txt')

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

def get_latitude_longitude(court):
    lls = open(court_path, encoding='utf-8').readlines()
    for ll in lls:
        if court == ll.split(':')[0]:
            lat_lng = ll.split(':')[1].strip('\n').split(',')
            lat = lat_lng[0]
            lon = lat_lng[1]

            return lat, lon


def law_list_segment(item):
    seg_law_list = []
    if item['law_list'] != []:
        for i in range(len(item['law_list'])):
            split_list = list(jieba.cut(item['law_list'][i].replace(' ','').replace('、',' ')))
            remain_list = [x for x in split_list if x != ' ']
            del remain_list[-5:]
            for j in remain_list[2:-1]:
                seg_law_list.append(remain_list[0]+remain_list[1]+j+remain_list[-1])

        return seg_law_list

def transform(raw_data):
    global city, court
    result = []
    for item in raw_data:
        # 分出地區與法院
        city_court_list = list(jieba.cut(item['judge_id'].replace(' ', '')))
        if city_court_list[0] == '最高法院':
            city = '臺北'
            court = '最高法院'
        if city_court_list[1] == '高等法院':
            city = '臺北'
            court = '高等法院'
        if city_court_list[1] == '高等法院' and city_court_list[3] == '分院':
            city = city_court_list[2]
            court = city_court_list[1] + city +city_court_list[3]
        if city_court_list[2] == '地方法院':
            city = city_court_list[1]
            court = city + city_court_list[2]
        if city_court_list[0] == '福建' and city_court_list[2] == '金門':
            city = city_court_list[2]
            court = city_court_list[1] + city + city_court_list[3]
        if city_court_list[0] == '福建' and city_court_list[2] == '地方法院':
            city = city_court_list[1]
            court = city + city_court_list[2]
        if city_court_list[2] == '少年及家事法院':
            city = city_court_list[1]
            court = city + city_court_list[2]

        # 將"judge_date"民國時間轉換成西元時間
        dates = list(jieba.cut(item['judge_date'].replace(' ', '')))
        if len(dates) > 5:
            date_time = str(int(dates[1])+1911)+'-'+dates[3]+'-'+dates[5]
            content = item['judge_content'].replace(' ', '').replace('　', '').split(',')
            result.append(find_tags(item, date_time, content, city, court))

    return result

def find_tags(item, date_time, content, city, court):
    data = {
        'judge_title': item['judge_id'],
        'city': city,
        'location': {
            'lat': get_latitude_longitude(court)[0],
            'lon': get_latitude_longitude(court)[1]
        },
        'court': court,
        'judge_date': date_time,
        'judge_reason': item['judge_reason'],
        'judge_content': item['judge_content'],
        'judgment_list': item['judgment_list'],
        'law_list': law_list_segment(item)
    }

    tag_type_list = []
    keyword_list = []

    # 開啟reason檔案
    with open(reason_path, newline='') as c1:
        reason_list = csv.reader(c1)
        for label in reason_list:
            keyword = label[0]
            tag_type = label[1]
            tag = label[2]

            # 判斷是否含有關鍵字，有就寫1，沒有忽略
            if keyword in str(content) and tag_type != 'other':
                tag_type_list.append(tag_type)
                keyword_list.append(keyword)
                data[tag] = 1

    # 開啟win_lose檔案
    with open(win_lose_path, newline='') as c0:
        win_lose_list = csv.reader(c0)
        for label in win_lose_list:
            keyword = label[0]
            tag_type = label[1]
            tag = label[2]
            win_lose_result = label[3]

            # 判斷是否含有關鍵字，若有關鍵字則讀出tag跟輸贏結果
            if keyword in str(content):
                data['win_lose'] = win_lose_result
                # print(keyword, tag_type, tag, data['win_lose'])
                tag_type_list.append(tag_type)

    data['tag_type'] = sorted(set(tag_type_list), key=tag_type_list.index)
    data['keywords'] = sorted(set(keyword_list), key=keyword_list.index)

    # lawyer欄位：只有被告請律師=-1，兩方都請律師 = 0, 只有原告請律師=1, 都沒請律師=NaN
    actors = str(content).split('主文')[0]
    if '律師' in actors and '本件上訴應委任律師為訴訟代理人' not in actors:
        lawyer_str = actors.split('律師')
        part = lawyer_str[0][-17:-9]
        for s in range(1, len(lawyer_str)):
            part = part + lawyer_str[s][-17:-9]

        if '原告' and '被告' in part:
            data['lawyer'] = 0
        elif '上訴人' and '被上訴人' in part:
            data['lawyer'] = 0
        elif '抗告人' and '相對人' in part:
            data['lawyer'] = 0
        elif '原告' or '上訴人' or '聲請人' or '抗告人' in part and '反訴原告' not in part:
            data['lawyer'] = 1
        elif '被告' or '被上訴人' or '相對人' in part and '反訴被告' not in part:
            data['lawyer'] = -1
            # print(part)
        else:
            data['lawyer'] = 'NaN'
    print(data)
    return data

def main():
    # 載入Raw data
    with open(raw_data_path, encoding='utf-8') as r:
        raw_data = json.load(r)
    trans_data = transform(raw_data)

    # 輸出檔案
    final_data = []
    for i in trans_data:
        if 'win_lose' in dict.keys(i):
            final_data.append(i)

    print(len(raw_data))
    print(len(final_data))
    json.dump(final_data, open(clean_data_path, 'w',encoding='utf-8'), ensure_ascii=False)
    print('檔案輸出成功')

if __name__ == '__main__':
    main()