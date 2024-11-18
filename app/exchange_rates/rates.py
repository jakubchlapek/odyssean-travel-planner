import requests
from app import app, db
from app.models import ExchangeRates
from datetime import datetime, timezone, timedelta

BASE_URL = "https://api.fxratesapi.com/latest"

def fetch_rates(currency="PLN"):
    """Fetch the latest exchange rates from the API"""
    app.logger.info(f"Fetching exchange rates for base currency {currency}")
    params = {"base": currency}
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # Raises an HTTPError if the response code is 4xx/5xx
        data = response.json()
        app.logger.info(f"Successfully fetched exchange rates for {currency}")
        return data
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error fetching exchange rates for {currency}: {e}")
        raise


def update_exchange_rates():
    """Update the exchange rates in the database if 24 hours have passed since the last update. Used in the CLI flask command.
    
    Returns:
        int: 0 if the rates were updated, -1 if the rates were already up to date"""
    app.logger.info("Checking if exchange rates need to be updated.")
    last_update = db.session.query(ExchangeRates.last_updated).order_by(ExchangeRates.last_updated.desc()).first()
    
    if last_update:
        last_update = last_update[0].replace(tzinfo=timezone.utc)  # Make sure it's timezone-aware
        
    # Check if 24 hours have passed since the last update
    if last_update and last_update > datetime.now(timezone.utc) - timedelta(days=1):
        app.logger.info("Exchange rates are already up to date.")
        return -1
    
    try:
        data = fetch_rates() 
        rates = data["rates"]

        app.logger.info(f"Updating exchange rates for {len(rates)} currencies.")
        for currency, rate in rates.items():
            exchange_rate = db.session.query(ExchangeRates).filter_by(currency_to=currency).first()
            if exchange_rate:
                exchange_rate.rate = rate
                app.logger.info(f"Updated rate for {currency}.")
            else:
                new_rate = ExchangeRates(currency_to=currency, rate=rate, last_updated=datetime.now(timezone.utc))
                db.session.add(new_rate)
                app.logger.info(f"Added new rate for {currency}.")
        
        db.session.commit()
        app.logger.info("Exchange rates successfully updated in the database.")
        return 0
    except Exception as e:
        app.logger.error(f"Error updating exchange rates: {e}")
        raise
    
    
