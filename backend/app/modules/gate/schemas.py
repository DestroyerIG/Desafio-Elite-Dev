from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ValidationResult


class GateValidationCreate(BaseModel):
    event_id: UUID
    credential: str = Field(min_length=1, max_length=2048)

    @field_validator("credential")
    @classmethod
    def normalize_credential(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Informe o QR ou código do ingresso.")
        return normalized


class GateValidationResponse(BaseModel):
    result: ValidationResult
    message: str
    ticket_id: UUID | None
    public_code: str | None
    validated_at: datetime
