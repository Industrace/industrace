<template>
  <div class="network-map-page">
    <div class="page-header">
      <h1>{{ $t('networkmap.title') }}</h1>
      <p class="page-description">{{ $t('networkmap.strings.description') }}</p>
    </div>

    <!-- Filtri -->
    <div class="filters-section">
      <Card>
        <template #title>
          <i class="pi pi-filter"></i>
          {{ $t('networkmap.strings.filters') }}
        </template>
        <template #content>
          <div class="filters-grid">
            <div class="filter-item">
              <label>{{ $t('networkmap.strings.filterBySite') }}</label>
              <Dropdown 
                v-model="filters.siteId" 
                :options="sites" 
                optionLabel="name" 
                optionValue="id" 
                :placeholder="$t('networkmap.strings.allSites')"
                @change="applyFilters"
              />
            </div>
            <div class="filter-item">
              <label>{{ $t('networkmap.strings.filterByAssetType') }}</label>
              <Dropdown 
                v-model="filters.assetTypeId" 
                :options="assetTypes" 
                optionLabel="name" 
                optionValue="id" 
                :placeholder="$t('networkmap.strings.allTypes')"
                @change="applyFilters"
              />
            </div>
            <div class="filter-item">
              <label>{{ $t('networkmap.strings.filterByProtocol') }}</label>
              <MultiSelect 
                v-model="filters.protocols" 
                :options="availableProtocols" 
                :placeholder="$t('networkmap.strings.allProtocols')"
                @change="applyFilters"
              />
            </div>
            <div class="filter-item">
              <label>{{ $t('networkmap.strings.showOnlyConnected') }}</label>
              <Checkbox 
                v-model="filters.showOnlyConnected" 
                :binary="true"
                @change="applyFilters"
              />
            </div>
          </div>
          <div class="filters-actions">
            <Button 
              :label="$t('networkmap.strings.clearFilters')" 
              icon="pi pi-times" 
              severity="secondary" 
              @click="clearFilters"
            />
            <Button 
              :label="$t('networkmap.strings.exportMap')" 
              icon="pi pi-download" 
              @click="exportMap"
            />
          </div>
        </template>
      </Card>
    </div>

    <!-- Statistiche -->
    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-number">{{ networkStats.totalAssets }}</div>
          <div class="stat-label">{{ $t('networkmap.strings.totalAssets') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ networkStats.connectedAssets }}</div>
          <div class="stat-label">{{ $t('networkmap.strings.connectedAssets') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ networkStats.totalConnections }}</div>
          <div class="stat-label">{{ $t('networkmap.strings.totalConnections') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-number">{{ networkStats.isolatedAssets }}</div>
          <div class="stat-label">{{ $t('networkmap.strings.isolatedAssets') }}</div>
        </div>
      </div>
    </div>

    <!-- Mappa di rete -->
    <div class="network-map-container">
      <Card>
        <template #title>
          <div class="map-header">
            <span>{{ $t('networkmap.strings.networkTopology') }}</span>
            <div class="map-controls">
              <Button icon="pi pi-plus" size="small" @click="zoomIn" :title="$t('networkmap.strings.zoomIn')" />
              <Button icon="pi pi-minus" size="small" @click="zoomOut" :title="$t('networkmap.strings.zoomOut')" />
              <Button icon="pi pi-refresh" size="small" @click="resetView" :title="$t('networkmap.strings.resetView')" />
              <Button icon="pi pi-arrows-alt" size="small" @click="fitToScreen" :title="$t('networkmap.strings.fitToScreen')" />
              <Button icon="pi pi-sitemap" size="small" @click="togglePhysics" :title="$t('networkmap.strings.togglePhysics')" />
            </div>
          </div>
        </template>
        <template #content>
          <div ref="networkContainer" class="network-container"></div>
          <div v-if="loading" class="loading-overlay">
            <ProgressSpinner />
            <span>{{ $t('networkmap.strings.loading') }}</span>
          </div>
        </template>
      </Card>
    </div>

    <!-- Dialog per dettagli asset -->
    <Dialog 
      v-model:visible="showAssetDetails" 
      :header="selectedAsset?.name || $t('networkmap.strings.assetDetails')" 
      modal 
      style="width: 600px"
    >
      <div v-if="selectedAsset" class="asset-details">
        <div class="detail-row">
          <strong>{{ $t('networkmap.strings.assetType') }}:</strong>
          <span>{{ selectedAsset.asset_type?.name || '-' }}</span>
        </div>
        <div class="detail-row">
          <strong>{{ $t('networkmap.strings.site') }}:</strong>
          <span>{{ selectedAsset.site?.name || '-' }}</span>
        </div>
        <div class="detail-row">
          <strong>{{ $t('networkmap.strings.status') }}:</strong>
          <span>{{ selectedAsset.status?.name || '-' }}</span>
        </div>
        <div class="detail-row">
          <strong>{{ $t('networkmap.strings.riskScore') }}:</strong>
          <span>{{ selectedAsset.risk_score || '-' }}</span>
        </div>
        <div class="detail-row">
          <strong>{{ $t('networkmap.strings.connections') }}:</strong>
          <span>{{ selectedAsset.connectionCount || 0 }}</span>
        </div>
        <div class="detail-actions">
          <Button 
            :label="$t('networkmap.strings.viewDetails')" 
            icon="pi pi-external-link" 
            @click="viewAssetDetails"
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { Network } from 'vis-network/standalone/esm/vis-network'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import MultiSelect from 'primevue/multiselect'
import Checkbox from 'primevue/checkbox'
import Dialog from 'primevue/dialog'
import ProgressSpinner from 'primevue/progressspinner'
import api from '@/api/api'
import { getNetworkMapRiskColor } from '@/composables/useRiskLabels'

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

// Refs
const networkContainer = ref(null)
const loading = ref(false)
const showAssetDetails = ref(false)
const selectedAsset = ref(null)
let network = null

// Dati
const assets = ref([])
const connections = ref([])
const sites = ref([])
const assetTypes = ref([])
const availableProtocols = ref([])

// Filtri
const filters = ref({
  siteId: null,
  assetTypeId: null,
  protocols: [],
  showOnlyConnected: false
})

// Statistiche
const networkStats = computed(() => {
  const totalAssets = assets.value.length
  const connectedAssets = new Set()
  const isolatedAssets = new Set()
  
  connections.value.forEach(conn => {
    if (conn.parent_asset) connectedAssets.add(conn.parent_asset.id)
    if (conn.child_asset) connectedAssets.add(conn.child_asset.id)
  })
  
  assets.value.forEach(asset => {
    if (!connectedAssets.has(asset.id)) {
      isolatedAssets.add(asset.id)
    }
  })
  
  return {
    totalAssets,
    connectedAssets: connectedAssets.size,
    totalConnections: connections.value.length,
    isolatedAssets: isolatedAssets.size
  }
})

// Computed per dati filtrati
const filteredAssets = computed(() => {
  let filtered = assets.value
  
  if (filters.value.siteId) {
    filtered = filtered.filter(asset => asset.site_id === filters.value.siteId)
  }
  
  if (filters.value.assetTypeId) {
    filtered = filtered.filter(asset => asset.asset_type_id === filters.value.assetTypeId)
  }
  
  if (filters.value.protocols.length > 0) {
    filtered = filtered.filter(asset => 
      asset.protocols && asset.protocols.some(protocol => 
        filters.value.protocols.includes(protocol)
      )
    )
  }
  
  if (filters.value.showOnlyConnected) {
    const connectedAssetIds = new Set()
    connections.value.forEach(conn => {
      if (conn.parent_asset) connectedAssetIds.add(conn.parent_asset.id)
      if (conn.child_asset) connectedAssetIds.add(conn.child_asset.id)
    })
    filtered = filtered.filter(asset => connectedAssetIds.has(asset.id))
  }
  
  return filtered
})

const filteredConnections = computed(() => {
  const filteredAssetIds = new Set(filteredAssets.value.map(asset => asset.id))
  
  return connections.value.filter(conn => {
    const parentIncluded = conn.parent_asset && filteredAssetIds.has(conn.parent_asset.id)
    const childIncluded = conn.child_asset && filteredAssetIds.has(conn.child_asset.id)
    return parentIncluded && childIncluded
  })
})

// Funzioni per il grafo
function buildNetworkData() {
  const nodes = []
  const edges = []
  const nodeIds = new Set()
  
  // Aggiungi nodi per gli asset
  filteredAssets.value.forEach(asset => {
    if (!nodeIds.has(asset.id)) {
      nodes.push({
        id: asset.id,
        label: asset.name,
        title: `${asset.name}\n${asset.asset_type?.name || ''}\n${asset.site?.name || ''}`,
        shape: 'box',
        color: getAssetColor(asset),
        font: { bold: true, size: 14 },
        size: 25,
        asset: asset
      })
      nodeIds.add(asset.id)
    }
  })
  
  // Aggiungi archi per le connessioni
  filteredConnections.value.forEach(conn => {
    if (conn.parent_asset && conn.child_asset) {
      edges.push({
        from: conn.parent_asset.id,
        to: conn.child_asset.id,
        label: conn.connection_type || '',
        title: `${conn.parent_asset.name} ↔ ${conn.child_asset.name}\n${conn.connection_type || ''}`,
        color: { color: '#2196f3', width: 2 },
        arrows: 'to',
        smooth: { type: 'dynamic' }
      })
    }
  })
  
  return { nodes, edges }
}

function getAssetColor(asset) {
  if (asset.risk_score !== null && asset.risk_score !== undefined) {
    return getNetworkMapRiskColor(asset.risk_score)
  }
  if (asset.asset_type?.name?.toLowerCase().includes('switch')) return '#4caf50'
  if (asset.asset_type?.name?.toLowerCase().includes('router')) return '#2196f3'
  if (asset.asset_type?.name?.toLowerCase().includes('server')) return '#9c27b0'
  return '#e3eaff'
}

function renderNetwork() {
  if (!networkContainer.value) return
  
  const data = buildNetworkData()
  const options = {
    layout: {
      hierarchical: false,
      improvedLayout: true
    },
    nodes: {
      shape: 'dot',
      size: 20,
      font: { size: 12 },
      borderWidth: 2,
      shadow: true
    },
    edges: {
      width: 2,
      color: { color: '#bbb' },
      smooth: { type: 'dynamic' },
      shadow: true
    },
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -30000,
        springLength: 120,
        springConstant: 0.04
      },
      stabilization: {
        enabled: true,
        iterations: 1000
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      zoomView: true,
      dragView: true,
      selectConnectedEdges: true
    },
    manipulation: {
      enabled: false
    }
  }
  
  if (network) {
    network.destroy()
  }
  
  network = new Network(networkContainer.value, data, options)
  
  // Eventi
  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0]
      const node = data.nodes.find(n => n.id === nodeId)
      if (node && node.asset) {
        selectedAsset.value = node.asset
        showAssetDetails.value = true
      }
    }
  })
  
  // Fit iniziale
  setTimeout(() => {
    if (network) network.fit()
  }, 500)
}

