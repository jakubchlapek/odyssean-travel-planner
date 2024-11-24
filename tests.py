import os
os.environ['DATABASE_URL'] = 'sqlite://'

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import User, Trip, Component, Participant, ComponentCategory, ComponentType, ExchangeRates, get_exchange_rate
from hashlib import md5
from decimal import Decimal

        
class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Populate exchange rates for PLN and USD
        db.session.add(ExchangeRates(currency_to="PLN", rate=1.0))
        db.session.add(ExchangeRates(currency_to="USD", rate=0.25))
        db.session.commit()
        
        # Populate component categories and types
        db.session.add(ComponentCategory(category_name="Accommodation"))
        db.session.add(ComponentType(category_id=0, type_name="Hotel"))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        """Test password hashing and checking."""
        u = User(username="traveler", email="traveler@example.com")
        u.set_password('backpack')
        self.assertNotEqual(u.password_hash, 'backpack')
        self.assertFalse(u.check_password('cruise'))
        self.assertTrue(u.check_password('backpack'))

    def test_user_trip_relationship(self):
        """Test user-trip relationship."""
        # Create mock user
        u = User(username="traveler", email="traveler@example.com")
        db.session.add(u)
        db.session.commit()
        # Add 2 trips
        t1 = Trip(user_id=u.id, trip_name="Paris 2024")
        t2 = Trip(user_id=u.id, trip_name="Scotland 2025")
        db.session.add_all([t1, t2])
        db.session.commit()
        # Check if they have been added properly
        u_t = db.session.scalars(u.trips.select()).all()
        self.assertEqual(len(u_t), 2)
        self.assertEqual(u_t[0].trip_name, "Paris 2024")
        self.assertEqual(u_t[1].trip_name, "Scotland 2025")

    def test_get_total_cost_no_components(self):
        """Test get_total_cost method for trips without components."""
        # Create mock user
        u = User(username="traveler", email="traveler@example.com")
        db.session.add(u)
        db.session.commit()
        # Add empty trip
        t = Trip(user_id=u.id, trip_name="Trip1")
        db.session.add(t)
        db.session.commit()
        # Trip without components should have a cost of 0.0
        self.assertEqual(t.get_total_cost(), 0.0) 

    def test_get_total_cost_with_components(self):
        """Test get_total_cost method for trips with components."""
        # Create mock user
        u = User(username="traveler", email="traveler@example.com")
        db.session.add(u)
        db.session.commit()
        # Add empty trip
        t = Trip(user_id=u.id, trip_name="Trip1")
        db.session.add(t)
        db.session.commit()
        # Add 2 components
        c1 = Component(trip=t, category_id = 1, type_id = 1, component_name="Hotel Eiffel Tower", base_cost=200.00, currency="PLN")
        c2 = Component(trip=t, category_id = 1, type_id = 1, component_name="Flight to Paris", base_cost=300.00, currency="PLN")
        db.session.add_all([c1, c2])
        db.session.commit()
        # Trip with components should calculate total cost correctly
        self.assertEqual(t.get_total_cost(), 500.0) 
        
    def test_preferred_currency_default(self):
        """Test the default preferred currency for a new user."""
        u = User(username="traveler", email="traveler@example.com")
        db.session.add(u)
        db.session.commit()
        self.assertEqual(u.preferred_currency, "PLN")
        
    def test_avatar_url(self):
        """Test if avatar URL is generated correctly."""
        u = User(username="avatar_user", email="avatar@example.com")
        expected_url = f"https://www.gravatar.com/avatar/{md5('avatar@example.com'.encode('utf-8')).hexdigest()}?d=identicon&s=128"
        self.assertEqual(u.avatar(128), expected_url)
        
    def test_get_active_components(self):
        """Test retrieving only active components of a trip."""
        u = User(username="traveler", email="traveler@example.com")
        db.session.add(u)
        db.session.commit()
        t = Trip(user_id=u.id, trip_name="Active Test Trip")
        db.session.add(t)
        db.session.commit()
        c1 = Component(trip=t, category_id=0, type_id=0, component_name="Active Component", base_cost=100, currency="PLN", is_active=True)
        c2 = Component(trip=t, category_id=0, type_id=0, component_name="Inactive Component", base_cost=150, currency="PLN", is_active=False)
        db.session.add_all([c1, c2])
        db.session.commit()
        active_components = t.get_active_components()
        self.assertEqual(len(active_components), 1)
        self.assertEqual(active_components[0].component_name, "Active Component")

        
    def test_cost_conversion(self):
        """Test component cost conversion using exchange rates."""
        u = User(username="traveler", email="traveler@example.com", preferred_currency="EUR")
        db.session.add(u)
        db.session.commit()
        t = Trip(user_id=u.id, trip_name="Conversion Test Trip")
        db.session.add(t)
        db.session.commit()
        c = Component(trip_id=t.id, category_id=0, type_id=0, component_name="Expensive Component", base_cost=100, currency="PLN")
        db.session.add(c)
        db.session.commit()
        rate = 0.2  # Assume 1 PLN = 0.2 EUR
        db.session.add(ExchangeRates(currency_to="EUR", rate=rate))
        db.session.commit()
        total_cost = c.base_cost * get_exchange_rate("PLN", "EUR")
        self.assertAlmostEqual(total_cost, Decimal(20.0), places=2)
        
        
    def test_component_relationships(self):
        """Test relationships of component with trip, category, and type."""
        u = User(username="traveler", email="traveler@example.com")
        db.session.add(u)
        db.session.commit()
        t = Trip(user_id=u.id, trip_name="Rel Test Trip")
        db.session.add(t)
        db.session.commit()
        category = ComponentCategory(category_name="Transport")
        db.session.add(category)
        db.session.commit()
        type_ = ComponentType(category_id=category.id, type_name="Bus")
        db.session.add(type_)
        db.session.commit()
        c = Component(trip_id=t.id, category_id=category.id, type_id=type_.id, component_name="Luxury Hotel", base_cost=500, currency="USD")
        db.session.add(c)
        db.session.commit()
        self.assertEqual(c.trip, t)
        self.assertEqual(c.category, category)
        self.assertEqual(c.type, type_)

    def test_missing_exchange_rate(self):
        """Test error raised for missing exchange rate."""
        with self.assertRaises(ValueError):
            get_exchange_rate("PLN", "XYZ")
            

if __name__ == '__main__':
    unittest.main(verbosity=2)
