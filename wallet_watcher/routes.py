import os
import secrets
from flask import render_template, url_for, flash, redirect, request
from wallet_watcher.form import (RegistrationForm, LoginForm, ContactForm, EnterForm, EditForm, DeleteForm,
                                 UpdateAccountForm, RequestResetForm, ResetPasswordForm)
from wallet_watcher import app, mongo, bcrypt, login_manager, mail
import time
from datetime import date, timedelta
import pymongo
from flask_login import UserMixin, current_user, login_user, logout_user, login_required
from bson.objectid import ObjectId
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_mail import Message


client = pymongo.MongoClient(host='localhost', port=27017)
db = client.wallet_watcher


def get_reset_token(user_id, expires_sec=1800):
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'_id': user_id}).decode('utf-8')


def verify_reset_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)
    except:
        return None
    return user_id


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.is_submitted():
        msg = Message('Wallet Watcher Contact Request from {} {}'.format(form.firstname.data, form.lastname.data),
                      sender='noreply@googlemail.com',
                      recipients=['raymondcyang0219@gmail.com'])
        msg.body = '''Email: {}
Name: {} {}

Note:
{}
'''.format(form.email.data, form.firstname.data, form.lastname.data, form.note.data)
        mail.send(msg)
        flash('Your request has been sent.', 'info')
        return redirect(url_for('home'))
    else:
        print('failed')
    return render_template('contact.html', title='Contact', form=form)


class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username

    @staticmethod
    def check_password():
        form = LoginForm()
        collection = db.users
        result = collection.find_one({'user_name': form.username.data})
        try:
            password = result['password']
            return bcrypt.check_password_hash(password, form.password.data)
        except:
            return flash('The Email does not exist.', 'danger')


@login_manager.user_loader
def load_user(username):
    u = mongo.db.users.find_one({"user_name": username})
    if u is not None:
        curr_user = User(username=u['user_name'])
        curr_user.id = username
        return curr_user


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('enter'))
    form = LoginForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({"user_name": form.username.data})
        if user and User.check_password():
            user_obj = User(username=user['user_name'])
            login_user(user_obj, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Welcome back, {}!'.format(user['first_name']), 'success')
            return redirect(next_page) if next_page else redirect(url_for('enter'))
        elif User.check_password() is False:
            flash('The password is incorrect.', 'danger')
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('enter'))
    form = RegistrationForm()
    connection = mongo.db.users

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        connection.insert({'profile_image_name': '/static/profile_img/default.jpg',
                           'user_name': request.form.get('username'),
                           'first_name': request.form.get('first_name'),
                           'last_name': request.form.get('last_name'),
                           'email': request.form.get('email'),
                           'password': hashed_password})
        flash('{}, your account has been created!'.format(form.first_name.data), 'success')
        return redirect(url_for('enter'))
    return render_template('register.html', title='Register', form=form)


@app.route('/enter', methods=['GET', 'POST'])
@login_required
def enter():
    form = EnterForm()
    connection = mongo.db.records
    t = time.time()

    if current_user.is_authenticated:
        if form.validate_on_submit():
            connection.insert({'user_name': current_user.username,
                               'time_zone': time.strftime('%Z', time.localtime(t)),
                               'date': time.strftime('%Y-%m-%d', time.localtime(t)),
                               'time': time.strftime('%H:%M', time.localtime(t)),
                               'category': request.form.get('category'),
                               'currency': request.form.get('currency'),
                               'amount': request.form.get('amount'),
                               'note': request.form.get('note')})
            flash('The New Record Has Been Added!', 'success')
            return redirect(url_for('enter'))

    return render_template('enter_form.html', title='Enter Form', form=form)


def save_image(form_image):
    random_rex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    picture_fn = random_rex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_img', picture_fn)
    form_image.save(picture_path)
    return '/static/profile_img/' + picture_fn


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    connection = mongo.db.users
    user = connection.find_one({'user_name': current_user.username})
    profile_image = url_for('static', filename='profile_img/default.jpg')
    connection2 = mongo.db.records
    currency = connection2.find_one({'user_name': current_user.username})['currency']

    if request.method == 'GET':
        form.first_name.data = user['first_name']
        form.last_name.data = user['last_name']
        form.email.data = user['email']
        form.currency.date = currency
    elif form.validate_on_submit():
        # print(form.currency.data)
        # print(user['user_name'])
        if form.profile_image_name.data:
            image_file_name = save_image(form.profile_image_name.data)
            connection.update({'_id': ObjectId(user['_id'])}, {'$set':
                {
                    'profile_image_name': image_file_name  # profile_image
                }
            })
        connection.update({'_id': ObjectId(user['_id'])}, {'$set':
            {
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'email': form.email.data
            }
        })
        connection2.update_many({'user_name': user['user_name']}, {'$set':
            {
                'currency': form.currency.data
            }
        })
        flash('The Account Has Been Updated!', 'success')
        return redirect(url_for('account'))
    return render_template('account.html', title='Account', user=user, form=form, profile_image=profile_image)


@app.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    form = EditForm()
    connection = mongo.db.records
    # Descending
    records = connection.find({'user_name': current_user.username}).sort(
        [("date", pymongo.DESCENDING), ("time", pymongo.DESCENDING)])
    return render_template('history.html', title='History', records=records, form=form)


# Display records and sorted by categories


def mongo_filter(category):
    connection = mongo.db.records
    # Descending

    offset = int(request.args['offset'])
    limit = int(request.args['limit'])
    get_last_id = connection.find({'user_name': current_user.username, 'category': category}).sort(
        [("_id", pymongo.DESCENDING)]).limit(limit)
    last_id = get_last_id[offset]['_id']
    records = connection.find({'user_name': current_user.username, 'category': category,
                               '_id': {'$lte': last_id}}).sort([("date", pymongo.DESCENDING),
                                                               ("time", pymongo.DESCENDING)]).limit(limit)
    next_url = '/record/' + category[:4] + '?limit=' + str(limit) + '&offset=' + str(offset + limit)
    last_url = '/record/' + category[:4] + '?limit=' + str(limit) + '&offset=' + str(offset - limit)
    print(next_url)
    print(last_url)
    return render_template('record_filter.html', title=category, records=records, next_url=next_url, last_url=last_url)


@app.route('/record/Food', methods=['GET', 'POST'])
@login_required
def food_dining():
    return mongo_filter('Food and Dining')


@app.route('/record/Bill', methods=['GET', 'POST'])
@login_required
def bill():
    return mongo_filter('Bills and Utilities')


@app.route('/record/Shop', methods=['GET', 'POST'])
@login_required
def shopping():
    return mongo_filter('Shopping')


