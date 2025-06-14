from pydantic import BaseModel

class CapitalUpdateRequest(BaseModel):
    capital: float