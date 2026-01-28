from pydantic import BaseModel

class AnalyzeProfileRequest(BaseModel):
    user_id: int
    user_input: str