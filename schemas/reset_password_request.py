from pydantic import BaseModel


class ResetPasswordRequest(BaseModel):
    user_id: str
    new_password: str