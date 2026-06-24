<template>
  <PrintLayout 
    :options="printOptions" 
    :page-info="{ current: 1, total: 1 }"
    :qr-code="qrCodeUrl"
  >
    <div class="asset-card">
      <!-- Main section -->
      <div class="asset-main">
        <div class="asset-header">
          <div class="asset-title">
            <h2 class="asset-name">{{ asset.name }}</h2>
            <div class="asset-tag">{{ asset.tag }}</div>
          </div>
          <div class="asset-status">
            <div class="status-badge" :class="statusClass">
              {{ asset.status?.name || 'N/A' }}
            </div>
          </div>
        </div>

        <!-- Photo and main information -->
        <div class="asset-content">
          <div class="asset-photo" v-if="options.includePhoto && asset.photos?.length">
            <img :src="asset.photos[0].url" :alt="asset.name" class="photo" />
          </div>
          
          <div class="asset-info">
            <!-- Advanced field configuration -->
            <div v-if="options.fields && options.fields.length > 0" class="custom-fields-grid">
              <div 
                v-for="field in visibleFields" 
                :key="field.name"
                class="info-item"
                :style="{ width: field.width || 'auto' }"
              >
                <label>{{ field.label || getFieldLabel(field.name) }}:</label>
                <span>{{ getFieldValue(field.name) }}</span>
              </div>
            </div>
            
            <!-- Fallback to standard fields if advanced configuration is not set -->
            <div v-else class="info-grid">
              <div class="info-item">
                <label>Serial Number:</label>
                <span>{{ asset.serial_number || 'N/A' }}</span>
              </div>
              <div class="info-item">
                <label>Model:</label>
                <span>{{ asset.model || 'N/A' }}</span>
              </div>
              <div class="info-item">
                <label>Manufacturer:</label>
                <span>{{ asset.manufacturer?.name || 'N/A' }}</span>
              </div>
              <div class="info-item">
                <label>Type:</label>
                <span>{{ asset.asset_type?.name || 'N/A' }}</span>
              </div>
              <div class="info-item">
                <label>Site:</label>
                <span>{{ asset.site?.name || 'N/A' }}</span>
              </div>
              <div class="info-item">
                <label>Location:</label>
                <span>{{ asset.location?.name || 'N/A' }}</span>
              </div>
              <div class="info-item">
                <label>Firmware:</label>
                <span>{{ asset.firmware_version || 'N/A' }}</span>
              </div>
              <div class="info-item" v-if="asset.ip_address">
                <label>IP Address:</label>
                <span>{{ asset.ip_address }}</span>
              </div>
              <div class="info-item" v-if="asset.installation_date">
                <label>Installation Date:</label>
                <span>{{ formatDate(asset.installation_date) }}</span>
              </div>
              <div class="info-item" v-if="asset.business_criticality">
                <label>Business Criticality:</label>
                <span>{{ asset.business_criticality }}</span>
              </div>
              <div class="info-item" v-if="asset.security_zone">
                <label>Security Zone:</label>
                <span>{{ asset.security_zone?.name || 'N/A' }}</span>
              </div>
              <div class="info-item" v-if="asset.area">
                <label>Area:</label>
                <span>{{ asset.area?.name || asset.area?.code || 'N/A' }}</span>
              </div>
              <div class="info-item" v-if="asset.remote_access !== undefined">
                <label>Remote Access:</label>
                <span>{{ asset.remote_access ? 'Yes' : 'No' }}</span>
              </div>
              <div class="info-item" v-if="asset.remote_access_type && asset.remote_access_type !== 'none'">
                <label>Remote Access Type:</label>
                <span>{{ formatRemoteAccessType(asset.remote_access_type) }}</span>
              </div>
              <div class="info-item" v-if="asset.protocols && asset.protocols.length > 0">
                <label>Protocols:</label>
                <span>{{ asset.protocols.join(', ') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Custom Fields -->
        <div v-if="options.includeCustomFields && asset.custom_fields" class="custom-fields-section">
          <h3 class="section-title">Custom Fields</h3>
          <div class="custom-fields-grid">
            <div 
              v-for="(value, key) in asset.custom_fields" 
              :key="key" 
              class="custom-field-item"
            >
              <label>{{ key }}:</label>
              <span>{{ value }}</span>
            </div>
          </div>
        </div>

        <!-- Connessioni -->
        <div v-if="options.includeConnections && asset.connections?.length" class="connections-section">
          <h3 class="section-title">{{ t('assets.tabs.connections') || 'Connections' }}</h3>
          <div class="connections-list-compact">
            <div 
              v-for="connection in limitedConnections" 
              :key="connection.id || connection.connection_type" 
              class="connection-item-compact"
            >
              <span class="connection-type-compact">{{ connection.connection_type }}:</span>
              <span class="connection-target-compact">{{ connection.target_asset?.name || connection.target_ip || 'N/A' }}</span>
            </div>
          </div>
        </div>

        <!-- Note/Descrizione -->
        <div v-if="asset.description" class="notes-section">
          <h3 class="section-title">{{ t('assets.strings.notes') || 'Notes' }}</h3>
          <p class="notes-text">{{ truncateText(asset.description, 200) }}</p>
        </div>

        <!-- Contatti -->
        <div v-if="hasContacts" class="contacts-section">
          <h3 class="section-title">{{ t('assets.contacts.title') || 'Contacts' }}</h3>
          <div v-if="owners.length > 0" class="contact-group">
            <h4 class="contact-group-title">{{ t('assets.contacts.owners') || 'Owners' }}</h4>
            <div class="contacts-list">
              <div v-for="contact in owners" :key="contact.id || contact.email" class="contact-item">
                <div class="contact-name">{{ getContactName(contact) }}</div>
                <div class="contact-details">
                  <span v-if="contact.email">{{ contact.email }}</span>
                  <span v-if="contact.phone1">{{ contact.phone1 }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="pointsOfContact.length > 0" class="contact-group">
            <h4 class="contact-group-title">{{ t('assets.contacts.pointsOfContact') || 'Points of Contact' }}</h4>
            <div class="contacts-list">
              <div v-for="contact in pointsOfContact" :key="contact.id || contact.email" class="contact-item">
                <div class="contact-name">{{ getContactName(contact) }}</div>
                <div class="contact-details">
                  <span v-if="contact.email">{{ contact.email }}</span>
                  <span v-if="contact.phone1">{{ contact.phone1 }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Fornitori -->
        <div v-if="asset.suppliers && asset.suppliers.length > 0" class="suppliers-section">
          <h3 class="section-title">{{ t('assets.strings.suppliers') || 'Suppliers' }}</h3>
          <div class="suppliers-list">
            <div v-for="supplier in asset.suppliers" :key="supplier.id || supplier.name" class="supplier-item">
              <div class="supplier-name">{{ supplier.name }}</div>
              <div class="supplier-details">
                <span v-if="supplier.email">{{ supplier.email }}</span>
                <span v-if="supplier.phone">{{ supplier.phone }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- QR Code per accesso rapido -->
        <div v-if="options.includeQR" class="qr-section">
          <div class="qr-info">
            <p class="qr-text">Scan to access the full asset card</p>
            <div class="qr-code">
              <img :src="qrCodeUrl" alt="QR Code" class="qr-image" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </PrintLayout>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import i18n from '../../locales/loader-final.js'
import PrintLayout from './PrintLayout.vue'
import { formatRiskScore, getPrintRiskClass } from '../../composables/useRiskLabels'

const { t } = useI18n()

const props = defineProps({
  asset: {
    type: Object,
    required: true
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

const printOptions = computed(() => ({
  orientation: 'portrait',
  paperSize: 'a4',
  margin: 'normal',
  includeHeader: true,
  includeFooter: true,
  headerText: `Industrace - Scheda Asset: ${props.asset.name}`,
  footerText: 'Generato il {{date}} - Asset ID: {{assetId}}'
}))

const statusClass = computed(() => {
  const status = props.asset.status?.name?.toLowerCase() || ''
  if (status.includes('attivo') || status.includes('active')) return 'status-active'
  if (status.includes('inattivo') || status.includes('inactive')) return 'status-inactive'
  if (status.includes('manutenzione') || status.includes('maintenance')) return 'status-maintenance'
  return 'status-default'
})

const riskScoreClass = computed(() => getPrintRiskClass(props.asset.risk_score))

const qrCodeUrl = computed(() => {
  // Genera QR code con URL per accedere alla scheda
  const baseUrl = window.location.origin
  const assetUrl = `${baseUrl}/assets/${props.asset.id}`
  
  // Per ora restituiamo un placeholder SVG
  // In futuro potremmo implementare la generazione QR lato frontend
  return `data:image/svg+xml;base64,${btoa(`
    <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
      <rect width="100" height="100" fill="white" stroke="black" stroke-width="1"/>
      <text x="50" y="45" text-anchor="middle" font-size="8" fill="black">QR Code</text>
      <text x="50" y="55" text-anchor="middle" font-size="6" fill="gray">${assetUrl}</text>
    </svg>
  `)}`
})

// Computed per i campi visibili
const visibleFields = computed(() => {
  if (!props.options.fields) return []
  return props.options.fields.filter(field => field.visible !== false)
})

// Funzione per ottenere l'etichetta del campo
const getFieldLabel = (fieldName) => {
  const fieldLabels = {
    'asset_id': 'ID',
    'asset_name': 'Nome',
    'asset_type': 'Tipo',
    'asset_status': 'Stato',
    'asset_location': 'Posizione',
    'asset_site': 'Sito',
    'asset_manufacturer': 'Produttore',
    'asset_model': 'Modello',
    'asset_serial': 'Numero di Serie',
    'asset_ip': 'Indirizzo IP',
    'asset_firmware': 'Firmware',
    'asset_description': 'Descrizione',
    'asset_tag': 'Tag',
    'asset_purchase_date': 'Data Acquisto',
    'asset_warranty': 'Garanzia',
    'asset_value': 'Valore',
    'asset_notes': 'Note',
    'asset_risk_score': 'Risk Score',
    'asset_business_criticality': 'Criticità Business',
    'asset_installation_date': 'Data Installazione',
    'asset_last_maintenance': 'Ultima Manutenzione',
    'asset_security_zone': 'Security Zone',
    'asset_area': 'Area',
    'asset_remote_access': 'Accesso Remoto',
    'asset_remote_access_type': 'Tipo Accesso Remoto',
    'asset_protocols': 'Protocolli'
  }
  return fieldLabels[fieldName] || fieldName
}

// Funzione per ottenere la locale delle date
const getDateLocale = () => {
  const locale = i18n.global.locale.value;
  return locale === 'it' ? 'it-IT' : 'en-US';
}

// Funzione per ottenere il valore del campo
const getFieldValue = (fieldName) => {
  const asset = props.asset
  
  switch (fieldName) {
    case 'asset_id':
      return asset.id || 'N/A'
    case 'asset_name':
      return asset.name || 'N/A'
    case 'asset_type':
      return asset.asset_type?.name || 'N/A'
    case 'asset_status':
      return asset.status?.name || 'N/A'
    case 'asset_location':
      return asset.location?.name || 'N/A'
    case 'asset_site':
      return asset.site?.name || 'N/A'
    case 'asset_manufacturer':
      return asset.manufacturer?.name || 'N/A'
    case 'asset_model':
      return asset.model || 'N/A'
    case 'asset_serial':
      return asset.serial_number || 'N/A'
    case 'asset_ip':
      return asset.ip_address || 'N/A'
    case 'asset_firmware':
      return asset.firmware_version || 'N/A'
    case 'asset_description':
      return asset.description || 'N/A'
    case 'asset_tag':
      return asset.tag || 'N/A'
    case 'asset_purchase_date':
      return asset.purchase_date ? new Date(asset.purchase_date).toLocaleDateString(getDateLocale()) : 'N/A'
    case 'asset_warranty':
      return asset.warranty_expiry ? new Date(asset.warranty_expiry).toLocaleDateString(getDateLocale()) : 'N/A'
    case 'asset_value':
      return asset.value ? `€${asset.value}` : 'N/A'
    case 'asset_notes':
      return asset.notes || 'N/A'
    case 'asset_risk_score':
      return formatRiskScore(asset.risk_score, { suffix: true })
    case 'asset_business_criticality':
      return asset.business_criticality || 'N/A'
    case 'asset_installation_date':
      return asset.installation_date ? new Date(asset.installation_date).toLocaleDateString(getDateLocale()) : 'N/A'
    case 'asset_last_maintenance':
      return asset.last_maintenance_date ? new Date(asset.last_maintenance_date).toLocaleDateString(getDateLocale()) : 'N/A'
    case 'asset_security_zone':
      return asset.security_zone?.name || 'N/A'
    case 'asset_area':
      return asset.area?.name || asset.area?.code || 'N/A'
    case 'asset_remote_access':
      return asset.remote_access ? 'Yes' : 'No'
    case 'asset_remote_access_type':
      return formatRemoteAccessType(asset.remote_access_type) || 'N/A'
    case 'asset_protocols':
      return asset.protocols && asset.protocols.length > 0 ? asset.protocols.join(', ') : 'N/A'
    default:
      return 'N/A'
  }
}

// Funzioni helper
const formatDate = (date) => {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString(getDateLocale())
}

const formatRemoteAccessType = (type) => {
  if (!type || type === 'none') return 'N/A'
  const types = {
    'attended': 'Attended',
    'unattended': 'Unattended',
    'none': 'None'
  }
  return types[type] || type
}

const truncateText = (text, maxLength = 200) => {
  if (!text) return 'N/A'
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// Computed per contatti
const owners = computed(() => {
  if (!props.asset.contacts) return []
  return props.asset.contacts.filter(c => c.role === 'owner')
})

const pointsOfContact = computed(() => {
  if (!props.asset.contacts) return []
  return props.asset.contacts.filter(c => c.role === 'point_of_contact')
})

const hasContacts = computed(() => {
  return owners.value.length > 0 || pointsOfContact.value.length > 0
})

const getContactName = (contact) => {
  if (!contact) return 'N/A'
  const firstName = contact.first_name || ''
  const lastName = contact.last_name || ''
  const fullName = `${firstName} ${lastName}`.trim()
  return fullName || contact.email || 'N/A'
}

// Computed per connessioni limitate
const limitedConnections = computed(() => {
  if (!props.asset.connections) return []
  return props.asset.connections.slice(0, 6)
})
</script>

<style scoped>
.asset-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.asset-main {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 2px solid #333;
  padding-bottom: 10px;
}

.asset-title {
  flex: 1;
}

.asset-name {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin: 0 0 5px 0;
}

.asset-tag {
  font-size: 14px;
  color: #666;
  font-family: monospace;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
}

.asset-status {
  text-align: right;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
  text-transform: uppercase;
}

.status-active {
  background: #d4edda;
  color: #155724;
}

.status-inactive {
  background: #f8d7da;
  color: #721c24;
}

.status-maintenance {
  background: #fff3cd;
  color: #856404;
}

.status-default {
  background: #e2e3e5;
  color: #383d41;
}

.asset-content {
  display: flex;
  gap: 20px;
}

.asset-photo {
  flex-shrink: 0;
  width: 150px;
  height: 150px;
}

.photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.asset-info {
  flex: 1;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.info-item label {
  font-weight: bold;
  color: #333;
  font-size: 12px;
  text-transform: uppercase;
}

.info-item span {
  font-size: 14px;
  color: #666;
}

/* Sezioni */
.section-title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
  border-bottom: 1px solid #ddd;
  padding-bottom: 5px;
  margin-bottom: 15px;
}

.risk-section,
.custom-fields-section,
.connections-section,
.description-section,
.notes-section,
.contacts-section,
.suppliers-section {
  margin-top: 20px;
}

.risk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.risk-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.risk-item label {
  font-weight: bold;
  color: #333;
}

.risk-score {
  font-size: 18px;
  font-weight: bold;
  padding: 4px 12px;
  border-radius: 20px;
}

.risk-critical {
  background: #dc3545;
  color: white;
}

.risk-high {
  background: #fd7e14;
  color: white;
}

.risk-medium {
  background: #ffc107;
  color: #212529;
}

.risk-low {
  background: #28a745;
  color: white;
}

.risk-minimal {
  background: #6c757d;
  color: white;
}

.custom-fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 10px;
}

.custom-field-item {
  display: flex;
  justify-content: space-between;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.custom-field-item label {
  font-weight: bold;
  color: #333;
}

.connections-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.connection-item {
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid #007bff;
}

.connection-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.connection-type {
  font-weight: bold;
  color: #007bff;
  font-size: 12px;
  text-transform: uppercase;
}

.connection-target {
  color: #333;
}

.description-text,
.notes-text {
  line-height: 1.6;
  color: #333;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #28a745;
  font-size: 13px;
}

.notes-text {
  max-height: 150px;
  overflow: hidden;
}

/* Contatti */
.contacts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 15px;
}

.contact-group {
  margin-bottom: 15px;
}

.contact-group-title {
  font-size: 14px;
  font-weight: bold;
  color: #495057;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.contact-item {
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #007bff;
}

.contact-name {
  font-weight: bold;
  color: #333;
  font-size: 13px;
  margin-bottom: 4px;
}

.contact-details {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
  flex-wrap: wrap;
}

.contact-details span {
  display: inline-block;
}

/* Fornitori */
.suppliers-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.supplier-item {
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #ffc107;
}

.supplier-name {
  font-weight: bold;
  color: #333;
  font-size: 13px;
  margin-bottom: 4px;
}

.supplier-details {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #666;
  flex-wrap: wrap;
}

.supplier-details span {
  display: inline-block;
}

/* Connessioni compatte */
.connections-list-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.connection-item-compact {
  padding: 6px 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #007bff;
  font-size: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
}

.connection-type-compact {
  font-weight: bold;
  color: #007bff;
  text-transform: uppercase;
  font-size: 11px;
}

.connection-target-compact {
  color: #333;
  flex: 1;
}

.qr-section {
  text-align: center;
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.qr-text {
  font-size: 12px;
  color: #666;
  margin-bottom: 10px;
}

.qr-code {
  display: inline-block;
}

.qr-image {
  width: 80px;
  height: 80px;
  border: 1px solid #ddd;
}

/* Stili per stampa */
@media print {
  .asset-card {
    page-break-inside: avoid;
  }
  
  .section-title {
    page-break-after: avoid;
  }
  
  .risk-grid,
  .custom-fields-grid {
    page-break-inside: avoid;
  }
}
</style> 