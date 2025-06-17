from pydantic import BaseModel

class CapitalUpdateRequest(BaseModel):
    capital: float
    ganancias: float = 0