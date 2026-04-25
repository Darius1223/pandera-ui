import pandera.pandas as pa
from pandera.typing.pandas import Series


class UserSchema(pa.DataFrameModel):
    user_id: Series[int] = pa.Field(gt=0, description="Primary key")
    email: Series[str] = pa.Field(str_matches=r".+@.+\..+", description="User email address")
    age: Series[int] = pa.Field(ge=0, le=120, nullable=True, description="Age in years")
    role: Series[str] = pa.Field(isin=["admin", "editor", "viewer"], description="Access role")

    class Config:
        name = "users"
        description = "Registered platform users"
        coerce = True


class EventSchema(pa.DataFrameModel):
    event_id: Series[str] = pa.Field(description="UUID of the event")
    user_id: Series[int] = pa.Field(gt=0)
    event_type: Series[str] = pa.Field(isin=["click", "view", "purchase"])
    timestamp: Series[pa.DateTime]
    properties: Series[str] = pa.Field(nullable=True)

    class Config:
        name = "events"
