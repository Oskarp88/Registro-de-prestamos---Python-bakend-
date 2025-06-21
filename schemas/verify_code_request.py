from pydantic import BaseModel


class VerifyCodeRequest(BaseModel):
    email_or_username: str
    code: str