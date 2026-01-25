from pydantic import BaseModel


class User(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "username": "johndoe",
                "email": "john.doe@example.com",
                "full_name": "John Doe"
            }
        }