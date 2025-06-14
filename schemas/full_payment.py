from pydantic import BaseModel

class FullPayment(BaseModel):
    client_id: str