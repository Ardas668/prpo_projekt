from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from src.app.models.enums import RegistrationStatus

class RegistrationCreate(BaseModel):
    student_id: int
    term_id: int
    admin_override: bool = False
    admin_override_reason: str | None = None

class SelfRegistrationCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    term_id: int

class RegistrationResponse(BaseModel):
    id: int
    student_id: int
    term_id: int
    status: RegistrationStatus
    queue_position: int | None = None
    created_at: datetime
    cancelled_at: datetime | None = None
    admin_override: bool = False
    admin_override_reason: str | None = None
    student_name: str | None = None
    student_email: str | None = None
    course_name: str | None = None
    model_config = ConfigDict(from_attributes=True)

class RegistrationCancelResponse(BaseModel):
    cancelled_registration_id: int
    status: RegistrationStatus
    message: str
    promoted_student_id: int | None = None
    promoted_registration_id: int | None = None
