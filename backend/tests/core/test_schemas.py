from datetime import datetime

from app.schemas.base import TimestampSchema


def test_timestamp_schema_defaults():
    schema = TimestampSchema()
    assert schema.created_at is not None
    assert schema.updated_at is None


def test_timestamp_schema_serialization():
    dt = datetime(2023, 1, 1, 12, 0, 0)
    schema = TimestampSchema(created_at=dt, updated_at=dt)
    data = schema.model_dump(mode="json")
    assert data["created_at"] == "2023-01-01T12:00:00"
    assert data["updated_at"] == "2023-01-01T12:00:00"
