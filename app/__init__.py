from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler
import logging
import os

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/travel_planner.log', 
                                       maxBytes=10240, backupCount=10) # Chose rotating file handler to limit size of log file
    file_handler.setFormatter(logging.Formatter(
         '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')) # Format of log messages
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Starting up Travel Planner!')

from app.plotlydash.dashboard import init_dash_app
app = init_dash_app(app)
from app import routes, models, errors

@app.cli.command('update_exchange_rates')
def update_exchange_rates_command():
    """Command line command for updating exchange rates."""
    from app.exchange_rates.rates import update_exchange_rates
    update_exchange_rates()
    print("Exchange rates updated.")
    
@app.cli.command('seed')
def seed():
    """Command line command for populating the database with initial data."""
    with app.app_context():
        models.populate_initial_data()
        print("Database seeded with initial data.")

