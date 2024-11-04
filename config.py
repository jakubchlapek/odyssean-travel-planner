import os
basedir = os.path.abspath(os.path.dirname(__file__))

INIT_CATEGORIES = [
    'Accommodation',
    'Food',
    'Transport',
    'Entertainment',
    'Shopping',
    'Other'
]

INIT_TYPES = {
    'Accommodation': ['Hotel', 'Hostel', 'Camping', 'Apartment', 'Other'],
    'Food': ['Restaurant', 'Fast food', 'Cafe', 'Bar', 'Other'],
    'Transport': ['Plane', 'Train', 'Bus', 'Car', 'Other'],
    'Entertainment': ['Museum', 'Theatre', 'Cinema', 'Concert', 'Other'],
    'Shopping': ['Clothes', 'Electronics', 'Souvenirs', 'Other'],
    'Other': ['Other']
}

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ultra-secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')

