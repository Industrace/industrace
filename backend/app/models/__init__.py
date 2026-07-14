from app.database import Base
from .tenant import Tenant
from .user import User
from .site import Site
from .area import Area
from .asset_type import AssetType
from .location import Location, LocationFloorplan
from .manufacturer import Manufacturer
from .asset_communication import AssetCommunication
from .asset_interface import AssetInterface
from .asset_document import AssetDocument
from .asset_photo import AssetPhoto
from .asset_connection import AssetConnection
from .audit_log import AuditLog
from .asset_status import AssetStatus
from .contact import Contact
from .tenant_smtp_config import TenantSMTPConfig
from .tenant_syslog_config import TenantSyslogConfig
from .print_template import PrintTemplate
from .print_history import PrintHistory
from .api_key import ApiKey

# Notification models
from .notification_template import NotificationTemplate
from .notification_preference import NotificationPreference
from .notification_queue import NotificationQueue
from .notification_log import NotificationLog

# ISA/IEC 62443 Capability-based models
from .security_capability import SecurityCapability
from .sr_capability import SRCapability
from .asset_capability import AssetCapability
from .sr_assessment import SRAssessment
from .sr_assessment_evidence import SRAssessmentEvidence
from .conduit_asset import ConduitAsset

# ISA/IEC 62443 models
from .security_requirement import SecurityRequirement
from .requirement_enhancement import RequirementEnhancement
from .security_zone import SecurityZone
from .conduit import Conduit
from .security_requirement_compliance import SecurityRequirementCompliance
from .asset_zone_membership import AssetZoneMembership
from .evidence import Evidence

# Asset Dependencies
from .asset_dependency import AssetDependency

# Vulnerability Intelligence
from .vulnerability import Vulnerability, AssetVulnerability, VulnerabilityFeedSource

# Enterprise Authentication
from .tenant_sso_config import TenantSSOConfig
from .sso_oauth_state import SsoOAuthState

# Network Probes (devono essere importati prima di Asset se referenziano Asset via relationship string)
from .network_probe import NetworkProbe, ProbeHeartbeat, ProbeDataTransmission
from .discovered_device import DiscoveredDevice, DeviceDiscoveryStatus

# Questi modelli dipendono dagli altri (devono venire dopo)
from .supplier import Supplier, SupplierDocument
from .asset import Asset
from .role import Role
