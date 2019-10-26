from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, \
    TextAreaField
from wtforms.validators import InputRequired, Length, Email


class ContactForm(FlaskForm):
    firstname = StringField('First Name',
                            validators=[InputRequired()],
                            render_kw={"placeholder": "Raymond"})
    lastname = StringField('Last Name',
                           validators=[InputRequired()],
                           render_kw={"placeholder": "Yang"})
    email = StringField('Email',
                        validators=[InputRequired(), Email()])
    note = TextAreaField('Message',
                         validators=[InputRequired()],
                         render_kw={"placeholder": "Please Leave Me A Message :)"})
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField('User Name',
                           validators=[InputRequired()])
    password = PasswordField('Password',
                             validators=[InputRequired(), Length(min=6)])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')