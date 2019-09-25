from flask import Flask
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config['SECRET_KEY'] = 'c494256b541fc14fe6aa4a3532a6ca99'
app.config["MONGO_URI"] = "mongodb://localhost:27017/wallet_watcher"
mongo = PyMongo(app)


from wallet_watcher import routes