# backend/app/init_data/init_sr_capability_mappings.py
"""
Initialize mappings between Security Requirements (SR) and Security Capabilities.

This creates the SRCapability records that link each SR to the capabilities it requires.
"""
import logging
import re
from sqlalchemy.orm import Session
from app.models.security_requirement import SecurityRequirement
from app.models.security_capability import SecurityCapability
from app.models.sr_capability import SRCapability
from app.crud.security_capabilities import get_security_capability_by_code

logger = logging.getLogger(__name__)


def init_sr_capability_mappings(db: Session):
    """Create default mappings between SRs and Capabilities"""
    
    # Mapping rules: SR requirement_id pattern -> capability codes
    # Format: (sr_pattern, [(capability_code, importance), ...])
    mappings = [
        # FR 1 - Identification & Authentication Control
        ('SR 1.1', [('user_authentication', 'primary'), ('role_based_authentication', 'supporting')]),
        ('SR 1.2', [('device_authentication', 'primary'), ('certificate_based_authentication', 'supporting')]),
        ('SR 1.3', [('role_based_authentication', 'primary'), ('user_authentication', 'supporting')]),
        ('SR 1.4', [('user_authentication', 'primary')]),
        ('SR 1.5', [('certificate_based_authentication', 'primary'), ('secure_key_management', 'supporting')]),
        ('SR 1.6', [('centralized_identity_integration', 'primary')]),
        ('SR 1.7', [('user_authentication', 'primary')]),
        ('SR 1.8', [('device_authentication', 'primary')]),
        ('SR 1.9', [('certificate_based_authentication', 'primary')]),
        ('SR 1.10', [('user_authentication', 'primary')]),
        ('SR 1.11', [('device_authentication', 'primary')]),
        ('SR 1.12', [('certificate_based_authentication', 'primary')]),
        ('SR 1.13', [('centralized_identity_integration', 'primary')]),
        
        # FR 2 - Use Control
        ('SR 2.1', [('role_based_access_control', 'primary'), ('privilege_separation', 'supporting')]),
        ('SR 2.2', [('role_based_access_control', 'primary')]),
        ('SR 2.3', [('role_based_access_control', 'primary')]),
        ('SR 2.4', [('role_based_access_control', 'primary')]),
        ('SR 2.5', [('session_locking_timeout', 'primary')]),
        ('SR 2.6', [('session_locking_timeout', 'primary')]),
        ('SR 2.7', [('least_privilege_enforcement', 'primary')]),
        ('SR 2.8', [('command_authorization', 'primary')]),
        ('SR 2.9', [('privilege_separation', 'primary')]),
        ('SR 2.10', [('role_based_access_control', 'primary')]),
        
        # FR 3 - System Integrity
        ('SR 3.1', [('configuration_integrity_monitoring', 'primary')]),
        ('SR 3.2', [('malware_protection', 'primary')]),
        ('SR 3.3', [('secure_boot', 'primary'), ('firmware_integrity_validation', 'supporting')]),
        ('SR 3.4', [('patch_management_capability', 'primary'), ('configuration_integrity_monitoring', 'supporting')]),
        ('SR 3.5', [('configuration_integrity_monitoring', 'primary')]),
        ('SR 3.6', [('firmware_integrity_validation', 'primary')]),
        ('SR 3.7', [('secure_boot', 'primary')]),
        ('SR 3.8', [('malware_protection', 'primary')]),
        ('SR 3.9', [('patch_management_capability', 'primary')]),
        ('SR 3.10', [('configuration_integrity_monitoring', 'primary')]),
        
        # FR 4 - Data Confidentiality
        ('SR 4.1', [('encrypted_communication_transit', 'primary'), ('encrypted_data_rest', 'supporting')]),
        ('SR 4.2', [('encrypted_data_rest', 'primary'), ('secure_key_management', 'supporting')]),
        ('SR 4.3', [('sensitive_data_classification', 'primary')]),
        ('SR 4.4', [('encrypted_communication_transit', 'primary')]),
        
        # FR 5 - Restricted Data Flow
        ('SR 5.1', [('network_segmentation', 'primary')]),
        ('SR 5.2', [('firewalling_traffic_filtering', 'primary'), ('protocol_whitelisting', 'supporting')]),
        ('SR 5.3', [('firewalling_traffic_filtering', 'primary')]),
        ('SR 5.4', [('unidirectional_communication', 'primary')]),
        ('SR 5.5', [('dmz_enforcement', 'primary')]),
        ('SR 5.6', [('network_segmentation', 'primary')]),
        ('SR 5.7', [('firewalling_traffic_filtering', 'primary')]),
        
        # FR 6 - Timely Response to Events
        ('SR 6.1', [('security_event_logging', 'primary')]),
        ('SR 6.2', [('centralized_log_collection', 'primary')]),
        ('SR 6.3', [('centralized_log_collection', 'primary'), ('security_event_logging', 'supporting')]),
        ('SR 6.4', [('security_event_logging', 'primary')]),
        ('SR 6.5', [('intrusion_detection', 'primary'), ('alerting_notification', 'supporting')]),
        ('SR 6.6', [('alerting_notification', 'primary')]),
        ('SR 6.7', [('incident_response_procedures', 'primary')]),
        
        # FR 7 - Resource Availability
        ('SR 7.1', [('rate_limiting_dos_protection', 'primary')]),
        ('SR 7.2', [('resource_monitoring', 'primary')]),
        ('SR 7.3', [('backup_restore', 'primary')]),
        ('SR 7.4', [('backup_restore', 'primary'), ('redundancy', 'supporting')]),
        ('SR 7.5', [('redundancy', 'primary')]),
        ('SR 7.6', [('failsafe_behavior', 'primary')]),
        ('SR 7.7', [('resource_monitoring', 'primary')]),
    ]
    
    created_count = 0
    skipped_count = 0
    missing_sr_count = 0
    missing_capability_count = 0
    missing_srs = []
    
    # Get all SRs
    all_srs = db.query(SecurityRequirement).all()
    sr_by_id = {sr.requirement_id: sr for sr in all_srs}
    
    # Get all capabilities
    all_capabilities = db.query(SecurityCapability).all()
    capability_by_code = {cap.code: cap for cap in all_capabilities}
    
    # Process mappings
    for sr_pattern, capability_mappings in mappings:
        # Find matching SRs (handle both "SR 1.1" and "SR1.1" formats)
        matching_srs = []
        for sr_id, sr in sr_by_id.items():
            # Normalize both pattern and SR ID for comparison
            normalized_pattern = sr_pattern.replace(' ', '')
            normalized_sr_id = sr_id.replace(' ', '')
            if normalized_sr_id == normalized_pattern:
                matching_srs.append(sr)
        
        if not matching_srs:
            # Try to find by pattern matching
            pattern_re = re.compile(sr_pattern.replace(' ', r'\s*'))
            for sr_id, sr in sr_by_id.items():
                if pattern_re.match(sr_id):
                    matching_srs.append(sr)
        
        if not matching_srs:
            # SR not found - this is normal if the database doesn't have all SRs
            missing_sr_count += 1
            missing_srs.append(sr_pattern)
            continue
        
        # Create mappings for each matching SR
        for sr in matching_srs:
            for capability_code, importance in capability_mappings:
                capability = capability_by_code.get(capability_code)
                if not capability:
                    # Capability not found - this is a real error
                    logger.warning(f"Capability not found: {capability_code} (for {sr.requirement_id})")
                    missing_capability_count += 1
                    continue
                
                # Check if mapping already exists
                existing = (
                    db.query(SRCapability)
                    .filter(
                        SRCapability.sr_id == sr.id,
                        SRCapability.capability_id == capability.id
                    )
                    .first()
                )
                
                if existing:
                    # Update importance if different
                    if existing.importance != importance:
                        existing.importance = importance
                        db.commit()
                    skipped_count += 1
                    continue
                
                # Create new mapping
                sr_cap = SRCapability(
                    sr_id=sr.id,
                    capability_id=capability.id,
                    importance=importance
                )
                db.add(sr_cap)
                created_count += 1
    
    db.commit()
    
    # Summary
    print(f"✅ Created {created_count} SR-Capability mappings")
    if skipped_count > 0:
        print(f"ℹ️  Skipped {skipped_count} existing mappings")
    if missing_sr_count > 0:
        print(f"ℹ️  {missing_sr_count} SR patterns not found in database (normal if database doesn't have all SRs)")
        if len(missing_srs) <= 10:  # Show list if not too many
            print(f"   Missing SRs: {', '.join(missing_srs)}")
    if missing_capability_count > 0:
        print(f"⚠️  {missing_capability_count} capabilities not found (check capability initialization)")
    
    return created_count

