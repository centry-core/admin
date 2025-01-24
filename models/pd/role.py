from pydantic.v1 import BaseModel


class RoleDetailModel(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
