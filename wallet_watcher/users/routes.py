from flask import Blueprint, render_template, url_for, flash, redirect, request
from wallet_watcher.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                                        RequestResetForm, ResetPasswordForm)
from wallet_watcher import mongo, bcrypt
from flask_login import current_user, login_user, logout_user, login_required
from bson.objectid import ObjectId
from wallet_watcher.users.utils import save_image, send_reset_email
from wallet_watcher.main.routes import verify_reset_token, User
users = Blueprint('users', __name__)


@users.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('records.enter'))
    form = LoginForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({"user_name": form.username.data})
        if user and User.check_password():
            user_obj = User(username=user['user_name'])
            login_user(user_obj, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Welcome back, {}!'.format(user['first_name']), 'success')
            return redirect(next_page) if next_page else redirect(url_for('records.enter'))
        elif User.check_password() is False:
            flash('The password is incorrect.', 'danger')
    return render_template('login.html', title='Sign In', form=form)


@users.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('users.login'))


@users.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('records.enter'))
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
        return redirect(url_for('records.enter'))
    return render_template('register.html', title='Register', form=form)


@users.route('/account', methods=['GET', 'POST'])
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
        return redirect(url_for('users.account'))
    return render_template('account.html', title='Account', user=user, form=form, profile_image=profile_image)



@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('records.enter'))
    form = RequestResetForm()
    if form.validate_on_submit():
        connection = mongo.db.users
        user = connection.find_one({'email': form.email.data})
        user_id = str(user['_id'])
        user_fname = user['first_name']
        user_lname = user['last_name']
        send_reset_email(form.email.data, user_id, user_fname, user_lname)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    connection = mongo.db.users
    if current_user.is_authenticated:
        return redirect(url_for('records.enter'))
    user = verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token.', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(request.form.get('password')).decode('utf-8')
        connection.update({'_id': ObjectId(user['_id'])}, {'$set': {'password': hashed_password}})
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)