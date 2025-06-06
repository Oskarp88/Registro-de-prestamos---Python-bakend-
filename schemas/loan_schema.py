from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class PaymentHistoryItem(BaseModel):
    date: datetime
    status: str  # "pendiente", "pago", "mora", "no pago"
    interestPayment: float
    paymentAmount: float

class LoanCreate(BaseModel):
    client_id: str
    total_loan: float
    interest: Optional[float] = None  # se calculará como 15% del total_loan
    payment_amount: Optional[float] = 0.0  # si abona algo
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime  # fecha donde pagará la primera cuota
    status: str = "pendiente"
    history: List[PaymentHistoryItem] = []
