import os
import sys
import click
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import Form
from wtforms import StringField, SubmitField, validators, PasswordField, ValidationError
from wtforms.fields.html5 import EmailField
from flask.model.model_LR_user import find_factor

es = Elasticsearch('172.28.0.7:9200')

# 測試用
# es = Elasticsearch('192.168.234.134:9200')

app = Flask(__name__)
bootstrap = Bootstrap(app)

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
bootstrap = Bootstrap(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)  # 實體擴展


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user


login_manager.login_view = 'login'


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
    click.echo('Done.')


class UserReister(db.Model):
    """記錄使用者資料的資料表"""
    __tablename__ = 'UserRgeisters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return 'username:%s, email:%s' % (self.username, self.email)


class FormRegister(Form):
    """依照Model來建置相對應的Form

    password2: 用來確認兩次的密碼輸入相同
    """
    username = StringField('UserName', validators=[
        validators.DataRequired(),
        validators.Length(3, 15)
    ])
    email = EmailField('Email', validators=[
        validators.DataRequired(),
        validators.Length(1, 50),
        validators.Email()
    ])
    password = PasswordField('PassWord', validators=[
        validators.DataRequired(),
        validators.Length(5, 10),
        validators.EqualTo('password2', message='PASSWORD NEED MATCH')
    ])
    password2 = PasswordField('Confirm PassWord', validators=[
        validators.DataRequired()
    ])
    submit = SubmitField('Register New Account')

    def validate_email(self, field):
        if UserReister.query.filter_by(email=field.data).first():
            raise ValidationError('Email already register by somebody')

    def validate_username(self, field):
        if UserReister.query.filter_by(username=field.data).first():
            raise ValidationError('UserName already register by somebody')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)


@app.errorhandler(400)
def bad_request(e):
    return render_template('400.html'), 400


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/')
def home():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('home'))
    return render_template('index.html')


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))

        user = User.query.first()
        user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('home'))

    return render_template('settings.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = FormRegister()
    if form.validate_on_submit():
        user = UserReister(
            username=form.username.data,
            email=form.email.data,
            password_hash=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        return 'Success Thank You'
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))

        user = User.query.first()
        # 驗證用戶名和密碼是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)  # 登入用户
            flash('Login success.')
            return redirect(url_for('home'))  # 重定向主頁

        flash('Invalid username or password.')  # 如果驗證失敗顯示錯誤信息
        return redirect(url_for('login'))  # 重回登錄頁面

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()  # 登出
    flash('Goodbye.')
    return redirect(url_for('home'))  # 重回首頁


# 關鍵字搜尋
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        return redirect(url_for('search_result', keywords=request.values['keyword']))
    return render_template('search.html')


# 關鍵字搜尋結果
@app.route('/search/search_result/<keywords>')
def search_result(keywords):
    data = {'query': {'match': {'keywords': keywords}}}
    results = es.search(index='judicial_1', body=data)['hits']['hits'][0:3]
    return render_template('search_result.html', keywords=keywords, results=results)


# 故事預測
@app.route('/win_lose', methods=['GET', 'POST'])
def win_lose():
    if request.method == 'POST':
        return redirect(url_for('win_lose_result', keywords=request.values['keyword']))
    return render_template('win_lose.html')


# 故事預測結果
@app.route('/win_lose/win_lose_result/<keywords>')
def win_lose_result(keywords):
    results = find_factor(keywords)
    return render_template('win_lose_result.html', keywords=keywords, results=results)


# 統計查詢/總圖表
@app.route('/statistic_total')
def statistic_total():
    return render_template('statistic_total.html')


# 統計查詢/地區統計
@app.route('/statistic_locations')
def statistic_locations():
    return render_template('statistic_location.html')


# 統計查詢/地區統計/臺北
@app.route('/statistic_location/臺北')
def statistic_location_taipei():
    return render_template('statistic_location_taipei.html')


# 統計查詢/地區統計/新北
@app.route('/statistic_location/新北')
def statistic_location_newtaipei():
    return render_template('statistic_location_newtaipei.html')


# 統計查詢/地區統計/桃園
@app.route('/statistic_location/桃園')
def statistic_location_taoyuan():
    return render_template('statistic_location_taoyuan.html')


# 統計查詢/地區統計/新竹
@app.route('/statistic_location/新竹')
def statistic_location_hsinchu():
    return render_template('statistic_location_hsinchu.html')


# 統計查詢/地區統計/苗栗
@app.route('/statistic_location/苗栗')
def statistic_location_miaoli():
    return render_template('statistic_location_miaoli.html')


# 統計查詢/地區統計/臺中
@app.route('/statistic_location/臺中')
def statistic_location_taichung():
    return render_template('statistic_location_taichung.html')


# 統計查詢/地區統計/彰化
@app.route('/statistic_location/彰化')
def statistic_location_changhua():
    return render_template('statistic_location_changhua.html')


# 統計查詢/地區統計/南投
@app.route('/statistic_location/南投')
def statistic_location_nantou():
    return render_template('statistic_location_nantou.html')


# 統計查詢/地區統計/雲林
@app.route('/statistic_location/雲林')
def statistic_location_yunlin():
    return render_template('statistic_location_yunlin.html')


# 統計查詢/地區統計/嘉義
@app.route('/statistic_location/嘉義')
def statistic_location_chiayi():
    return render_template('statistic_location_chiayi.html')


# 統計查詢/地區統計/臺南
@app.route('/statistic_location/臺南')
def statistic_location_tainan():
    return render_template('statistic_location_tainan.html')


# 統計查詢/地區統計/高雄
@app.route('/statistic_location/高雄')
def statistic_location_kaohsiung():
    return render_template('statistic_location_kaohsiung.html')


# 統計查詢/地區統計/屏東
@app.route('/statistic_location/屏東')
def statistic_location_pingtung():
    return render_template('statistic_location_pingtung.html')


# 統計查詢/地區統計/宜蘭
@app.route('/statistic_location/宜蘭')
def statistic_location_yilan():
    return render_template('statistic_location_yilan.html')


# 統計查詢/地區統計/花蓮
@app.route('/statistic_location/花蓮')
def statistic_location_hualien():
    return render_template('statistic_location_hualien.html')


# 統計查詢/地區統計/臺東
@app.route('/statistic_location/臺東')
def statistic_location_taitung():
    return render_template('statistic_location_taitung.html')


# 統計查詢/地區統計/澎湖
@app.route('/statistic_location/澎湖')
def statistic_location_penghu():
    return render_template('statistic_location_penghu.html')


if __name__ == '__main__':
    app.config['JSON_AS_ASCII'] = False
    app.run(debug=True, host='0.0.0.0', port=5000)
