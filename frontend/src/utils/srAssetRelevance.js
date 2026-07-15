function normalizeSrId(requirementId) {
  return (requirementId || '').replace(/\s+/g, ' ').trim()
}

function getFrNumber(requirementId) {
  const match = normalizeSrId(requirementId).match(/SR\s*(\d+)/i)
  return match ? parseInt(match[1], 10) : null
}

function getSrSubNumber(requirementId) {
  const match = normalizeSrId(requirementId).match(/SR\s*\d+\.(\d+)/i)
  return match ? parseInt(match[1], 10) : null
}

function assetTypeNormalized(asset) {
  const raw = asset?.asset_type || asset?.asset_type_name || ''
  return String(raw).toLowerCase()
}

function assetTypeMatchesTypicalRoles(assetTypeName, typicalRoles) {
  if (!assetTypeName || !typicalRoles?.length) return false
  const normalized = assetTypeName.replace(/[\s\-_]/g, '')
  for (const role of typicalRoles) {
    const roleNorm = String(role).toLowerCase().replace(/[\s\-_]/g, '')
    if (!roleNorm) continue
    if (normalized.includes(roleNorm) || roleNorm.includes(normalized)) return true
    const mappings = {
      plc: ['plc', 'controller', 'programmable'],
      hmi: ['hmi', 'human', 'machine', 'interface'],
      server: ['server', 'scada', 'historian'],
      firewall: ['firewall', 'fw'],
      rtu: ['rtu', 'remote', 'terminal'],
      router: ['router', 'switch'],
      data_diode: ['diode', 'unidirectional'],
    }
    if (mappings[roleNorm]) {
      if (mappings[roleNorm].some((keyword) => normalized.includes(keyword))) return true
    }
  }
  return false
}

function matchesAnyPattern(assetType, patterns) {
  return patterns.some((pattern) => pattern.test(assetType))
}

function boolLabel(value) {
  return value ? 'YES' : 'NO'
}

export function getAssetTechnicalCharacteristics(asset, sr, t) {
  const characteristics = {}
  if (!asset || !sr) return characteristics

  const srId = normalizeSrId(sr.requirement_id)
  const fr = getFrNumber(srId)
  const sub = getSrSubNumber(srId)
  const assetType = assetTypeNormalized(asset)

  if (asset.remote_access !== undefined) {
    characteristics[t('isa62443.compliance.remoteAccess')] = boolLabel(asset.remote_access)
  }
  if (asset.remote_access && asset.remote_access_type) {
    characteristics[t('isa62443.compliance.remoteAccessType')] = asset.remote_access_type
  }
  if (asset.business_criticality) {
    characteristics[t('assets.fields.businessCriticality')] = asset.business_criticality
  }
  if (assetType) {
    characteristics[t('assets.fields.assetType')] = asset.asset_type || asset.asset_type_name
  }

  if (fr === 2 && [5, 6, 11].includes(sub)) {
    characteristics[t('isa62443.compliance.interactiveSessions')] = boolLabel(
      asset.remote_access || /hmi|engineering|workstation|scada/.test(assetType)
    )
    characteristics[t('isa62443.compliance.sessionLockSupported')] = boolLabel(
      asset.custom_fields?.session_lock_supported === true
    )
  }

  if (fr === 3) {
    characteristics[t('assets.fields.firmwareVersion')] = asset.firmware_version || 'N/A'
    if (asset.last_update_date) {
      characteristics[t('isa62443.compliance.lastUpdate')] = asset.last_update_date
    }
  }

  if (fr === 5) {
    characteristics[t('isa62443.securityZones.networkSegment')] =
      asset.network_segment || asset.custom_fields?.network_segment || 'N/A'
  }

  if (fr === 6) {
    characteristics[t('isa62443.compliance.centralizedLogging')] = boolLabel(
      asset.custom_fields?.centralized_logging === true ||
        /siem|historian|server|scada/.test(assetType)
    )
  }

  if (fr === 7) {
    characteristics[t('isa62443.compliance.redundancy')] = boolLabel(
      asset.custom_fields?.redundancy === true || asset.custom_fields?.redundant === true
    )
  }

  if (asset.capabilities?.length) {
    for (const capEntry of asset.capabilities) {
      const capName = capEntry.capability?.name || capEntry.capability?.code
      if (!capName) continue
      const status = capEntry.status === 'verified' ? 'YES' : capEntry.status === 'inferred' ? 'INFERRED' : 'DECLARED'
      characteristics[capName] = status
    }
  }

  if (Object.keys(characteristics).length === 0 && srId) {
    characteristics[t('isa62443.compliance.remoteAccess')] = boolLabel(asset.remote_access)
  }

  return characteristics
}

export function isAssetRelevantForSR(asset, sr, assessmentData) {
  if (!asset || !sr) return false

  const assetId = String(asset.id || asset.asset_id || '')
  const evidenceAssets = assessmentData?.available_evidence?.assets || []
  if (evidenceAssets.some((entry) => String(entry.asset_id) === assetId)) {
    return true
  }

  const requiredCaps = assessmentData?.required_capabilities || []
  const assetType = assetTypeNormalized(asset)
  const fr = getFrNumber(sr.requirement_id)
  const sub = getSrSubNumber(sr.requirement_id)

  for (const cap of requiredCaps) {
    if (!cap.applies_to_asset) continue
    if (assetTypeMatchesTypicalRoles(assetType, cap.typical_roles)) return true
  }

  switch (fr) {
    case 1:
      return asset.remote_access ||
        matchesAnyPattern(assetType, [/hmi/, /engineering/, /workstation/, /server/, /scada/, /operator/])
    case 2:
      if ([5, 6, 11].includes(sub)) {
        return asset.remote_access ||
          matchesAnyPattern(assetType, [/hmi/, /engineering/, /workstation/, /scada/])
      }
      return matchesAnyPattern(assetType, [/hmi/, /plc/, /engineering/, /server/, /workstation/]) ||
        asset.remote_access
    case 3:
      return matchesAnyPattern(assetType, [/plc/, /hmi/, /server/, /rtu/, /engineering/, /controller/, /switch/])
    case 4:
      return asset.remote_access ||
        matchesAnyPattern(assetType, [/server/, /historian/, /database/, /engineering/, /hmi/])
    case 5:
      return matchesAnyPattern(assetType, [/firewall/, /router/, /switch/, /gateway/, /diode/, /dmz/, /conduit/])
    case 6:
      return matchesAnyPattern(assetType, [/server/, /scada/, /historian/, /siem/, /hmi/, /plc/])
    case 7:
      return ['critical', 'high'].includes(asset.business_criticality) ||
        matchesAnyPattern(assetType, [/plc/, /server/, /rtu/, /controller/])
    default:
      return false
  }
}

export function mergeSrAssetLists(evidenceAssets, legacyAssets, sr, assessmentData) {
  const merged = new Map()

  for (const entry of evidenceAssets || []) {
    merged.set(String(entry.asset_id), {
      id: entry.asset_id,
      name: entry.asset_name,
      asset_type: entry.asset_type,
      capabilities: entry.capabilities,
    })
  }

  for (const asset of legacyAssets || []) {
    const id = String(asset.id)
    if (merged.has(id)) continue
    if (isAssetRelevantForSR(asset, sr, assessmentData)) {
      merged.set(id, asset)
    }
  }

  return Array.from(merged.values())
}
