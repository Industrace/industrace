"""Reusable Pydantic v2 field validator mixins."""
from pydantic import field_validator

from app.schemas.validators import (
    validate_business_criticality,
    validate_email,
    validate_impact_value,
    validate_ip_address,
    validate_mac_address,
    validate_password,
    validate_phone,
    validate_physical_access_ease,
    validate_purdue_level,
    validate_remote_access_type,
    validate_risk_score,
    validate_tax_code,
    validate_tenant_slug,
    validate_vat_number,
    validate_vlan,
    validate_website,
)


class PhoneWebsiteEmailMixin:
    @field_validator("phone")
    @classmethod
    def _validate_phone_field(cls, v):
        return validate_phone(v)

    @field_validator("website")
    @classmethod
    def _validate_website_field(cls, v):
        return validate_website(v)

    @field_validator("email")
    @classmethod
    def _validate_email_field(cls, v):
        return validate_email(v)


class SupplierFieldsMixin(PhoneWebsiteEmailMixin):
    @field_validator("vat_number")
    @classmethod
    def _validate_vat_number_field(cls, v):
        return validate_vat_number(v)

    @field_validator("tax_code")
    @classmethod
    def _validate_tax_code_field(cls, v):
        return validate_tax_code(v)


class AssetRiskFieldsMixin:
    @field_validator("impact_value")
    @classmethod
    def _validate_impact_value_field(cls, v):
        return validate_impact_value(v)

    @field_validator("purdue_level")
    @classmethod
    def _validate_purdue_level_field(cls, v):
        return validate_purdue_level(v)

    @field_validator("risk_score")
    @classmethod
    def _validate_risk_score_field(cls, v):
        return validate_risk_score(v)

    @field_validator("business_criticality")
    @classmethod
    def _validate_business_criticality_field(cls, v):
        return validate_business_criticality(v)

    @field_validator("remote_access_type")
    @classmethod
    def _validate_remote_access_type_field(cls, v):
        return validate_remote_access_type(v)

    @field_validator("physical_access_ease")
    @classmethod
    def _validate_physical_access_ease_field(cls, v):
        return validate_physical_access_ease(v)


class AssetInterfaceFieldsMixin:
    @field_validator("ip_address")
    @classmethod
    def _validate_ip_address_field(cls, v):
        return validate_ip_address(v)

    @field_validator("mac_address")
    @classmethod
    def _validate_mac_address_field(cls, v):
        return validate_mac_address(v)

    @field_validator("vlan")
    @classmethod
    def _validate_vlan_field(cls, v):
        return validate_vlan(v)


class SetupFieldsMixin:
    @field_validator("tenant_slug")
    @classmethod
    def _validate_tenant_slug_field(cls, v):
        return validate_tenant_slug(v)

    @field_validator("admin_password")
    @classmethod
    def _validate_admin_password_field(cls, v):
        return validate_password(v)
