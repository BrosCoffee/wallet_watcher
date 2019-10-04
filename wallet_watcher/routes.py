from flask import render_template, url_for, flash, redirect, request
from wallet_watcher.form import RegistrationForm, LoginForm, ContactForm, EnterForm, EditForm, DeleteForm
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
        result = collection.find_one({'email': form.email.data})
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
        user = mongo.db.users.find_one({"email": form.email.data})
        if user and User.check_password():
            user_obj = User(username=user['user_name'])
            login_user(user_obj, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Welcome back, {}!'.format(user['first_name']), 'success')
            return redirect(next_page) if next_page else redirect(url_for('history'))
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

        connection.insert({'user_name': request.form.get('username'),
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


@app.route('/account')
@login_required
def account():
    return render_template('account.html', title='Account')


@app.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    form = EditForm()
    connection = mongo.db.records
    # Descending
    records = connection.find({'user_name': current_user.username}).sort([("date", pymongo.DESCENDING), ("time", pymongo.DESCENDING)])
    return render_template('history.html', title='History', records=records, form=form)


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
        return redirect(url_for('history'))
    elif delete_form.submit_delete.data and delete_form.is_submitted():
        connection.delete_one({'_id': ObjectId(record_id)})
        flash('The Record Has Been Deleted!', 'success')
        return redirect(url_for('history'))
    return render_template('edit.html', title='Edit', form=form, record=record, delete_form=delete_form)


@app.route('/summary')
@login_required
def summary():
    return render_template('summary.html', title='Summary')