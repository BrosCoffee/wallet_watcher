from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, DecimalField
from wtforms.validators import InputRequired, DataRequired


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