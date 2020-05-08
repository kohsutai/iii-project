from flask import Flask, render_template, jsonify, request, redirect, url_for
from elasticsearch import Elasticsearch
from flask_bootstrap import Bootstrap

# es = Elasticsearch('172.28.0.7:9200')

# 測試用
es = Elasticsearch('192.168.234.134:9200')

app = Flask(__name__)
bootstrap = Bootstrap(app)


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        return redirect(url_for('search_result', keywords=request.values['keyword']))
    return render_template('search.html')


@app.route('/search/search_result/<keywords>')
def search_result(keywords):
    data = {'query': {'match': {'judge_content': keywords}}}
    results = es.search(index='judicial_test', body=data)['hits']['hits'][0:3]
    # return jsonify(results)
    return render_template('search_result.html', results=results)


@app.route('/win_lose')
def win_lose():
    return render_template('win_lose.html')


@app.route('/statistic_keywords')
def statistic_keywords():
    return render_template('statistic_keywords.html')


@app.route('/statistic_laws')
def statistic_laws():
    return render_template('statistic_laws.html')


@app.route('/statistic_locations')
def statistic_locations():
    return render_template('statistic_location.html')


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(debug=True, host='0.0.0.0', port=5000)
