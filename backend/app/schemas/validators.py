from pydantic import validator
from app.errors.validation_errors import (
    InvalidImpactValueError,
    InvalidPurdueLevelError,
    InvalidRiskScoreError,
    InvalidBusinessCriticalityError,
    InvalidRemoteAccessTypeError,
    InvalidPhysicalAccessEaseError,
    InvalidIPAddressError,
    InvalidMACAddressError,
    InvalidVLANError,
    InvalidEmailError,
    InvalidPhoneError,
    InvalidURLError,
    InvalidVATNumberError,
    InvalidTaxCodeError,
    InvalidTenantSlugError,
    InvalidPasswordError
)
import re
import ipaddress


def validate_impact_value(cls, v):
    """Validate impact value (1-5 scale)"""
    if v is None:
        return v
    if v < 1 or v > 5:
        raise InvalidImpactValueError('impact_value')
    return v


def validate_purdue_level(cls, v):
    """Validate Purdue level (0.0-5.0 scale)"""
    if v is None:
        return v
    if v < 0.0 or v > 5.0:
        raise InvalidPurdueLevelError('purdue_level')
    return v


def validate_risk_score(cls, v):
    """Validate risk score (0.0-10.0 scale)"""
    if v is None:
        return v
    if v < 0.0 or v > 10.0:
        raise InvalidRiskScoreError('risk_score')
    return v


def validate_business_criticality(cls, v):
    """Validate business criticality values"""
    if v is None:
        return v
    allowed_values = ['low', 'medium', 'high', 'critical']
    if v.lower() not in allowed_values:
        raise InvalidBusinessCriticalityError('business_criticality')
    return v.lower()


def validate_remote_access_type(cls, v):
    """Validate remote access type values"""
    if v is None:
        return v
    allowed_values = ['none', 'attended', 'unattended']
    if v.lower() not in allowed_values:
        raise InvalidRemoteAccessTypeError('remote_access_type')
    return v.lower()


def validate_physical_access_ease(cls, v):
    """Validate physical access ease values"""
    if v is None:
        return v
    # Support both old values (for backward compatibility) and new values
    allowed_values = ['internal', 'dmz', 'external', 'unrestricted', 'controlled', 'restricted']
    if v.lower() not in allowed_values:
        raise InvalidPhysicalAccessEaseError('physical_access_ease')
    return v.lower()


def validate_ip_address(cls, v):
    """Validate IP address format - more permissive for non-standard addresses"""
    if v is None or v == "":
        return v
    
    # Se è già una stringa valida di IP, la accettiamo
    try:
        ipaddress.ip_address(v)
        return v
    except ValueError:
        # Se non è un IP valido ma sembra essere un identificatore o nome host,
        # lo accettiamo comunque per non bloccare l'importazione
        if isinstance(v, str) and len(v.strip()) > 0:
            # Log dell'IP non valido ma lo accettiamo comunque
            print(f"⚠️  IP non valido accettato: {v}")
            return v
        else:
            raise InvalidIPAddressError('ip_address')


def validate_mac_address(cls, v):
    """Validate MAC address format"""
    if v is None or v == "":
        return v
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    if not mac_pattern.match(v):
        raise InvalidMACAddressError('mac_address')
    return v


def validate_vlan(cls, v):
    """Validate VLAN number (1-4094)"""
    if v is None or v == "":
        return v
    try:
        vlan_num = int(v)
        if vlan_num < 1 or vlan_num > 4094:
            raise InvalidVLANError('vlan')
        return v
    except ValueError:
        raise InvalidVLANError('vlan')


def validate_email(cls, v):
    """Validate email format"""
    if v is None or v == "":
        return v
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    if not email_pattern.match(v):
        raise InvalidEmailError('email')
    return v


def validate_phone(cls, v):
    """Validate phone number format"""
    if v is None or v == "":
        return v
    # Remove spaces, dashes, and parentheses for validation
    clean_phone = re.sub(r'[\s\-\(\)]', '', v)
    if not re.match(r'^\+?[0-9]{7,15}$', clean_phone):
        raise InvalidPhoneError('phone')
    return v


def validate_website(cls, v):
    """Validate website URL format"""
    if v is None or v == "":
        return v
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if not url_pattern.match(v):
        raise InvalidURLError('website')
    return v


def validate_vat_number(cls, v):
    """Validate VAT number format (International formats)"""
    if v is None or v == "":
        return v
    # Remove spaces and convert to uppercase
    vat = re.sub(r'\s', '', v).upper()
    
    # More flexible VAT number patterns
    vat_patterns = [
        r'^[A-Z]{2}[0-9A-Z]{5,15}$',  # Generic: 2 letters + 5-15 alphanumeric
        r'^[0-9A-Z]{8,15}$',          # Generic: 8-15 alphanumeric (no country prefix)
    ]
    
    for pattern in vat_patterns:
        if re.match(pattern, vat):
            return v
    
    raise InvalidVATNumberError('vat_number')


def validate_tax_code(cls, v):
    """Validate tax code format (International formats)"""
    if v is None or v == "":
        return v
    # Remove spaces and convert to uppercase
    tax_code = re.sub(r'\s', '', v).upper()
    
    # More flexible tax code patterns
    tax_patterns = [
        r'^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$',  # Italian Codice Fiscale
        r'^[A-Z0-9]{6,20}$',  # Generic alphanumeric (most countries)
        r'^[0-9]{6,15}$',     # Numeric only (some countries)
    ]
    
    for pattern in tax_patterns:
        if re.match(pattern, tax_code):
            return v
    
    raise InvalidTaxCodeError('tax_code')


def validate_tenant_slug(cls, v):
    """Validate tenant slug format"""
    if v is None or v == "":
        return v
    if not re.match(r'^[a-z0-9-]+$', v):
        raise InvalidTenantSlugError('tenant_slug')
    return v


def validate_password_strength(password: str, allow_weak: bool = False) -> None:
    """
    Validate password strength.
    Requires (unless allow_weak=True):
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    
    Args:
        password: The password to validate
        allow_weak: If True, skip validation (for default accounts that require password change)
    """
    if password is None or password == "":
        return
    
    # Allow weak passwords for default accounts that require password change
    if allow_weak:
        return
    
    import re
    
    # Minimum length: 12 characters
    if len(password) < 12:
        raise InvalidPasswordError('password')
    
    # At least one uppercase letter
    if not re.search(r'[A-Z]', password):
        raise InvalidPasswordError('password')
    
    # At least one lowercase letter
    if not re.search(r'[a-z]', password):
        raise InvalidPasswordError('password')
    
    # At least one number
    if not re.search(r'\d', password):
        raise InvalidPasswordError('password')
    
    # At least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\[\]\\/_+=\-~`]', password):
        raise InvalidPasswordError('password')


def validate_password(cls, v):
    """
    Validate password strength (Pydantic validator).
    Requires:
    - Minimum 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    validate_password_strength(v, allow_weak=False)
    return v 