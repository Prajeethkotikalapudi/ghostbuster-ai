"""
Unit Tests for Impossible Geo-Velocity Travel Service
"""

import unittest
from datetime import datetime, timedelta
from services.geo_velocity import geo_velocity_service


class TestGeoVelocity(unittest.TestCase):

    def test_01_plausible_commute_speed(self):
        """Mumbai Bandra to Mumbai Airport (12 km in 20 mins -> ~36 km/h) is plausible."""
        t1 = datetime.utcnow()
        t2 = t1 + timedelta(minutes=20)
        
        res = geo_velocity_service.calculate_velocity(
            prev_lat=19.0596, prev_lon=72.8295, prev_time=t1, # Bandra
            curr_lat=19.0896, curr_lon=72.8656, curr_time=t2  # Airport
        )
        self.assertFalse(res["is_impossible_travel"])
        self.assertLess(res["velocity_kmh"], 100.0)
        print(f"[PASS] Plausible City Transit: {res['distance_km']} km in {res['time_delta_minutes']}m -> {res['velocity_kmh']} km/h")

    def test_02_impossible_intercontinental_travel(self):
        """Delhi to New York (11,750 km in 10 minutes -> ~70,500 km/h) MUST be flagged."""
        t1 = datetime.utcnow()
        t2 = t1 + timedelta(minutes=10)

        res = geo_velocity_service.calculate_velocity(
            prev_lat=28.6139, prev_lon=77.2090, prev_time=t1,  # Delhi
            curr_lat=40.7128, curr_lon=-74.0060, curr_time=t2  # New York
        )
        self.assertTrue(res["is_impossible_travel"])
        self.assertGreater(res["velocity_kmh"], 850.0)
        print(f"[PASS] Impossible Travel Flagged: {res['distance_km']} km in {res['time_delta_minutes']}m -> {res['velocity_kmh']} km/h")


if __name__ == "__main__":
    unittest.main()
