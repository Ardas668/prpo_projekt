from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CertificateIssueRequest(BaseModel):
    registration_id: int
    lecturer_approved: bool = True

class CertificateResponse(BaseModel):
    id: int
    registration_id: int
    certificate_number: str
    issued_at: datetime
    student_name: str | None = None
    course_name: str | None = None
    model_config = ConfigDict(from_attributes=True)