@app.route('/record/Ente', methods=['GET', 'POST'])
@login_required
def entertainment():
    return mongo_filter('Entertainment')


@app.route('/record/Pers', methods=['GET', 'POST'])
@login_required
def personal_care():
    return mongo_filter('Personal Care')


@app.route('/record/Heal', methods=['GET', 'POST'])
@login_required
def health():
    return mongo_filter('Health and Fitness')


@app.route('/record/Tran', methods=['GET', 'POST'])
@login_required
def transport():
    return mongo_filter('Transport and Auto')


@app.route('/record/Fees', methods=['GET', 'POST'])
@login_required
def fees():
    return mongo_filter('Fees and Charges')


@app.route('/record/Educ', methods=['GET', 'POST'])
@login_required
def education():
    return mongo_filter('Education')


@app.route('/record/Gift', methods=['GET', 'POST'])
@login_required
def gift():
    return mongo_filter('Gifts and Donation')


@app.route('/record/Busi', methods=['GET', 'POST'])
@login_required
def business():
    return mongo_filter('Business Services')


@app.route('/record/Inve', methods=['GET', 'POST'])
@login_required
def investment():
    return mongo_filter('Investment')


@app.route('/record/Trav', methods=['GET', 'POST'])
@login_required
def travel():
    return mongo_filter('Travel')


@app.route('/record/Kids', methods=['GET', 'POST'])
@login_required
def kids_elderly():
    return mongo_filter('Kids and Elderly')


@app.route('/record/Taxe', methods=['GET', 'POST'])
@login_required
def taxes():
    return mongo_filter('Taxes')


@app.route('/record/Othe', methods=['GET', 'POST'])
@login_required
def others():
    return mongo_filter('Others')


@app.route('/edit/<record_id>', methods=['GET', 'POST'])
@login_required
def edit(record_id):
    form = EditForm()
    delete_form = DeleteForm()
    connection = mongo.db.records
    record = connection.find_one({'_id': ObjectId(record_id)})
    if request.method == 'GET':
        form.category.data = record['category']
        form.currency.data = record['currency']
        form.amount.data = float(record['amount'])
        form.note.data = record['note']
    elif form.submit_update.data and form.validate_on_submit():
        connection.update({'_id': ObjectId(record_id)}, {'$set':
            {
                'category': request.form.get('category'),
                'currency': request.form.get('currency'),
                'amount': request.form.get('amount'),
                'note': request.form.get('note')
            }
        })
        flash('The Record Has Been Updated!', 'success')
        return redirect(url_for('record'))
    elif delete_form.submit_delete.data and delete_form.is_submitted():
        connection.delete_one({'_id': ObjectId(record_id)})
        flash('The Record Has Been Deleted!', 'success')
        return redirect(url_for('record'))
    return render_template('edit.html', title='Edit', form=form, record=record, delete_form=delete_form)


