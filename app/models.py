import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime, timezone
from typing import Optional
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin # Adds safe implementations of 4 elements (is_authenticated, get_id(), etc...)
from app import db, login
from config import INIT_CATEGORIES, INIT_TYPES


class User(UserMixin, db.Model):
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
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    category_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)

    component_types: so.WriteOnlyMapped['ComponentType'] = so.relationship(back_populates='category')
    components: so.WriteOnlyMapped['Component'] = so.relationship(back_populates='category')

    def __repr__(self):
        return f'<Component category {self.category_name}>'
    
@sa.event.listens_for(ComponentCategory.__table__, 'after_create')
def create_categories(*args, **kwargs):
    for category_name in INIT_CATEGORIES:
        db.session.add(ComponentCategory(category_name=category_name))
    db.session.commit()
    

class ComponentType(db.Model):    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    category_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(ComponentCategory.id, name='fk_component_type_category_id'), index=True)
    type_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)

    category: so.Mapped[ComponentCategory] = so.relationship(back_populates='component_types')
    components: so.WriteOnlyMapped['Component'] = so.relationship(back_populates='type')

    def __repr__(self):
        return f'<Component category {self.category_name}>'
    
@sa.event.listens_for(ComponentType.__table__, 'after_create')
def create_types(*args, **kwargs):
    for category_name, types in INIT_TYPES.items():
        category = db.session.scalar(
            sa.select(ComponentCategory)
            .where(ComponentCategory.category_name == category_name))
        for type_name in types:
            db.session.add(ComponentType(category_id=category.id, type_name=type_name))
    db.session.commit()
    

class Component(db.Model):    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    trip_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('trip.id', name='fk_component_trip_id', ondelete='CASCADE'), index=True)
    category_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('component_category.id', name='fk_component_category_id'), index=True, default=1)  # Category 1 is neutral
    type_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey('component_type.id', name='fk_component_type_id'), index=True, default=1)
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
        return f'<Component name {self.component_name}, cost {self.base_cost}>'
    

class ExchangeRates(db.Model):    
    id: so.Mapped[int] = so.mapped_column(sa.Integer, primary_key=True)
    currency_from: so.Mapped[str] = so.mapped_column(sa.String(3))
    currency_to: so.Mapped[str] = so.mapped_column(sa.String(3))
    rate: so.Mapped[float] = so.mapped_column(sa.DECIMAL(10, 6))  # Conversion rate
    last_updated: so.Mapped[datetime] = so.mapped_column(default=datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ExchangeRate {self.currency_from} to {self.currency_to} at rate {self.rate}>'
