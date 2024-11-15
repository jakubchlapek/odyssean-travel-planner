import requests
from app import db
from app.models import ExchangeRates
import sqlalchemy as sa
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.fxratesapi.com/latest"

def fetch_rates(currency='PLN'):
    """Fetch the latest exchange rates from the API"""
    params = {"base": currency}
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data


def get_exchange_rate(currency_from, currency_to):
    """Calculate the exchange rate from currency_from to currency_to using the PLN exchange rates from the database. 
    Done this way to avoid making multiple API calls and being rate limited.
    
    Args:
        currency_from (str): Currency code to convert from
        currency_to (str): Currency code to convert to
        
    Returns:
        float: Exchange rate from currency_from to currency_to"""
    # Get the rate in PLN for each currency
    rates = db.session.query(ExchangeRates.currency_to, ExchangeRates.rate).filter(
        ExchangeRates.currency_to.in_([currency_from, currency_to])
    ).all()
    
    rates_dict = {currency: rate for currency, rate in rates}

    if currency_from not in rates_dict or currency_to not in rates_dict:
        raise ValueError("One or both of the currency codes are not available in the database.")

    return rates_dict[currency_to] / rates_dict[currency_from]


def update_exchange_rates():
    """Update the exchange rates in the database with the latest data from the API if they haven't been updated in the last 24 hours."""
    last_update = db.session.query(ExchangeRates.last_updated).order_by(ExchangeRates.last_updated.desc()).first()
    # TODO: Fix this 
    if last_update:
        last_update = last_update[0].replace(tzinfo=timezone.utc) # Workaround (for some reason i think the db strips the timezone from the field)
    
    # Check if 24 hours have passed since the last update
    if last_update and last_update > datetime.now(timezone.utc) - timedelta(days=1):
        print("Exchange rates are already up to date.")
        return
    
    data = fetch_rates()
    rates = data["rates"]

    for currency, rate in rates.items():
        # Either update existing or create new entries
        exchange_rate = db.session.query(ExchangeRates).filter_by(currency_to=currency).first()
        if exchange_rate:
            exchange_rate.rate = rate
            exchange_rate.last_updated = datetime.now(timezone.utc)
        else:
            new_rate = ExchangeRates(currency_to=currency, rate=rate, last_updated=datetime.now(timezone.utc))
            db.session.add(new_rate)
            
    db.session.commit()
    
    

