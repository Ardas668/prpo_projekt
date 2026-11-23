import enum

class RegistrationStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    WAITING_LIST = "WAITING_LIST"
    CANCELLED = "CANCELLED"
