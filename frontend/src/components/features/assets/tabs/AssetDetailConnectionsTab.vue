<template>
  <div>
    <h2>{{ t('assets.connections.title') }}</h2>
    <Button :label="t('assets.connections.addConnection')" icon="pi pi-plus" class="mb-3" @click="showAddConnectionDialog = true" />
    <AssetConnectionsTable 
      :connections="mappedConnections" 
      @edit-connection="onEditConnection" 
      @delete-connection="onDeleteConnection"
      @create-dependency="onCreateDependency"
    />
    <AssetConnectionGraph :connections="mappedConnections" />
    
    <!-- Dialog per aggiungere connessione -->
    <Dialog v-model:visible="showAddConnectionDialog" :header="t('assets.connections.addConnection')" modal style="width: 400px" :closable="true" :dismissableMask="true" @hide="resetAddConnectionForm">
      <div class="p-fluid">
        <div class="field">
          <label>{{ t('assets.connections.localInterface') }}</label>
          <Dropdown v-model="selectedLocalInterface" :options="localInterfaces" optionLabel="name" optionValue="id" :placeholder="t('common.strings.select')" />
        </div>
        <div class="field">
          <label>{{ t('assets.connections.remoteAsset') }}</label>
          <Dropdown v-model="selectedRemoteAsset" :options="remoteAssets" optionLabel="name" optionValue="id" :placeholder="t('common.strings.select')" />
        </div>
        <div class="field">
          <label>{{ t('assets.connections.remoteInterface') }}</label>
          <Dropdown v-model="selectedRemoteInterface" :options="remoteInterfaces" optionLabel="name" optionValue="id" :placeholder="t('common.strings.select')" :disabled="!selectedRemoteAsset" />
        </div>
        <Button :label="t('common.actions.save')" icon="pi pi-check" class="mt-3" @click="addConnection" :disabled="!selectedLocalInterface || !selectedRemoteAsset || !selectedRemoteInterface" />
      </div>
    </Dialog>

    <!-- Dialog per creare dipendenza da connessione -->
    <Dialog 
      v-model:visible="showCreateDependencyDialog" 
      :header="t('assetDependencies.createDependencyFromConnection')" 
      modal 
      style="width: 600px" 
      :closable="true" 
      :dismissableMask="true"
    >
      <AssetDependencyForm 
        v-if="suggestedDependencyData"
        :assetId="assetId"
        :suggestedData="suggestedDependencyData"
        @submit="handleCreateDependency"
        @cancel="showCreateDependencyDialog = false"
      />
    </Dialog>

    <!-- Dialog per modificare connessione -->
    <Dialog v-model:visible="showEditConnectionDialog" :header="t('assets.connections.editConnection')" modal style="width: 400px" :closable="true" :dismissableMask="true">
      <div class="p-fluid">
        <div class="field">
          <label>{{ t('assets.connections.localInterface') }}</label>
          <Dropdown v-model="editConnectionData.interfaceA.id" :options="localInterfaces" optionLabel="name" optionValue="id" :placeholder="t('common.strings.select')" />
        </div>
        <div class="field">
          <label>{{ t('assets.connections.remoteAsset') }}</label>
          <Dropdown v-model="editConnectionData.assetB.id" :options="remoteAssets" optionLabel="name" optionValue="id" :placeholder="t('common.strings.select')" />
        </div>
        <div class="field">
          <label>{{ t('assets.connections.remoteInterface') }}</label>
          <Dropdown v-model="editConnectionData.interfaceB.id" :options="editRemoteInterfaces" optionLabel="name" optionValue="id" :placeholder="t('common.strings.select')" :disabled="!editConnectionData.assetB.id" />
        </div>
        <Button :label="t('common.actions.save')" icon="pi pi-check" class="mt-3" @click="saveEditConnection" :disabled="!editConnectionData.interfaceA.id || !editConnectionData.assetB.id || !editConnectionData.interfaceB.id" />
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import AssetConnectionsTable from '@/components/tables/AssetConnectionsTable.vue'
import AssetConnectionGraph from '../components/AssetConnectionGraph.vue'
import AssetDependencyForm from './components/AssetDependencyForm.vue'
import api from '@/api/api'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  assetInterfaces: { type: Array, default: () => [] }
})

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()

