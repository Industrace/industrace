import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export const AUDIT_ACTIONS = [
  'create', 'update', 'delete', 'login', 'logout',
  'bulk_update', 'bulk_soft_delete', 'soft_delete', 'restore', 'hard_delete', 'empty_trash',
  'update_custom_fields', 'update_position', 'update_contacts', 'add_contact', 'delete_contact', 'update_suppliers',
  'mark_asset_reviewed', 'skip_asset_review', 'bulk_mark_assets_reviewed', 'recalculate_all_review_dates',
  'reset_password', 'get', 'export', 'import', 'deactivate', 'activate', 'api_key_used', 'list',
  'create_security_zone', 'update_security_zone', 'delete_security_zone',
  'calculate_zone_sl', 'recalculate_zone_sla',
  'create_asset_zone_membership', 'update_asset_zone_membership', 'delete_asset_zone_membership',
  'create_conduit', 'update_conduit', 'delete_conduit', 'calculate_conduit_sl',
  'create_sr_assessment', 'delete_notification_preference',
  'deauthorize', 'onboard', 'sso_login', 'import_users', 'update_vulnerability_status',
]

export const AUDIT_ENTITIES = [
  'Asset', 'User', 'Site', 'Location', 'Supplier', 'Contact',
  'AssetType', 'AssetStatus', 'Manufacturer', 'Role', 'Tenant', 'Area',
  'ApiKey', 'AssetDocument', 'AssetPhoto', 'AssetInterface', 'AssetConnection',
  'AssetDependency', 'AssetCapability', 'SecurityZone', 'AssetZoneMembership', 'Conduit',
  'Vulnerability', 'VulnerabilityFeedSource', 'AssetVulnerability',
  'TenantSSOConfig', 'TenantFeatures', 'LocationFloorplan', 'SupplierDocument',
  'NotificationPreference', 'NetworkProbe', 'DiscoveredDevice', 'TenantSyslogConfig',
]

export const ASSET_TIMELINE_ACTIONS = [
  'create', 'update', 'delete', 'soft_delete', 'restore', 'hard_delete',
  'bulk_update', 'update_custom_fields', 'update_position',
  'update_contacts', 'add_contact', 'delete_contact', 'update_suppliers',
  'mark_asset_reviewed', 'skip_asset_review', 'bulk_mark_assets_reviewed',
]

const ENTITY_ROUTES = {
  Asset: (id) => ({ name: 'AssetDetail', params: { id } }),
  Site: (id) => ({ name: 'SiteDetail', params: { id } }),
  Supplier: (id) => ({ name: 'SupplierDetail', params: { id } }),
  Contact: (id) => ({ name: 'ContactDetail', params: { id } }),
  Manufacturer: (id) => ({ name: 'ManufacturerDetail', params: { id } }),
  AssetType: (id) => ({ name: 'AssetTypeDetail', params: { id } }),
}

const ACTION_SEVERITY = {
  create: 'success',
  update: 'info',
  delete: 'danger',
  login: 'warning',
  logout: 'secondary',
  soft_delete: 'warning',
  hard_delete: 'danger',
  restore: 'success',
  bulk_update: 'info',
  mark_asset_reviewed: 'success',
}

const ACTION_CLASS = {
  create: 'bg-green-500',
  update: 'bg-blue-500',
  delete: 'bg-red-500',
  login: 'bg-yellow-500',
  logout: 'bg-gray-500',
  soft_delete: 'bg-orange-500',
  restore: 'bg-green-500',
}

const ACTION_ICON = {
  create: 'pi pi-plus',
  update: 'pi pi-pencil',
  delete: 'pi pi-trash',
  login: 'pi pi-sign-in',
  logout: 'pi pi-sign-out',
  soft_delete: 'pi pi-inbox',
  restore: 'pi pi-replay',
  mark_asset_reviewed: 'pi pi-check',
}

const ENTITY_ICONS = {
  Asset: 'pi pi-desktop',
  User: 'pi pi-user',
  Site: 'pi pi-building',
  Location: 'pi pi-map-marker',
  Supplier: 'pi pi-briefcase',
  Contact: 'pi pi-address-book',
  AssetType: 'pi pi-tag',
  AssetStatus: 'pi pi-circle-fill',
  Manufacturer: 'pi pi-cog',
  NetworkProbe: 'pi pi-wifi',
  SecurityZone: 'pi pi-shield',
  Vulnerability: 'pi pi-exclamation-triangle',
}

export function useAuditLogLabels(actionList = AUDIT_ACTIONS, entityList = AUDIT_ENTITIES) {
  const { t, te } = useI18n()

  const actionOptions = computed(() =>
    actionList.map((value) => ({
      label: getActionLabel(value),
      value,
    }))
  )

  const entityOptions = computed(() =>
    entityList.map((value) => ({
      label: getEntityLabel(value),
      value,
    }))
  )

  function getActionLabel(action) {
    if (!action) return '-'
    const key = `auditlog.actions.${action}`
    return te(key) ? t(key) : action
  }

  function getEntityLabel(entity) {
    if (!entity) return '-'
    const key = `auditlog.entities.${entity}`
    return te(key) ? t(key) : entity
  }

  function getActionSeverity(action) {
    return ACTION_SEVERITY[action] || 'info'
  }

  function getActionClass(action) {
    return ACTION_CLASS[action] || 'bg-gray-500'
  }

  function getActionIcon(action) {
    return ACTION_ICON[action] || 'pi pi-info'
  }

  function getEntityIcon(entity) {
    return ENTITY_ICONS[entity] || 'pi pi-file'
  }

  function getEntityRoute(entity, entityId) {
    const builder = ENTITY_ROUTES[entity]
    return builder ? builder(entityId) : null
  }

  function canNavigateToEntity(entity) {
    return Boolean(ENTITY_ROUTES[entity])
  }

  function formatDescription(log) {
    if (!log?.description) return '-'
    let description = log.description
    if (log.entity_name && log.entity_id) {
      description = description.replace(String(log.entity_id), log.entity_name)
    }
    return description
  }

  return {
    actionOptions,
    entityOptions,
    getActionLabel,
    getEntityLabel,
    getActionSeverity,
    getActionClass,
    getActionIcon,
    getEntityIcon,
    getEntityRoute,
    canNavigateToEntity,
    formatDescription,
  }
}