// Controlli del grafo
function zoomIn() {
  if (network) {
    const scale = network.getScale()
    network.moveTo({ scale: scale * 1.2 })
  }
}

function zoomOut() {
  if (network) {
    const scale = network.getScale()
    network.moveTo({ scale: scale / 1.2 })
  }
}

function resetView() {
  if (network) {
    network.fit()
  }
}

function fitToScreen() {
  if (network) {
    network.fit()
  }
}

function togglePhysics() {
  if (network) {
    const physics = network.getOptions().physics
    physics.enabled = !physics.enabled
    network.setOptions({ physics })
  }
}

// Funzioni per i filtri
function applyFilters() {
  renderNetwork()
}

function clearFilters() {
  filters.value = {
    siteId: null,
    assetTypeId: null,
    protocols: [],
    showOnlyConnected: false
  }
  renderNetwork()
}

// Funzioni per l'esportazione
function exportMap() {
  // TODO: Implementare esportazione PNG/SVG
  toast.add({
    severity: 'info',
    summary: $t('networkmap.strings.exportInfo'),
    detail: $t('networkmap.strings.exportNotImplemented'),
    life: 3000
  })
}

// Funzioni per i dettagli
function viewAssetDetails() {
  if (selectedAsset.value) {
    router.push(`/assets/${selectedAsset.value.id}`)
  }
}