// Stato
const connections = ref([])
const connectionsNodes = ref([])
const connectionsEdges = ref([])
const showAddConnectionDialog = ref(false)
const showEditConnectionDialog = ref(false)
const selectedLocalInterface = ref(null)
const selectedRemoteAsset = ref(null)
const selectedRemoteInterface = ref(null)
const remoteAssets = ref([])
const editConnectionData = ref({
  interfaceA: { id: null },
  assetB: { id: null },
  interfaceB: { id: null },
  id: null
})
const showCreateDependencyDialog = ref(false)
const suggestedDependencyData = ref(null)

// Computed
const localInterfaces = computed(() => props.assetInterfaces || [])

const remoteInterfaces = computed(() => {
  if (!selectedRemoteAsset.value) return []
  const assetObj = remoteAssets.value.find(a => a.id === selectedRemoteAsset.value)
  if (!assetObj) return []
  if (!selectedLocalInterface.value) return assetObj.interfaces || []
  const localType = localInterfaces.value.find(i => i.id === selectedLocalInterface.value)?.type
  if (!localType) return assetObj.interfaces || []
  // Matching case-insensitive per gestire "Ethernet" vs "ethernet"
  const localTypeLower = String(localType).toLowerCase()
  return (assetObj.interfaces || []).filter(i => {
    if (!i || !i.type) return false
    return String(i.type).toLowerCase() === localTypeLower
  })
})

const editRemoteInterfaces = computed(() => {
  if (!editConnectionData.value?.assetB?.id) return []
  const assetObj = remoteAssets.value.find(a => a.id === editConnectionData.value.assetB.id)
  if (!assetObj) return []
  if (!editConnectionData.value.interfaceA?.id) return assetObj.interfaces || []
  const localType = localInterfaces.value.find(i => i.id === editConnectionData.value.interfaceA.id)?.type
  if (!localType) return assetObj.interfaces || []
  // Matching case-insensitive per gestire "Ethernet" vs "ethernet"
  const localTypeLower = String(localType).toLowerCase()
  return (assetObj.interfaces || []).filter(i => {
    if (!i || !i.type) return false
    return String(i.type).toLowerCase() === localTypeLower
  })
})

const mappedConnections = computed(() =>
  connections.value
    .map(conn => {
      const mapped = {
        id: conn.id,
        dependency_status: conn.dependency_status
      }
      
      if (conn.parent_asset_id === props.assetId) {
        return {
          ...mapped,
          interfaceA: conn.local_interface,
          assetA: conn.parent_asset,
          interfaceB: conn.remote_interface,
          assetB: conn.child_asset
        }
      } else {
        return {
          ...mapped,
          interfaceA: conn.remote_interface,
          assetA: conn.child_asset,
          interfaceB: conn.local_interface,
          assetB: conn.parent_asset
        }
      }
    })
    .sort((a, b) => {
      const nameA = a.interfaceA?.name?.toLowerCase() || ''
      const nameB = b.interfaceA?.name?.toLowerCase() || ''
      return nameA.localeCompare(nameB)
    })
)

// Funzioni
async function fetchConnections() {
  if (!props.assetId) return
  try {
    // Carica connessioni con dependency_status incluso
    const res = await api.get(`/assets/${props.assetId}/connections`, {
      params: { include_dependency_status: true }
    })
    connections.value = res.data || []
    // Popola nodi e archi per il grafo
    const nodesSet = new Set()
    const edgesArr = []
    res.data.forEach(conn => {
      // Gestisci entrambi i formati (con o senza dependency_status)
      const parentAsset = conn.parent_asset || conn.local_asset
      const childAsset = conn.child_asset || conn.remote_asset
      const localInterface = conn.local_interface
      const remoteInterface = conn.remote_interface
      
      // Aggiungi nodi
      if (parentAsset) {
        nodesSet.add(JSON.stringify({ id: parentAsset.id, label: parentAsset.name }))
      }
      if (childAsset) {
        nodesSet.add(JSON.stringify({ id: childAsset.id, label: childAsset.name }))
      }
      // Aggiungi edge
      if (parentAsset && childAsset && localInterface && remoteInterface) {
        edgesArr.push({
          from: parentAsset.id,
          to: childAsset.id,
          label: `${localInterface.name} ↔ ${remoteInterface.name}`,
          color: '#2196f3'
        })
      }
    })
    connectionsNodes.value = Array.from(nodesSet).map(s => JSON.parse(s))
    connectionsEdges.value = edgesArr
  } catch (e) {
    console.error('Error fetching connections:', e)
    console.error('Error response:', e.response?.data)
    toast.add({ 
      severity: 'error', 
      summary: t('common.strings.error'), 
      detail: e.response?.data?.detail || e.message || t('assets.connections.fetchError') 
    })
  }
}

