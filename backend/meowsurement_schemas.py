"""Bounded request contracts for account-integrated Meowsurement."""
from __future__ import annotations

from datetime import date as CalendarDate
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PrescriptionEyeInput(Input):
    sph: float | None = Field(default=None, ge=-999.99, le=999.99)
    cyl: float | None = Field(default=None, ge=-999.99, le=999.99)
    axis: int | None = Field(default=None, ge=0, le=180)
    add: float | None = Field(default=None, ge=-999.99, le=999.99)


class ProfilePrescriptionInput(Input):
    date: CalendarDate | None = None
    od: PrescriptionEyeInput = Field(default_factory=PrescriptionEyeInput)
    os: PrescriptionEyeInput = Field(default_factory=PrescriptionEyeInput)
    notes: str = Field(default="", max_length=4000)
    pd_total: float | None = Field(default=None, gt=0, le=999.99)
    pd_right: float | None = Field(default=None, gt=0, le=999.99)
    pd_left: float | None = Field(default=None, gt=0, le=999.99)

    @field_validator("date", mode="before")
    @classmethod
    def blank_date(cls, value):
        return None if value == "" else value


class CustomerProfileInput(Input):
    expected_version: int = Field(ge=0)
    name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    birth_date: CalendarDate | None = None
    gender: Literal["male", "female", "unspecified"] | None = None
    address: str | None = Field(default=None, max_length=2000)
    prescription: ProfilePrescriptionInput | None = None

    @field_validator("birth_date", "gender", mode="before")
    @classmethod
    def blank_optional(cls, value):
        return None if value == "" else value


class FrameSpecificationInput(Input):
    a: float | None = Field(default=None, gt=0, le=99999.99)
    b: float | None = Field(default=None, gt=0, le=99999.99)
    dbl: float | None = Field(default=None, gt=0, le=99999.99)
    ed: float | None = Field(default=None, gt=0, le=99999.99)
    temple_length: float | None = Field(default=None, gt=0, le=99999.99)
    symmetric: bool = False
    enabled: bool = False
    source_note: str | None = Field(default=None, max_length=2000)


class VariantSpecificationInput(Input):
    variant_id: str = Field(min_length=1, max_length=64)
    inherit_default: bool = True
    specification: FrameSpecificationInput | None = None


class ProductSpecificationInput(Input):
    expected_version: int = Field(ge=0)
    specification: FrameSpecificationInput
    variants: list[VariantSpecificationInput] = Field(default_factory=list, max_length=200)


class ManualFrameInput(Input):
    a: float = Field(gt=0, le=99999.99)
    b: float = Field(gt=0, le=99999.99)
    dbl: float = Field(gt=0, le=99999.99)
    ed: float | None = Field(default=None, gt=0, le=99999.99)
    model: str = Field(default="Frame ukuran manual", max_length=160)


class SessionCreateInput(Input):
    product_id: str | None = Field(default=None, min_length=1, max_length=64)
    variant_id: str | None = Field(default=None, min_length=1, max_length=64)
    manual_frame: ManualFrameInput | None = None
    expected_profile_version: int = Field(ge=1)
    expected_spec_version: int | None = Field(default=None, ge=1)
    examination_date: CalendarDate | None = None
    working_distance_cm: float = Field(default=40, gt=0, le=10000)
    required_parameters: list[str] = Field(default_factory=lambda: ["distance_pd"], min_length=1, max_length=8)
    mode: Literal["manual", "semi_automatic"] = "semi_automatic"
    device: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def frame_source(self):
        if self.product_id is not None:
            if self.variant_id is None or self.expected_spec_version is None or self.manual_frame is not None:
                raise ValueError("Frame katalog memerlukan varian dan versi spesifikasi, tanpa ukuran manual")
        elif self.manual_frame is None or self.variant_id is not None or self.expected_spec_version is not None:
            raise ValueError("Pilih frame katalog atau isi ukuran manual A, B, dan DBL")
        return self


class RevisionInput(Input):
    expected_revision_id: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=5, max_length=2000)
    data: dict[str, Any]


class RevisionActionInput(Input):
    expected_revision_id: str = Field(min_length=1, max_length=64)


class ReviewInput(RevisionActionInput):
    decision: Literal["approved", "needs_remeasure", "needs_verification"]
    note: str = Field(min_length=5, max_length=4000)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExportInput(Input):
    revision_id: str = Field(min_length=1, max_length=64)
    format: Literal["pdf", "csv", "json", "print"]
    confirmed: bool
    include_photos: bool = False
    photo_ids: list[str] = Field(default_factory=list, max_length=3)


class DeletePhotoInput(Input):
    reason: str = Field(default="Foto dihapus atas permintaan pemilik akun.", min_length=5, max_length=1000)