// Caricamento dati
async function fetchData() {
  loading.value = true
  try {
    const [assetsRes, connectionsRes, sitesRes, assetTypesRes] = await Promise.all([
      api.getAssetsForNetworkMap(),
      api.getAllConnections(),
      api.getSites(),
      api.getAssetTypes()
    ])
    
    assets.value = assetsRes.data
    connections.value = connectionsRes.data
    sites.value = sitesRes.data
    assetTypes.value = assetTypesRes.data
    
    // Estrai protocolli disponibili
    const protocols = new Set()
    assets.value.forEach(asset => {
      if (asset.protocols) {
        asset.protocols.forEach(protocol => protocols.add(protocol))
      }
    })
    availableProtocols.value = Array.from(protocols).map(p => ({ label: p, value: p }))
    
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: $t('common.messages.error'),
      detail: $t('networkmap.messages.fetchError'),
      life: 5000
    })
  } finally {
    loading.value = false
  }
}

// Watchers
watch([filteredAssets, filteredConnections], () => {
  renderNetwork()
}, { deep: true })

// Lifecycle
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.network-map-page {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.page-header h1 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.page-description {
  color: #64748b;
  margin: 0;
}

.filters-section {
  margin-bottom: 1.5rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-item label {
  font-weight: 500;
  color: #374151;
}

.filters-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.stats-section {
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

.network-map-container {
  margin-bottom: 2rem;
}

.map-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.map-controls {
  display: flex;
  gap: 0.5rem;
}

.network-container {
  width: 100%;
  height: 600px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fafbfc;
  position: relative;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  z-index: 10;
}

.asset-details {
  padding: 1rem 0;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e2e8f0;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-actions {
  margin-top: 1rem;
  text-align: center;
}

@media (max-width: 768px) {
  .filters-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .network-container {
    height: 400px;
  }
  
  .map-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .map-controls {
    justify-content: center;
  }
}
</style> 