async function fetchRemoteAssets() {
  try {
    // Carica tutti gli asset con interfacce (aumenta il limite per assicurarsi di avere tutti gli asset)
    const res = await api.getAssets({ include_interfaces: true, limit: 1000 })
    
    // La risposta è paginata: { data: [...], total: ..., skip: ..., limit: ... }
    const assetsArray = res.data?.data || res.data || []
    
    if (!Array.isArray(assetsArray)) {
      console.error('fetchRemoteAssets - Invalid response format:', res)
      remoteAssets.value = []
      return
    }
    
    // Normalizza gli ID per il confronto (gestisce sia stringhe che UUID)
    const currentAssetId = String(props.assetId)
    const filtered = assetsArray.filter(a => {
      if (!a || !a.id) return false
      const assetId = String(a.id)
      return assetId !== currentAssetId
    })
    
    remoteAssets.value = filtered
  } catch (e) {
    console.error('Error fetching remote assets:', e)
    console.error('Error response:', e.response?.data)
    remoteAssets.value = []
    toast.add({ 
      severity: 'error', 
      summary: t('common.strings.error'), 
      detail: e.response?.data?.detail || e.message || 'Errore nel caricamento degli asset remoti' 
    })
  }
}

async function addConnection() {
  try {
    await api.createAssetConnection(props.assetId, {
      local_interface_id: selectedLocalInterface.value,
      remote_interface_id: selectedRemoteInterface.value
    })
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.connections.addConnectionSuccess') })
    showAddConnectionDialog.value = false
    resetAddConnectionForm()
    await fetchConnections()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.connections.addConnectionError') })
  }
}

function resetAddConnectionForm() {
  selectedLocalInterface.value = null
  selectedRemoteAsset.value = null
  selectedRemoteInterface.value = null
}

function resetEditConnectionForm() {
  editConnectionData.value = {
    interfaceA: { id: null },
    assetB: { id: null },
    interfaceB: { id: null },
    id: null
  }
}

function onEditConnection(row) {
  editConnectionData.value = {
    interfaceA: { id: row.interfaceA?.id || null },
    assetB: { id: row.assetB?.id || null },
    interfaceB: { id: row.interfaceB?.id || null },
    id: row.id || null
  }
  showEditConnectionDialog.value = true
}

async function onDeleteConnection(row) {
  confirm.require({
    message: t('assets.connections.confirmDelete'),
    header: t('common.strings.confirm'),
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await api.deleteAssetConnection(props.assetId, row.id)
        toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.connections.deleteSuccess') })
        await fetchConnections()
      } catch (e) {
        toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.connections.deleteError') })
      }
    }
  })
}

async function saveEditConnection() {
  try {
    await api.updateAssetConnection(props.assetId, editConnectionData.value.id, {
      local_interface_id: editConnectionData.value.interfaceA.id,
      remote_interface_id: editConnectionData.value.interfaceB.id
    })
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.connections.editSuccess') })
    showEditConnectionDialog.value = false
    resetEditConnectionForm()
    await fetchConnections()
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.connections.editError') })
  }
}

async function onCreateDependency(connectionRow) {
  try {
    // Trova la connessione originale
    const connection = connections.value.find(c => c.id === connectionRow.id)
    if (!connection) return
    
    // Ottieni suggerimento dal backend
    const res = await api.get(`/assets/${props.assetId}/connections/${connection.id}/suggest-dependency`)
    suggestedDependencyData.value = res.data
    showCreateDependencyDialog.value = true
  } catch (e) {
    console.error('Error getting dependency suggestion:', e)
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: t('assetDependencies.errorLoading') 
    })
  }
}

// Lifecycle
onMounted(async () => {
  await fetchConnections()
  await fetchRemoteAssets()
})

watch(() => props.assetId, async (newId, oldId) => {
  if (newId !== oldId) {
    await fetchConnections()
    await fetchRemoteAssets()
  }
})

watch(showAddConnectionDialog, val => {
  if (val) fetchRemoteAssets()
})

async function handleCreateDependency(dependencyData) {
  try {
    await api.createAssetDependency(dependencyData)
    toast.add({ 
      severity: 'success', 
      summary: t('common.messages.success'), 
      detail: t('assetDependencies.dependencyAdded') 
    })
    showCreateDependencyDialog.value = false
    suggestedDependencyData.value = null
    await fetchConnections() // Ricarica per aggiornare i badge
  } catch (e) {
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: e.response?.data?.detail || t('assetDependencies.errorAdding') 
    })
  }
}
</script> 