from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

class PaymentHistoryItem(BaseModel):    
    date: datetime
    total_loan: float
    status: str  # "pendiente", "pagado", "mora", "no pago"
    due_date: str
    interestPayment: float
    paymentAmount: float

class LoanCreate(BaseModel):
    client_id: str
    total_loan: float
    total_loan_history:  Optional[float] = 0.0
    total_interest_history:  Optional[float] = 0.0
    name: str
    interest: Optional[float] = None  # se calculará como 15% del total_loan
    payment_amount: Optional[float] = 0.0  # si abona algo
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: str  # fecha donde pagará la cuota
    status: str = "pendiente"
    history: List[PaymentHistoryItem] = []
    interest10: bool = True
    day: int = 0
