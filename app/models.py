import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from typing import Optional
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin # Adds safe implementations of 4 elements (is_authenticated, get_id(), etc...)
from app import app, db, login
from hashlib import md5
import numpy as np


class User(UserMixin, db.Model):
    """User model for storing user data.
    
    Fields:
    - id: primary key | int
    - username: unique username | str
    - email: unique email | str
    - about_me: user's about me | str
    - preferred_currency: user's preferred currency as an 3-letter ICO code | str 
    - password_hash: hashed password | str 
    - created_at: datetime of user creation | datetime

    Foreign key relationships:
    - trips: one-to-many relationship with Trip model"""
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(12), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    preferred_currency: so.Mapped[Optional[str]] = so.mapped_column(sa.String(3), default="PLN")
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    
    trips: so.WriteOnlyMapped['Trip'] = so.relationship(back_populates='user')


    def set_password(self, password: str) -> None:
        if not isinstance(password, str):
            raise TypeError("Password must be a string.")
        if not password:
            raise ValueError("Password cannot be empty.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    def __repr__(self):
        return f'<User {self.username}>'    
    

@login.user_loader
def load_user(id): # Function for flask-login
    return db.session.get(User, int(id))


class Trip(db.Model):
    """Trip model for storing trip data.

    Fields:
    - id: primary key | int
    - user_id: foreign key to User model | int
    - trip_name: name of the trip | str
    - created_at: datetime of trip creation | datetime

    Foreign key relationships:
    - user: many-to-one relationship with User model
    - components: one-to-many relationship with Component model"""
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, name='fk_trip_user_id'), index=True)
    trip_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    created_at: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    
    user: so.Mapped[User] = so.relationship(back_populates='trips')
    components: so.WriteOnlyMapped['Component'] = so.relationship(cascade='all, delete', back_populates='trip', passive_deletes=True)

    def get_total_cost(self) -> float:
        """Get the total cost of all components in the trip converted to the user's preferred currency. Rounded to 2 decimal places."""
        components = db.session.scalars(self.components.select())
        cost = np.sum(
            component.base_cost * get_exchange_rate(component.currency, self.user.preferred_currency)
            for component in components
        )

        if not cost:
            cost = 0.0
        return round(cost, 2)

    def __repr__(self):
        return f'<Trip {self.trip_name}, trip_id {self.id}, user_id {self.user_id}>'


class ComponentCategory(db.Model):    
    """Component category model for storing component categories.

    Fields:
    - id: primary key | int
    - category_name: unique category name | str

    Foreign key relationships:
    - component_types: one-to-many relationship with ComponentType model
    - components: one-to-many relationship with Component model"""
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    category_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)

    component_types: so.WriteOnlyMapped['ComponentType'] = so.relationship(back_populates='category')
    components: so.WriteOnlyMapped['Component'] = so.relationship(back_populates='category')

    def __repr__(self):
        return f'<Component category {self.category_name}>'
    

class ComponentType(db.Model):    
    """Component type model for storing component types.

    Fields:
    - id: primary key | int
    - category_id: foreign key to ComponentCategory model | int
    - type_name: unique type name | str

    Foreign key relationships:
    - category: many-to-one relationship with ComponentCategory model
    - components: one-to-many relationship with Component model"""
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    category_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(ComponentCategory.id, name='fk_component_type_category_id'), index=True)
    type_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)

    category: so.Mapped[ComponentCategory] = so.relationship(back_populates='component_types')
    components: so.WriteOnlyMapped['Component'] = so.relationship(back_populates='type')

    def __repr__(self):
        return f'<Component type {self.type_name}, type_id {self.id}, category_id {self.category_id}>'
    

