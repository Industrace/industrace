import axios from 'axios'
import { useAuthStore } from '@/store/auth'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true 
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const auth = useAuthStore()
      auth.logout()
    }
    return Promise.reject(error)
  }
)

export default {
  async login(email, password) {
    const formData = new FormData()
    formData.append('email', email)
    formData.append('password', password)
    
    const response = await api.post('/login', formData)
    return response.data
  },
  getCurrentUser() {
    return api.get('/users/me')
  },
  getAssets(params = {}) {
    return api.get('/assets', { params })
  },
  getAssetsForNetworkMap() {
    return api.get('/assets/for-network-map')
  },
  getAssetsByLocation(locationId, params = {}) {
    return api.get(`/assets/by-location/${locationId}`, { params })
  },
  getAsset(id) {
    return api.get(`/assets/${id}`)
  },
  createAsset(assetData) {
    return api.post('/assets', assetData)
  },
  deleteAsset(id) {
    return api.delete(`/assets/${id}`)
  },
  updateAsset(id, formData) {
    return api.put(`/assets/${id}`, formData)
  },
  updateAssetCustomFields(id,formData){
    return api.patch(`/assets/${id}/custom-fields`, formData)
  },
  getSites(params = {}) {
    return api.get('/sites', { params })
  },
  getSite(id) {
    return api.get(`/sites/${id}`)
  },
  getAreas(params = {}) {
    return api.get('/areas', { params })
  },
  getAreasTrash(params = {}) {
    return api.get('/areas/trash', { params })
  },
  getArea(id) {
    return api.get(`/areas/${id}`)
  },
  createArea(areaData) {
    return api.post('/areas', areaData)
  },
  updateArea(id, areaData) {
    return api.put(`/areas/${id}`, areaData)
  },
  deleteArea(id) {
    return api.delete(`/areas/${id}`)
  },
  restoreArea(id) {
    return api.patch(`/areas/${id}/restore`)
  },
  hardDeleteArea(id) {
    return api.delete(`/areas/${id}/hard`)
  },
  emptyAreasTrash() {
    return api.delete('/areas/trash/empty')
  },
  getAreasBySite(siteId) {
    return api.get(`/areas/site/${siteId}`)
  },
  getLocations(formData) {
    return api.get('/locations', {
      params: formData
    })
  },
  updateLocation(id,formData) {
    return api.put(`/locations/${id}`, formData)
  },

  createLocation(formData) {
    return api.post(`/locations`, formData)
  },
  uploadFloorplan(locationId, formData) {
    return api.post(`/locations/${locationId}/floorplan`, formData)
  },
  getFloorplanFile(locationId, floorplanId) {
    return api.get(`/locations/${locationId}/floorplan/${floorplanId}/file`, { responseType: 'blob' })
  },
  createSite(siteData) {
    return api.post('/sites', siteData)
  },
  updateSite(id, formData) {
    return api.put(`/sites/${id}`, formData)
  },
  deleteSite(id) {
    return api.delete(`/sites/${id}`)
  },
  getSitesTrash(params = {}) {
    return api.get('/sites/trash', { params })
  },
  restoreSite(id) {
    return api.patch(`/sites/${id}/restore`)
  },
  hardDeleteSite(id) {
    return api.delete(`/sites/${id}/hard`)
  },
  emptySitesTrash() {
    return api.delete('/sites/trash/empty')
  },
  getAssetTypes() {
    return api.get('/asset-types')
  },
  getDashboardStats() {
    return api.get('/dashboard/stats')
  },
  getRiskyAssets(limit = 10) {
    return api.get('/dashboard/risky-assets', { params: { limit } })
  },
  getReviewsSummary() {
    return api.get('/dashboard/reviews-summary')
  },
  getDependenciesSummary() {
    return api.get('/dashboard/dependencies-summary')
  },
  getVulnerabilitiesSummary() {
    return api.get('/dashboard/vulnerabilities-summary')
  },
  getComplianceSummary() {
    return api.get('/dashboard/compliance-summary')
  },
  getExposureSummary() {
    return api.get('/dashboard/exposure')
  },
  getRecentChanges(limit = 10) {
    return api.get('/dashboard/recent-changes', { params: { limit } })
  },
  getEvidenceMissing() {
    return api.get('/dashboard/evidence-missing')
  },
  getAssetConnections(id) {
    return api.get(`/assets/${id}/connections`)
  },
  getAllConnections() {
    return api.get('/asset-connections')
  },
  createAssetConnection(assetId, connectionData) {
    return api.post(`/assets/${assetId}/connections`,connectionData)
  },
  updateAssetConnection(assetId, connectionId, connectionData) {
    return api.put(`/assets/${assetId}/connections/${connectionId}`, connectionData)
  },
  deleteAssetConnection(assetId,connectionId) {
    return api.delete(`/assets/${assetId}/connections/${connectionId}`)
  },
  uploadAssetPhoto(assetId, formData) {
    return api.post(`/assets/${assetId}/photos`, formData)
  },
  deleteAssetPhoto(assetId, photoId) {
    return api.delete(`/assets/${assetId}/photos/${photoId}`)
  },
  uploadAssetDocument(assetId, formData) {
    return api.post(`/assets/${assetId}/documents`, formData)
  },
  deleteAssetDocument(assetId, documentId) {
    return api.delete(`/assets/${assetId}/documents/${documentId}`)
  },
  updatePosition(assetId,position) {
    return api.patch(`/assets/${assetId}/position`, position)
  },
  uploadPcapFile(formData) {
    return api.post(`/pcap/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" }
      }) 
  },
  getAssetCommunications(assetId) {
    return api.get(`/assets/${assetId}/communications`)
  },
  getSuppliers() {
    return api.get('/suppliers')
  },
  getSetupStatus() {
    return api.get('/setup/status')
  },
  initializeSetup(setupData, setupToken = null) {
    const headers = setupToken ? { 'X-Setup-Token': setupToken } : {}
    return api.post('/setup/initialize', setupData, { headers })
  },
  testDatabaseConnection(setupToken = null) {
    const headers = setupToken ? { 'X-Setup-Token': setupToken } : {}
    return api.post('/setup/test-database', null, { headers })
  },
  getSupplier(id) {
    return api.get(`/suppliers/${id}`)
  },
  createSupplier(supplierData) {
    return api.post('/suppliers', supplierData)
  },
  updateSupplier(id, supplierData) {
    return api.put(`/suppliers/${id}`, supplierData)
  },
  deleteSupplier(id) {
    return api.delete(`/suppliers/${id}`)
  },
  getManufacturers() {
    return api.get('/manufacturers')
  },
  getManufacturersTrash(params = {}) {
    return api.get('/manufacturers/trash', { params })
  },
  getManufacturer(id) {
    return api.get(`/manufacturers/${id}`)
  },
  createManufacturer(manufacturerData) {
    return api.post('/manufacturers', manufacturerData)
  },
  updateManufacturer(id, manufacturerData) {
    return api.put(`/manufacturers/${id}`, manufacturerData)
  },
  deleteManufacturer(id) {
    return api.delete(`/manufacturers/${id}`)
  },
  restoreManufacturer(id) {
    return api.patch(`/manufacturers/${id}/restore`)
  },
  hardDeleteManufacturer(id) {
    return api.delete(`/manufacturers/${id}/hard`)
  },
  getAssetType(id) {
    return api.get(`/asset-types/${id}`)
  },
  createAssetType(assettypeData) {
    return api.post('/asset-types', assettypeData)
  },
  updateAssetType(id, assettypeData) {
    return api.put(`/asset-types/${id}`, assettypeData)
  },
  deleteAssetType(id) {
    return api.delete(`/asset-types/${id}`)
  },
  getUsers() {
    return api.get('/users')
  },
  getRoles() {
    return api.get('/roles')
  },
  getRole(id) {
    return api.get(`/roles/${id}`)
  },
  createRole(roleData) {
    return api.post('/roles', roleData)
  },
  updateRole(id, roleData) {
    return api.put(`/roles/${id}`, roleData)
  },
  deleteRole(id) {
    return api.delete(`/roles/${id}`)
  },
  testUserPermissions() {
    return api.get('/roles/test/permissions')
  },
  getUser(id) {
    return api.get(`/users/${id}`)
  },
  resetUserPassword(id) {
    return api.post(`/users/${id}/reset-password`)
  },
  createUser(userData) {
    return api.post('/users', userData, {
      params: {
        tenant_id: localStorage.getItem('tenant_id')
      }
    })
  },
  updateUser(id, userData) {
    return api.put(`/users/${id}`, userData)
  },
  updateUserRole(id, role_id) {
    return api.patch(`/users/${id}/role`, { role_id })
  },
  deleteUser(id) {
    return api.delete(`/users/${id}`)
  },
  logout() {
    return api.post('/logout')
  },
  refresh() {
    return api.post('/refresh')
  },
  getAssetStatuses() {
    return api.get('/asset-statuses')
  },
  createAssetStatus(data) {
    return api.post('/asset-statuses', data)
  },
  updateAssetStatus(id, data) {
    return api.put(`/asset-statuses/${id}`, data)
  },
  deleteAssetStatus(id) {
    return api.delete(`/asset-statuses/${id}`)
  },
  getSiteContacts(siteId) {
    return api.get(`/sites/${siteId}/contacts`)
  },
  updateSiteContacts(siteId, contactIds) {
    return api.put(`/sites/${siteId}/contacts`, contactIds, {
      headers: { 'Content-Type': 'application/json' }
    })
  },
  deleteSiteContact(siteId, contactId) {
    return api.delete(`/sites/${siteId}/contacts/${contactId}`)
  },
  getContacts() {
    return api.get('/contacts')
  },
  createContact(contactData) {
    return api.post('/contacts', contactData)
  },
  getSupplierContacts(supplierId) {
    return api.get(`/suppliers/${supplierId}/contacts`)
  },
  updateSupplierContacts(supplierId, contactIds) {
    return api.put(`/suppliers/${supplierId}/contacts`, contactIds, {
      headers: { 'Content-Type': 'application/json' }
    })
  },
  deleteSupplierContact(supplierId, contactId) {
    return api.delete(`/suppliers/${supplierId}/contacts/${contactId}`)
  },
  getAssetContacts(assetId) {
    return api.get(`/assets/${assetId}/contacts`)
  },
  getAssetOwners(assetId) {
    return api.get(`/assets/${assetId}/contacts/owners`)
  },
  getAssetPointsOfContact(assetId) {
    return api.get(`/assets/${assetId}/contacts/points-of-contact`)
  },
  addAssetContactWithRole(assetId, contactData) {
    return api.post(`/assets/${assetId}/contacts`, contactData)
  },
  updateAssetContacts(assetId, contactsData) {
    return api.put(`/assets/${assetId}/contacts`, contactsData, {
      headers: { 'Content-Type': 'application/json' }
    })
  },
  deleteAssetContact(assetId, contactId) {
    return api.delete(`/assets/${assetId}/contacts/${contactId}`)
  },
  getTenantReviewSettings() {
    return api.get('/assets/review/settings')
  },
  updateTenantReviewSettings(data) {
    return api.patch('/assets/review/settings', data)
  },
  // Asset Reviews
  getAssetReviewStatus(assetId) {
    return api.get(`/assets/${assetId}/review-status`)
  },
  markAssetAsReviewed(assetId, reviewData) {
    return api.post(`/assets/${assetId}/review`, reviewData)
  },
  skipAssetReview(assetId, skipData) {
    return api.post(`/assets/${assetId}/review/skip`, skipData)
  },
  getDueAssets(params = {}) {
    return api.get('/assets/review/due', { params })
  },
  getOverdueAssets(params = {}) {
    return api.get('/assets/review/overdue', { params })
  },
  getUpcomingAssets(params = {}) {
    return api.get('/assets/review/upcoming', { params })
  },
  bulkReviewAssets(bulkData) {
    return api.post('/assets/review/bulk', bulkData)
  },
  recalculateReviewDates() {
    return api.post('/assets/review/recalculate-all')
  },
  // Notifications
  getNotificationTemplates() {
    return api.get('/notifications/templates')
  },
  getNotificationTemplate(templateCode) {
    return api.get(`/notifications/templates/${templateCode}`)
  },
  createTemplateOverride(templateCode) {
    return api.post(`/notifications/templates/${templateCode}/override`)
  },
  deleteTemplateOverride(templateCode) {
    return api.delete(`/notifications/templates/${templateCode}/override`)
  },
  updateNotificationTemplate(templateCode, data) {
    return api.put(`/notifications/templates/${templateCode}`, data)
  },
  getNotificationPreferences() {
    return api.get('/notifications/preferences')
  },
  createNotificationPreference(preferenceData) {
    return api.post('/notifications/preferences', preferenceData)
  },
  updateNotificationPreference(preferenceId, preferenceData) {
    return api.put(`/notifications/preferences/${preferenceId}`, preferenceData)
  },
  deleteNotificationPreference(preferenceId) {
    return api.delete(`/notifications/preferences/${preferenceId}`)
  },
  getNotificationQueue(params = {}) {
    return api.get('/notifications/queue', { params })
  },
  retryNotification(queueId) {
    return api.post(`/notifications/queue/${queueId}/retry`)
  },
  cancelNotification(queueId) {
    return api.delete(`/notifications/queue/${queueId}`)
  },
  getNotificationLogs(params = {}) {
    return api.get('/notifications/logs', { params })
  },
  testNotification(testData) {
    return api.post('/notifications/test', testData)
  },
  processNotificationQueue(batchSize = 50) {
    return api.post('/notifications/queue/process', null, { params: { batch_size: batchSize } })
  },
  // ISA/IEC 62443 - Security Zones
  getSecurityZones(params = {}) {
    return api.get('/security-zones', { params })
  },
  getSecurityZone(id) {
    return api.get(`/security-zones/${id}`)
  },
  createSecurityZone(zoneData) {
    return api.post('/security-zones', zoneData)
  },
  updateSecurityZone(id, zoneData) {
    return api.put(`/security-zones/${id}`, zoneData)
  },
  deleteSecurityZone(id) {
    return api.delete(`/security-zones/${id}`)
  },
  getZoneAssets(zoneId) {
    return api.get(`/security-zones/${zoneId}/assets`)
  },
  getZoneMemberships(zoneId, params = {}) {
    return api.get(`/security-zones/${zoneId}/memberships`, { params })
  },
  getAssetZoneMemberships(assetId) {
    return api.get(`/assets/${assetId}/zone-memberships`)
  },
  getAssetCompliance(assetId) {
    return api.get(`/compliance/asset/${assetId}`)
  },
  createZoneMembership(zoneId, membershipData) {
    return api.post(`/security-zones/${zoneId}/memberships`, membershipData)
  },
  updateZoneMembership(zoneId, membershipId, membershipData) {
    return api.put(`/security-zones/${zoneId}/memberships/${membershipId}`, membershipData)
  },
  deleteZoneMembership(zoneId, membershipId) {
    return api.delete(`/security-zones/${zoneId}/memberships/${membershipId}`)
  },
  getZoneCompliance(zoneId) {
    return api.get(`/compliance/zone/${zoneId}`)
  },
  getZoneFoundationRequirements(zoneId) {
    return api.get(`/compliance/zone/${zoneId}/foundation-requirements`)
  },
  getZoneSecurityRequirementsByFR(zoneId, frId) {
    return api.get(`/compliance/zone/${zoneId}/security-requirements/${frId}`)
  },
  // New capability-based assessment endpoints
  getSRAssessmentAssist(zoneId, srId) {
    return api.get(`/compliance/zone/${zoneId}/sr/${srId}/assessment-assist`)
  },
  createOrUpdateSRAssessment(zoneId, srId, assessmentData) {
    return api.post(`/compliance/zone/${zoneId}/sr/${srId}/assessment`, assessmentData)
  },
  exportZoneAudit(zoneId, format = 'json') {
    return api.get(`/compliance/zone/${zoneId}/audit-export`, {
      params: { format },
      responseType: format === 'csv' ? 'blob' : 'json',
    })
  },
  getAssetSecurityRequirements(assetId) {
    return api.get(`/compliance/asset/${assetId}/security-requirements`)
  },
  createOrUpdateAssetSRAssessment(assetId, srId, assessmentData) {
    return api.post(`/compliance/asset/${assetId}/sr/${srId}/assessment`, assessmentData)
  },
  recalculateAssetIec62443(assetId) {
    return api.post(`/compliance/asset/${assetId}/recalculate`)
  },
  getConduitSecurityRequirements(conduitId) {
    return api.get(`/compliance/conduit/${conduitId}/security-requirements`)
  },
  getSrRequirementEnhancements(srId) {
    return api.get(`/compliance/sr/${srId}/requirement-enhancements`)
  },
  createOrUpdateConduitSRAssessment(conduitId, srId, assessmentData) {
    return api.post(`/compliance/conduit/${conduitId}/sr/${srId}/assessment`, assessmentData)
  },
  getSRInvolvedAssets(zoneId, srId) {
    return api.get(`/compliance/zone/${zoneId}/sr/${srId}/assets`)
  },
  getSRInvolvedConduits(zoneId, srId) {
    return api.get(`/compliance/zone/${zoneId}/sr/${srId}/conduits`)
  },
  getZoneRisk(zoneId) {
    return api.get(`/security-zones/${zoneId}/risk`)
  },
  recalculateZoneSLA(zoneId) {
    return api.post(`/security-zones/${zoneId}/recalculate-sla`)
  },
  calculateZoneSecurityLevel(zoneId) {
    return api.post(`/security-zones/${zoneId}/calculate-sl`)
  },
  // ISA/IEC 62443 - Conduits
  getConduits(params = {}) {
    return api.get('/conduits', { params })
  },
  getConduit(id) {
    return api.get(`/conduits/${id}`)
  },
  createConduit(conduitData) {
    return api.post('/conduits', conduitData)
  },
  updateConduit(id, conduitData) {
    return api.put(`/conduits/${id}`, conduitData)
  },
  deleteConduit(id) {
    return api.delete(`/conduits/${id}`)
  },
  recalculateConduitSLA(conduitId) {
    return api.post(`/conduits/${conduitId}/calculate-sl`)
  },
  // ISA/IEC 62443 - Compliance
  getSecurityRequirements(params = {}) {
    return api.get('/compliance/requirements', { params })
  },
  getGapAnalysis(zoneId = null) {
    const url = zoneId 
      ? `/compliance/gap-analysis?zone_id=${zoneId}`
      : '/compliance/gap-analysis'
    return api.get(url)
  },
  // Asset Dependencies
  getAssetDependencies(params = {}) {
    return api.get('/asset-dependencies', { params })
  },
  getAssetDependency(id) {
    return api.get(`/asset-dependencies/${id}`)
  },
  createAssetDependency(dependencyData) {
    return api.post('/asset-dependencies', dependencyData)
  },
  updateAssetDependency(id, dependencyData) {
    return api.put(`/asset-dependencies/${id}`, dependencyData)
  },
  deleteAssetDependency(id) {
    return api.delete(`/asset-dependencies/${id}`)
  },
  getDependenciesForAsset(assetId) {
    return api.get(`/asset-dependencies/assets/${assetId}/dependencies`)
  },
  getDependentsOfAsset(assetId) {
    return api.get(`/asset-dependencies/assets/${assetId}/dependents`)
  },
  getRiskPropagation(assetId, maxDepth = 5) {
    return api.get(`/asset-dependencies/assets/${assetId}/risk-propagation`, {
      params: { max_depth: maxDepth }
    })
  },
  getRiskFromDependencies(assetId) {
    return api.get(`/asset-dependencies/assets/${assetId}/risk-from-dependencies`)
  },
  getImpactAnalysis(assetId) {
    return api.get(`/asset-dependencies/asset/${assetId}/impact-analysis`)
  },
  getDependencyChain(assetId) {
    return api.get(`/asset-dependencies/asset/${assetId}/chain`)
  },
  // Vulnerability Intelligence
  getVulnerabilities(params = {}) {
    return api.get('/vulnerabilities', { params })
  },
  getVulnerability(id) {
    return api.get(`/vulnerabilities/${id}`)
  },
  getVulnerabilityAffectedAssets(vulnerabilityId, params = {}) {
    return api.get(`/vulnerabilities/${vulnerabilityId}/assets`, { params })
  },
  getAssetVulnerabilities(assetId) {
    return api.get(`/vulnerabilities/assets/${assetId}`)
  },
  updateAssetVulnerability(assetId, assetVulnId, updateData) {
    return api.put(`/vulnerabilities/assets/${assetId}/vulnerabilities/${assetVulnId}`, updateData)
  },
  matchVulnerabilitiesToAsset(assetId) {
    return api.post(`/vulnerabilities/assets/${assetId}/match-vulnerabilities`)
  },
  matchAssetsToVulnerability(vulnerabilityId, params = {}) {
    return api.post(`/vulnerabilities/${vulnerabilityId}/match-assets`, null, { params })
  },
  getVulnerabilityStats() {
    return api.get('/vulnerabilities/stats')
  },
  getVulnerabilityFeedSources() {
    return api.get('/vulnerabilities/feeds')
  },
  createVulnerabilityFeedSource(feedData) {
    return api.post('/vulnerabilities/feeds', feedData)
  },
  updateVulnerabilityFeedSource(id, feedData) {
    return api.put(`/vulnerabilities/feeds/${id}`, feedData)
  },
  deleteVulnerabilityFeedSource(id) {
    return api.delete(`/vulnerabilities/feeds/${id}`)
  },
  syncVulnerabilityFeed(feedSourceId) {
    return api.post(`/vulnerabilities/feeds/${feedSourceId}/sync`)
  },
  uploadLocalFeed(file, feedData) {
    const formData = new FormData()
    formData.append('file', file)
    Object.keys(feedData).forEach(key => {
      formData.append(key, feedData[key])
    })
    return api.post('/vulnerabilities/feeds/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  // Asset Capabilities
  getAssetCapabilities(assetId) {
    return api.get(`/assets/${assetId}/capabilities`)
  },
  createAssetCapability(assetId, data) {
    return api.post(`/assets/${assetId}/capabilities`, data)
  },
  updateAssetCapability(assetId, capabilityId, data) {
    return api.put(`/assets/${assetId}/capabilities/${capabilityId}`, data)
  },
  deleteAssetCapability(assetId, capabilityId) {
    return api.delete(`/assets/${assetId}/capabilities/${capabilityId}`)
  },
  bulkUpdateAssetCapabilities(assetId, data) {
    return api.post(`/assets/${assetId}/capabilities/bulk`, data)
  },

  // Evidence API
  getEvidences(params = {}) {
    return api.get('/evidence', { params })
  },
  createEvidence(data) {
    return api.post('/evidence', data)
  },
  updateEvidence(evidenceId, data) {
    return api.put(`/evidence/${evidenceId}`, data)
  },
  deleteEvidence(evidenceId) {
    return api.delete(`/evidence/${evidenceId}`)
  },
  // Enterprise Auth (SSO)
  checkSSOEnabled(tenantId = null) {
    const params = tenantId ? { tenant_id: tenantId } : {}
    return api.get('/auth/sso/enabled', { params })
  },
  getSSOConfig() {
    return api.get('/auth/sso/config')
  },
  createSSOConfig(configData) {
    return api.post('/auth/sso/config', configData)
  },
  updateSSOConfig(configData) {
    return api.put('/auth/sso/config', configData)
  },
  deleteSSOConfig() {
    return api.delete('/auth/sso/config')
  },
  startSSOConnect() {
    return api.post('/auth/sso/connect/start')
  },
  testSSOConnection() {
    return api.post('/auth/sso/test')
  },
  getUserAuthMethods(userId) {
    return api.get(`/auth/sso/users/${userId}/auth-methods`)
  },
  // Azure AD User Import
  listAzureADUsers(params = {}) {
    return api.get('/auth/sso/azure-ad/users', { params })
  },
  importAzureADUsers(importData) {
    return api.post('/auth/sso/azure-ad/import', importData)
  },
  getContact(id) {
    return api.get(`/contacts/${id}`)
  },
  getAuditLogs(params = {}) {
    return api.get('/audit-logs', { params })
  },
  exportAuditLogs(params = {}) {
    return api.get('/audit-logs/export', { params, responseType: 'blob' })
  },
  previewAssetImportXlsx(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/assets/import/xlsx/preview', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  confirmAssetImportXlsx(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/assets/import/xlsx/confirm', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  bulkUpdateAssets(ids, fields) {
    return api.post('/assets/bulk-update', { ids, fields })
  },
  bulkSoftDeleteAssets(ids) {
    return api.post('/assets/bulk-soft-delete', { ids })
  },
  getLocationsTrash() {
    return api.get('/locations/trash')
  },
  deleteLocation(id) {
    return api.delete(`/locations/${id}`)
  },
  restoreLocation(id) {
    return api.patch(`/locations/${id}/restore`)
  },
  hardDeleteLocation(id) {
    return api.delete(`/locations/${id}/hard`)
  },
  getContactsTrash() {
    return api.get('/contacts/trash')
  },
  restoreContact(id) {
    return api.patch(`/contacts/${id}/restore`)
  },
  hardDeleteContact(id) {
    return api.delete(`/contacts/${id}/hard`)
  },
  deleteContact(id) {
    return api.delete(`/contacts/${id}`)
  },
  updateContact(id, data) {
    return api.put(`/contacts/${id}`, data)
  },
  getAssetsTrash() {
    return api.get('/assets/trash')
  },
  emptyAssetsTrash() {
    return api.delete('/assets/trash/empty')
  },
  restoreAsset(id) {
    return api.patch(`/assets/${id}/restore`)
  },
  hardDeleteAsset(id) {
    return api.delete(`/assets/${id}/hard`)
  },
  getSuppliersTrash() {
    return api.get('/suppliers/trash')
  },
  restoreSupplier(id) {
    return api.patch(`/suppliers/${id}/restore`)
  },
  hardDeleteSupplier(id) {
    return api.delete(`/suppliers/${id}/hard`)
  },
  getSMTPConfig() {
    return api.get('/smtp-config')
  },
  setSMTPConfig(data) {
    return api.post('/smtp-config', data)
  },
  testSMTPConfig(configData) {
    return api.post('/smtp-config/test', configData)
  },

  getSyslogConfig() {
    return api.get('/syslog-config')
  },
  getSyslogConfigExists() {
    return api.get('/syslog-config/exists')
  },
  setSyslogConfig(data) {
    return api.post('/syslog-config', data)
  },
  testSyslogConfig(configData) {
    return api.post('/syslog-config/test', configData)
  },

  getTenantFeatures() {
    return api.get('/tenant-features')
  },
  updateTenantFeatures(data) {
    return api.patch('/tenant-features', data)
  },

  // Risk Scoring APIs
  calculateAssetRisk(assetId) {
    return api.post(`/assets/${assetId}/calculate-risk`)
  },
  
  getRiskOverview() {
    return api.get('/assets/risk-overview')
  },
  
  recalculateAllRiskScores() {
    return api.post('/assets/recalculate-all-risk-scores')
  },
  
  // Global Search API
  globalSearch(query, limit = 5) {
    return api.get('/search/global', { params: { q: query, limit } })
  },

  // Print System APIs
  getPrintTemplates() {
    return api.get('/print/templates')
  },
  
  getPrintTemplate(id) {
    return api.get(`/print/templates/${id}`)
  },
  
  createPrintTemplate(templateData) {
    return api.post('/print/templates', templateData)
  },
  
  updatePrintTemplate(id, templateData) {
    return api.put(`/print/templates/${id}`, templateData)
  },
  
  deletePrintTemplate(id) {
    return api.delete(`/print/templates/${id}`)
  },
  
  generatePrint(assetId, templateId, options = {}) {
    return api.post(`/print/generate`, {
      asset_id: assetId,
      template_id: templateId,
      options
    })
  },
  
  downloadPrint(printId) {
    return api.get(`/print/download/${printId}`, { responseType: 'blob' })
  },
  
  getPrintHistory(assetId = null) {
    const params = assetId ? { asset_id: assetId } : {}
    return api.get('/print/history', { params })
  },
  
  generateQRCode(text) {
    return api.post('/print/qr-code', { text }, { responseType: 'blob' })
  },
  
  getAssetForPrint(assetId) {
    return api.get(`/assets/${assetId}/print-data`)
  },
  
  initDefaultTemplates() {
    return api.post('/print/templates/init-defaults')
  },
  exportSuppliersCsv() {
    return api.get('/suppliers/export', { responseType: 'blob' });
  },
  previewSupplierImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/suppliers/import/xlsx/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  confirmSupplierImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/suppliers/import/xlsx/confirm', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportContactsCsv() {
    return api.get('/contacts/export', { responseType: 'blob' });
  },
  previewContactImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/contacts/import/xlsx/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  confirmContactImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/contacts/import/xlsx/confirm', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportManufacturersCsv() {
    return api.get('/manufacturers/export', { responseType: 'blob' });
  },
  exportUsersCsv() {
    return api.get('/users/export', { responseType: 'blob' });
  },
  previewUserImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/users/import/xlsx/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  confirmUserImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/users/import/xlsx/confirm', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportSitesCsv() {
    return api.get('/sites/export', { responseType: 'blob' });
  },
  previewSiteImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/sites/import/xlsx/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  confirmSiteImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/sites/import/xlsx/confirm', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportLocationsCsv() {
    return api.get('/locations/export', { responseType: 'blob' });
  },
  previewLocationImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/locations/import/xlsx/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  confirmLocationImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/locations/import/xlsx/confirm', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  previewManufacturerImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/manufacturers/import/xlsx/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  confirmManufacturerImportXlsx(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/manufacturers/import/xlsx/confirm', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  bulkUpdateManufacturers(ids, fields) {
    return api.post('/manufacturers/bulk-update', { ids, fields });
  },
  bulkUpdateLocations(ids, fields) {
    return api.post('/locations/bulk-update', { ids, fields });
  },
  createAssetInterfacesBulk(interfaces) {
    return api.post('/asset-interfaces/bulk', interfaces)
  },
  previewPcapImport(formData) {
    return api.post('/pcap/preview', formData, {
      headers: { "Content-Type": "multipart/form-data" }
    })
  },
  getSupportedProtocols() {
    return api.get('/pcap/protocols')
  },
  getInterfaceProtocols() {
    return api.get('/pcap/interface-protocols')
  },
  getAssetSuppliers(assetId) {
    return api.get(`/assets/${assetId}/suppliers`)
  },
  updateAssetSuppliers(assetId, supplierIds) {
    return api.put(`/assets/${assetId}/suppliers`, supplierIds)
  },
  getSuppliers() {
    return api.get('/suppliers')
  },
  changePassword(passwordData) {
    return api.post('/users/reset-password', passwordData)
  },
  updateNotificationsPreference(notificationsEnabled) {
    return api.patch('/users/me/notifications', { notifications_enabled: notificationsEnabled })
  },

  // Printed Kit API
  generatePrintedKit(options = {}) {
    return api.post('/print/kit', options)
  },

  downloadPrintedKit(filename) {
    return api.get(`/print/kit/download/${filename}`, {
      responseType: 'blob'
    })
  },

  // Network Probes (Industrace PRO)
  getNetworkProbes(params = {}) {
    return api.get('/network-probes', { params })
  },
  createNetworkProbe(probeData) {
    return api.post('/network-probes', probeData)
  },
  updateNetworkProbe(probeId, updateData) {
    return api.put(`/network-probes/${probeId}`, updateData)
  },
  deauthorizeNetworkProbe(probeId) {
    return api.post(`/network-probes/${probeId}/deauthorize`)
  },
  deleteNetworkProbe(probeId) {
    return api.delete(`/network-probes/${probeId}`)
  },
  getNetworkProbeStatus(probeId) {
    return api.get(`/network-probes/${probeId}/status`)
  },
  getNetworkProbeConfiguration(probeId, apiKey) {
    return api.get(`/network-probes/configuration/${probeId}`, {
      headers: { 'X-API-Key': apiKey }
    })
  },
  getNetworkProbesOverview() {
    // Aggregazioni leggere lato backend (total/active/error + health percentage)
    return api.get('/network-probes/overview')
  },
  getDiscoveredDevices(params = {}) {
    return api.get('/discovered-devices', { params })
  },
  updateDiscoveredDevice(deviceId, updateData) {
    return api.put(`/discovered-devices/${deviceId}`, updateData)
  },
  onboardDiscoveredDevice(deviceId, payload = {}) {
    return api.post(`/discovered-devices/${deviceId}/onboard`, payload)
  },
  
  // Generic HTTP methods for direct API calls
  get(url, config = {}) {
    return api.get(url, config)
  },
  post(url, data = null, config = {}) {
    return api.post(url, data, config)
  },
  put(url, data = null, config = {}) {
    return api.put(url, data, config)
  },
  patch(url, data = null, config = {}) {
    return api.patch(url, data, config)
  },
  delete(url, config = {}) {
    return api.delete(url, config)
  }
}
