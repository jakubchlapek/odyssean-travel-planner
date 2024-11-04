from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, DecimalField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, NumberRange, InputRequired, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from app.models import User, Trip, ExchangeRates, ComponentCategory, ComponentType


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username): # wtflask automatically checks any validate_<field_name> with validation and will raise ValidationErrors
        '''Raise a ValidationError if username taken'''
        exists = db.session.scalar(
            sa.select(sa.exists().where(User.username == username.data)))
        if exists:
            raise ValidationError('Please use a different username.')
        
    def validate_email(self, email):
        '''Raise a ValidationError if email taken'''
        exists = db.session.scalar(
            sa.select(sa.exists().where(User.email == email.data)))
        if exists:
            raise ValidationError('Please use a different email address.')
        

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    currency = StringField('Preferred currency', validators=[DataRequired(), Length(min=3, max=3)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        '''Raise a ValidationError if username taken and different from current user's username'''
        if self.original_username != username.data:
            user = db.session.scalar(sa.select(
                sa.exists().where(User.username == username.data)))
            if user is not None:
                raise ValidationError('Please use a different username.')
            
    def validate_currency(self, currency):
        '''Raise a ValidationError if currency not in ExchangeRates table.'''
        #exists = db.session.scalar(sa.select(
        #    sa.exists().where(ExchangeRates.currency_from == currency.data)))
        exists = currency in ["PLN", "EUR", "USD"] # temporary before exchangerates implementation
        if not exists:
            raise ValidationError('Please choose an existing currency.')
        

class TripForm(FlaskForm):
    trip_name = StringField('Trip name', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_trip_name(self, trip_name):
        '''Raise a ValidationError if trip name already selected by the same user.'''
        trip = so.aliased(Trip)
        exists = db.session.scalar(sa.select(
            sa.exists().where(sa.and_(trip.trip_name == trip_name.data, self.user_id == trip.user_id))))
        if exists:
            raise ValidationError('Please choose a different trip name.')
        
class ComponentForm(FlaskForm):
    component_name = StringField('Component name', validators=[DataRequired()])
    category_id = SelectField('Category name', choices=[], validators=[DataRequired()], default=1)
    type_id = SelectField('Type name', choices=[], coerce=int, validators=[DataRequired()])
    base_cost = DecimalField('Cost', default=0.0, places=2, validators=[InputRequired(), NumberRange(min=0)])
    currency = StringField('Cost currency', default="PLN", validators=[Length(min=3, max=3)])
    description = TextAreaField('Description', validators=[Length(min=0, max=140)], render_kw={"placeholder": "Describe your component here."})
    start_date = DateField('Start date', validators=[Optional()])
    end_date = DateField('End date', validators=[Optional()])
    submit = SubmitField('Submit')

    def validate_category_id(self, category_id):
        '''Raise a ValidationError if category not in ComponentCategory table.'''
        exists = db.session.scalar(sa.select(
            sa.exists().where(ComponentCategory.id == category_id.data)))
        if not exists:
            raise ValidationError('Please choose an existing category.')
        
    def validate_type_id(self, type_id):
        '''Raise a ValidationError if type not in ComponentType table.'''
        exists = db.session.scalar(sa.select(
            sa.exists().where(ComponentType.id == type_id.data)))
        if not exists:
            raise ValidationError('Please choose an existing type.')
        
    def validate_currency(self, currency):
        #exists = db.session.scalar(sa.select(
        #    sa.exists().where(ExchangeRates.currency_from == currency.data)))
        exists = currency.data in ["PLN", "EUR", "USD"] # temporary before ExchangeRates implementation
        if not exists:
            raise ValidationError('Please choose an existing currency.')


    def validate(self, **kwargs):
        # Standard validators
        rv = FlaskForm.validate(self)
        # Ensure all standard validators are met
        if rv:
            # Ensure end date >= start date
            if self.start_date.data and self.end_date.data and (self.start_date.data > self.end_date.data):
                self.end_date.errors.append('Finish date must be set after the starting date.')
                return False
            return True
        return False


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')