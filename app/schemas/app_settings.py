from pydantic import BaseModel, Field

from app.schemas.common import TimestampedResponse


class AppSettingsUpdate(BaseModel):
    business_name: str = Field(min_length=1, max_length=150)


class AppSettingsRead(TimestampedResponse):
    id: int
    business_name: str
