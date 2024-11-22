from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, DateField, DecimalField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, NumberRange, InputRequired, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import app, db
from app.models import User, Trip, ExchangeRates, ComponentCategory, ComponentType


class LoginForm(FlaskForm):
    """Form for logging in a user."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=12)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Form for registering a new user."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=12)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username): # wtflask automatically checks any validate_<field_name> with validation and will raise ValidationErrors
        '''Raise a ValidationError if username taken'''
        app.logger.info(f"Validating username: {username.data}")
        exists = db.session.scalar(
            sa.select(sa.exists().where(User.username == username.data)))
        if exists:
            app.logger.warning(f"Username {username.data} is already taken.")
            raise ValidationError('Please use a different username.')
        app.logger.info(f"Username {username.data} is available.")
        
    def validate_email(self, email):
        '''Raise a ValidationError if email taken'''
        app.logger.info(f"Validating email: {email.data}")
        exists = db.session.scalar(
            sa.select(sa.exists().where(User.email == email.data)))
        if exists:
            app.logger.warning(f"Email {email.data} is already taken.")
            raise ValidationError('Please use a different email address.')
        app.logger.info(f"Email {email.data} is available.")
        

class EditProfileForm(FlaskForm):
    """Form for editing user profile."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=12)])
    currency = SelectField('Preferred currency', choices=[], validators=[DataRequired(), Length(min=3, max=3)])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)], render_kw={"placeholder": "Tell us about yourself."})
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        '''Raise a ValidationError if username taken and different from current user's username'''
        app.logger.info(f"Validating new username: {username.data} (current: {self.original_username})")
        if self.original_username != username.data:
            user = db.session.scalar(sa.select(
                sa.exists().where(User.username == username.data)))
            if user is not None:
                app.logger.warning(f"Username {username.data} is already taken.")
                raise ValidationError('Please use a different username.')
            app.logger.info(f"Username {username.data} is available for update.")
            
    def validate_currency(self, currency):
        '''Raise a ValidationError if currency not in ExchangeRates table.'''
        app.logger.info(f"Validating currency: {currency.data}")
        exists = db.session.scalar(sa.select(
            sa.exists().where(ExchangeRates.currency_to == currency.data)))
        if not exists:
            app.logger.warning(f"Currency {currency.data} not found in ExchangeRates table.")
            raise ValidationError('Please choose an existing currency.')
        app.logger.info(f"Currency {currency.data} is valid.")
        

class TripForm(FlaskForm):
    """Form for adding a new trip."""
    trip_name = StringField('Trip name', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_trip_name(self, trip_name):
        '''Raise a ValidationError if trip name already selected by the same user.'''
        app.logger.info(f"Validating trip name: {trip_name.data} for user {self.user_id}")
        trip = so.aliased(Trip)
        exists = db.session.scalar(sa.select(
            sa.exists().where(sa.and_(trip.trip_name == trip_name.data, self.user_id == trip.user_id))))
        if exists:
            app.logger.warning(f"Trip name {trip_name.data} already exists for user {self.user_id}.")
            raise ValidationError('Please choose a different trip name.')
        app.logger.info(f"Trip name {trip_name.data} is available for user {self.user_id}.")
        
class ComponentForm(FlaskForm):
    """Form for adding or editing a trip component."""
    component_name = StringField('Component name', validators=[DataRequired()])
    category_id = SelectField('Category name', choices=[], coerce=int, validators=[DataRequired()])
    type_id = SelectField('Type name', choices=[], coerce=int, validators=[DataRequired()])
    base_cost = DecimalField('Cost', default=0.0, places=2, validators=[InputRequired(), NumberRange(min=0)])
    currency = SelectField('Cost currency', choices=[], default="PLN", validators=[Length(min=3, max=3)])
    participant_name = SelectField('Participant', choices=[], coerce=int, validators=[Optional()])
    description = TextAreaField('Description', validators=[Length(min=0, max=140)], render_kw={"placeholder": "Describe your component here."})
    link = StringField('Link', validators=[Length(min=0, max=2083)], render_kw={"placeholder": "Add a link to your component."})
    start_date = DateField('Start date', validators=[Optional()])
    end_date = DateField('End date', validators=[Optional()])
    submit = SubmitField('Submit')

    def validate_category_id(self, category_id):
        '''Raise a ValidationError if category not in ComponentCategory table.'''
        app.logger.info(f"Validating category ID: {category_id.data}")
        exists = db.session.scalar(sa.select(
            sa.exists().where(ComponentCategory.id == category_id.data)))
        if not exists:
            app.logger.warning(f"Category ID {category_id.data} not found in ComponentCategory table.")
            raise ValidationError('Please choose an existing category.')
        app.logger.info(f"Category ID {category_id.data} is valid.")
        
    def validate_type_id(self, type_id):
        '''Raise a ValidationError if type not in ComponentType table.'''
        app.logger.info(f"Validating type ID: {type_id.data}")
        exists = db.session.scalar(sa.select(
            sa.exists().where(ComponentType.id == type_id.data)))
        if not exists:
            app.logger.warning(f"Type ID {type_id.data} not found in ComponentType table.")
            raise ValidationError('Please choose an existing type.')
        app.logger.info(f"Type ID {type_id.data} is valid.")
        
    def validate_currency(self, currency):
        '''Raise a ValidationError if currency not in ExchangeRates table.'''
        app.logger.info(f"Validating currency: {currency.data}")
        exists = db.session.scalar(sa.select(
            sa.exists().where(ExchangeRates.currency_to == currency.data)))
        if not exists:
            app.logger.warning(f"Currency {currency.data} not found in ExchangeRates table.")
            raise ValidationError('Please choose an existing currency.')
        app.logger.info(f"Currency {currency.data} is valid.")


    def validate(self, **kwargs):
        # Standard validators
        rv = FlaskForm.validate(self)
        # Ensure all standard validators are met
        if rv:
            # Ensure end date >= start date
            if self.start_date.data and self.end_date.data and (self.start_date.data > self.end_date.data):
                app.logger.warning(f"End date {self.end_date.data} is before start date {self.start_date.data}.")
                self.end_date.errors.append('Finish date must be set after the starting date.')
                return False
            app.logger.info(f"Date range for component is valid: {self.start_date.data} to {self.end_date.data}")
            return True
        return False


class ParticipantForm(FlaskForm):
    participant_name = StringField('Participant', validators=[DataRequired(), Length(min=3, max=20)])
    submit = SubmitField('Submit')
    
    def validate(self, **kwargs):
        app.logger.info("Validating participant form submission.")
        return super().validate(**kwargs)


class EmptyForm(FlaskForm):
    """Empty form for CSRF protection or deletes."""
    submit = SubmitField('Submit')
    
    def validate(self, **kwargs):
        app.logger.info("Validating empty form submission.")
        return super().validate(**kwargs)