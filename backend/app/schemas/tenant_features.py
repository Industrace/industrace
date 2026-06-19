from pydantic import BaseModel, Field


class TenantFeaturesRead(BaseModel):
    iec62443: bool = Field(..., description="ISA/IEC 62443 compliance module (zones, conduits, SR assessments)")


class TenantFeaturesUpdate(BaseModel):
    iec62443: bool
