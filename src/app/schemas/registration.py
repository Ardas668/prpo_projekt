from pydantic import BaseModel, ConfigDict
from datetime import datetime
from src.app.models.enums import RegistrationStatus

class RegistrationCreate(BaseModel):
    student_id: int
    term_id: int
    admin_override: bool = False
    admin_override_reason: str | None = None

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
    course_name: str | None = None
    model_config = ConfigDict(from_attributes=True)

class RegistrationCancelResponse(BaseModel):
    cancelled_registration_id: int
    status: RegistrationStatus
    message: str
    promoted_student_id: int | None = None
    promoted_registration_id: int | None = None
