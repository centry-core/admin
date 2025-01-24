from pydantic.v1 import BaseModel, EmailStr


class UserInputFieldPD(BaseModel):
    user_email: EmailStr
