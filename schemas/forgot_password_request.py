from pydantic import BaseModel


class ForgotPasswordRequest(BaseModel):
    email_or_username: str