@app.route('/chart', methods=['GET', 'POST'])
@login_required
def chart():
    connection = mongo.db.records
    connection2 = mongo.db.records
    currency = connection2.find_one({'user_name': current_user.username})['currency']

    # Descending
    # records = connection.find({'user_name': current_user.username}).sort(
    #     [('date', pymongo.DESCENDING), ('time', pymongo.DESCENDING)])
    today = str(date.today())
    week_ago = str(date.today() - timedelta(7))
    month_ago = str(date.today() - timedelta(30))

    def mongo_filter_all(category):
        return connection.find({'user_name': current_user.username, 'category': category}).sort(
            [('date', pymongo.DESCENDING), ('time', pymongo.DESCENDING)])

    def mongo_filter_today(category):
        return connection.find({'user_name': current_user.username, 'category': category, 'date': today}).sort(
            [('date', pymongo.DESCENDING), ('time', pymongo.DESCENDING)])

    def mongo_filter_week(category):
        return connection.find({'user_name': current_user.username, 'category': category,
                                'date': {'$gt': week_ago}}).sort([('date', pymongo.DESCENDING),
                                                                  ('time', pymongo.DESCENDING)])

    def mongo_filter_month(category):
        return connection.find({'user_name': current_user.username, 'category': category,
                                'date': {'$gt': month_ago}}).sort([('date', pymongo.DESCENDING),
                                                                   ('time', pymongo.DESCENDING)])

    # Creating variables dynamically is an anti-pattern and should be avoided.
    category_01 = mongo_filter_all('Food and Dining')
    category_01_amount = 0
    for i in category_01:
        category_01_amount += float(i['amount'])
    category_01_show = mongo_filter_all('Food and Dining').limit(4)

    category_01_today = mongo_filter_today('Food and Dining')
    category_01_amount_today = 0
    for i in category_01_today:
        category_01_amount_today += float(i['amount'])
    category_01_show_today = mongo_filter_today('Food and Dining').limit(4)

    category_01_week = mongo_filter_week('Food and Dining')
    category_01_amount_week = 0
    for i in category_01_week:
        category_01_amount_week += float(i['amount'])
    category_01_show_week = mongo_filter_week('Food and Dining').limit(4)

    category_01_month = mongo_filter_month('Food and Dining')
    category_01_amount_month = 0
    for i in category_01_month:
        category_01_amount_month += float(i['amount'])
    category_01_show_month = mongo_filter_month('Food and Dining').limit(4)

    category_02 = mongo_filter_all('Bills and Utilities')
    category_02_amount = 0
    for i in category_02:
        category_02_amount += float(i['amount'])
    category_02_show = mongo_filter_all('Bills and Utilities').limit(4)

    category_02_today = mongo_filter_today('Bills and Utilities')
    category_02_amount_today = 0
    for i in category_02_today:
        category_02_amount_today += float(i['amount'])
    category_02_show_today = mongo_filter_today('Bills and Utilities').limit(4)

    category_02_week = mongo_filter_week('Bills and Utilities')
    category_02_amount_week = 0
    for i in category_02_week:
        category_02_amount_week += float(i['amount'])
    category_02_show_week = mongo_filter_week('Bills and Utilities').limit(4)

    category_02_month = mongo_filter_month('Bills and Utilities')
    category_02_amount_month = 0
    for i in category_02_month:
        category_02_amount_month += float(i['amount'])
    category_02_show_month = mongo_filter_month('Bills and Utilities').limit(4)

    category_03 = mongo_filter_all('Shopping')
    category_03_amount = 0
    for i in category_03:
        category_03_amount += float(i['amount'])
    category_03_show = mongo_filter_all('Shopping').limit(4)

    category_03_today = mongo_filter_today('Shopping')
    category_03_amount_today = 0
    for i in category_03_today:
        category_03_amount_today += float(i['amount'])
    category_03_show_today = mongo_filter_today('Shopping').limit(4)

    category_03_week = mongo_filter_week('Shopping')
    category_03_amount_week = 0
    for i in category_03_week:
        category_03_amount_week += float(i['amount'])
    category_03_show_week = mongo_filter_week('Shopping').limit(4)

    category_03_month = mongo_filter_month('Shopping')
    category_03_amount_month = 0
    for i in category_03_month:
        category_03_amount_month += float(i['amount'])
    category_03_show_month = mongo_filter_month('Shopping').limit(4)

    category_04 = mongo_filter_all('Entertainment')
    category_04_amount = 0
    for i in category_04:
        category_04_amount += float(i['amount'])
    category_04_show = mongo_filter_all('Entertainment').limit(4)

    category_04_today = mongo_filter_today('Entertainment')
    category_04_amount_today = 0
    for i in category_04_today:
        category_04_amount_today += float(i['amount'])
    category_04_show_today = mongo_filter_today('Entertainment').limit(4)

    category_04_week = mongo_filter_week('Entertainment')
    category_04_amount_week = 0
    for i in category_04_week:
        category_04_amount_week += float(i['amount'])
    category_04_show_week = mongo_filter_week('Entertainment').limit(4)

    category_04_month = mongo_filter_month('Entertainment')
    category_04_amount_month = 0
    for i in category_04_month:
        category_04_amount_month += float(i['amount'])
    category_04_show_month = mongo_filter_month('Entertainment').limit(4)

    category_05 = mongo_filter_all('Personal Care')
    category_05_amount = 0
    for i in category_05:
        category_05_amount += float(i['amount'])
    category_05_show = mongo_filter_all('Personal Care').limit(4)

    category_05_today = mongo_filter_today('Personal Care')
    category_05_amount_today = 0
    for i in category_05_today:
        category_05_amount_today += float(i['amount'])
    category_05_show_today = mongo_filter_today('Personal Care').limit(4)

    category_05_week = mongo_filter_week('Personal Care')
    category_05_amount_week = 0
    for i in category_05_week:
        category_05_amount_week += float(i['amount'])
    category_05_show_week = mongo_filter_week('Personal Care').limit(4)

    category_05_month = mongo_filter_month('Personal Care')
    category_05_amount_month = 0
    for i in category_05_month:
        category_05_amount_month += float(i['amount'])
    category_05_show_month = mongo_filter_month('Personal Care').limit(4)

    category_06 = mongo_filter_all('Health and Fitness')
    category_06_amount = 0
    for i in category_06:
        category_06_amount += float(i['amount'])
    category_06_show = mongo_filter_all('Health and Fitness').limit(4)

    category_06_today = mongo_filter_today('Health and Fitness')
    category_06_amount_today = 0
    for i in category_06_today:
        category_06_amount_today += float(i['amount'])
    category_06_show_today = mongo_filter_today('Health and Fitness').limit(4)

    category_06_week = mongo_filter_week('Health and Fitness')
    category_06_amount_week = 0
    for i in category_06_week:
        category_06_amount_week += float(i['amount'])
    category_06_show_week = mongo_filter_week('Health and Fitness').limit(4)

    category_06_month = mongo_filter_month('Health and Fitness')
    category_06_amount_month = 0
    for i in category_06_month:
        category_06_amount_month += float(i['amount'])
    category_06_show_month = mongo_filter_month('Health and Fitness').limit(4)

    category_07 = mongo_filter_all('Transport and Auto')
    category_07_amount = 0
    for i in category_07:
        category_07_amount += float(i['amount'])
    category_07_show = mongo_filter_all('Transport and Auto').limit(4)

    category_07_today = mongo_filter_today('Transport and Auto')
    category_07_amount_today = 0
    for i in category_07_today:
        category_07_amount_today += float(i['amount'])
    category_07_show_today = mongo_filter_today('Transport and Auto').limit(4)

    category_07_week = mongo_filter_week('Transport and Auto')
    category_07_amount_week = 0
    for i in category_07_week:
        category_07_amount_week += float(i['amount'])
    category_07_show_week = mongo_filter_week('Transport and Auto').limit(4)

    category_07_month = mongo_filter_month('Transport and Auto')
    category_07_amount_month = 0
    for i in category_07_month:
        category_07_amount_month += float(i['amount'])
    category_07_show_month = mongo_filter_month('Transport and Auto').limit(4)

    category_08 = mongo_filter_all('Fees and Charges')
    category_08_amount = 0
    for i in category_08:
        category_08_amount += float(i['amount'])
    category_08_show = mongo_filter_all('Fees and Charges').limit(4)

    category_08_today = mongo_filter_today('Fees and Charges')
    category_08_amount_today = 0
    for i in category_08_today:
        category_08_amount_today += float(i['amount'])
    category_08_show_today = mongo_filter_today('Fees and Charges').limit(4)

    category_08_week = mongo_filter_week('Fees and Charges')
    category_08_amount_week = 0
    for i in category_08_week:
        category_08_amount_week += float(i['amount'])
    category_08_show_week = mongo_filter_week('Fees and Charges').limit(4)

    category_08_month = mongo_filter_month('Fees and Charges')
    category_08_amount_month = 0
    for i in category_08_month:
        category_08_amount_month += float(i['amount'])
    category_08_show_month = mongo_filter_month('Fees and Charges').limit(4)

    category_09 = mongo_filter_all('Education')
    category_09_amount = 0
    for i in category_09:
        category_09_amount += float(i['amount'])
    category_09_show = mongo_filter_all('Education').limit(4)

    category_09_today = mongo_filter_today('Education')
    category_09_amount_today = 0
    for i in category_09_today:
        category_09_amount_today += float(i['amount'])
    category_09_show_today = mongo_filter_today('Education').limit(4)

    category_09_week = mongo_filter_week('Education')
    category_09_amount_week = 0
    for i in category_09_week:
        category_09_amount_week += float(i['amount'])
    category_09_show_week = mongo_filter_week('Education').limit(4)

    category_09_month = mongo_filter_month('Education')
    category_09_amount_month = 0
    for i in category_09_month:
        category_09_amount_month += float(i['amount'])
    category_09_show_month = mongo_filter_month('Education').limit(4)

    category_10 = mongo_filter_all('Gifts and Donation')
    category_10_amount = 0
    for i in category_10:
        category_10_amount += float(i['amount'])
    category_10_show = mongo_filter_all('Gifts and Donation').limit(4)

    category_10_today = mongo_filter_today('Gifts and Donation')
    category_10_amount_today = 0
    for i in category_10_today:
        category_10_amount_today += float(i['amount'])
    category_10_show_today = mongo_filter_today('Gifts and Donation').limit(4)

    category_10_week = mongo_filter_week('Gifts and Donation')
    category_10_amount_week = 0
    for i in category_10_week:
        category_10_amount_week += float(i['amount'])
    category_10_show_week = mongo_filter_week('Gifts and Donation').limit(4)

    category_10_month = mongo_filter_month('Gifts and Donation')
    category_10_amount_month = 0
    for i in category_10_month:
        category_10_amount_month += float(i['amount'])
    category_10_show_month = mongo_filter_month('Gifts and Donation').limit(4)

    category_11 = mongo_filter_all('Business Services')
    category_11_amount = 0
    for i in category_11:
        category_11_amount += float(i['amount'])
    category_11_show = mongo_filter_all('Business Services').limit(4)

    category_11_today = mongo_filter_today('Business Services')
    category_11_amount_today = 0
    for i in category_11_today:
        category_11_amount_today += float(i['amount'])
    category_11_show_today = mongo_filter_today('Business Services').limit(4)

    category_11_week = mongo_filter_week('Business Services')
    category_11_amount_week = 0
    for i in category_11_week:
        category_11_amount_week += float(i['amount'])
    category_11_show_week = mongo_filter_week('Business Services').limit(4)

    category_11_month = mongo_filter_month('Business Services')
    category_11_amount_month = 0
    for i in category_11_month:
        category_11_amount_month += float(i['amount'])
    category_11_show_month = mongo_filter_month('Business Services').limit(4)

    category_12 = mongo_filter_all('Investment')
    category_12_amount = 0
    for i in category_12:
        category_12_amount += float(i['amount'])
    category_12_show = mongo_filter_all('Investment').limit(4)

    category_12_today = mongo_filter_today('Investment')
    category_12_amount_today = 0
    for i in category_12_today:
        category_12_amount_today += float(i['amount'])
    category_12_show_today = mongo_filter_today('Investment').limit(4)

    category_12_week = mongo_filter_week('Investment')
    category_12_amount_week = 0
    for i in category_12_week:
        category_12_amount_week += float(i['amount'])
    category_12_show_week = mongo_filter_week('Investment').limit(4)

    category_12_month = mongo_filter_month('Investment')
    category_12_amount_month = 0
    for i in category_12_month:
        category_12_amount_month += float(i['amount'])
    category_12_show_month = mongo_filter_month('Investment').limit(4)

    category_13 = mongo_filter_all('Travel')
    category_13_amount = 0
    for i in category_13:
        category_13_amount += float(i['amount'])
    category_13_show = mongo_filter_all('Travel').limit(4)

    category_13_today = mongo_filter_today('Travel')
    category_13_amount_today = 0
    for i in category_13_today:
        category_13_amount_today += float(i['amount'])
    category_13_show_today = mongo_filter_today('Travel').limit(4)

    category_13_week = mongo_filter_week('Travel')
    category_13_amount_week = 0
    for i in category_13_week:
        category_13_amount_week += float(i['amount'])
    category_13_show_week = mongo_filter_week('Travel').limit(4)

    category_13_month = mongo_filter_month('Travel')
    category_13_amount_month = 0
    for i in category_13_month:
        category_13_amount_month += float(i['amount'])
    category_13_show_month = mongo_filter_month('Travel').limit(4)

    category_14 = mongo_filter_all('Kids and Elderly')
    category_14_amount = 0
    for i in category_14:
        category_14_amount += float(i['amount'])
    category_14_show = mongo_filter_all('Kids and Elderly').limit(4)

    category_14_today = mongo_filter_today('Kids and Elderly')
    category_14_amount_today = 0
    for i in category_14_today:
        category_14_amount_today += float(i['amount'])
    category_14_show_today = mongo_filter_today('Kids and Elderly').limit(4)

    category_14_week = mongo_filter_week('Kids and Elderly')
    category_14_amount_week = 0
    for i in category_14_week:
        category_14_amount_week += float(i['amount'])
    category_14_show_week = mongo_filter_week('Kids and Elderly').limit(4)

    category_14_month = mongo_filter_month('Kids and Elderly')
    category_14_amount_month = 0
    for i in category_14_month:
        category_14_amount_month += float(i['amount'])
    category_14_show_month = mongo_filter_month('Kids and Elderly').limit(4)

    category_15 = mongo_filter_all('Taxes')
    category_15_amount = 0
    for i in category_15:
        category_15_amount += float(i['amount'])
    category_15_show = mongo_filter_all('Taxes').limit(4)

    category_15_today = mongo_filter_today('Taxes')
    category_15_amount_today = 0
    for i in category_15_today:
        category_15_amount_today += float(i['amount'])
    category_15_show_today = mongo_filter_today('Taxes').limit(4)

    category_15_week = mongo_filter_week('Taxes')
    category_15_amount_week = 0
    for i in category_15_week:
        category_15_amount_week += float(i['amount'])
    category_15_show_week = mongo_filter_week('Taxes').limit(4)

    category_15_month = mongo_filter_month('Taxes')
    category_15_amount_month = 0
    for i in category_15_month:
        category_15_amount_month += float(i['amount'])
    category_15_show_month = mongo_filter_month('Taxes').limit(4)

    category_16 = mongo_filter_all('Others')
    category_16_amount = 0
    for i in category_16:
        category_16_amount += float(i['amount'])
    category_16_show = mongo_filter_all('Others').limit(4)

    category_16_today = mongo_filter_today('Others')
    category_16_amount_today = 0
    for i in category_16_today:
        category_16_amount_today += float(i['amount'])
    category_16_show_today = mongo_filter_today('Others').limit(4)

    category_16_week = mongo_filter_week('Others')
    category_16_amount_week = 0
    for i in category_16_week:
        category_16_amount_week += float(i['amount'])
    category_16_show_week = mongo_filter_week('Others').limit(4)

    category_16_month = mongo_filter_month('Others')
    category_16_amount_month = 0
    for i in category_16_month:
        category_16_amount_month += float(i['amount'])
    category_16_show_month = mongo_filter_month('Others').limit(4)

    category_amount_show_list = [(category_01_amount, category_01_show), (category_02_amount, category_02_show),
                                 (category_03_amount, category_03_show), (category_04_amount, category_04_show),
                                 (category_05_amount, category_05_show), (category_06_amount, category_06_show),
                                 (category_07_amount, category_07_show), (category_08_amount, category_08_show),
                                 (category_09_amount, category_09_show), (category_10_amount, category_10_show),
                                 (category_11_amount, category_11_show), (category_12_amount, category_12_show),
                                 (category_13_amount, category_13_show), (category_14_amount, category_14_show),
                                 (category_15_amount, category_15_show), (category_16_amount, category_16_show)]

    total_amount_all = 0
    for i in category_amount_show_list:
        (a, b) = i
        total_amount_all += a
    total_amount_all = round(total_amount_all, 2)

    category_amount_show_today_list = [(category_01_amount_today, category_01_show_today),
                                       (category_02_amount_today, category_02_show_today),
                                       (category_03_amount_today, category_03_show_today),
                                       (category_04_amount_today, category_04_show_today),
                                       (category_05_amount_today, category_05_show_today),
                                       (category_06_amount_today, category_06_show_today),
                                       (category_07_amount_today, category_07_show_today),
                                       (category_08_amount_today, category_08_show_today),
                                       (category_09_amount_today, category_09_show_today),
                                       (category_10_amount_today, category_10_show_today),
                                       (category_11_amount_today, category_11_show_today),
                                       (category_12_amount_today, category_12_show_today),
                                       (category_13_amount_today, category_13_show_today),
                                       (category_14_amount_today, category_14_show_today),
                                       (category_15_amount_today, category_15_show_today),
                                       (category_16_amount_today, category_16_show_today)]

    total_amount_today = 0
    for i in category_amount_show_today_list:
        (a, b) = i
        total_amount_today += a
    total_amount_today = round(total_amount_today, 2)

    category_amount_show_week_list = [(category_01_amount_week, category_01_show_week),
                                      (category_02_amount_week, category_02_show_week),
                                      (category_03_amount_week, category_03_show_week),
                                      (category_04_amount_week, category_04_show_week),
                                      (category_05_amount_week, category_05_show_week),
                                      (category_06_amount_week, category_06_show_week),
                                      (category_07_amount_week, category_07_show_week),
                                      (category_08_amount_week, category_08_show_week),
                                      (category_09_amount_week, category_09_show_week),
                                      (category_10_amount_week, category_10_show_week),
                                      (category_11_amount_week, category_11_show_week),
                                      (category_12_amount_week, category_12_show_week),
                                      (category_13_amount_week, category_13_show_week),
                                      (category_14_amount_week, category_14_show_week),
                                      (category_15_amount_week, category_15_show_week),
                                      (category_16_amount_week, category_16_show_week)]

    total_amount_week = 0
    for i in category_amount_show_week_list:
        (a, b) = i
        total_amount_week += a
    total_amount_week = round(total_amount_week, 2)

    category_amount_show_month_list = [(category_01_amount_month, category_01_show_month),
                                       (category_02_amount_month, category_02_show_month),
                                       (category_03_amount_month, category_03_show_month),
                                       (category_04_amount_month, category_04_show_month),
                                       (category_05_amount_month, category_05_show_month),
                                       (category_06_amount_month, category_06_show_month),
                                       (category_07_amount_month, category_07_show_month),
                                       (category_08_amount_month, category_08_show_month),
                                       (category_09_amount_month, category_09_show_month),
                                       (category_10_amount_month, category_10_show_month),
                                       (category_11_amount_month, category_11_show_month),
                                       (category_12_amount_month, category_12_show_month),
                                       (category_13_amount_month, category_13_show_month),
                                       (category_14_amount_month, category_14_show_month),
                                       (category_15_amount_month, category_15_show_month),
                                       (category_16_amount_month, category_16_show_month)]

    total_amount_month = 0
    for i in category_amount_show_month_list:
        (a, b) = i
        total_amount_month += a
    total_amount_month = round(total_amount_month, 2)

    sorted_by_amount_all = sorted(category_amount_show_list, key=lambda tup: tup[0], reverse=True)
    sorted_by_amount_today = sorted(category_amount_show_today_list, key=lambda tup: tup[0], reverse=True)
    sorted_by_amount_week = sorted(category_amount_show_week_list, key=lambda tup: tup[0], reverse=True)
    sorted_by_amount_month = sorted(category_amount_show_month_list, key=lambda tup: tup[0], reverse=True)

    return render_template('chart.html', title='Chart', sorted_by_amount_all=sorted_by_amount_all,
                           sorted_by_amount_today=sorted_by_amount_today, sorted_by_amount_week=sorted_by_amount_week,
                           sorted_by_amount_month=sorted_by_amount_month, currency=currency,
                           total_amount_today=total_amount_today, total_amount_week=total_amount_week,
                           total_amount_month=total_amount_month, total_amount_all=total_amount_all)


