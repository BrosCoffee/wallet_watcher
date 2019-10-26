from flask import Blueprint, render_template, url_for, flash, redirect
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from wallet_watcher.main.forms import ContactForm, LoginForm
from flask_mail import Message
from wallet_watcher import app, mongo, bcrypt, login_manager, mail
from flask_login import UserMixin
import pymongo

main = Blueprint('main', __name__)
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


@main.route('/')
@main.route('/home')
def home():
    return render_template('home.html')


@main.route('/about')
def about():
    return render_template('about.html')


@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.is_submitted():
        msg = Message('Wallet Watcher Contact Request from {} {}'.format(form.firstname.data, form.lastname.data),
                      sender='noreply@googlemail.com',
                      recipients=['raymondcyang0219@gmail.com'])
        msg.body = '''Email: {}
Name: {} {}

Message:
{}
'''.format(form.email.data, form.firstname.data, form.lastname.data, form.note.data)
        mail.send(msg)
        flash('Your request has been sent.', 'info')
        return redirect(url_for('main.home'))
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