from flask import render_template, url_for, flash, redirect, request
from wallet_watcher.form import RegistrationForm, LoginForm, ContactForm, EnterForm
from wallet_watcher import app, mongo
import time


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Welcome back, {}!'.format(form.email.data), 'success')
        return redirect(url_for('enter'))
    return render_template('login.html', title='Login', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    connection = mongo.db.users

    if form.validate_on_submit():
        connection.insert({'user_name': request.form.get('username'),
                           'first_name': request.form.get('first_name'),
                           'last_name': request.form.get('last_name'),
                           'email': request.form.get('email'),
                           'password': request.form.get('password'),
                           'confirm_password': request.form.get('confirm_password')})
        flash('Account created for {}!'.format(form.username.data), 'success')
        return redirect(url_for('enter'))
    return render_template('register.html', title='Register', form=form)


@app.route('/enter', methods=['GET', 'POST'])
def enter():
    form = EnterForm()
    connection = mongo.db.records
    t = time.time()

    if form.validate_on_submit():
        connection.insert({'user_id': request.form.get('user_id'),
                           'time_zone': time.strftime('%Z', time.localtime(t)),
                           'date': time.strftime('%Y-%m-%d', time.localtime(t)),
                           'time': time.strftime('%H:%M', time.localtime(t)),
                           'category': request.form.get('category'),
                           'currency': request.form.get('currency'),
                           'amount': request.form.get('amount'),
                           'note': request.form.get('note')})
        flash('The New Record Has Been Added!', 'success')
        return redirect(url_for('enter'))

    return render_template('enter_form.html', title='Enter_Form', form=form)


@app.route('/history')
def history():
    return render_template('history_tab.html')