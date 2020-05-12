# 直接讀取理由清單檔案

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.externals import joblib  # jbolib 儲存模型的模組
import csv

clean_data_path = "C:/Users/Big data/Anaconda3/envs/Project/Flask/clean_data.json"
reason_path = "C:/Users/Big data/Anaconda3/envs/Project/Flask/reason.csv"
win_lose_path = "C:/Users/Big data/Anaconda3/envs/Project/Flask/win_lose.csv"
model_data_path = "C:/Users/Big data/Anaconda3/envs/Project/Flask/model/model_data.json"


def find_reasons(r_path):
    reasons = []
    with open(r_path, newline='') as c1:
        reason_list = csv.reader(c1)
        for label in reason_list:
            tag_type = label[1]
            tag = label[2]
            reasons.append(tag_type)
            reasons.append(tag)

    reasons = sorted(set(reasons), key=reasons.index)
    return reasons


# Preprocessing用來：
# 去除判決內容,清單們及高相關性項目
# 類別項目 "court", "judge_court", "judge_place", "city", "lawyer" 用one-hot encoding重新編碼
# 把處理過的DF連起來，遺漏值補0
def Preprocessing(df):
    df1 = df.drop(['judge_content', 'judgment_list', 'law_list', 'keywords', 'tag_type'], axis=1)
    df2 = pd.DataFrame(pd.get_dummies(df1[["court", "judge_court", "city", "lawyer"]]))
    df = pd.concat([df1, df2], axis=1).fillna(0)
    return df


# 用masks挑出相同離婚理由的判決,挑選欄位來建模
def masks(df, factor):
    df = df[df[str(factor)] == 1]  # 篩選資料
    x = df[[str(factor), 'foreigner', 'proof', 'noshow', "lawyer_both", "lawyer_plaintiff", "lawyer_defendant",
            "lawyer_none", "judge_court_地方法院", "judge_court_高等法院", "judge_court_最高法院", "judge_court_少年及家事法院"]]  # 挑選欄位
    y = df[['win_lose']]
    print(x.columns)
    return x, y


# 建模 Logistic Regression
def lr_model(x, y):
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=20200506)  # random_state 種子值
    lr = LogisticRegression()
    lr.fit(x_train, y_train)
    accuracy_train = round(lr.score(x_train, y_train), 4)
    accuracy_test = round(lr.score(x_test, y_test), 4)

    return lr, accuracy_train, accuracy_test


def main():
    file = pd.read_json(clean_data_path, encoding="utf-8")
    # print(file)
    df = Preprocessing(file)

    for i in find_reasons(reason_path):
        try:
            x, y = masks(df, i)
            lr, accuracy_train, accuracy_test = lr_model(x, y)
            joblib.dump(lr, 'C:/Users/Big data/Anaconda3/envs/Project/Flask/model/s_lr_%s.pkl' % i)
            print(i)
            print('accuracy_train: ', accuracy_train, )
            print('accuracy_test: ', accuracy_test)

        except Exception:
            print(i, Exception)


if __name__ == '__main__':
    main()

# 卡在奇怪的地方我也很無奈：找個方式存每個模型的訓驗及測試準確率
