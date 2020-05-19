import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from elasticsearch import Elasticsearch
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import Form, FlaskForm
from wtforms import StringField, SubmitField, validators, PasswordField, BooleanField
from wtforms.fields.html5 import EmailField
from flask.model.model_LR_user import find_factor
from flask_bcrypt import Bcrypt

es = Elasticsearch('172.28.0.7:9200')

# 測試用
# es = Elasticsearch('192.168.234.134:9200')

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
                                        os.path.join(app.root_path, 'data_register.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)



@login_manager.user_loader
def load_user(user_id):
    user = UserRegister.query.get(int(user_id))
    return user


login_manager.login_view = 'login'


class UserRegister(db.Model, UserMixin):
    """記錄使用者資料的資料表"""
    __tablename__ = 'UserRegisters'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(50), nullable=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf8')


    def check_password(self, password):
        """
        密碼驗證，驗證使用者輸入的密碼跟資料庫內的加密密碼是否相符
        :param password: 使用者輸入的密碼
        :return: True/False
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return 'username:%s, email:%s' % (self.username, self.email)


class FormRegister(Form):
    """依照Model來建置相對應的Form
    
    password2: 用來確認兩次的密碼輸入相同
    """
    username = StringField('UserName', validators=[
        validators.DataRequired(),
        validators.Length(1, 30)
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
        if UserRegister.query.filter_by(email=field.data).first():
            raise ValidationError('Email already register by somebody')

    def validate_username(self, field):
        if UserRegister.query.filter_by(username=field.data).first():
            raise  ValidationError('UserName already register by somebody')


class FormLogin(FlaskForm):
    """
    使用者登入使用
    以email為主要登入帳號，密碼需做解碼驗證
    記住我的部份透過flask-login來實現
    """

    email = EmailField('Email', validators=[
        validators.DataRequired(),
        validators.Length(5, 30),
        validators.Email()
    ])

    password = PasswordField('PassWord', validators=[
        validators.DataRequired()
    ])

    remember_me = BooleanField('Keep Logged in')

    submit = SubmitField('Log in')





@app.route('/')
def home():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('home'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = FormLogin()
    if form.validate_on_submit():
        #  當使用者按下login之後，先檢核帳號是否存在系統內。
        user = UserRegister.query.filter_by(email=form.email.data).first()
        if user:
            #  當使用者存在資料庫內再核對密碼是否正確。
            if user.check_password(form.password.data):
                login_user(user)
                flash('Login success.')
                return redirect(url_for('home'))
            else:
                #  如果密碼驗證錯誤，就顯示錯誤訊息。
                flash('Wrong Email or Password')
        else:
            #  如果資料庫無此帳號，就顯示錯誤訊息。
            flash('Wrong Email or Password')
    return render_template('login.html', form=form)



@app.route('/register', methods=['GET', 'POST'])
def register():
    form =FormRegister()
    if form.validate_on_submit():
        user = UserRegister(
            username = form.username.data,
            email = form.email.data,
            password = form.password.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Success Thank You')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('home'))


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
