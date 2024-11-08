import os
os.environ['DATABASE_URL'] = 'sqlite://'

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import User, Trip, Component

class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

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

if __name__ == '__main__':
    unittest.main(verbosity=2)
