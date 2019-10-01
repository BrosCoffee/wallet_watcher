# import time
# t = time.time()
#
# print(time.strftime('%Y-%m-%d %H:%M %Z', time.localtime(t)))
# # '2019-05-27 12:03 CEST'
#
# print(time.strftime('%Y-%m-%d', time.localtime(t)))
#
# print(time.strftime('%H:%M', time.localtime(t)))
#
# print(time.strftime('%Z', time.localtime(t)))
#
# print(time.strftime('%Y-%m-%d %H:%M %Z', time.gmtime(t)))
# '2019-05-27 10:03 GMT'

# from wallet_watcher import mongo
#
# connection = mongo.db.users
# user = connection.find({'user_name': 'yja89219'})
# print(type(user))

# import pymongo
# client = pymongo.MongoClient(host='localhost', port=27017)
# db = client.wallet_watcher
# collection = db.users
# result = collection.find_one({'user_name': 'yja89219'})
# print(result)

class User:
    def __init__(self, username):
        self.username = username

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username

    @staticmethod
    def check_password(password_hash, password):
        return check_password_hash(password_hash, password)


    @login.user_loader
    def load_user(username):
        u = mongo.db.Users.find_one({"Name": username})
        if not u:
            return None
        return User(username=u['Name'])


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = Login()
        if form.validate_on_submit():
            user = mongo.db.Users.find_one({"Name": form.name.data})
            if user and User.check_password(user['Password'], form.password.data):
                user_obj = User(username=user['Name'])
                login_user(user_obj)
                next_page = request.args.get('next')
                if not next_page or url_parse(next_page).netloc != '':
                    next_page = url_for('index')
                return redirect(next_page)
            else:
                flash("Invalid username or password")
        return render_template('login.html', title='Sign In', form=form)


    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('login'))
