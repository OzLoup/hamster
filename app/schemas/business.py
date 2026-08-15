from app.schemas.common import TimestampedResponse


class BusinessRead(TimestampedResponse):
    id: int
    name: str
    is_active: bool
