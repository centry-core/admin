from pydantic import BaseModel, EmailStr


class UserInputFieldPD(BaseModel):
    user_email: EmailStr
