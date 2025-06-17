from datetime import datetime
from pydantic import BaseModel, Field

class HistoryGananciasCreate(BaseModel):
    amount: float
    state: str
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    client_name: str = ""