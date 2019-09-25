from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField,\
                    TextAreaField, SelectField, DecimalField
from wtforms.validators import InputRequired, DataRequired, Length, Email, EqualTo


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


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
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
                         validators=[InputRequired],
                         render_kw={"placeholder": "Please Leave Me A Message :)"})
    submit = SubmitField('Submit')


class EnterForm(FlaskForm):
    categories = [('Food & Dining', 'Food & Dining'), ('Bills & Utilities', 'Bills & Utilities'),
                  ('Shopping', 'Shopping'), ('Entertainment', 'Entertainment'),
                  ('Personal Care', 'Personal Care'), ('Health & Fitness', 'Health & Fitness'),
                  ('Transport & Auto', 'Transport & Auto'), ('Fees & Charges', 'Fees & Charges'),
                  ('Education', 'Education'), ('Gifts & Donation', 'Gifts & Donation'),
                  ('Business Services', 'Business Services'), ('Investment', 'Investment'),
                  ('Travel', 'Travel'), ('Kids & Elderly', 'Kids & Elderly'), ('Taxes', 'Taxes'),
                  ('Others', 'Others')]
    category = SelectField('Expense Categories',
                           choices=categories)
    currencies = [('USD', 'USD $'), ('NTD', 'NTD $'), ('JPY', 'JPY ¥'), ('EUR', 'EUR €')]

    currency = SelectField('Currency',
                           choices=currencies,
                           validators=[InputRequired()])

    amount = DecimalField('Amount',
                          validators=[DataRequired()],
                          render_kw={"placeholder": "20.00"})
    note = TextAreaField('Note (Optional)',
                         render_kw={"placeholder": "ex: Miller's Ale house for dinner."})
    submit = SubmitField('Submit')
