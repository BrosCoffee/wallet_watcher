import os
from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config["MONGO_URI"] = "mongodb://localhost:27017/wallet_watcher"
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# 'EMAIL_USER' and 'EMAIL_PASS' are at .bash_profile
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)

from wallet_watcher.main.routes import main
from wallet_watcher.records.routes import records
from wallet_watcher.users.routes import users
from wallet_watcher.errors.handlers import errors

app.register_blueprint(main)
app.register_blueprint(records)
app.register_blueprint(users)
app.register_blueprint(errors)