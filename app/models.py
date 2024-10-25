import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin # Adds safe implementations of 4 elements (is_authenticated, get_id(), etc...)
from app import db, login

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
@login.user_loader
def load_user(id): # Function for flask-login
    return db.session.get(User, int(id))