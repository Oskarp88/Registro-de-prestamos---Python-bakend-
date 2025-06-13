from pydantic import BaseModel

class PaymentAmount(BaseModel):
    client_id: str
    payment_amount: float