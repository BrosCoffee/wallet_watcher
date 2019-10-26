import os
import secrets
from flask import url_for
from wallet_watcher import app, mail
from flask_mail import Message
from wallet_watcher.main.routes import get_reset_token


def save_image(form_image):
    random_rex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    picture_fn = random_rex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_img', picture_fn)
    form_image.save(picture_path)
    return '/static/profile_img/' + picture_fn


def send_reset_email(user, user_id, user_fname, user_lname):
    token = get_reset_token(user_id)
    msg = Message('Wallet Watcher Password Reset Request -- {} {}'.format(user_fname, user_lname),
                  sender='noreply@googlemail.com',
                  recipients=[user, 'raymondcyang0219@gmail.com'])
    msg.body = '''To reset your password, visit the following link:
{}
If you did not make this request then simply ignore this email and no changes will be made.
'''.format(url_for('users.reset_token', token=token, _external=True))
    mail.send(msg)

