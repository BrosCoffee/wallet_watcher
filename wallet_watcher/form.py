from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, \
    TextAreaField, SelectField, DecimalField
from wtforms.validators import InputRequired, DataRequired, Length, Email, \
    EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
import pymongo
from wallet_watcher import mongo
from flask_login import current_user

connection = mongo.db.records


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


class ContactForm(FlaskForm):
    firstname = StringField('First Name',
                            validators=[InputRequired()],
                            render_kw={"placeholder": "Raymond"})
    lastname = StringField('Last Name',
                           validators=[InputRequired()],
                           render_kw={"placeholder": "Yang"})
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
    note = TextAreaField('Note',
                         validators=[InputRequired()],
                         render_kw={"placeholder": "Please Leave Me A Message :)"})
    submit = SubmitField('Submit')


class EnterForm(FlaskForm):
    categories = [('Food and Dining', 'Food and Dining'), ('Bills and Utilities', 'Bills and Utilities'),
                  ('Shopping', 'Shopping'), ('Entertainment', 'Entertainment'),
                  ('Personal Care', 'Personal Care'), ('Health and Fitness', 'Health and Fitness'),
                  ('Transport and Auto', 'Transport and Auto'), ('Fees and Charges', 'Fees and Charges'),
                  ('Education', 'Education'), ('Gifts and Donation', 'Gifts and Donation'),
                  ('Business Services', 'Business Services'), ('Investment', 'Investment'),
                  ('Travel', 'Travel'), ('Kids and Elderly', 'Kids and Elderly'), ('Taxes', 'Taxes'),
                  ('Others', 'Others')]
    category = SelectField('Expense Categories',
                           choices=categories)
    currencies = [('USD $', 'USD $'), ('NTD $', 'NTD $'), ('JPY ¥', 'JPY ¥'), ('EUR €', 'EUR €')]

    currency = SelectField('Currency',
                           choices=currencies,
                           validators=[InputRequired()])

    amount = DecimalField('Amount',
                          validators=[DataRequired()],
                          render_kw={"placeholder": "20.00"})
    note = TextAreaField('Note (Optional)',
                         render_kw={"placeholder": "ex: Miller's Ale house for dinner."})
    submit = SubmitField('Submit')


class EditForm(FlaskForm):
    categories = [('Food and Dining', 'Food and Dining'), ('Bills and Utilities', 'Bills and Utilities'),
                  ('Shopping', 'Shopping'), ('Entertainment', 'Entertainment'),
                  ('Personal Care', 'Personal Care'), ('Health and Fitness', 'Health and Fitness'),
                  ('Transport and Auto', 'Transport and Auto'), ('Fees and Charges', 'Fees and Charges'),
                  ('Education', 'Education'), ('Gifts and Donation', 'Gifts and Donation'),
                  ('Business Services', 'Business Services'), ('Investment', 'Investment'),
                  ('Travel', 'Travel'), ('Kids and Elderly', 'Kids and Elderly'), ('Taxes', 'Taxes'),
                  ('Others', 'Others')]
    category = SelectField('Expense Categories',
                           choices=categories)
    currencies = [('USD $', 'USD $'), ('NTD $', 'NTD $'), ('JPY ¥', 'JPY ¥'), ('EUR €', 'EUR €')]

    currency = SelectField('Currency',
                           choices=currencies,
                           validators=[InputRequired()])

    amount = DecimalField('Amount',
                          validators=[DataRequired()])
    note = TextAreaField('Note (Optional)')
    object_id = StringField()
    submit_update = SubmitField('Update')


class DeleteForm(FlaskForm):
    submit_delete = SubmitField('Delete')


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
    password = PasswordField('Password',
                             validators=[InputRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[InputRequired(), Length(min=6, max=20),
                                                 EqualTo('password', 'Passwords must match.')])
    submit = SubmitField('Reset Password')