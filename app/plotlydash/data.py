import pandas as pd
from app import db
from app.models import Component, Trip
from config import Config
import sqlalchemy as sa

category_names = {i + 1: category for i, category in enumerate(Config.INIT_CATEGORIES)}
type_names = {i + 1: type_name for i, type_name in enumerate({type_ for types in Config.INIT_TYPES.values() for type_ in types})}


def fetch_data(trip_id: int):
    """Fetch components list and trip name from the database, run it to create_dataframe and return it."""
    if not trip_id or not isinstance(trip_id, int):
        return None
    trip = db.first_or_404(sa.select(Trip).where(Trip.id == trip_id))
    components = db.session.scalars(trip.components.select()).all()
    data = data_to_dict(components, trip.trip_name, trip.get_total_cost())
    return data


def data_to_dict(components: list[Component], trip_name: str, trip_total_cost: float) -> dict:
    """Create a dictionary created from a list of components."""
    if not components:
        return dict()
    
    data = { # Dictionary with default values for missing data
        "component_name": [getattr(c, 'component_name', None) for c in components],
        "category_name": [category_names.get(c.category_id, "Unknown Category") for c in components],
        "subcategory_name": [type_names.get(c.type_id, "Unknown Subcategory") for c in components],
        "base_cost": [getattr(c, 'base_cost', 0.0) for c in components],
        "link": [getattr(c, 'link', None) for c in components], 
        "description": [getattr(c, 'description', "") for c in components],
        "start_date": [getattr(c, 'start_date', pd.NaT) for c in components], 
        "end_date": [getattr(c, 'end_date', pd.NaT) for c in components],      
        "currency": [getattr(c, 'currency', "PLN") for c in components],
        "total_cost": trip_total_cost,     
        "title": trip_name
    }
    
    return data