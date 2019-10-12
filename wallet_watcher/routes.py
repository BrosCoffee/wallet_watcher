import os
import secrets
from flask import render_template, url_for, flash, redirect, request
from wallet_watcher.form import RegistrationForm, LoginForm, ContactForm, EnterForm, EditForm, DeleteForm, \
    UpdateAccountForm
from wallet_watcher import app, mongo, bcrypt, login_manager
import time
import pymongo
from flask_login import UserMixin, current_user, login_user, logout_user, login_required
from bson.objectid import ObjectId

client = pymongo.MongoClient(host='localhost', port=27017)
db = client.wallet_watcher


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
        print(form.currency.data)
        print(user['user_name'])
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
# ---------->


def mongo_filter(category):
    form = EditForm()
    connection = mongo.db.records
    # Descending
    records = connection.find({'user_name': current_user.username, 'category': category}).sort(
        [("date", pymongo.DESCENDING), ("time", pymongo.DESCENDING)])
    return render_template('record_filter.html', title=category, records=records, form=form)


@app.route('/record/Food', methods=['GET', 'POST'])
@login_required
def food_dining():
    return mongo_filter('Food & Dining')


@app.route('/record/Bill', methods=['GET', 'POST'])
@login_required
def bill():
    return mongo_filter('Bills & Utilities')


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
    return mongo_filter('Health & Fitness')


@app.route('/record/Tran', methods=['GET', 'POST'])
@login_required
def transport():
    return mongo_filter('Transport & Auto')


@app.route('/record/Fees', methods=['GET', 'POST'])
@login_required
def fees():
    return mongo_filter('Fees & Charges')


@app.route('/record/Educ', methods=['GET', 'POST'])
@login_required
def education():
    return mongo_filter('Education')


@app.route('/record/Gift', methods=['GET', 'POST'])
@login_required
def gift():
    return mongo_filter('Gifts & Donation')


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
    return mongo_filter('Kids & Elderly')


@app.route('/record/Taxe', methods=['GET', 'POST'])
@login_required
def taxes():
    return mongo_filter('Taxes')


@app.route('/record/Othe', methods=['GET', 'POST'])
@login_required
def others():
    return mongo_filter('Others')
# ---------->


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


@app.route('/summary')
@login_required
def summary():
    return render_template('summary.html', title='Summary')


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

    def mongo_filter(category):
        return connection.find({'user_name': current_user.username, 'category': category}).sort(
            [('date', pymongo.DESCENDING), ('time', pymongo.DESCENDING)])

    # Creating variables dynamically is an anti-pattern and should be avoided.
    category_01 = mongo_filter('Food & Dining')
    category_01_amount = 0
    for i in category_01:
        category_01_amount += float(i['amount'])
    category_01_show = mongo_filter('Food & Dining').limit(4)

    category_02 = mongo_filter('Bills & Utilities')
    category_02_amount = 0
    for i in category_02:
        category_02_amount += float(i['amount'])
    category_02_show = mongo_filter('Bills & Utilities').limit(4)

    category_03 = mongo_filter('Shopping')
    category_03_amount = 0
    for i in category_03:
        category_03_amount += float(i['amount'])
    category_03_show = mongo_filter('Shopping').limit(4)

    category_04 = mongo_filter('Entertainment')
    category_04_amount = 0
    for i in category_04:
        category_04_amount += float(i['amount'])
    category_04_show = mongo_filter('Entertainment').limit(4)

    category_05 = mongo_filter('Personal Care')
    category_05_amount = 0
    for i in category_05:
        category_05_amount += float(i['amount'])
    category_05_show = mongo_filter('Personal Care').limit(4)

    category_06 = mongo_filter('Health & Fitness')
    category_06_amount = 0
    for i in category_06:
        category_06_amount += float(i['amount'])
    category_06_show = mongo_filter('Health & Fitness').limit(4)

    category_07 = mongo_filter('Transport & Auto')
    category_07_amount = 0
    for i in category_07:
        category_07_amount += float(i['amount'])
    category_07_show = mongo_filter('Transport & Auto').limit(4)

    category_08 = mongo_filter('Fees & Charges')
    category_08_amount = 0
    for i in category_08:
        category_08_amount += float(i['amount'])
    category_08_show = mongo_filter('Fees & Charges').limit(4)

    category_09 = mongo_filter('Education')
    category_09_amount = 0
    for i in category_09:
        category_09_amount += float(i['amount'])
    category_09_show = mongo_filter('Education').limit(4)

    category_10 = mongo_filter('Gifts & Donation')
    category_10_amount = 0
    for i in category_10:
        category_10_amount += float(i['amount'])
    category_10_show = mongo_filter('Gifts & Donation').limit(4)

    category_11 = mongo_filter('Business Services')
    category_11_amount = 0
    for i in category_11:
        category_11_amount += float(i['amount'])
    category_11_show = mongo_filter('Business Services').limit(4)

    category_12 = mongo_filter('Investment')
    category_12_amount = 0
    for i in category_12:
        category_12_amount += float(i['amount'])
    category_12_show = mongo_filter('Investment').limit(4)

    category_13 = mongo_filter('Travel')
    category_13_amount = 0
    for i in category_13:
        category_13_amount += float(i['amount'])
    category_13_show = mongo_filter('Travel').limit(4)

    category_14 = mongo_filter('Kids & Elderly')
    category_14_amount = 0
    for i in category_14:
        category_14_amount += float(i['amount'])
    category_14_show = mongo_filter('Kids & Elderly').limit(4)

    category_15 = mongo_filter('Taxes')
    category_15_amount = 0
    for i in category_15:
        category_15_amount += float(i['amount'])
    category_15_show = mongo_filter('Taxes').limit(4)

    category_16 = mongo_filter('Others')
    category_16_amount = 0
    for i in category_16:
        category_16_amount += float(i['amount'])
    category_16_show = mongo_filter('Others').limit(4)

    category_amount_show_list = [(category_01_amount, category_01_show), (category_02_amount, category_02_show),
                                 (category_03_amount, category_03_show), (category_04_amount, category_04_show),
                                 (category_05_amount, category_05_show), (category_06_amount, category_06_show),
                                 (category_07_amount, category_07_show), (category_08_amount, category_08_show),
                                 (category_09_amount, category_09_show), (category_10_amount, category_10_show),
                                 (category_11_amount, category_11_show), (category_12_amount, category_12_show),
                                 (category_13_amount, category_13_show), (category_14_amount, category_14_show),
                                 (category_15_amount, category_15_show), (category_16_amount, category_16_show)]
    sorted_by_amount = sorted(category_amount_show_list, key=lambda tup: tup[0], reverse=True)

    return render_template('record.html', title='History', form=form, sorted_by_amount=sorted_by_amount,
                           currency=currency)
