from pydantic import BaseModel

class InterestPaymentRequest(BaseModel):
    client_id: str
    paid_interest: float
