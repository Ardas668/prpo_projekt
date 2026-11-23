from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal

class CourseBase(BaseModel):
    name: str = Field(..., max_length=200)
    annotation: str | None = None
    hours_duration: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    is_accredited: bool = False

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
