# backend/app/init_data/init_security_requirements.py
"""
Initialize ISA/IEC 62443 Security Requirements.
Based on ISA/IEC 62443-3-3:2013 standard.

Structure:
- FR 1-7: Foundational Requirements (7 macro-categories)
- SR X.Y: Security Requirements (52 SR in IEC 62443-3-3:2013)
"""
from sqlalchemy.orm import Session
from app.models import SecurityRequirement
import uuid


# ISA/IEC 62443-3-3 Security Requirements (SR); each SR belongs to one of FR 1–7.
SECURITY_REQUIREMENTS_DATA = [
        # FR 1 - Identification and Authentication Control (IAC)
        # SR 1.1 - SR 1.13
        {
            'requirement_id': 'SR 1.1',
            'requirement_category': 'SR',
            'title': 'Human user identification and authentication',
            'description': 'The IACS shall identify and authenticate all human users before allowing access to IACS resources.',
            'requirement_text': 'The IACS shall identify and authenticate all human users before allowing access to IACS resources.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.1'
        },
        {
            'requirement_id': 'SR 1.2',
            'requirement_category': 'SR',
            'title': 'Software process and device identification and authentication',
            'description': 'The IACS shall identify and authenticate all software processes and devices.',
            'requirement_text': 'The IACS shall identify and authenticate all software processes and devices before allowing access to IACS resources.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.2'
        },
        {
            'requirement_id': 'SR 1.3',
            'requirement_category': 'SR',
            'title': 'Account management',
            'description': 'The IACS shall manage user accounts.',
            'requirement_text': 'The IACS shall manage user accounts, including the ability to create, modify, disable, and delete accounts.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.3'
        },
        {
            'requirement_id': 'SR 1.4',
            'requirement_category': 'SR',
            'title': 'Identifier management',
            'description': 'The IACS shall manage identifiers.',
            'requirement_text': 'The IACS shall manage identifiers for all users, software processes, and devices.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.4'
        },
        {
            'requirement_id': 'SR 1.5',
            'requirement_category': 'SR',
            'title': 'Authenticator management',
            'description': 'The IACS shall manage authenticators.',
            'requirement_text': 'The IACS shall manage authenticators for all users, software processes, and devices.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.5'
        },
        {
            'requirement_id': 'SR 1.6',
            'requirement_category': 'SR',
            'title': 'Wireless access management',
            'description': 'The IACS shall manage wireless access.',
            'requirement_text': 'The IACS shall manage wireless access, including the ability to configure, monitor, and control wireless connections.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.6'
        },
        {
            'requirement_id': 'SR 1.7',
            'requirement_category': 'SR',
            'title': 'Strength of password-based authentication',
            'description': 'The IACS shall enforce strong password policies.',
            'requirement_text': 'The IACS shall enforce strong password policies, including minimum length, complexity, and expiration requirements.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.7'
        },
        {
            'requirement_id': 'SR 1.8',
            'requirement_category': 'SR',
            'title': 'Public key infrastructure certificates',
            'description': 'The IACS shall support PKI certificates for authentication.',
            'requirement_text': 'The IACS shall support PKI certificates for authentication of users, software processes, and devices.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.8'
        },
        {
            'requirement_id': 'SR 1.9',
            'requirement_category': 'SR',
            'title': 'Strength of public key-based authentication',
            'description': 'The IACS shall enforce strong public key authentication.',
            'requirement_text': 'The IACS shall enforce strong public key authentication, including key length and algorithm requirements.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.9'
        },
        {
            'requirement_id': 'SR 1.10',
            'requirement_category': 'SR',
            'title': 'Authentication using biometrics',
            'description': 'The IACS shall support biometric authentication.',
            'requirement_text': 'The IACS shall support biometric authentication for users where appropriate.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 3,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.10'
        },
        {
            'requirement_id': 'SR 1.11',
            'requirement_category': 'SR',
            'title': 'Unsuccessful login attempts',
            'description': 'The IACS shall limit unsuccessful login attempts.',
            'requirement_text': 'The IACS shall limit the number of unsuccessful login attempts and implement appropriate actions after exceeding the limit.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.11'
        },
        {
            'requirement_id': 'SR 1.12',
            'requirement_category': 'SR',
            'title': 'System use notification',
            'description': 'The IACS shall display system use notifications.',
            'requirement_text': 'The IACS shall display appropriate system use notifications to users.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.12'
        },
        {
            'requirement_id': 'SR 1.13',
            'requirement_category': 'SR',
            'title': 'Access via untrusted networks',
            'description': 'The IACS shall control access via untrusted networks.',
            'requirement_text': 'The IACS shall control and secure access via untrusted networks, including the use of VPN or other secure channels.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 1.13'
        },
        # FR 2 - Use Control (UC)
        # SR 2.1 - SR 2.12
        {
            'requirement_id': 'SR 2.1',
            'requirement_category': 'SR',
            'title': 'Authorization enforcement',
            'description': 'The IACS shall enforce authorization policies.',
            'requirement_text': 'The IACS shall enforce authorization policies for all users, software processes, and devices.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.1'
        },
        {
            'requirement_id': 'SR 2.2',
            'requirement_category': 'SR',
            'title': 'Wireless use control',
            'description': 'The IACS shall control wireless access.',
            'requirement_text': 'The IACS shall control wireless access, including the ability to restrict, monitor, and audit wireless connections.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.2'
        },
        {
            'requirement_id': 'SR 2.3',
            'requirement_category': 'SR',
            'title': 'Use control for portable and mobile devices',
            'description': 'The IACS shall control portable and mobile devices.',
            'requirement_text': 'The IACS shall control the use of portable and mobile devices, including the ability to restrict, monitor, and audit their use.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.3'
        },
        {
            'requirement_id': 'SR 2.4',
            'requirement_category': 'SR',
            'title': 'Mobile code',
            'description': 'The IACS shall control mobile code.',
            'requirement_text': 'The IACS shall control mobile code, including the ability to restrict, monitor, and audit its execution.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.4'
        },
        {
            'requirement_id': 'SR 2.5',
            'requirement_category': 'SR',
            'title': 'Session lock',
            'description': 'The IACS shall provide session lock capability.',
            'requirement_text': 'The IACS shall provide the capability to lock sessions after a period of inactivity.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.5'
        },
        {
            'requirement_id': 'SR 2.6',
            'requirement_category': 'SR',
            'title': 'Remote session termination',
            'description': 'The IACS shall provide remote session termination capability.',
            'requirement_text': 'The IACS shall provide the capability to terminate remote sessions, including automatic termination after a specified period.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': False,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.6'
        },
        {
            'requirement_id': 'SR 2.7',
            'requirement_category': 'SR',
            'title': 'Concurrent session control',
            'description': 'The IACS shall control concurrent sessions.',
            'requirement_text': 'The IACS shall control the number of concurrent sessions per user.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.7'
        },
        {
            'requirement_id': 'SR 2.8',
            'requirement_category': 'SR',
            'title': 'Auditable events',
            'description': 'The IACS shall define and log auditable events.',
            'requirement_text': 'The IACS shall define and log auditable events, including authentication, authorization, and system changes.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.8'
        },
        {
            'requirement_id': 'SR 2.9',
            'requirement_category': 'SR',
            'title': 'Audit storage capacity',
            'description': 'The IACS shall manage audit storage capacity.',
            'requirement_text': 'The IACS shall manage audit storage capacity to ensure sufficient space for audit logs.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.9'
        },
        {
            'requirement_id': 'SR 2.10',
            'requirement_category': 'SR',
            'title': 'Response to audit processing failures',
            'description': 'The IACS shall respond to audit processing failures.',
            'requirement_text': 'The IACS shall respond appropriately to audit processing failures, including the ability to alert administrators.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.10'
        },
        {
            'requirement_id': 'SR 2.11',
            'requirement_category': 'SR',
            'title': 'Timestamps',
            'description': 'The IACS shall use timestamps in audit logs.',
            'requirement_text': 'The IACS shall use accurate timestamps in audit logs, synchronized across all system components.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.11'
        },
        {
            'requirement_id': 'SR 2.12',
            'requirement_category': 'SR',
            'title': 'Non-repudiation',
            'description': 'The IACS shall provide non-repudiation capability.',
            'requirement_text': 'The IACS shall provide non-repudiation capability for critical actions, ensuring that actions cannot be denied.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 3,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.12'
        },
        {
            'requirement_id': 'SR 2.13',
            'requirement_category': 'SR',
            'title': 'Use of physical diagnostic and test interfaces',
            'description': 'The IACS shall restrict use of physical diagnostic and test interfaces.',
            'requirement_text': (
                'The IACS shall enforce that physical diagnostic and test interfaces are only '
                'enabled during maintenance or diagnostic sessions and are disabled otherwise.'
            ),
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 2.13'
        },
        # FR 3 - System Integrity (SI)
        # SR 3.1 - SR 3.9
        {
            'requirement_id': 'SR 3.1',
            'requirement_category': 'SR',
            'title': 'Communication integrity',
            'description': 'The IACS shall protect communication integrity.',
            'requirement_text': 'The IACS shall protect the integrity of communications, including the ability to detect and prevent unauthorized modification.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.1'
        },
        {
            'requirement_id': 'SR 3.2',
            'requirement_category': 'SR',
            'title': 'Malicious code protection',
            'description': 'The IACS shall protect against malicious code.',
            'requirement_text': 'The IACS shall protect against malicious code, including the ability to detect, prevent, and remove malware.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.2'
        },
        {
            'requirement_id': 'SR 3.3',
            'requirement_category': 'SR',
            'title': 'Security functionality verification',
            'description': 'The IACS shall verify security functionality.',
            'requirement_text': 'The IACS shall verify that security functionality is operating correctly, including periodic testing and validation.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.3'
        },
        {
            'requirement_id': 'SR 3.4',
            'requirement_category': 'SR',
            'title': 'Software and information integrity',
            'description': 'The IACS shall protect software and information integrity.',
            'requirement_text': 'The IACS shall protect the integrity of software and information, including the ability to detect and prevent unauthorized modification.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.4'
        },
        {
            'requirement_id': 'SR 3.5',
            'requirement_category': 'SR',
            'title': 'Input validation',
            'description': 'The IACS shall validate input.',
            'requirement_text': 'The IACS shall validate all input to prevent unauthorized access or modification.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.5'
        },
        {
            'requirement_id': 'SR 3.6',
            'requirement_category': 'SR',
            'title': 'Deterministic output',
            'description': 'The IACS shall provide deterministic output.',
            'requirement_text': 'The IACS shall provide deterministic output, ensuring predictable behavior under all conditions.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.6'
        },
        {
            'requirement_id': 'SR 3.7',
            'requirement_category': 'SR',
            'title': 'Error handling',
            'description': 'The IACS shall handle errors securely.',
            'requirement_text': 'The IACS shall handle errors securely, including the ability to prevent information disclosure through error messages.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.7'
        },
        {
            'requirement_id': 'SR 3.8',
            'requirement_category': 'SR',
            'title': 'Session integrity',
            'description': 'The IACS shall protect session integrity.',
            'requirement_text': 'The IACS shall protect session integrity, including the ability to detect and prevent unauthorized modification of session data.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': False,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.8'
        },
        {
            'requirement_id': 'SR 3.9',
            'requirement_category': 'SR',
            'title': 'Protection of audit information',
            'description': 'The IACS shall protect audit information.',
            'requirement_text': 'The IACS shall protect audit information from unauthorized access, modification, or deletion.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 3.9'
        },
        # FR 4 - Data Confidentiality (DC)
        # SR 4.1 - SR 4.3
        {
            'requirement_id': 'SR 4.1',
            'requirement_category': 'SR',
            'title': 'Information confidentiality',
            'description': 'The IACS shall protect information confidentiality.',
            'requirement_text': 'The IACS shall protect the confidentiality of information, including the ability to encrypt sensitive data.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 4.1'
        },
        {
            'requirement_id': 'SR 4.2',
            'requirement_category': 'SR',
            'title': 'Use of cryptography',
            'description': 'The IACS shall use cryptography appropriately.',
            'requirement_text': 'The IACS shall use cryptography appropriately, including the use of approved algorithms and key management.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 4.2'
        },
        {
            'requirement_id': 'SR 4.3',
            'requirement_category': 'SR',
            'title': 'User session confidentiality',
            'description': 'The IACS shall protect user session confidentiality.',
            'requirement_text': 'The IACS shall protect the confidentiality of user sessions, including the ability to encrypt session data.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': False,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 4.3'
        },
        # FR 5 - Restricted Data Flow (RDF)
        # SR 5.1 - SR 5.4
        {
            'requirement_id': 'SR 5.1',
            'requirement_category': 'SR',
            'title': 'Network segmentation',
            'description': 'The IACS shall provide network segmentation.',
            'requirement_text': 'The IACS shall provide network segmentation to restrict data flow between network segments.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 5.1'
        },
        {
            'requirement_id': 'SR 5.2',
            'requirement_category': 'SR',
            'title': 'Zone boundary protection',
            'description': 'The IACS shall protect zone boundaries.',
            'requirement_text': 'The IACS shall protect zone boundaries, including the ability to control and monitor data flow between zones.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': False,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 5.2'
        },
        {
            'requirement_id': 'SR 5.3',
            'requirement_category': 'SR',
            'title': 'General-purpose person-to-person communication restrictions',
            'description': 'The IACS shall restrict general purpose communication.',
            'requirement_text': 'The IACS shall restrict general purpose person-to-person communication, including the ability to block or monitor such communications.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 5.3'
        },
        {
            'requirement_id': 'SR 5.4',
            'requirement_category': 'SR',
            'title': 'Application partitioning',
            'description': 'The IACS shall provide application partitioning.',
            'requirement_text': 'The IACS shall provide application partitioning to restrict data flow between applications.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 5.4'
        },
        # FR 6 - Timely Response to Events (TRE)
        # SR 6.1 - SR 6.2
        {
            'requirement_id': 'SR 6.1',
            'requirement_category': 'SR',
            'title': 'Audit log accessibility',
            'description': 'The IACS shall provide access to audit logs.',
            'requirement_text': 'The IACS shall provide access to audit logs, including the ability to view, search, and export log data.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 6.1'
        },
        {
            'requirement_id': 'SR 6.2',
            'requirement_category': 'SR',
            'title': 'Continuous monitoring',
            'description': 'The IACS shall provide continuous monitoring.',
            'requirement_text': 'The IACS shall provide continuous monitoring of security events, including the ability to detect and alert on suspicious activities.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 6.2'
        },
        # FR 7 - Resource Availability (RA)
        # SR 7.1 - SR 7.8
        {
            'requirement_id': 'SR 7.1',
            'requirement_category': 'SR',
            'title': 'Denial of service protection',
            'description': 'The IACS shall protect against denial of service.',
            'requirement_text': 'The IACS shall protect against denial of service attacks, including the ability to detect, prevent, and recover from such attacks.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.1'
        },
        {
            'requirement_id': 'SR 7.2',
            'requirement_category': 'SR',
            'title': 'Resource management',
            'description': 'The IACS shall manage resources.',
            'requirement_text': 'The IACS shall manage system resources, including the ability to monitor and control resource usage.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.2'
        },
        {
            'requirement_id': 'SR 7.3',
            'requirement_category': 'SR',
            'title': 'Control system backup',
            'description': 'The IACS shall provide backup capability.',
            'requirement_text': 'The IACS shall provide backup capability, including the ability to create, store, and restore backups.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.3'
        },
        {
            'requirement_id': 'SR 7.4',
            'requirement_category': 'SR',
            'title': 'Control system recovery and reconstitution',
            'description': 'The IACS shall provide recovery capability.',
            'requirement_text': 'The IACS shall provide recovery and reconstitution capability, including the ability to restore system functionality after a security incident.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.4'
        },
        {
            'requirement_id': 'SR 7.5',
            'requirement_category': 'SR',
            'title': 'Emergency power',
            'description': 'The IACS shall provide emergency power.',
            'requirement_text': 'The IACS shall provide emergency power capability to ensure continued operation during power outages.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 2,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.5'
        },
        {
            'requirement_id': 'SR 7.6',
            'requirement_category': 'SR',
            'title': 'Network and security configuration settings',
            'description': 'The IACS shall manage network and security configuration settings.',
            'requirement_text': 'The IACS shall manage network and security configuration settings, including the ability to control and monitor configuration changes.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.6'
        },
        {
            'requirement_id': 'SR 7.7',
            'requirement_category': 'SR',
            'title': 'Least functionality',
            'description': 'The IACS shall implement least functionality principle.',
            'requirement_text': 'The IACS shall implement the principle of least functionality, ensuring that only necessary functions are enabled.',
            'applies_to_zones': True,
            'applies_to_conduits': True,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.7'
        },
        {
            'requirement_id': 'SR 7.8',
            'requirement_category': 'SR',
            'title': 'Control system component inventory',
            'description': 'The IACS shall maintain component inventory.',
            'requirement_text': 'The IACS shall maintain an inventory of control system components, including hardware, software, and firmware.',
            'applies_to_zones': True,
            'applies_to_conduits': False,
            'applies_to_assets': True,
            'min_security_level': 1,
            'max_security_level': 4,
            'standard_version': '62443-3-3:2013',
            'section_reference': 'SR 7.8'
        },
]

# Backward-compatible alias for tests and tooling
SECURITY_REQUIREMENTS = SECURITY_REQUIREMENTS_DATA


def init_security_requirements(db: Session):
    """Create default ISA/IEC 62443 Security Requirements"""
    requirements = SECURITY_REQUIREMENTS_DATA
    created_count = 0
    for req_data in requirements:
        # Check if requirement already exists
        existing = (
            db.query(SecurityRequirement)
            .filter(SecurityRequirement.requirement_id == req_data['requirement_id'])
            .first()
        )
        
        if not existing:
            requirement = SecurityRequirement(
                id=uuid.uuid4(),
                **req_data
            )
            db.add(requirement)
            created_count += 1
        else:
            # Update existing requirement
            for key, value in req_data.items():
                setattr(existing, key, value)
    
    db.commit()
    return created_count


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        count = init_security_requirements(db)
        print(f"Created {count} security requirements")
    finally:
        db.close()