@app.route('/record', methods=['GET', 'POST'])
@login_required
def record():
    form = EditForm()
    connection = mongo.db.records
    connection2 = mongo.db.records
    currency = connection2.find_one({'user_name': current_user.username})['currency']

    # Descending
    # records = connection.find({'user_name': current_user.username}).sort(
    #     [('date', pymongo.DESCENDING), ('time', pymongo.DESCENDING)])
    today = str(date.today())
    week_ago = str(date.today() - timedelta(7))
    month_ago = str(date.today() - timedelta(30))

    def mongo_filter_all(category):
        return connection.find({'user_name': current_user.username, 'category': category}).sort(
            [('date', pymongo.DESCENDING), ('time', pymongo.DESCENDING)])

    def mongo_filter_today(category):
        return connection.find({'user_name': current_user.username, 'category': category, 'date': today}).sort(
            [('date', pymongo.DESCENDING), ('time', pymongo.DESCENDING)])

    def mongo_filter_week(category):
        return connection.find({'user_name': current_user.username, 'category': category,
                                'date': {'$gt': week_ago}}).sort([('date', pymongo.DESCENDING),
                                                                  ('time', pymongo.DESCENDING)])

    def mongo_filter_month(category):
        return connection.find({'user_name': current_user.username, 'category': category,
                                'date': {'$gt': month_ago}}).sort([('date', pymongo.DESCENDING),
                                                                   ('time', pymongo.DESCENDING)])

    # Creating variables dynamically is an anti-pattern and should be avoided.
    category_01 = mongo_filter_all('Food and Dining')
    category_01_amount = 0
    for i in category_01:
        category_01_amount += float(i['amount'])
    category_01_show = mongo_filter_all('Food and Dining').limit(4)

    category_01_today = mongo_filter_today('Food and Dining')
    category_01_amount_today = 0
    for i in category_01_today:
        category_01_amount_today += float(i['amount'])
    category_01_show_today = mongo_filter_today('Food and Dining').limit(4)

    category_01_week = mongo_filter_week('Food and Dining')
    category_01_amount_week = 0
    for i in category_01_week:
        category_01_amount_week += float(i['amount'])
    category_01_show_week = mongo_filter_week('Food and Dining').limit(4)

    category_01_month = mongo_filter_month('Food and Dining')
    category_01_amount_month = 0
    for i in category_01_month:
        category_01_amount_month += float(i['amount'])
    category_01_show_month = mongo_filter_month('Food and Dining').limit(4)

    category_02 = mongo_filter_all('Bills and Utilities')
    category_02_amount = 0
    for i in category_02:
        category_02_amount += float(i['amount'])
    category_02_show = mongo_filter_all('Bills and Utilities').limit(4)

    category_02_today = mongo_filter_today('Bills and Utilities')
    category_02_amount_today = 0
    for i in category_02_today:
        category_02_amount_today += float(i['amount'])
    category_02_show_today = mongo_filter_today('Bills and Utilities').limit(4)

    category_02_week = mongo_filter_week('Bills and Utilities')
    category_02_amount_week = 0
    for i in category_02_week:
        category_02_amount_week += float(i['amount'])
    category_02_show_week = mongo_filter_week('Bills and Utilities').limit(4)

    category_02_month = mongo_filter_month('Bills and Utilities')
    category_02_amount_month = 0
    for i in category_02_month:
        category_02_amount_month += float(i['amount'])
    category_02_show_month = mongo_filter_month('Bills and Utilities').limit(4)

    category_03 = mongo_filter_all('Shopping')
    category_03_amount = 0
    for i in category_03:
        category_03_amount += float(i['amount'])
    category_03_show = mongo_filter_all('Shopping').limit(4)

    category_03_today = mongo_filter_today('Shopping')
    category_03_amount_today = 0
    for i in category_03_today:
        category_03_amount_today += float(i['amount'])
    category_03_show_today = mongo_filter_today('Shopping').limit(4)

    category_03_week = mongo_filter_week('Shopping')
    category_03_amount_week = 0
    for i in category_03_week:
        category_03_amount_week += float(i['amount'])
    category_03_show_week = mongo_filter_week('Shopping').limit(4)

    category_03_month = mongo_filter_month('Shopping')
    category_03_amount_month = 0
    for i in category_03_month:
        category_03_amount_month += float(i['amount'])
    category_03_show_month = mongo_filter_month('Shopping').limit(4)

    category_04 = mongo_filter_all('Entertainment')
    category_04_amount = 0
    for i in category_04:
        category_04_amount += float(i['amount'])
    category_04_show = mongo_filter_all('Entertainment').limit(4)

    category_04_today = mongo_filter_today('Entertainment')
    category_04_amount_today = 0
    for i in category_04_today:
        category_04_amount_today += float(i['amount'])
    category_04_show_today = mongo_filter_today('Entertainment').limit(4)

    category_04_week = mongo_filter_week('Entertainment')
    category_04_amount_week = 0
    for i in category_04_week:
        category_04_amount_week += float(i['amount'])
    category_04_show_week = mongo_filter_week('Entertainment').limit(4)

    category_04_month = mongo_filter_month('Entertainment')
    category_04_amount_month = 0
    for i in category_04_month:
        category_04_amount_month += float(i['amount'])
    category_04_show_month = mongo_filter_month('Entertainment').limit(4)

    category_05 = mongo_filter_all('Personal Care')
    category_05_amount = 0
    for i in category_05:
        category_05_amount += float(i['amount'])
    category_05_show = mongo_filter_all('Personal Care').limit(4)

    category_05_today = mongo_filter_today('Personal Care')
    category_05_amount_today = 0
    for i in category_05_today:
        category_05_amount_today += float(i['amount'])
    category_05_show_today = mongo_filter_today('Personal Care').limit(4)

    category_05_week = mongo_filter_week('Personal Care')
    category_05_amount_week = 0
    for i in category_05_week:
        category_05_amount_week += float(i['amount'])
    category_05_show_week = mongo_filter_week('Personal Care').limit(4)

    category_05_month = mongo_filter_month('Personal Care')
    category_05_amount_month = 0
    for i in category_05_month:
        category_05_amount_month += float(i['amount'])
    category_05_show_month = mongo_filter_month('Personal Care').limit(4)

    category_06 = mongo_filter_all('Health and Fitness')
    category_06_amount = 0
    for i in category_06:
        category_06_amount += float(i['amount'])
    category_06_show = mongo_filter_all('Health and Fitness').limit(4)

    category_06_today = mongo_filter_today('Health and Fitness')
    category_06_amount_today = 0
    for i in category_06_today:
        category_06_amount_today += float(i['amount'])
    category_06_show_today = mongo_filter_today('Health and Fitness').limit(4)

    category_06_week = mongo_filter_week('Health and Fitness')
    category_06_amount_week = 0
    for i in category_06_week:
        category_06_amount_week += float(i['amount'])
    category_06_show_week = mongo_filter_week('Health and Fitness').limit(4)

    category_06_month = mongo_filter_month('Health and Fitness')
    category_06_amount_month = 0
    for i in category_06_month:
        category_06_amount_month += float(i['amount'])
    category_06_show_month = mongo_filter_month('Health and Fitness').limit(4)

    category_07 = mongo_filter_all('Transport and Auto')
    category_07_amount = 0
    for i in category_07:
        category_07_amount += float(i['amount'])
    category_07_show = mongo_filter_all('Transport and Auto').limit(4)

    category_07_today = mongo_filter_today('Transport and Auto')
    category_07_amount_today = 0
    for i in category_07_today:
        category_07_amount_today += float(i['amount'])
    category_07_show_today = mongo_filter_today('Transport and Auto').limit(4)

    category_07_week = mongo_filter_week('Transport and Auto')
    category_07_amount_week = 0
    for i in category_07_week:
        category_07_amount_week += float(i['amount'])
    category_07_show_week = mongo_filter_week('Transport and Auto').limit(4)

    category_07_month = mongo_filter_month('Transport and Auto')
    category_07_amount_month = 0
    for i in category_07_month:
        category_07_amount_month += float(i['amount'])
    category_07_show_month = mongo_filter_month('Transport and Auto').limit(4)

    category_08 = mongo_filter_all('Fees and Charges')
    category_08_amount = 0
    for i in category_08:
        category_08_amount += float(i['amount'])
    category_08_show = mongo_filter_all('Fees and Charges').limit(4)

    category_08_today = mongo_filter_today('Fees and Charges')
    category_08_amount_today = 0
    for i in category_08_today:
        category_08_amount_today += float(i['amount'])
    category_08_show_today = mongo_filter_today('Fees and Charges').limit(4)

    category_08_week = mongo_filter_week('Fees and Charges')
    category_08_amount_week = 0
    for i in category_08_week:
        category_08_amount_week += float(i['amount'])
    category_08_show_week = mongo_filter_week('Fees and Charges').limit(4)

    category_08_month = mongo_filter_month('Fees and Charges')
    category_08_amount_month = 0
    for i in category_08_month:
        category_08_amount_month += float(i['amount'])
    category_08_show_month = mongo_filter_month('Fees and Charges').limit(4)

    category_09 = mongo_filter_all('Education')
    category_09_amount = 0
    for i in category_09:
        category_09_amount += float(i['amount'])
    category_09_show = mongo_filter_all('Education').limit(4)

    category_09_today = mongo_filter_today('Education')
    category_09_amount_today = 0
    for i in category_09_today:
        category_09_amount_today += float(i['amount'])
    category_09_show_today = mongo_filter_today('Education').limit(4)

    category_09_week = mongo_filter_week('Education')
    category_09_amount_week = 0
    for i in category_09_week:
        category_09_amount_week += float(i['amount'])
    category_09_show_week = mongo_filter_week('Education').limit(4)

    category_09_month = mongo_filter_month('Education')
    category_09_amount_month = 0
    for i in category_09_month:
        category_09_amount_month += float(i['amount'])
    category_09_show_month = mongo_filter_month('Education').limit(4)

    category_10 = mongo_filter_all('Gifts and Donation')
    category_10_amount = 0
    for i in category_10:
        category_10_amount += float(i['amount'])
    category_10_show = mongo_filter_all('Gifts and Donation').limit(4)

    category_10_today = mongo_filter_today('Gifts and Donation')
    category_10_amount_today = 0
    for i in category_10_today:
        category_10_amount_today += float(i['amount'])
    category_10_show_today = mongo_filter_today('Gifts and Donation').limit(4)

    category_10_week = mongo_filter_week('Gifts and Donation')
    category_10_amount_week = 0
    for i in category_10_week:
        category_10_amount_week += float(i['amount'])
    category_10_show_week = mongo_filter_week('Gifts and Donation').limit(4)

    category_10_month = mongo_filter_month('Gifts and Donation')
    category_10_amount_month = 0
    for i in category_10_month:
        category_10_amount_month += float(i['amount'])
    category_10_show_month = mongo_filter_month('Gifts and Donation').limit(4)

    category_11 = mongo_filter_all('Business Services')
    category_11_amount = 0
    for i in category_11:
        category_11_amount += float(i['amount'])
    category_11_show = mongo_filter_all('Business Services').limit(4)

    category_11_today = mongo_filter_today('Business Services')
    category_11_amount_today = 0
    for i in category_11_today:
        category_11_amount_today += float(i['amount'])
    category_11_show_today = mongo_filter_today('Business Services').limit(4)

    category_11_week = mongo_filter_week('Business Services')
    category_11_amount_week = 0
    for i in category_11_week:
        category_11_amount_week += float(i['amount'])
    category_11_show_week = mongo_filter_week('Business Services').limit(4)

    category_11_month = mongo_filter_month('Business Services')
    category_11_amount_month = 0
    for i in category_11_month:
        category_11_amount_month += float(i['amount'])
    category_11_show_month = mongo_filter_month('Business Services').limit(4)

    category_12 = mongo_filter_all('Investment')
    category_12_amount = 0
    for i in category_12:
        category_12_amount += float(i['amount'])
    category_12_show = mongo_filter_all('Investment').limit(4)

    category_12_today = mongo_filter_today('Investment')
    category_12_amount_today = 0
    for i in category_12_today:
        category_12_amount_today += float(i['amount'])
    category_12_show_today = mongo_filter_today('Investment').limit(4)

    category_12_week = mongo_filter_week('Investment')
    category_12_amount_week = 0
    for i in category_12_week:
        category_12_amount_week += float(i['amount'])
    category_12_show_week = mongo_filter_week('Investment').limit(4)

    category_12_month = mongo_filter_month('Investment')
    category_12_amount_month = 0
    for i in category_12_month:
        category_12_amount_month += float(i['amount'])
    category_12_show_month = mongo_filter_month('Investment').limit(4)

    category_13 = mongo_filter_all('Travel')
    category_13_amount = 0
    for i in category_13:
        category_13_amount += float(i['amount'])
    category_13_show = mongo_filter_all('Travel').limit(4)

    category_13_today = mongo_filter_today('Travel')
    category_13_amount_today = 0
    for i in category_13_today:
        category_13_amount_today += float(i['amount'])
    category_13_show_today = mongo_filter_today('Travel').limit(4)

    category_13_week = mongo_filter_week('Travel')
    category_13_amount_week = 0
    for i in category_13_week:
        category_13_amount_week += float(i['amount'])
    category_13_show_week = mongo_filter_week('Travel').limit(4)

    category_13_month = mongo_filter_month('Travel')
    category_13_amount_month = 0
    for i in category_13_month:
        category_13_amount_month += float(i['amount'])
    category_13_show_month = mongo_filter_month('Travel').limit(4)

    category_14 = mongo_filter_all('Kids and Elderly')
    category_14_amount = 0
    for i in category_14:
        category_14_amount += float(i['amount'])
    category_14_show = mongo_filter_all('Kids and Elderly').limit(4)

    category_14_today = mongo_filter_today('Kids and Elderly')
    category_14_amount_today = 0
    for i in category_14_today:
        category_14_amount_today += float(i['amount'])
    category_14_show_today = mongo_filter_today('Kids and Elderly').limit(4)

    category_14_week = mongo_filter_week('Kids and Elderly')
    category_14_amount_week = 0
    for i in category_14_week:
        category_14_amount_week += float(i['amount'])
    category_14_show_week = mongo_filter_week('Kids and Elderly').limit(4)

    category_14_month = mongo_filter_month('Kids and Elderly')
    category_14_amount_month = 0
    for i in category_14_month:
        category_14_amount_month += float(i['amount'])
    category_14_show_month = mongo_filter_month('Kids and Elderly').limit(4)

    category_15 = mongo_filter_all('Taxes')
    category_15_amount = 0
    for i in category_15:
        category_15_amount += float(i['amount'])
    category_15_show = mongo_filter_all('Taxes').limit(4)

    category_15_today = mongo_filter_today('Taxes')
    category_15_amount_today = 0
    for i in category_15_today:
        category_15_amount_today += float(i['amount'])
    category_15_show_today = mongo_filter_today('Taxes').limit(4)

    category_15_week = mongo_filter_week('Taxes')
    category_15_amount_week = 0
    for i in category_15_week:
        category_15_amount_week += float(i['amount'])
    category_15_show_week = mongo_filter_week('Taxes').limit(4)

    category_15_month = mongo_filter_month('Taxes')
    category_15_amount_month = 0
    for i in category_15_month:
        category_15_amount_month += float(i['amount'])
    category_15_show_month = mongo_filter_month('Taxes').limit(4)

    category_16 = mongo_filter_all('Others')
    category_16_amount = 0
    for i in category_16:
        category_16_amount += float(i['amount'])
    category_16_show = mongo_filter_all('Others').limit(4)

    category_16_today = mongo_filter_today('Others')
    category_16_amount_today = 0
    for i in category_16_today:
        category_16_amount_today += float(i['amount'])
    category_16_show_today = mongo_filter_today('Others').limit(4)

    category_16_week = mongo_filter_week('Others')
    category_16_amount_week = 0
    for i in category_16_week:
        category_16_amount_week += float(i['amount'])
    category_16_show_week = mongo_filter_week('Others').limit(4)

    category_16_month = mongo_filter_month('Others')
    category_16_amount_month = 0
    for i in category_16_month:
        category_16_amount_month += float(i['amount'])
    category_16_show_month = mongo_filter_month('Others').limit(4)

    category_amount_show_list = [(category_01_amount, category_01_show), (category_02_amount, category_02_show),
                                 (category_03_amount, category_03_show), (category_04_amount, category_04_show),
                                 (category_05_amount, category_05_show), (category_06_amount, category_06_show),
                                 (category_07_amount, category_07_show), (category_08_amount, category_08_show),
                                 (category_09_amount, category_09_show), (category_10_amount, category_10_show),
                                 (category_11_amount, category_11_show), (category_12_amount, category_12_show),
                                 (category_13_amount, category_13_show), (category_14_amount, category_14_show),
                                 (category_15_amount, category_15_show), (category_16_amount, category_16_show)]

    total_amount_all = 0
    for i in category_amount_show_list:
        (a, b) = i
        total_amount_all += a
    total_amount_all = round(total_amount_all, 2)

    category_amount_show_today_list = [(category_01_amount_today, category_01_show_today),
                                       (category_02_amount_today, category_02_show_today),
                                       (category_03_amount_today, category_03_show_today),
                                       (category_04_amount_today, category_04_show_today),
                                       (category_05_amount_today, category_05_show_today),
                                       (category_06_amount_today, category_06_show_today),
                                       (category_07_amount_today, category_07_show_today),
                                       (category_08_amount_today, category_08_show_today),
                                       (category_09_amount_today, category_09_show_today),
                                       (category_10_amount_today, category_10_show_today),
                                       (category_11_amount_today, category_11_show_today),
                                       (category_12_amount_today, category_12_show_today),
                                       (category_13_amount_today, category_13_show_today),
                                       (category_14_amount_today, category_14_show_today),
                                       (category_15_amount_today, category_15_show_today),
                                       (category_16_amount_today, category_16_show_today)]

    total_amount_today = 0
    for i in category_amount_show_today_list:
        (a, b) = i
        total_amount_today += a
    total_amount_today = round(total_amount_today, 2)

    category_amount_show_week_list = [(category_01_amount_week, category_01_show_week),
                                      (category_02_amount_week, category_02_show_week),
                                      (category_03_amount_week, category_03_show_week),
                                      (category_04_amount_week, category_04_show_week),
                                      (category_05_amount_week, category_05_show_week),
                                      (category_06_amount_week, category_06_show_week),
                                      (category_07_amount_week, category_07_show_week),
                                      (category_08_amount_week, category_08_show_week),
                                      (category_09_amount_week, category_09_show_week),
                                      (category_10_amount_week, category_10_show_week),
                                      (category_11_amount_week, category_11_show_week),
                                      (category_12_amount_week, category_12_show_week),
                                      (category_13_amount_week, category_13_show_week),
                                      (category_14_amount_week, category_14_show_week),
                                      (category_15_amount_week, category_15_show_week),
                                      (category_16_amount_week, category_16_show_week)]

    total_amount_week = 0
    for i in category_amount_show_week_list:
        (a, b) = i
        total_amount_week += a
    total_amount_week = round(total_amount_week, 2)

    category_amount_show_month_list = [(category_01_amount_month, category_01_show_month),
                                       (category_02_amount_month, category_02_show_month),
                                       (category_03_amount_month, category_03_show_month),
                                       (category_04_amount_month, category_04_show_month),
                                       (category_05_amount_month, category_05_show_month),
                                       (category_06_amount_month, category_06_show_month),
                                       (category_07_amount_month, category_07_show_month),
                                       (category_08_amount_month, category_08_show_month),
                                       (category_09_amount_month, category_09_show_month),
                                       (category_10_amount_month, category_10_show_month),
                                       (category_11_amount_month, category_11_show_month),
                                       (category_12_amount_month, category_12_show_month),
                                       (category_13_amount_month, category_13_show_month),
                                       (category_14_amount_month, category_14_show_month),
                                       (category_15_amount_month, category_15_show_month),
                                       (category_16_amount_month, category_16_show_month)]

    total_amount_month = 0
    for i in category_amount_show_month_list:
        (a, b) = i
        total_amount_month += a
    total_amount_month = round(total_amount_month, 2)

    sorted_by_amount_all = sorted(category_amount_show_list, key=lambda tup: tup[0], reverse=True)
    sorted_by_amount_today = sorted(category_amount_show_today_list, key=lambda tup: tup[0], reverse=True)
    sorted_by_amount_week = sorted(category_amount_show_week_list, key=lambda tup: tup[0], reverse=True)
    sorted_by_amount_month = sorted(category_amount_show_month_list, key=lambda tup: tup[0], reverse=True)

    return render_template('record.html', title='Record', form=form, sorted_by_amount_all=sorted_by_amount_all,
                           sorted_by_amount_today=sorted_by_amount_today, sorted_by_amount_week=sorted_by_amount_week,
                           sorted_by_amount_month=sorted_by_amount_month, currency=currency,
                           total_amount_today=total_amount_today, total_amount_week=total_amount_week,
                           total_amount_month=total_amount_month, total_amount_all=total_amount_all)


def send_reset_email(user, user_id, user_fname, user_lname):
    token = get_reset_token(user_id)
    msg = Message('Wallet Watcher Password Reset Request -- {} {}'.format(user_fname, user_lname),
                  sender='noreply@googlemail.com',
                  recipients=[user, 'raymondcyang0219@gmail.com'])
    msg.body = '''To reset your password, visit the following link:
{}
If you did not make this request then simply ignore this email and no changes will be made.
'''.format(url_for('reset_token', token=token, _external=True))
    mail.send(msg)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('enter'))
    form = RequestResetForm()
    if form.validate_on_submit():
        connection = mongo.db.users
        user = connection.find_one({'email': form.email.data})
        user_id = str(user['_id'])
        user_fname = user['first_name']
        user_lname = user['last_name']
        send_reset_email(form.email.data, user_id, user_fname, user_lname)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    connection = mongo.db.users
    if current_user.is_authenticated:
        return redirect(url_for('enter'))
    user = verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        connection.update({'_id': ObjectId(user['_id'])}, {'$set': {'password': hashed_password}})
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

