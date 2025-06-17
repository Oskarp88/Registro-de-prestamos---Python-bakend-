from pydantic import BaseModel

class CapitalOperationRequest(BaseModel):
    amount: float

class TransferRequest(BaseModel):
    amount: float
