import jieba
import json
import os
from pymongo import MongoClient
from bson.json_util import dumps

if os.path.isfile('/home/data/raw_data.json'):
    os.remove('/home/data/raw_data.json')
if os.path.isfile('/home/data/clean_data.json'):
    os.remove('/home/data/clean_data.json')

# 建立Mongodb連線
mongodb_client = MongoClient('172.28.0.2:27017')
db = mongodb_client['iii-project']
collection = db['judicial']

# 將資料從Mongodb取出
output = []
for i in collection.find():
    output.append(i)

with open("/home/data/raw_data.json",'w',encoding='utf-8') as f:
    f.write(dumps(output, ensure_ascii=False))

# 載入自定義詞典&停用詞
jieba.load_userdict("/home/data/userdict.txt")
def stopwordslist(filepath):
    stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8').readlines()]
    return stopwords

# 斷字斷詞
def seg_sentence(sentence):
    sentence_seged = jieba.cut(sentence.strip())
    stopwords = stopwordslist("/home/data/stopword.txt")
    outstr = ''
    for word in sentence_seged:
        if word not in stopwords:
            if word != '\t':
                outstr += word
                outstr += "/"
    return outstr

def wordcut(raw_data):
    for i in raw_data:
        # 將"judge_date"民國時間轉換成西元時間
        dates = list(jieba.cut(i['judge_date']))
        date_time = str(int(dates[2])+1911)+'-'+dates[6]+'-'+dates[10]

        # 將"judge_content"進行斷自斷詞
        seq_content = seg_sentence(i['judge_content'].replace(' ',''))

        # 將結果另存新檔(clean_data.json)
        with open('/home/data/clean_data.json', 'a', encoding='utf-8') as c:
            data = {'id': str(i['_id']['$oid']),
                    'judge_title': str(i['judge_id']),
                    'judge_date': date_time,
                    'judge_reason': str(i['judge_reason']),
                    'judge_content': seq_content,
                    'judgment_list': str(i['judgment_list']),
                    'law_list': str(i['law_list'])
                    }
            c.write(json.dumps(data, ensure_ascii=False))
    print('輸出成功')

def main():
    # 載入Raw data
    with open('/home/data/raw_data.json', encoding='utf-8') as r:
        raw_data = json.load(r)
    wordcut(raw_data)

if __name__ == '__main__':
    main()
