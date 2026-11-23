from pydantic import BaseModel, EmailStr, Field, ConfigDict

class LecturerBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone: str | None = Field(None, max_length=50)

class LecturerCreate(LecturerBase):
    pass

class LecturerResponse(LecturerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
