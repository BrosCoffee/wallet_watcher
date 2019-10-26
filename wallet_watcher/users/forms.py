from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import InputRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
import pymongo


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[InputRequired(), Length(min=2, max=20)])
    first_name = StringField('First Name',
                             validators=[InputRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name',
                            validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
    password = PasswordField('Password',
                             validators=[InputRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[InputRequired(), Length(min=6, max=20),
                                                 EqualTo('password', 'Passwords must match.')])
    submit = SubmitField('Sign up')

    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client.wallet_watcher
    collection = db.users

    def validate_username(self, username):
        result = self.collection.find_one({'user_name': username.data})
        if result is not None:
            raise ValidationError('The username is taken. Please choose a different one.')

    def validate_email(self, email):
        result = self.collection.find_one({'email': email.data})
        if result is not None:
            raise ValidationError('The email is taken. Please choose a different one.')


class UpdateAccountForm(FlaskForm):
    profile_image_name = FileField('Update Profile Image',
                                   validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    first_name = StringField('First Name',
                             validators=[InputRequired(), Length(min=2, max=20)])
    last_name = StringField('Last Name',
                            validators=[InputRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
    currencies = [('USD $', 'USD $'), ('NTD $', 'NTD $'), ('JPY ¥', 'JPY ¥'), ('EUR €', 'EUR €')]

    currency = SelectField('Currency',
                           choices=currencies,
                           validators=[InputRequired()])

    submit = SubmitField('Confirm')

    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client.wallet_watcher
    collection = db.users

    def validate_email(self, email):
        result = self.collection.find_one({'email': email.data})
        current = self.collection.find_one({'user_name': current_user.username})
        if result is not None:
            if email.data != current['email']:
                raise ValidationError('The email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField('User Name',
                           validators=[InputRequired()])
    password = PasswordField('Password',
                             validators=[InputRequired(), Length(min=6)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client.wallet_watcher
    collection = db.users

    def validate_email(self, email):
        result = self.collection.find_one({'email': email.data})
        if result is None:
            raise ValidationError('There is no account with that email. You must register first.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password',
                             validators=[InputRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[InputRequired(), Length(min=6, max=20),
                                                 EqualTo('password', 'Passwords must match.')])
    submit = SubmitField('Reset Password')