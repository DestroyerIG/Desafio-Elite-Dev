from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import SeatStatus


class SeatSectionConfigure(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    row_count: int = Field(gt=0, le=52)
    seats_per_row: int = Field(gt=0, le=100)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()


class SeatMapConfigure(BaseModel):
    stage_label: str = Field(default="Palco", min_length=1, max_length=80)
    sections: list[SeatSectionConfigure] = Field(min_length=1, max_length=20)

    @field_validator("stage_label")
    @classmethod
    def normalize_stage_label(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_sections(self) -> "SeatMapConfigure":
        names = [section.name.casefold() for section in self.sections]
        if len(names) != len(set(names)):
            raise ValueError("Os nomes dos setores não podem se repetir.")
        total = sum(
            section.row_count * section.seats_per_row for section in self.sections
        )
        if total > 2_000:
            raise ValueError("O mapa pode conter no máximo 2.000 assentos.")
        return self


class SeatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    row_label: str
    number: int
    label: str
    position: int
    status: SeatStatus


class SeatSectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    position: int
    row_count: int
    seats_per_row: int
    seats: list[SeatResponse]


class SeatMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    stage_label: str
    version: int
    sections: list[SeatSectionResponse]


class SeatHoldCreate(BaseModel):
    seat_ids: list[UUID] = Field(min_length=1, max_length=10)

    @field_validator("seat_ids")
    @classmethod
    def reject_duplicates(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Um mesmo assento não pode ser selecionado duas vezes.")
        return value
