# backend/app/schemas/mfa.py
from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MfaStatusResponse(BaseModel):
    totp_enabled: bool
    totp_verified_at: Optional[datetime] = None
    backup_codes_remaining: int = 0
    policy: str = "optional"
    enrollment_deadline_days: int = 7
    requires_enrollment: bool = False
    past_grace: bool = False
    can_self_disable: bool = True


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class MfaVerifySetupRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)


class MfaDisableRequest(BaseModel):
    password: str
    code: str


class MfaRegenerateBackupRequest(BaseModel):
    code: str


class BackupCodesResponse(BaseModel):
    backup_codes: List[str]


class MfaLoginRequest(BaseModel):
    mfa_token: str
    code: str


class MfaPolicyResponse(BaseModel):
    mfa_policy: Literal["optional", "required_admins", "required_all"]
    mfa_enrollment_deadline_days: int = 7
    mfa_policy_enforced_at: Optional[str] = None


class MfaPolicyUpdate(BaseModel):
    mfa_policy: Literal["optional", "required_admins", "required_all"]
    mfa_enrollment_deadline_days: int = Field(7, ge=0, le=365)


class AdminMfaStatusResponse(BaseModel):
    user_id: UUID
    totp_enabled: bool
    totp_verified_at: Optional[datetime] = None
    backup_codes_remaining: int = 0
