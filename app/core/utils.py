from datetime import datetime

from neo4j.time import DateTime


def convert_neo4j_datetime(value):
    """Convert neo4j.time.DateTime to Python datetime"""
    if value is None:
        return None
    if isinstance(value, DateTime):
        return datetime(
            year=value.year,
            month=value.month,
            day=value.day,
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            microsecond=value.nanosecond // 1000,
        )
    return value
