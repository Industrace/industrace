# backend/app/init_data/init_security_capabilities.py
"""
Initialize ISA/IEC 62443 Security Capabilities.
Initial catalog of practical and realistic security capabilities organized by Foundation Requirements (FR).

This is a healthy initial set (20-30 capabilities are more than sufficient to start).
"""
from sqlalchemy.orm import Session
from app.models.security_capability import SecurityCapability
from app.crud.security_capabilities import get_security_capability_by_code, create_security_capability
from app.schemas.security_capability import SecurityCapabilityCreate


def init_security_capabilities(db: Session):
    """Create default ISA/IEC 62443 Security Capabilities"""
    
    capabilities = [
        # FR 1 – Identification & Authentication Control
        {
            'code': 'user_authentication',
            'name': 'User Authentication',
            'description': 'Capability to authenticate human users before allowing access to system resources.',
            'category': 'identity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['hmi', 'server']
        },
        {
            'code': 'device_authentication',
            'name': 'Device Authentication',
            'description': 'Capability to authenticate devices and software processes before allowing access to system resources.',
            'category': 'identity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': True,
            'typical_roles': ['plc', 'rtu']
        },
        {
            'code': 'role_based_authentication',
            'name': 'Role-Based Authentication',
            'description': 'Capability to authenticate users based on their assigned roles.',
            'category': 'identity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['hmi', 'server']
        },
        {
            'code': 'certificate_based_authentication',
            'name': 'Certificate-Based Authentication',
            'description': 'Capability to authenticate using digital certificates (X.509, PKI).',
            'category': 'identity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': True,
            'typical_roles': ['server', 'firewall']
        },
        {
            'code': 'centralized_identity_integration',
            'name': 'Centralized Identity Integration',
            'description': 'Capability to integrate with centralized identity management systems (LDAP, Active Directory, etc.).',
            'category': 'identity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server']
        },
        
        # FR 2 – Use Control
        {
            'code': 'role_based_access_control',
            'name': 'Role-Based Access Control (RBAC)',
            'description': 'Capability to enforce access control based on user roles and permissions.',
            'category': 'access_control',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['hmi', 'server']
        },
        {
            'code': 'privilege_separation',
            'name': 'Privilege Separation',
            'description': 'Capability to separate and isolate privileges between different system components or users.',
            'category': 'access_control',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server']
        },
        {
            'code': 'least_privilege_enforcement',
            'name': 'Least Privilege Enforcement',
            'description': 'Capability to enforce the principle of least privilege, granting only the minimum necessary permissions.',
            'category': 'access_control',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['all']
        },
        {
            'code': 'session_locking_timeout',
            'name': 'Session Locking / Timeout',
            'description': 'Capability to automatically lock sessions after a period of inactivity or timeout.',
            'category': 'access_control',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['hmi']
        },
        {
            'code': 'command_authorization',
            'name': 'Command Authorization',
            'description': 'Capability to authorize and validate commands before execution, especially for control systems.',
            'category': 'access_control',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['plc']
        },
        
        # FR 3 – System Integrity
        {
            'code': 'secure_boot',
            'name': 'Secure Boot',
            'description': 'Capability to verify the integrity of boot firmware and software during system startup.',
            'category': 'system_integrity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['plc', 'server']
        },
        {
            'code': 'firmware_integrity_validation',
            'name': 'Firmware Integrity Validation',
            'description': 'Capability to validate the integrity of firmware before loading or execution.',
            'category': 'system_integrity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['plc']
        },
        {
            'code': 'patch_management_capability',
            'name': 'Patch Management Capability',
            'description': 'Capability to manage, test, and apply security patches and updates in a controlled manner.',
            'category': 'system_integrity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server']
        },
        {
            'code': 'malware_protection',
            'name': 'Malware Protection',
            'description': 'Capability to detect, prevent, and remove malicious software (antivirus, antimalware, application whitelisting).',
            'category': 'system_integrity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server', 'hmi']
        },
        {
            'code': 'configuration_integrity_monitoring',
            'name': 'Configuration Integrity Monitoring',
            'description': 'Capability to monitor and detect unauthorized changes to system configuration.',
            'category': 'system_integrity',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['all']
        },
        
        # FR 4 – Data Confidentiality
        {
            'code': 'encrypted_communication_transit',
            'name': 'Encrypted Communication in Transit',
            'description': 'Capability to encrypt data during transmission over networks (TLS, IPSec, etc.).',
            'category': 'data_confidentiality',
            'applies_to_asset': False,
            'applies_to_zone': False,
            'applies_to_conduit': True,
            'typical_roles': ['network']
        },
        {
            'code': 'encrypted_data_rest',
            'name': 'Encrypted Data at Rest',
            'description': 'Capability to encrypt data when stored on disk or in databases.',
            'category': 'data_confidentiality',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server']
        },
        {
            'code': 'secure_key_management',
            'name': 'Secure Key Management',
            'description': 'Capability to securely generate, store, rotate, and manage cryptographic keys.',
            'category': 'data_confidentiality',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server']
        },
        {
            'code': 'sensitive_data_classification',
            'name': 'Sensitive Data Classification',
            'description': 'Capability to classify and label sensitive data according to its confidentiality level.',
            'category': 'data_confidentiality',
            'applies_to_asset': False,
            'applies_to_zone': True,
            'applies_to_conduit': False,
            'typical_roles': []
        },
        
        # FR 5 – Restricted Data Flow
        {
            'code': 'network_segmentation',
            'name': 'Network Segmentation',
            'description': 'Capability to logically or physically segment networks to restrict data flow between zones.',
            'category': 'boundary_protection',
            'applies_to_asset': False,
            'applies_to_zone': True,
            'applies_to_conduit': False,
            'typical_roles': []
        },
        {
            'code': 'firewalling_traffic_filtering',
            'name': 'Firewalling / Traffic Filtering',
            'description': 'Capability to filter and control network traffic based on rules and policies.',
            'category': 'boundary_protection',
            'applies_to_asset': False,
            'applies_to_zone': False,
            'applies_to_conduit': True,
            'typical_roles': ['firewall']
        },
        {
            'code': 'unidirectional_communication',
            'name': 'Unidirectional Communication',
            'description': 'Capability to enforce one-way data flow (data diode) to prevent unauthorized data exfiltration.',
            'category': 'boundary_protection',
            'applies_to_asset': False,
            'applies_to_zone': False,
            'applies_to_conduit': True,
            'typical_roles': ['data_diode']
        },
        {
            'code': 'protocol_whitelisting',
            'name': 'Protocol Whitelisting',
            'description': 'Capability to allow only approved network protocols and block all others.',
            'category': 'boundary_protection',
            'applies_to_asset': False,
            'applies_to_zone': False,
            'applies_to_conduit': True,
            'typical_roles': ['firewall']
        },
        {
            'code': 'dmz_enforcement',
            'name': 'DMZ Enforcement',
            'description': 'Capability to enforce a demilitarized zone (DMZ) architecture for secure data exchange.',
            'category': 'boundary_protection',
            'applies_to_asset': False,
            'applies_to_zone': True,
            'applies_to_conduit': False,
            'typical_roles': []
        },
        
        # FR 6 – Timely Response to Events
        {
            'code': 'security_event_logging',
            'name': 'Security Event Logging',
            'description': 'Capability to log security-relevant events (authentication, authorization, configuration changes, etc.).',
            'category': 'monitoring',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['all']
        },
        {
            'code': 'centralized_log_collection',
            'name': 'Centralized Log Collection',
            'description': 'Capability to collect and aggregate logs from multiple sources into a centralized system.',
            'category': 'monitoring',
            'applies_to_asset': False,
            'applies_to_zone': True,
            'applies_to_conduit': False,
            'typical_roles': []
        },
        {
            'code': 'intrusion_detection',
            'name': 'Intrusion Detection',
            'description': 'Capability to detect unauthorized access attempts, anomalies, or security violations.',
            'category': 'monitoring',
            'applies_to_asset': False,
            'applies_to_zone': True,
            'applies_to_conduit': False,
            'typical_roles': []
        },
        {
            'code': 'alerting_notification',
            'name': 'Alerting and Notification',
            'description': 'Capability to generate alerts and notifications when security events are detected.',
            'category': 'monitoring',
            'applies_to_asset': False,
            'applies_to_zone': True,
            'applies_to_conduit': False,
            'typical_roles': []
        },
        {
            'code': 'incident_response_procedures',
            'name': 'Incident Response Procedures',
            'description': 'Capability to execute defined procedures for responding to security incidents.',
            'category': 'monitoring',
            'applies_to_asset': False,
            'applies_to_zone': True,
            'applies_to_conduit': False,
            'typical_roles': []
        },
        
        # FR 7 – Resource Availability
        {
            'code': 'redundancy',
            'name': 'Redundancy',
            'description': 'Capability to provide redundant components or systems to ensure availability in case of failure.',
            'category': 'resource_availability',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['plc', 'server']
        },
        {
            'code': 'failsafe_behavior',
            'name': 'Fail-Safe Behavior',
            'description': 'Capability to enter a safe state when failures or security violations are detected.',
            'category': 'resource_availability',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['plc']
        },
        {
            'code': 'rate_limiting_dos_protection',
            'name': 'Rate Limiting / DoS Protection',
            'description': 'Capability to limit request rates and protect against denial-of-service attacks.',
            'category': 'resource_availability',
            'applies_to_asset': False,
            'applies_to_zone': False,
            'applies_to_conduit': True,
            'typical_roles': ['firewall']
        },
        {
            'code': 'backup_restore',
            'name': 'Backup & Restore',
            'description': 'Capability to create backups and restore system state in case of data loss or corruption.',
            'category': 'resource_availability',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server']
        },
        {
            'code': 'resource_monitoring',
            'name': 'Resource Monitoring',
            'description': 'Capability to monitor system resources (CPU, memory, disk, network) to detect and prevent exhaustion.',
            'category': 'resource_availability',
            'applies_to_asset': True,
            'applies_to_zone': False,
            'applies_to_conduit': False,
            'typical_roles': ['server']
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for cap_data in capabilities:
        # Check if capability already exists
        existing = get_security_capability_by_code(db, cap_data['code'])
        if existing:
            skipped_count += 1
            continue
        
        # Create capability
        capability_in = SecurityCapabilityCreate(**cap_data)
        create_security_capability(db, capability_in)
        created_count += 1
    
    if created_count > 0:
        print(f"✅ Created {created_count} Security Capabilities")
    if skipped_count > 0:
        print(f"ℹ️  Skipped {skipped_count} existing Security Capabilities")
    
    return created_count