class Component(db.Model):    
    """Component model for storing trip components.

    Fields:
    - id: primary key | int
    - trip_id: foreign key to Trip model | int
    - category_id: foreign key to ComponentCategory model | int
    - type_id: foreign key to ComponentType model | int
    - component_name: name of the component | str
    - base_cost: base cost of the component | float
    - currency: currency of the base cost as a 3-letter ICO code | str
    - description: description of the component | str | optional
    - link: URL to the component | str | optional
    - start_date: start date of the component | datetime | optional
    - end_date: end date of the component | datetime | optional
    
    Foreign key relationships:
    - trip: many-to-one relationship with Trip model
    - category: many-to-one relationship with ComponentCategory model
    - type: many-to-one relationship with ComponentType model"""
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    trip_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('trip.id', name='fk_component_trip_id', ondelete='CASCADE'), index=True)
    category_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('component_category.id', name='fk_component_category_id'), index=True)
    type_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('component_type.id', name='fk_component_type_id'), index=True)
    component_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    base_cost: so.Mapped[float] = so.mapped_column(sa.DECIMAL(10, 2))
    currency: so.Mapped[str] = so.mapped_column(sa.String(3))
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.Text)
    link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(2083)) # lowest common denominator for URL length
    start_date: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)
    end_date: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)

    trip: so.Mapped[Trip] = so.relationship(back_populates='components')
    category: so.Mapped[ComponentCategory] = so.relationship(back_populates='components')
    type: so.Mapped[ComponentType] = so.relationship(back_populates='components')

    def __repr__(self):
        return f'{self.component_name}, {self.base_cost} {self.currency}'
    

class ExchangeRates(db.Model):
    """Exchange rates model for storing currency conversion rates. It stores rates from PLN to other currencies, 
    from which other rates can be calculated (to limit the memory taken up in the database).

    Fields:
    - currency_to: currency to convert to as a 3-letter ICO code | primary key | str
    - rate: conversion rate | float
    - last_updated: datetime of last rate update | datetime"""
    currency_to: so.Mapped[str] = so.mapped_column(sa.String(3), primary_key=True)
    rate: so.Mapped[float] = so.mapped_column(sa.DECIMAL(18, 9))  # Conversion rate
    last_updated: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime, 
        default=lambda: datetime.now(timezone.utc), 
        onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ExchangeRate PLN to {self.currency_to} at rate {self.rate}>'

# Helpers
def populate_initial_data():
    """Seed the database with categories and types and commit changes to session."""
    # Add categories
    for category_name in Config.INIT_CATEGORIES:
        existing_category = db.session.query(ComponentCategory).filter_by(category_name=category_name).first()
        if not existing_category:
            db.session.add(ComponentCategory(category_name=category_name))

    # Add types to categories
    for category_name, types in Config.INIT_TYPES.items():
        category = db.session.query(ComponentCategory).filter_by(category_name=category_name).first()
        if category:
            for type_name in types:
                existing_type = db.session.query(ComponentType).filter_by(category_id=category.id, type_name=type_name).first()
                if not existing_type:
                    db.session.add(ComponentType(category_id=category.id, type_name=type_name))

    db.session.commit()


def get_exchange_rate(currency_from, currency_to):
    """Calculate the exchange rate from currency_from to currency_to using the PLN exchange rates from the database. 
    Done this way to avoid making multiple API calls and being rate limited.
    
    Args:
        currency_from (str): Currency code to convert from
        currency_to (str): Currency code to convert to
        
    Returns:
        float: Exchange rate from currency_from to currency_to"""
    app.logger.info(f"Calculating exchange rate from {currency_from} to {currency_to}")
    # Get the rate in PLN for each currency
    rates = db.session.query(ExchangeRates.currency_to, ExchangeRates.rate).filter(
        ExchangeRates.currency_to.in_([currency_from, currency_to])
    ).all()
    
    rates_dict = {currency: rate for currency, rate in rates}

    if currency_from not in rates_dict or currency_to not in rates_dict:
        app.logger.warning(f"Currency rates for {currency_from} or {currency_to} not found in the database.")
        raise ValueError("One or both of the currency codes are not available in the database.")

    exchange_rate = rates_dict[currency_to] / rates_dict[currency_from]
    app.logger.info(f"Exchange rate from {currency_from} to {currency_to}: {exchange_rate}")
    return exchange_rate