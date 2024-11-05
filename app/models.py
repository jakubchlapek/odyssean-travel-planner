import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from typing import Optional
from config import Config
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin # Adds safe implementations of 4 elements (is_authenticated, get_id(), etc...)
from app import db, login


class User(UserMixin, db.Model):
    """User model for storing user data.
    
    Fields:
    - id: primary key | int
    - username: unique username | str
    - email: unique email | str
    - preferred_currency: user's preferred currency as an 3-letter ICO code | str
    - password_hash: hashed password | str
    - created_at: timestamp of user creation | datetime

    Foreign key relationships:
    - trips: one-to-many relationship with Trip model"""
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    preferred_currency: so.Mapped[Optional[str]] = so.mapped_column(sa.String(3), default="PLN")
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    created_at: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    
    trips: so.WriteOnlyMapped['Trip'] = so.relationship(back_populates='user')


    def set_password(self, password: str) -> None:
        if not isinstance(password, str):
            raise TypeError("Password must be a string.")
        if not password:
            raise ValueError("Password cannot be empty.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
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
    - created_at: timestamp of trip creation | datetime

    Foreign key relationships:
    - user: many-to-one relationship with User model
    - components: one-to-many relationship with Component model"""
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, name='fk_trip_user_id'), index=True)
    trip_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    created_at: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    
    user: so.Mapped[User] = so.relationship(back_populates='trips')
    components: so.WriteOnlyMapped['Component'] = so.relationship(cascade='all, delete', back_populates='trip', passive_deletes=True)

    def get_total_cost(self) -> float:
        cost = db.session.query(sa.func.sum(Component.base_cost)).filter(Component.trip_id == self.id).scalar()
        if not cost:
            cost = 0.0
        return cost

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
    - description: description of the component | str
    - start_date: start date of the component | datetime
    - end_date: end date of the component | datetime
    
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
    start_date: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)
    end_date: so.Mapped[Optional[datetime]] = so.mapped_column(sa.DateTime)

    trip: so.Mapped[Trip] = so.relationship(back_populates='components')
    category: so.Mapped[ComponentCategory] = so.relationship(back_populates='components')
    type: so.Mapped[ComponentType] = so.relationship(back_populates='components')

    def __repr__(self):
        return f'<Component name {self.component_name}, category {self.category_id}, type {self.type_id}, cost {self.base_cost}>'
    

class ExchangeRates(db.Model):
    """Exchange rates model for storing currency conversion rates.

    Fields:
    - id: primary key | int
    - currency_from: currency to convert from as a 3-letter ICO code | str
    - currency_to: currency to convert to as a 3-letter ICO code | str
    - rate: conversion rate | float
    - last_updated: timestamp of last rate update | datetime"""
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    currency_from: so.Mapped[str] = so.mapped_column(sa.String(3))
    currency_to: so.Mapped[str] = so.mapped_column(sa.String(3))
    rate: so.Mapped[float] = so.mapped_column(sa.DECIMAL(10, 6))  # Conversion rate
    last_updated: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ExchangeRate {self.currency_from} to {self.currency_to} at rate {self.rate}>'


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

