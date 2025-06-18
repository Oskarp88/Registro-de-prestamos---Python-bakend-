from datetime import datetime
from pydantic import BaseModel, Field

class Notifications(BaseModel):
    client_id: str
    mesage: str
    creation_date: datetime = Field(default_factory=datetime.utcnow)
