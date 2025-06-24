from pydantic import BaseModel

class CapitalUpdateRequest(BaseModel):
    capital: float
    ganancias: float = 0
    history_capital: float
    history_interest: float