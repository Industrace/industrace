# backend/app/init_data/iec62443_re_texts.py
"""
Requirement Enhancement (RE) texts for IEC 62443-3-3:2013 (52 SR × levels 1–4).
Paraphrased from normative tables; keys are requirement_id (e.g. "SR 1.1").
Updated on backend startup via init_requirement_enhancements.
"""
from typing import Dict

# RE level -> text (paraphrased from IEC 62443-3-3:2013 tables)
RE_TEXTS: Dict[str, Dict[int, str]] = {
    "SR 1.1": {
        1: "The control system shall provide the capability to identify and authenticate all human users.",
        2: "The control system shall provide the capability to uniquely identify and authenticate all human users.",
        3: "The control system shall provide the capability to uniquely identify and authenticate all human users before allowing access.",
        4: "The control system shall provide the capability to uniquely identify and authenticate all human users before allowing access to any control system function.",
    },
    "SR 1.2": {
        1: "The control system shall provide the capability to identify and authenticate all software processes and devices.",
        2: "The control system shall provide the capability to uniquely identify and authenticate all software processes and devices.",
        3: "The control system shall provide the capability to uniquely identify and authenticate all software processes and devices before allowing access.",
        4: "The control system shall provide the capability to uniquely identify and authenticate all software processes and devices before allowing access to any control system function.",
    },
    "SR 1.3": {
        1: "The control system shall provide the capability to manage accounts for all human users.",
        2: "The control system shall provide the capability to manage accounts for all human users, including adding, modifying, and removing accounts.",
        3: "The control system shall provide the capability to manage accounts for all human users, including adding, modifying, disabling, and removing accounts.",
        4: "The control system shall provide the capability to manage accounts for all human users, including adding, modifying, disabling, and removing accounts, and shall enforce approval procedures.",
    },
    "SR 1.4": {
        1: "The control system shall provide the capability to manage identifiers for all users.",
        2: "The control system shall provide the capability to manage identifiers for all users, software processes, and devices.",
        3: "The control system shall provide the capability to ensure unique identifiers for users, software processes, and devices.",
        4: "The control system shall provide the capability to ensure unique identifiers for users, software processes, and devices and prevent identifier reuse without controlled lifecycle management.",
    },
    "SR 1.5": {
        1: "The control system shall provide the capability to manage authenticators for human users.",
        2: "The control system shall provide the capability to manage authenticators for human users and non-human entities.",
        3: "The control system shall provide the capability to enforce lifecycle controls for authenticators (issuance, update, revocation).",
        4: "The control system shall provide the capability to enforce lifecycle controls and strong protection for authenticators, including secure storage and recovery handling.",
    },
    "SR 1.6": {
        1: "The control system shall provide the capability to manage and monitor wireless access where used.",
        2: "The control system shall provide the capability to authorize and control wireless access based on role and policy.",
        3: "The control system shall provide the capability to restrict wireless access to approved use cases and detect unauthorized wireless access attempts.",
        4: "The control system shall provide the capability to restrict wireless access to approved use cases, detect unauthorized attempts, and enforce strong cryptographic protection.",
    },
    "SR 1.7": {
        1: "The control system shall provide the capability to enforce password-based authentication policy.",
        2: "The control system shall provide the capability to enforce password complexity and minimum length.",
        3: "The control system shall provide the capability to enforce password complexity, reuse constraints, and periodic change requirements.",
        4: "The control system shall provide the capability to enforce password complexity, reuse constraints, periodic changes, and additional hardening controls for privileged accounts.",
    },
    "SR 1.8": {
        1: "The control system shall provide the capability to support PKI certificates for authentication.",
        2: "The control system shall provide the capability to use PKI certificates for authentication of users, software processes, and devices.",
        3: "The control system shall use PKI certificates for authentication and validate certificate chains before granting access.",
        4: "The control system shall use PKI certificates for authentication, validate certificate chains, and enforce certificate lifecycle management.",
    },
    "SR 1.9": {
        1: "The control system shall provide the capability to enforce strength requirements for public key-based authentication.",
        2: "The control system shall enforce minimum key length and approved algorithms for public key authentication.",
        3: "The control system shall enforce approved algorithms, key lengths, and key lifecycle requirements for public key authentication.",
        4: "The control system shall enforce approved algorithms, key lengths, lifecycle requirements, and periodic re-keying for public key authentication.",
    },
    "SR 1.10": {
        1: "The control system shall provide the capability to support biometric authentication where appropriate.",
        2: "The control system shall support biometric authentication with defined false accept and false reject rates.",
        3: "The control system shall support biometric authentication with defined performance thresholds and liveness detection where applicable.",
        4: "The control system shall support biometric authentication with defined thresholds, liveness detection, and protected storage of biometric templates.",
    },
    "SR 1.11": {
        1: "The control system shall provide the capability to limit unsuccessful login attempts.",
        2: "The control system shall limit unsuccessful login attempts and take defined actions after exceeding the limit.",
        3: "The control system shall limit unsuccessful login attempts, lock or delay accounts, and generate audit records.",
        4: "The control system shall limit unsuccessful login attempts, enforce lockout or delay policies, generate audit records, and alert administrators on repeated failures.",
    },
    "SR 1.12": {
        1: "The control system shall provide the capability to display system use notifications to users.",
        2: "The control system shall display system use notifications before granting access.",
        3: "The control system shall display system use notifications before granting access and require acknowledgment where configured.",
        4: "The control system shall display system use notifications before granting access, require acknowledgment, and log acknowledgment events.",
    },
    "SR 1.13": {
        1: "The control system shall provide the capability to control access via untrusted networks.",
        2: "The control system shall control access via untrusted networks using secure channels.",
        3: "The control system shall control access via untrusted networks using secure channels and enforce policy before access.",
        4: "The control system shall control access via untrusted networks using secure channels, enforce policy, and audit remote access sessions.",
    },
    # FR 2 — Use Control (UC) / audit-related SRs
    "SR 2.1": {
        1: "The control system shall provide the capability to enforce authorization policies.",
        2: "The control system shall provide the capability to enforce authorization policies for all users and processes.",
        3: "The control system shall enforce authorization policies for all users, software processes, and devices before granting access.",
        4: "The control system shall enforce authorization policies for all users, software processes, and devices before granting access to any control system function.",
    },
    "SR 2.2": {
        1: "The control system shall provide the capability to control wireless access where used.",
        2: "The control system shall provide the capability to restrict and monitor wireless connections.",
        3: "The control system shall restrict wireless access to authorized use cases and audit wireless connections.",
        4: "The control system shall restrict wireless access to authorized use cases, audit connections, and enforce policy on wireless interfaces.",
    },
    "SR 2.3": {
        1: "The control system shall provide the capability to control use of portable and mobile devices.",
        2: "The control system shall provide the capability to restrict and monitor portable and mobile devices.",
        3: "The control system shall restrict portable and mobile device use to authorized cases and audit such use.",
        4: "The control system shall restrict portable and mobile device use to authorized cases, audit use, and enforce connection policy before access.",
    },
    "SR 2.4": {
        1: "The control system shall provide the capability to control mobile code execution.",
        2: "The control system shall provide the capability to restrict and monitor mobile code.",
        3: "The control system shall restrict mobile code to approved sources and monitor execution.",
        4: "The control system shall restrict mobile code to approved sources, monitor execution, and block unauthorized mobile code.",
    },
    "SR 2.5": {
        1: "The control system shall provide the capability to lock sessions after inactivity.",
        2: "The control system shall provide the capability to lock interactive sessions after a configurable inactivity period.",
        3: "The control system shall lock interactive sessions after inactivity and require re-authentication to resume.",
        4: "The control system shall lock interactive sessions after inactivity, require re-authentication, and support administrator-defined timeout policies.",
    },
    "SR 2.6": {
        1: "The control system shall provide the capability to terminate remote sessions.",
        2: "The control system shall provide the capability to terminate remote sessions manually and automatically.",
        3: "The control system shall terminate remote sessions after a specified period or on administrator request.",
        4: "The control system shall terminate remote sessions after a specified period or on request and log termination events.",
    },
    "SR 2.7": {
        1: "The control system shall provide the capability to limit concurrent sessions per user.",
        2: "The control system shall provide the capability to configure limits on concurrent sessions per user.",
        3: "The control system shall enforce configured limits on concurrent sessions and deny excess sessions.",
        4: "The control system shall enforce concurrent session limits, deny excess sessions, and audit session limit violations.",
    },
    "SR 2.8": {
        1: "The control system shall provide the capability to define and log auditable events.",
        2: "The control system shall provide the capability to log authentication, authorization, and system change events.",
        3: "The control system shall log defined auditable events including authentication, authorization, and security-relevant changes.",
        4: "The control system shall log all defined auditable events with sufficient detail to support security investigations.",
    },
    "SR 2.9": {
        1: "The control system shall provide the capability to manage audit log storage capacity.",
        2: "The control system shall provide the capability to monitor audit storage and alert when capacity is low.",
        3: "The control system shall manage audit storage to retain logs per policy and alert on capacity thresholds.",
        4: "The control system shall manage audit storage with retention policy, alerts, and protected overflow handling.",
    },
    "SR 2.10": {
        1: "The control system shall provide the capability to respond to audit processing failures.",
        2: "The control system shall provide the capability to alert administrators on audit processing failures.",
        3: "The control system shall alert administrators on audit failures and take defined compensating actions.",
        4: "The control system shall alert on audit failures, take compensating actions, and preserve evidence of failure handling.",
    },
    "SR 2.11": {
        1: "The control system shall provide the capability to use timestamps in audit records.",
        2: "The control system shall provide the capability to use synchronized timestamps in audit logs.",
        3: "The control system shall use accurate timestamps synchronized across components for audit records.",
        4: "The control system shall use accurate, synchronized timestamps on all audit records suitable for correlation and forensics.",
    },
    "SR 2.12": {
        1: "The control system shall provide the capability to support non-repudiation for critical actions.",
        2: "The control system shall provide the capability to bind critical actions to authenticated identities.",
        3: "The control system shall ensure critical actions are attributable to the acting identity and recorded in audit logs.",
        4: "The control system shall ensure critical actions cannot be repudiated, using strong binding of identity and protected audit evidence.",
    },
    "SR 2.13": {
        1: "The control system shall provide the capability to control use of physical diagnostic and test interfaces.",
        2: "The control system shall provide the capability to control use of physical diagnostic and test interfaces during maintenance only.",
        3: "The control system shall enforce that physical diagnostic and test interfaces are enabled only during maintenance or diagnostic sessions.",
        4: "The control system shall enforce that physical diagnostic and test interfaces are enabled only during maintenance or diagnostic sessions and are disabled otherwise.",
    },
    # FR 3 — System Integrity (SI)
    "SR 3.1": {
        1: "The control system shall provide the capability to protect the integrity of communicated information.",
        2: "The control system shall provide the capability to detect unauthorized modification of communicated information.",
        3: "The control system shall detect unauthorized modification of communicated information and generate an audit record.",
        4: "The control system shall detect unauthorized modification of communicated information, generate an audit record, and take defined actions to prevent further compromise.",
    },
    "SR 3.2": {
        1: "The control system shall provide the capability to protect against malicious code.",
        2: "The control system shall provide the capability to detect malicious code.",
        3: "The control system shall detect and prevent execution of malicious code.",
        4: "The control system shall detect, prevent, and remove malicious code and generate audit records of such events.",
    },
    "SR 3.3": {
        1: "The control system shall provide the capability to verify that security functionality is operating correctly.",
        2: "The control system shall verify security functionality on a periodic basis.",
        3: "The control system shall verify security functionality on a periodic basis and after security-relevant changes.",
        4: "The control system shall verify security functionality on a periodic basis and after changes, document results, and alert on verification failures.",
    },
    "SR 3.4": {
        1: "The control system shall provide the capability to protect the integrity of software and information.",
        2: "The control system shall provide the capability to detect unauthorized modification of software and information.",
        3: "The control system shall detect unauthorized modification of software and information and generate an audit record.",
        4: "The control system shall detect unauthorized modification of software and information, generate an audit record, and take defined actions to prevent further compromise.",
    },
    "SR 3.5": {
        1: "The control system shall provide the capability to validate input.",
        2: "The control system shall validate input and reject invalid input.",
        3: "The control system shall validate input syntax and semantics and reject invalid input.",
        4: "The control system shall validate input syntax and semantics, reject invalid input, and log validation failures.",
    },
    "SR 3.6": {
        1: "The control system shall provide the capability to ensure predictable output under defined conditions.",
        2: "The control system shall ensure output remains within defined bounds under fault conditions.",
        3: "The control system shall ensure deterministic, fail-safe output behavior under defined fault conditions.",
        4: "The control system shall ensure deterministic, fail-safe output behavior under defined fault conditions and document expected behavior.",
    },
    "SR 3.7": {
        1: "The control system shall provide the capability to handle errors without disclosing sensitive information.",
        2: "The control system shall limit information provided in error messages to authorized recipients.",
        3: "The control system shall limit error message content and log security-relevant errors securely.",
        4: "The control system shall limit error message content, log security-relevant errors securely, and prevent information disclosure through error handling.",
    },
    "SR 3.8": {
        1: "The control system shall provide the capability to protect session integrity.",
        2: "The control system shall provide the capability to detect unauthorized modification of session data.",
        3: "The control system shall detect unauthorized modification of session data and invalidate affected sessions.",
        4: "The control system shall detect unauthorized modification of session data, invalidate affected sessions, and generate audit records.",
    },
    "SR 3.9": {
        1: "The control system shall provide the capability to protect audit information.",
        2: "The control system shall protect audit information from unauthorized access.",
        3: "The control system shall protect audit information from unauthorized access, modification, and deletion.",
        4: "The control system shall protect audit information from unauthorized access, modification, and deletion using integrity mechanisms and access controls.",
    },
    # FR 4 — Data Confidentiality (DC)
    "SR 4.1": {
        1: "The control system shall provide the capability to protect the confidentiality of information.",
        2: "The control system shall protect the confidentiality of information during storage and transmission.",
        3: "The control system shall protect the confidentiality of information using encryption for sensitive data in storage and transmission.",
        4: "The control system shall protect the confidentiality of information using encryption, access controls, and defined key management for sensitive data.",
    },
    "SR 4.2": {
        1: "The control system shall provide the capability to use cryptography appropriately.",
        2: "The control system shall use approved cryptographic algorithms and modes.",
        3: "The control system shall use approved cryptographic algorithms, modes, and key management practices.",
        4: "The control system shall use approved cryptographic algorithms, modes, key management, and documented cryptographic profiles.",
    },
    "SR 4.3": {
        1: "The control system shall provide the capability to protect the confidentiality of user sessions.",
        2: "The control system shall protect user session confidentiality during transmission.",
        3: "The control system shall encrypt user session data during transmission.",
        4: "The control system shall encrypt user session data during transmission and protect session keys using approved mechanisms.",
    },
    # FR 5 — Restricted Data Flow (RDF)
    "SR 5.1": {
        1: "The control system shall provide the capability to segment networks to restrict data flow.",
        2: "The control system shall implement network segmentation between defined network segments.",
        3: "The control system shall implement network segmentation and control traffic between segments per policy.",
        4: "The control system shall implement network segmentation, enforce traffic policy between segments, and monitor inter-segment flows.",
    },
    "SR 5.2": {
        1: "The control system shall provide the capability to protect zone boundaries.",
        2: "The control system shall control data flow across zone boundaries.",
        3: "The control system shall control and monitor data flow across zone boundaries per policy.",
        4: "The control system shall control, monitor, and audit data flow across zone boundaries and deny unauthorized flows.",
    },
    "SR 5.3": {
        1: "The control system shall provide the capability to restrict general-purpose person-to-person communication.",
        2: "The control system shall block or monitor general-purpose person-to-person communication as defined by policy.",
        3: "The control system shall enforce restrictions on general-purpose person-to-person communication and log policy violations.",
        4: "The control system shall enforce restrictions on general-purpose person-to-person communication, log violations, and alert on unauthorized attempts.",
    },
    "SR 5.4": {
        1: "The control system shall provide the capability to partition applications to restrict data flow.",
        2: "The control system shall restrict data flow between applications using partitioning mechanisms.",
        3: "The control system shall enforce application partitioning and prevent unauthorized inter-application communication.",
        4: "The control system shall enforce application partitioning, prevent unauthorized communication, and audit partition policy violations.",
    },
    # FR 6 — Timely Response to Events (TRE)
    "SR 6.1": {
        1: "The control system shall provide the capability to access audit logs.",
        2: "The control system shall provide authorized users the capability to view and search audit logs.",
        3: "The control system shall provide authorized users the capability to view, search, and export audit logs.",
        4: "The control system shall provide authorized users the capability to view, search, and export audit logs with access controls and audit of log access.",
    },
    "SR 6.2": {
        1: "The control system shall provide the capability for continuous monitoring of security events.",
        2: "The control system shall monitor security events and generate alerts for defined conditions.",
        3: "The control system shall continuously monitor security events, detect suspicious activity, and alert administrators.",
        4: "The control system shall continuously monitor security events, detect suspicious activity, alert administrators, and support incident response workflows.",
    },
    # FR 7 — Resource Availability (RA)
    "SR 7.1": {
        1: "The control system shall provide the capability to protect against denial of service.",
        2: "The control system shall detect denial of service conditions.",
        3: "The control system shall detect and mitigate denial of service attacks.",
        4: "The control system shall detect, mitigate, and recover from denial of service attacks while preserving essential functions.",
    },
    "SR 7.2": {
        1: "The control system shall provide the capability to manage system resources.",
        2: "The control system shall monitor resource usage and enforce defined limits.",
        3: "The control system shall monitor resource usage, enforce limits, and take defined actions on threshold violations.",
        4: "The control system shall monitor resource usage, enforce limits, take defined actions on violations, and alert administrators.",
    },
    "SR 7.3": {
        1: "The control system shall provide the capability to create backups.",
        2: "The control system shall create and store backups on a defined schedule.",
        3: "The control system shall create, store, and protect backups according to policy.",
        4: "The control system shall create, store, protect, and verify backups according to policy with documented restore procedures.",
    },
    "SR 7.4": {
        1: "The control system shall provide the capability to recover from disruptions.",
        2: "The control system shall restore essential functionality after security incidents or failures.",
        3: "The control system shall recover and reconstitute system functionality using documented procedures after incidents.",
        4: "The control system shall recover and reconstitute system functionality, verify integrity after restore, and document recovery outcomes.",
    },
    "SR 7.5": {
        1: "The control system shall provide the capability for emergency power during outages.",
        2: "The control system shall maintain essential functions during short power outages.",
        3: "The control system shall maintain essential functions during defined outage durations using emergency power.",
        4: "The control system shall maintain essential functions during defined outage durations, test emergency power periodically, and document results.",
    },
    "SR 7.6": {
        1: "The control system shall provide the capability to manage network and security configuration settings.",
        2: "The control system shall control changes to network and security configuration settings.",
        3: "The control system shall control and monitor changes to network and security configuration settings.",
        4: "The control system shall control, monitor, and audit changes to network and security configuration settings with approval workflows.",
    },
    "SR 7.7": {
        1: "The control system shall provide the capability to enable only necessary functions (least functionality).",
        2: "The control system shall disable or remove unnecessary functions, ports, and services.",
        3: "The control system shall enforce least functionality and document enabled functions and services.",
        4: "The control system shall enforce least functionality, document enabled functions, and verify compliance on a defined basis.",
    },
    "SR 7.8": {
        1: "The control system shall provide the capability to maintain an inventory of control system components.",
        2: "The control system shall maintain an inventory of hardware, software, and firmware components.",
        3: "The control system shall maintain an accurate inventory of components and update it when changes occur.",
        4: "The control system shall maintain an accurate component inventory, update it on changes, and use it for vulnerability and patch management.",
    },
}
