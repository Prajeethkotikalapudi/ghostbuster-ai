"""
Impossible Travel & Geo-Velocity Anomaly Calculation Service
Uses the Haversine spherical trigonometric formula to determine if sequential transactions
are physically possible given human transit speed limits.
"""

import math
from typing import Optional, Tuple, Dict, Any
from datetime import datetime


class GeoVelocityService:
    # Earth's mean radius in kilometers
    EARTH_RADIUS_KM = 6371.0

    @classmethod
    def haversine_distance_km(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculates great-circle distance between two points on a sphere in kilometers.
        """
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(d_lat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(d_lon / 2.0) ** 2)
        
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_KM * c

    @classmethod
    def calculate_velocity(
        cls,
        prev_lat: Optional[float],
        prev_lon: Optional[float],
        prev_time: datetime,
        curr_lat: Optional[float],
        curr_lon: Optional[float],
        curr_time: datetime
    ) -> Dict[str, Any]:
        """
        Calculates physical speed required (km/h) between two geographical timestamps.
        Flags impossible travel (> 850 km/h).
        """
        if None in (prev_lat, prev_lon, curr_lat, curr_lon):
            return {
                "distance_km": 0.0,
                "time_delta_hours": 0.0,
                "velocity_kmh": 0.0,
                "is_impossible_travel": False,
                "confidence": 0.3
            }

        # Calculate time delta in hours
        time_delta_sec = abs((curr_time - prev_time).total_seconds())
        time_delta_hours = max(time_delta_sec / 3600.0, 0.0001) # Avoid zero division

        distance_km = cls.haversine_distance_km(prev_lat, prev_lon, curr_lat, curr_lon)
        velocity_kmh = distance_km / time_delta_hours

        # Commercial flight speed threshold (~850-900 km/h)
        is_impossible = velocity_kmh > 850.0 and distance_km > 100.0

        return {
            "distance_km": round(distance_km, 2),
            "time_delta_minutes": round(time_delta_sec / 60.0, 2),
            "velocity_kmh": round(velocity_kmh, 2),
            "is_impossible_travel": is_impossible,
            "confidence": 0.95
        }


geo_velocity_service = GeoVelocityService()
