from flask import Flask, render_template, jsonify, request, redirect, url_for
from elasticsearch import Elasticsearch

es = Elasticsearch('123.241.160.105:9200')

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        return redirect(url_for('search_result', keywords=request.values['keyword']))

    return render_template('search.html')


@app.route('/search_result/<keywords>')
def search_result(keywords):
    data = {'query': {'match': {'judge_content': keywords}}}
    results = es.search(index='judicial', doc_type='judgment', body=data)['hits']['hits'][0:3]
    # return jsonify(results)
    return render_template('search_result.html', results=results)


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(debug=True, host='0.0.0.0', port=5000)
